# routes/pdf_presentation_converter_routes.py - PDF TO PPTX CONVERTER ROUTES
# Dedicated routes for PDF to PowerPoint conversion
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

# Import PDF to PPTX utilities
from utils.pdf_converters.pdf_presentation_utils import PdfToPptxConverter

# Create PDF to PPTX converter blueprint
pdf_presentation_converter_bp = Blueprint('pdf_presentation_converter', __name__, url_prefix='/convert/pdf-to-pptx')

# Configuration
PDF_EXTENSIONS = {'pdf'}
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

@pdf_presentation_converter_bp.route('/', methods=['GET'])
def pdf_to_pptx_converter():
    """PDF to PowerPoint converter page"""
    try:
        return render_template('pdf_converters/pdf_presentation_converter.html')
    except Exception as e:
        logger.error(f'Error rendering PDF to PPTX converter page: {e}')
        return render_template('errors/500.html'), 500

@pdf_presentation_converter_bp.route('/', methods=['POST'])
@rate_limit(requests_per_minute=10, per_user=False)  # Rate limit for conversions
@validate_file_upload(
    allowed_types=['pdf'],
    max_size_mb=50,
    scan_malware=True
)
def convert_pdf_to_pptx():
    """Handle PDF to PowerPoint conversion requests"""
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
        if not allowed_file(file.filename, PDF_EXTENSIONS):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Only PDF files are allowed.'
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
        temp_dir = tempfile.mkdtemp(prefix='pdf_to_pptx_')
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
            result = convert_pdf_to_pptx_internal(temp_input, temp_dir, request.form)

            if result['success']:
                # Log successful conversion
                logger.info(f'Successful PDF to PPTX conversion: {filename}, IP: {request.remote_addr}')
                
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
        logger.warning(f'Security violation in PDF to PPTX conversion: {sve}, IP: {request.remote_addr}')
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
        logger.error(f'General PDF to PPTX conversion error: {e}, IP: {request.remote_addr}')
        return jsonify({
            'success': False,
            'error': 'Conversion request failed. Please check your request and try again.'
        }), 500

def convert_pdf_to_pptx_internal(input_path, temp_dir, form_data):
    """Convert PDF to PowerPoint internally"""
    try:
        # Get conversion parameters
        conversion_mode = form_data.get('conversion_mode', 'basic')
        ocr_language = form_data.get('ocr_language', 'eng')
        text_detection = form_data.get('text_detection', 'auto')
        preserve_images = form_data.get('preserve_images') == 'on'

        # Validate parameters
        if conversion_mode not in ['basic', 'accurate']:
            conversion_mode = 'basic'
        
        if ocr_language not in ['eng', 'spa', 'fra', 'deu', 'chi_sim', 'jpn']:
            ocr_language = 'eng'
        
        if text_detection not in ['auto', 'strict', 'relaxed']:
            text_detection = 'auto'

        # Initialize converter
        converter = PdfToPptxConverter()
        
        # Set output path
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_filename = f"{base_name}_converted.pptx"
        output_path = os.path.join(temp_dir, output_filename)

        # Perform conversion based on mode
        if conversion_mode == 'basic':
            success = converter.pdf_to_pptx_basic(
                input_path=input_path,
                output_path=output_path
            )
        else:  # accurate mode
            success = converter.pdf_to_pptx_accurate(
                input_path=input_path,
                output_path=output_path,
                ocr_language=ocr_language,
                text_detection=text_detection,
                preserve_images=preserve_images
            )

        if success and os.path.exists(output_path):
            return {
                'success': True,
                'output_path': output_path,
                'filename': output_filename,
                'mimetype': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            }
        else:
            return {
                'success': False,
                'error': 'PDF to PowerPoint conversion failed'
            }

    except Exception as e:
        logger.error(f'PDF to PPTX conversion error: {e}')
        return {
            'success': False,
            'error': f'Conversion error: {str(e)}'
        }

@pdf_presentation_converter_bp.route('/status', methods=['GET'])
def conversion_status():
    """Check conversion status and system health"""
    try:
        converter = PdfToPptxConverter()
        status = {
            'service': 'online',
            'timestamp': datetime.now().isoformat(),
            'features': {
                'pdf_to_pptx_basic': converter.is_pdf_conversion_available(),
                'pdf_to_pptx_accurate': converter.is_ocr_available()
            },
            'limits': {
                'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
                'supported_formats': {
                    'input': list(PDF_EXTENSIONS),
                    'output': ['pptx']
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

@pdf_presentation_converter_bp.errorhandler(413)
def file_too_large(e):
    """Handle file size exceeded errors"""
    return jsonify({
        'success': False,
        'error': f'File size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit'
    }), 413

@pdf_presentation_converter_bp.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@pdf_presentation_converter_bp.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f'Internal server error in PDF to PPTX converter: {e}')
    return render_template('errors/500.html'), 500