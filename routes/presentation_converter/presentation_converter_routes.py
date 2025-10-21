# routes/presentation_converter_routes.py - PRESENTATION CONVERTER ROUTES
# Follows Universal Security Framework and existing project patterns
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

# Import presentation utilities
from utils.presentation_converter.presentation_utils import PresentationConverter

# Create presentation converter blueprint
presentation_converter_bp = Blueprint('presentation_converter', __name__, url_prefix='/convert/presentation')

# Configuration
PPTX_EXTENSIONS = {'pptx', 'ppt'}
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

@presentation_converter_bp.route('/', methods=['GET'])
def presentation_converter():
    """Main presentation converter page"""
    try:
        return render_template('presentation_converter/presentation_converter.html')
    except Exception as e:
        logger.error(f'Error rendering presentation converter page: {e}')
        return render_template('errors/500.html'), 500

@presentation_converter_bp.route('/', methods=['POST'])
@rate_limit(requests_per_minute=10, per_user=False)  # Rate limit for conversions
@validate_file_upload(
    allowed_types=['pptx', 'ppt'],
    max_size_mb=50,
    scan_malware=True
)
def convert_presentation():
    """Handle presentation conversion requests"""
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

        # Validate file type (PPTX/PPT only)
        if not allowed_file(file.filename, PPTX_EXTENSIONS):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(PPTX_EXTENSIONS)}'
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
        temp_dir = tempfile.mkdtemp(prefix='presentation_')
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
                # Note: FileManager.cleanup_old_files requires an instance and works on files by age
                # For immediate temp directory cleanup, use shutil.rmtree directly
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.error(f'Malicious file detected: {filename}, issues: {", ".join(security_issues)}, IP: {request.remote_addr}')
                return jsonify({
                    'success': False,
                    'error': 'File failed security validation.'
                }), 400

            # Process PPTX to PDF conversion
            result = convert_pptx_to_pdf(temp_input, temp_dir, request.form)

            if result['success']:
                # Log successful conversion
                logger.info(f'Successful PPTX to PDF conversion: {filename}, IP: {request.remote_addr}')
                
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
        logger.warning(f'Security violation in presentation conversion: {sve}, IP: {request.remote_addr}')
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
        logger.error(f'General presentation conversion error: {e}, IP: {request.remote_addr}')
        return jsonify({
            'success': False,
            'error': 'Conversion request failed. Please check your request and try again.'
        }), 500

def convert_pptx_to_pdf(input_path, temp_dir, form_data):
    """Convert PowerPoint to PDF"""
    try:
        # Get conversion parameters
        quality = form_data.get('quality', 'high')
        page_range = form_data.get('page_range', 'all')
        custom_range = form_data.get('custom_range', '')

        # Validate parameters
        if quality not in ['high', 'medium', 'low']:
            quality = 'high'
        
        if page_range not in ['all', 'custom']:
            page_range = 'all'

        # Parse custom range if specified
        slide_range = None
        if page_range == 'custom' and custom_range:
            slide_range = parse_page_range(custom_range)
            if not slide_range:
                return {
                    'success': False,
                    'error': 'Invalid page range format. Use format like "1-5, 8, 10-12"'
                }

        # Initialize converter
        converter = PresentationConverter()
        
        # Set output path
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_filename = f"{base_name}_converted.pdf"
        output_path = os.path.join(temp_dir, output_filename)

        # Perform conversion
        success = converter.pptx_to_pdf(
            input_path=input_path,
            output_path=output_path,
            quality=quality,
            slide_range=slide_range
        )

        if success and os.path.exists(output_path):
            return {
                'success': True,
                'output_path': output_path,
                'filename': output_filename,
                'mimetype': 'application/pdf'
            }
        else:
            return {
                'success': False,
                'error': 'PowerPoint to PDF conversion failed'
            }

    except Exception as e:
        logger.error(f'PPTX to PDF conversion error: {e}')
        return {
            'success': False,
            'error': f'Conversion error: {str(e)}'
        }


def parse_page_range(range_string):
    """Parse page range string like "1-5, 8, 10-12" into list of page numbers"""
    try:
        pages = set()
        range_string = sanitize_user_input(range_string.strip())
        
        for part in range_string.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-', 1)
                start = int(start.strip())
                end = int(end.strip())
                if start <= end and start > 0:
                    pages.update(range(start, end + 1))
            else:
                page_num = int(part.strip())
                if page_num > 0:
                    pages.add(page_num)
        
        return sorted(list(pages)) if pages else None
    except (ValueError, AttributeError):
        return None

@presentation_converter_bp.route('/status', methods=['GET'])
def conversion_status():
    """Check conversion status and system health"""
    try:
        converter = PresentationConverter()
        status = {
            'service': 'online',
            'timestamp': datetime.now().isoformat(),
            'features': {
                'pptx_to_pdf': converter.is_pptx_conversion_available()
            },
            'limits': {
                'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
                'supported_formats': {
                    'input': list(PPTX_EXTENSIONS),
                    'output': ['pdf']
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

@presentation_converter_bp.errorhandler(413)
def file_too_large(e):
    """Handle file size exceeded errors"""
    return jsonify({
        'success': False,
        'error': f'File size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit'
    }), 413

@presentation_converter_bp.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@presentation_converter_bp.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f'Internal server error in presentation converter: {e}')
    return render_template('errors/500.html'), 500