# routes/image_converter/document_converter_routes.py - DOCUMENT CONVERTER ROUTES
# Dedicated routes for universal document conversion
from flask import Blueprint, request, render_template, jsonify, current_app, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
import shutil
import tempfile
import time
from datetime import datetime
import zipfile

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

# Import Document conversion utilities
from utils.document_converter.document_converter_utils import DocumentConverter

# Create Document converter blueprint
document_converter_bp = Blueprint('document_converter', __name__, url_prefix='/convert/documents')

# Configuration
DOCUMENT_EXTENSIONS = {
    'docx', 'doc', 'rtf', 'odt', 'txt', 'md', 'html', 'htm', 'epub', 'pdf'
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES = 10
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

@document_converter_bp.route('/', methods=['GET'])
def document_converter():
    """Document converter page"""
    try:
        return render_template('document_converter/document_converter.html')
    except Exception as e:
        logger.error(f'Error rendering document converter page: {e}')
        return render_template('errors/500.html'), 500

@document_converter_bp.route('/', methods=['POST'])
@document_converter_bp.route('', methods=['POST'])  # Handle requests without trailing slash
@rate_limit(requests_per_minute=10, per_user=False)  # Rate limit for conversions
@validate_file_upload(
    allowed_types=['docx', 'doc', 'rtf', 'odt', 'txt', 'md', 'html', 'htm', 'epub', 'pdf'],
    max_size_mb=50,
    scan_malware=True
)
def convert_documents():
    """Handle document conversion requests"""
    try:
        # Enhanced logging of request data
        logger.info(f"Document conversion request from IP: {request.remote_addr}")
        logger.info(f"Form data keys: {list(request.form.keys())}")
        logger.info(f"Files keys: {list(request.files.keys())}")
        
        # Check if files were uploaded
        if 'files' not in request.files:
            logger.warning("No files field in request")
            return jsonify({
                'success': False,
                'error': 'No files uploaded'
            }), 400

        files = request.files.getlist('files')
        logger.info(f"Number of files received: {len(files)}")
        
        if not files or all(file.filename == '' for file in files):
            logger.warning("No valid files found in request")
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400

        # Validate file count
        if len(files) > MAX_FILES:
            return jsonify({
                'success': False,
                'error': f'Maximum {MAX_FILES} files allowed. Please reduce the number of files.'
            }), 400

        # Validate all files
        validated_files = []
        logger.info("Starting file validation process...")
        
        for i, file in enumerate(files):
            logger.info(f"Processing file {i+1}: '{file.filename}'")
            
            if file.filename == '':
                logger.info(f"Skipping empty filename for file {i+1}")
                continue
                
            # Validate file extension
            if not allowed_file(file.filename, DOCUMENT_EXTENSIONS):
                logger.warning(f"Invalid file type rejected: {file.filename}")
                return jsonify({
                    'success': False,
                    'error': f'Invalid file type for {file.filename}. Supported formats: {", ".join(DOCUMENT_EXTENSIONS)}'
                }), 400

            # Enhanced security validation
            raw_filename = file.filename
            try:
                if not validate_filename(raw_filename):
                    logger.warning(f'Invalid filename blocked: {raw_filename}, IP: {request.remote_addr}')
                    return jsonify({
                        'success': False,
                        'error': f'Invalid filename: {raw_filename}. Please use a safe filename.'
                    }), 400
            except Exception as filename_error:
                logger.error(f"Error validating filename {raw_filename}: {filename_error}")
                return jsonify({
                    'success': False,
                    'error': f'Filename validation failed for {raw_filename}'
                }), 400

            # Sanitize filename
            try:
                safe_filename = sanitize_filename(raw_filename)
                filename = secure_filename(safe_filename)
                validated_files.append((file, filename))
                logger.info(f"File {i+1} validated successfully: {filename}")
            except Exception as sanitize_error:
                logger.error(f"Error sanitizing filename {raw_filename}: {sanitize_error}")
                return jsonify({
                    'success': False,
                    'error': f'Filename processing failed for {raw_filename}'
                }), 400

        if not validated_files:
            logger.warning("No validated files found after processing")
            return jsonify({
                'success': False,
                'error': 'No valid files found'
            }), 400
        
        logger.info(f"Successfully validated {len(validated_files)} files")
        
        # Merge option temporarily disabled
        merge_requested = False  # request.form.get('merge_files') == 'on'
        # if merge_requested and len(validated_files) < 2:
        #     logger.warning(f"Merge requested but only {len(validated_files)} file(s) provided")
        #     return jsonify({
        #         'success': False,
        #         'error': 'File merging requires at least 2 files. Please select multiple files or disable the merge option.'
        #     }), 400

        # Create temporary directory for this conversion
        temp_dir = tempfile.mkdtemp(prefix='document_converter_')
        temp_input_files = []

        try:
            # Save and validate uploaded files
            for file, filename in validated_files:
                temp_input = os.path.join(temp_dir, f'input_{filename}')
                file.save(temp_input)
                temp_input_files.append((temp_input, filename))

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
                        'error': f'File {filename} failed security validation.'
                    }), 400

            # Process conversion
            result = convert_documents_internal(temp_input_files, temp_dir, request.form)

            if result['success']:
                # Log successful conversion
                filenames = [f[1] for f in temp_input_files]
                logger.info(f'Successful document conversion: {", ".join(filenames)}, IP: {request.remote_addr}')
                
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
            filenames = [f[1] for f in temp_input_files] if temp_input_files else ['unknown']
            logger.error(f'Conversion processing error: {processing_error}, files: {", ".join(filenames)}')
            return jsonify({
                'success': False,
                'error': 'File processing failed. Please try again.'
            }), 500

    except SecurityViolationError as sve:
        logger.warning(f'Security violation in document conversion: {sve}, IP: {request.remote_addr}')
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
        logger.error(f'General document conversion error: {e}, IP: {request.remote_addr}')
        return jsonify({
            'success': False,
            'error': 'Conversion request failed. Please check your request and try again.'
        }), 500

def convert_documents_internal(input_files, temp_dir, form_data):
    """Convert documents internally"""
    try:
        # Debug logging of form data
        logger.info(f"Form data received: {dict(form_data)}")
        
        # Get conversion parameters
        output_format = form_data.get('output_format', 'docx')
        preserve_formatting = form_data.get('preserve_formatting') == 'on'
        include_images = form_data.get('include_images') == 'on'
        include_tables = form_data.get('include_tables') == 'on'
        include_hyperlinks = form_data.get('include_hyperlinks') == 'on'
        include_metadata = form_data.get('include_metadata') == 'on'
        include_footnotes = form_data.get('include_footnotes') == 'on'
        merge_files = False  # Merge option temporarily disabled
        # merge_files = form_data.get('merge_files') == 'on'
        ocr_scan = form_data.get('ocr_scan') == 'on'
        
        # PDF-specific options
        pdf_compression = form_data.get('pdf_compression', 'medium')
        pdf_password = form_data.get('pdf_password', '')
        pdf_page_size = form_data.get('pdf_page_size', 'A4')
        
        # Text-specific options
        text_encoding = form_data.get('text_encoding', 'utf-8')
        line_endings = form_data.get('line_endings', 'auto')

        # Enhanced debug logging
        logger.info(f"Conversion parameters - Format: '{output_format}', Formatting: {preserve_formatting}, "
                   f"Images: {include_images}, Tables: {include_tables}, Merge: {merge_files}, OCR: {ocr_scan}")
        
        # Validate parameters
        valid_formats = ['pdf', 'docx', 'html', 'markdown', 'rtf', 'odt', 'txt']
        if output_format not in valid_formats:
            return {
                'success': False,
                'error': f'Invalid output format: {output_format}. Supported formats: {", ".join(valid_formats)}'
            }

        # Merge validation temporarily disabled
        # if merge_files and len(input_files) < 2:
        #     logger.warning(f'Merge requested but only {len(input_files)} file(s) provided')
        #     return {
        #         'success': False,
        #         'error': f'File merging requires at least 2 files, but only {len(input_files)} file(s) were provided.'
        #     }

        # Initialize document converter
        converter = DocumentConverter()

        # Check if the conversion is available
        conversion_available = True
        if output_format == 'pdf' and not converter.is_pdf_conversion_available():
            conversion_available = False
        elif output_format == 'docx' and not converter.is_docx_conversion_available():
            conversion_available = False
        elif output_format == 'html' and not converter.is_html_conversion_available():
            conversion_available = False
        elif output_format == 'markdown' and not converter.is_markdown_conversion_available():
            conversion_available = False

        if not conversion_available:
            return {
                'success': False,
                'error': f'Conversion to {output_format.upper()} is not available. Please check server configuration.'
            }

        # Prepare conversion options
        conversion_options = {
            'preserve_formatting': preserve_formatting,
            'include_images': include_images,
            'include_tables': include_tables,
            'include_hyperlinks': include_hyperlinks,
            'include_metadata': include_metadata,
            'include_footnotes': include_footnotes,
            'ocr_scan': ocr_scan,
            'merge_files': merge_files,
            'text_encoding': text_encoding,
            'line_endings': line_endings,
            'pdf_compression': pdf_compression,
            'pdf_password': pdf_password,
            'pdf_page_size': pdf_page_size
        }

        # Perform conversion based on output format and file count
        if len(input_files) == 1 and not merge_files:
            # Single file conversion
            input_path, original_filename = input_files[0]
            output_filename = generate_output_filename(original_filename, output_format)
            output_path = os.path.join(temp_dir, f'output_{output_filename}')
            
            success, error_msg = converter.convert_single_document(
                input_path, output_path, output_format, conversion_options
            )
            
            if success:
                return {
                    'success': True,
                    'output_path': output_path,
                    'filename': output_filename,
                    'mimetype': get_mimetype(output_format)
                }
            else:
                return {
                    'success': False,
                    'error': error_msg or f'Failed to convert to {output_format.upper()}'
                }
        
        else:
            # Multiple files or merge conversion
            if merge_files:
                # Merge all files into one
                merged_filename = f'merged_document.{get_file_extension(output_format)}'
                output_path = os.path.join(temp_dir, f'output_{merged_filename}')
                
                success, error_msg = converter.merge_and_convert_documents(
                    [f[0] for f in input_files], output_path, output_format, conversion_options
                )
                
                if success:
                    return {
                        'success': True,
                        'output_path': output_path,
                        'filename': merged_filename,
                        'mimetype': get_mimetype(output_format)
                    }
                else:
                    return {
                        'success': False,
                        'error': error_msg or f'Failed to merge and convert to {output_format.upper()}'
                    }
            
            else:
                # Convert each file individually and zip the results
                converted_files = []
                conversion_errors = []
                
                for input_path, original_filename in input_files:
                    output_filename = generate_output_filename(original_filename, output_format)
                    output_path = os.path.join(temp_dir, f'output_{output_filename}')
                    
                    success, error_msg = converter.convert_single_document(
                        input_path, output_path, output_format, conversion_options
                    )
                    
                    if success:
                        converted_files.append((output_path, output_filename))
                    else:
                        conversion_errors.append(f'{original_filename}: {error_msg}')
                
                if not converted_files:
                    return {
                        'success': False,
                        'error': f'All conversions failed. Errors: {"; ".join(conversion_errors)}'
                    }
                
                # Create ZIP archive
                zip_filename = f'converted_documents_{output_format}.zip'
                zip_path = os.path.join(temp_dir, zip_filename)
                
                try:
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for file_path, filename in converted_files:
                            zipf.write(file_path, filename)
                    
                    # Log partial failures if any
                    if conversion_errors:
                        logger.warning(f'Partial conversion failures: {"; ".join(conversion_errors)}')
                    
                    return {
                        'success': True,
                        'output_path': zip_path,
                        'filename': zip_filename,
                        'mimetype': 'application/zip'
                    }
                    
                except Exception as zip_error:
                    logger.error(f'Failed to create ZIP archive: {zip_error}')
                    return {
                        'success': False,
                        'error': 'Failed to package converted files'
                    }

    except Exception as conversion_error:
        logger.error(f'Document conversion error: {conversion_error}')
        return {
            'success': False,
            'error': f'Conversion failed: {str(conversion_error)}'
        }

def generate_output_filename(original_filename, output_format):
    """Generate output filename with proper extension"""
    base_name = os.path.splitext(original_filename)[0]
    extension = get_file_extension(output_format)
    return f'{base_name}.{extension}'

def get_file_extension(format_name):
    """Get file extension for format"""
    extension_map = {
        'pdf': 'pdf',
        'docx': 'docx',
        'html': 'html',
        'markdown': 'md',
        'rtf': 'rtf',
        'odt': 'odt',
        'txt': 'txt'
    }
    return extension_map.get(format_name, format_name)

def get_mimetype(format_name):
    """Get MIME type for format"""
    mimetype_map = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'html': 'text/html',
        'markdown': 'text/markdown',
        'rtf': 'application/rtf',
        'odt': 'application/vnd.oasis.opendocument.text',
        'txt': 'text/plain'
    }
    return mimetype_map.get(format_name, 'application/octet-stream')

@document_converter_bp.route('/formats', methods=['GET'])
def get_supported_formats():
    """Get list of supported input and output formats"""
    try:
        converter = DocumentConverter()
        
        supported_formats = {
            'input_formats': list(DOCUMENT_EXTENSIONS),
            'output_formats': {
                'pdf': converter.is_pdf_conversion_available(),
                'docx': converter.is_docx_conversion_available(),
                'html': converter.is_html_conversion_available(),
                'markdown': converter.is_markdown_conversion_available(),
                'rtf': True,  # Always available
                'odt': True,  # Always available
                'txt': True   # Always available
            },
            'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
            'max_files': MAX_FILES
        }
        
        return jsonify({
            'success': True,
            'formats': supported_formats
        })
        
    except Exception as e:
        logger.error(f'Error getting supported formats: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to get supported formats'
        }), 500

@document_converter_bp.route('/preview/<path:filename>', methods=['GET'])
def preview_converted_file(filename):
    """Preview converted file (for supported formats like HTML, TXT, Markdown)"""
    try:
        # This would be implemented for previewing converted files
        # For now, return a simple response
        return jsonify({
            'success': False,
            'error': 'Preview functionality not yet implemented'
        }), 501
        
    except Exception as e:
        logger.error(f'Error previewing file: {e}')
        return jsonify({
            'success': False,
            'error': 'Preview failed'
        }), 500

# Error handlers
@document_converter_bp.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum file size is {MAX_FILE_SIZE // (1024 * 1024)}MB per file.'
    }), 413

@document_converter_bp.errorhandler(415)
def unsupported_media_type(e):
    return jsonify({
        'success': False,
        'error': f'Unsupported file type. Supported formats: {", ".join(DOCUMENT_EXTENSIONS)}'
    }), 415