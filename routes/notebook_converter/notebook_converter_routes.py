# routes/notebook_converter/notebook_converter_routes.py - NOTEBOOK CONVERTER ROUTES
# Dedicated routes for Jupyter notebook conversion
from flask import Blueprint, request, render_template, jsonify, current_app, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
import shutil
import tempfile
import time
from datetime import datetime

# Universal Security Framework Imports
from security.core.decorators import (
    rate_limit, validate_file_upload, require_authentication
)
from security.core.validators import validate_content, validate_user_input, validate_filename
from security.core.sanitizers import sanitize_filename, sanitize_user_input
from security.core.exceptions import (
    SecurityViolationError, MalwareDetectedError, InvalidFileTypeError,
    FileSizeExceededError, RateLimitExceededError
)

# Core utilities
from core.file_manager import FileManager
from core.logging_config import setup_logging

# Import Notebook conversion utilities
from utils.notebook_converter.notebook_utils import NotebookConverter

# Create Notebook converter blueprint
notebook_converter_bp = Blueprint('notebook_converter', __name__, url_prefix='/convert/notebook')

# Configuration
NOTEBOOK_EXTENSIONS = {'ipynb'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
TEMP_CLEANUP_DELAY = 3600  # 1 hour

# Initialize logging
import logging
logger = logging.getLogger(__name__)

def allowed_file(filename, allowed_extensions):
    """Check if file has allowed extension with enhanced security"""
    if not filename or not validate_filename(filename):
        return False
    
    safe_filename = sanitize_filename(filename)
    return '.' in safe_filename and \
           safe_filename.rsplit('.', 1)[1].lower() in allowed_extensions

@notebook_converter_bp.route('/', methods=['GET'])
def notebook_converter():
    """Notebook converter page"""
    try:
        return render_template('notebook_converter/notebook_converter.html')
    except Exception as e:
        logger.error(f'Error rendering notebook converter page: {e}')
        return render_template('errors/500.html'), 500

@notebook_converter_bp.route('/', methods=['POST'])
@rate_limit(requests_per_minute=10, per_user=False)  # Rate limit for conversions
@validate_file_upload(
    allowed_types=['ipynb'],
    max_size_mb=50,
    scan_malware=True
)
def convert_notebook():
    """Handle notebook conversion requests"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Validate file extension
        if not allowed_file(file.filename, NOTEBOOK_EXTENSIONS):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Only Jupyter notebook (.ipynb) files are allowed.'
            }), 400

        # Enhanced security validation
        raw_filename = file.filename
        if not validate_filename(raw_filename):
            logger.warning(f'Invalid filename blocked: {raw_filename}, IP: {request.remote_addr}')
            return jsonify({
                'success': False,
                'error': 'Invalid filename. Please use a safe filename.'
            }), 400

        # Sanitize filename
        safe_filename = sanitize_filename(raw_filename)
        filename = secure_filename(safe_filename)

        # Create temporary directory for this conversion
        temp_dir = tempfile.mkdtemp(prefix='notebook_converter_')
        temp_input = os.path.join(temp_dir, f'input_{filename}')

        try:
            # Save uploaded file
            file.save(temp_input)

            # Deep file content validation
            with open(temp_input, 'rb') as f:
                file_content = f.read()
            
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
            is_safe, security_issues = validate_content(file_content, file_ext)
            
            if not is_safe:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.error(f'Malicious file detected: {filename}, issues: {", ".join(security_issues)}, IP: {request.remote_addr}')
                return jsonify({
                    'success': False,
                    'error': 'File failed security validation.'
                }), 400

            # Process conversion
            result = convert_notebook_internal(temp_input, temp_dir, request.form)

            if result['success']:
                # Log successful conversion
                logger.info(f'Successful notebook conversion: {filename}, IP: {request.remote_addr}')
                
                # Send file and schedule cleanup
                def remove_temp_files():
                    time.sleep(TEMP_CLEANUP_DELAY)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                
                # Note: In production, use a proper task queue like Celery for cleanup
                import threading
                cleanup_thread = threading.Thread(target=remove_temp_files)
                cleanup_thread.daemon = True
                cleanup_thread.start()
                
                return send_file(
                    result['output_path'],
                    as_attachment=True,
                    download_name=result['filename'],
                    mimetype=result['mimetype']
                )
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)
                return jsonify({
                    'success': False,
                    'error': result['error']
                }), 500

        except Exception as processing_error:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error(f'Conversion processing error: {processing_error}, file: {filename}')
            return jsonify({
                'success': False,
                'error': 'File processing failed. Please try again.'
            }), 500

    except SecurityViolationError as sve:
        logger.warning(f'Security violation in notebook conversion: {sve}, IP: {request.remote_addr}')
        return jsonify({
            'success': False,
            'error': 'Security validation failed'
        }), 400
    except RateLimitExceededError:
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded. Please wait before trying again.'
        }), 429
    except Exception as e:
        logger.error(f'General notebook conversion error: {e}, IP: {request.remote_addr}')
        return jsonify({
            'success': False,
            'error': 'Conversion request failed. Please check your request and try again.'
        }), 500

def convert_notebook_internal(input_path, temp_dir, form_data):
    """Convert notebook internally"""
    try:
        # Debug logging of form data
        logger.info(f"Form data received: {dict(form_data)}")
        
        # Get conversion parameters
        output_format = form_data.get('output_format', 'html')
        include_code_cells = form_data.get('include_code_cells') == 'on'
        include_outputs = form_data.get('include_outputs') == 'on'
        include_metadata = form_data.get('include_metadata') == 'on'
        include_images = form_data.get('include_images') == 'on'

        # Enhanced debug logging
        logger.info(f"Raw form data received: {dict(form_data)}")
        logger.info(f"Parsed parameters - Format: '{output_format}', Code: {include_code_cells}, Outputs: {include_outputs}, Metadata: {include_metadata}, Images: {include_images}")
        
        # Validate parameters
        if output_format not in ['pdf', 'html', 'docx', 'markdown']:
            logger.warning(f"Invalid output format '{output_format}', defaulting to PDF")
            output_format = 'pdf'

        # Initialize converter
        converter = NotebookConverter()
        
        # Check if the requested format is available
        format_availability = {
            'pdf': converter.is_pdf_conversion_available(),
            'html': converter.is_html_conversion_available(), 
            'docx': converter.is_docx_conversion_available(),
            'markdown': converter.is_markdown_conversion_available()
        }
        
        if not format_availability[output_format]:
            logger.error(f"{output_format.upper()} conversion not available - dependencies missing")
            return {
                'success': False,
                'error': f'{output_format.upper()} conversion is not available due to missing dependencies'
            }
        
        # Set output path
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        
        # Set appropriate file extension based on format
        extensions = {
            'pdf': '.pdf',
            'html': '.html',
            'docx': '.docx',
            'markdown': '.md'
        }
        
        output_filename = f"{base_name}_converted{extensions[output_format]}"
        output_path = os.path.join(temp_dir, output_filename)

        # Prepare conversion options
        conversion_options = {
            'include_code_cells': include_code_cells,
            'include_outputs': include_outputs,
            'include_metadata': include_metadata,
            'include_images': include_images
        }

        # Perform conversion based on output format
        success = False
        
        if output_format == 'pdf':
            success = converter.notebook_to_pdf(
                input_path=input_path,
                output_path=output_path,
                **conversion_options
            )
        elif output_format == 'html':
            success = converter.notebook_to_html(
                input_path=input_path,
                output_path=output_path,
                **conversion_options
            )
        elif output_format == 'docx':
            success = converter.notebook_to_docx(
                input_path=input_path,
                output_path=output_path,
                **conversion_options
            )
        elif output_format == 'markdown':
            success = converter.notebook_to_markdown(
                input_path=input_path,
                output_path=output_path,
                **conversion_options
            )

        if success and os.path.exists(output_path):
            # Determine MIME type based on format
            mime_types = {
                'pdf': 'application/pdf',
                'html': 'text/html',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'markdown': 'text/markdown'
            }
            
            return {
                'success': True,
                'output_path': output_path,
                'filename': output_filename,
                'mimetype': mime_types.get(output_format, 'application/octet-stream')
            }
        else:
            return {
                'success': False,
                'error': f'Notebook to {output_format.upper()} conversion failed'
            }

    except Exception as e:
        logger.error(f'Notebook conversion error: {e}')
        return {
            'success': False,
            'error': f'Conversion error: {str(e)}'
        }

@notebook_converter_bp.route('/status', methods=['GET'])
def conversion_status():
    """Check conversion status and system health"""
    try:
        converter = NotebookConverter()
        status = {
            'service': 'online',
            'timestamp': datetime.now().isoformat(),
            'features': {
                'notebook_to_pdf': converter.is_pdf_conversion_available(),
                'notebook_to_html': converter.is_html_conversion_available(),
                'notebook_to_docx': converter.is_docx_conversion_available(),
                'notebook_to_markdown': converter.is_markdown_conversion_available()
            },
            'limits': {
                'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
                'supported_formats': {
                    'input': list(NOTEBOOK_EXTENSIONS),
                    'output': ['pdf', 'html', 'docx', 'markdown']
                }
            }
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f'Status check error: {e}')
        return jsonify({
            'service': 'error',
            'error': 'Status check failed'
        }), 500

@notebook_converter_bp.route('/formats', methods=['GET'])
def supported_formats():
    """Get list of supported input and output formats"""
    try:
        return jsonify({
            'input_formats': {
                'ipynb': {
                    'name': 'Jupyter Notebook',
                    'description': 'Interactive notebook with code, text, and outputs',
                    'mime_type': 'application/x-ipynb+json'
                }
            },
            'output_formats': {
                'pdf': {
                    'name': 'PDF Document',
                    'description': 'Portable Document Format for sharing and printing',
                    'mime_type': 'application/pdf'
                },
                'html': {
                    'name': 'HTML Document',
                    'description': 'Web-ready HTML format for online publishing',
                    'mime_type': 'text/html'
                },
                'docx': {
                    'name': 'Word Document',
                    'description': 'Microsoft Word format for editing',
                    'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                },
                'markdown': {
                    'name': 'Markdown',
                    'description': 'Plain text format for documentation',
                    'mime_type': 'text/markdown'
                }
            }
        })
    except Exception as e:
        logger.error(f'Formats endpoint error: {e}')
        return jsonify({
            'error': 'Failed to retrieve format information'
        }), 500

@notebook_converter_bp.errorhandler(413)
def file_too_large(e):
    """Handle file size exceeded errors"""
    return jsonify({
        'success': False,
        'error': f'File size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit'
    }), 413

@notebook_converter_bp.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@notebook_converter_bp.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f'Internal server error in notebook converter: {e}')
    return render_template('errors/500.html'), 500