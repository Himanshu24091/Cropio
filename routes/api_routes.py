# routes/api_routes.py - MIGRATED TO UNIVERSAL SECURITY FRAMEWORK
# Phase 2: API Security with Advanced Protection Against API Attacks & Abuse
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import tempfile
import base64

# UNIVERSAL SECURITY FRAMEWORK IMPORTS - Phase 2 API Security
from security.core.decorators import (
    rate_limit, validate_file_upload, require_authentication
)
from security.core.validators import validate_content, validate_user_input, validate_filename
from security.core.sanitizers import sanitize_filename, sanitize_user_input
from security.core.exceptions import (
    SecurityViolationError, MalwareDetectedError, InvalidFileTypeError,
    FileSizeExceededError, RateLimitExceededError
)

# Import the HEIC processor utility
from utils.image.heic_processor import HEICProcessor

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Configuration
ALLOWED_EXTENSIONS = {'heic', 'heif', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    """Check if file has allowed extension with enhanced security"""
    # NEW: Enhanced filename validation
    if not filename or not validate_filename(filename):
        return False
    
    # NEW: Sanitize filename first
    safe_filename = sanitize_filename(filename)
    
    return '.' in safe_filename and \
           safe_filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_bp.route('/heic-info', methods=['POST'])
# UNIVERSAL SECURITY FRAMEWORK - Phase 2 API Security Implementation
@rate_limit(requests_per_minute=30, per_user=False)  # NEW: API rate limiting
@validate_file_upload(  # NEW: Comprehensive file validation
    allowed_types=['heic', 'heif', 'jpg', 'jpeg', 'png'],
    max_size_mb=50,
    scan_malware=True
)
def heic_info():
    """API endpoint for getting HEIC file information"""
    try:
        # Check if HEIC support is available
        if not HEICProcessor.is_heic_supported():
            return jsonify({
                'success': False,
                'error': 'HEIC support is not available. Please install pillow-heif library.'
            }), 400

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

        # Validate file
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # NEW: Enhanced security validation for file handling
        raw_filename = file.filename
        
        # NEW: Additional filename validation
        if not validate_filename(raw_filename):
            current_app.logger.warning(
                f'Invalid filename blocked in API: {raw_filename}, IP: {request.remote_addr}'
            )
            return jsonify({
                'success': False,
                'error': 'Invalid filename. Please use a safe filename.'
            }), 400
        
        # NEW: Sanitize filename with security framework
        safe_filename = sanitize_filename(raw_filename)
        filename = secure_filename(safe_filename)
        
        # Save file temporarily with secure name
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}')
        file.save(temp_input.name)
        temp_input.close()
        
        # NEW: Deep file content validation
        try:
            with open(temp_input.name, 'rb') as f:
                file_content = f.read()
            
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
            is_safe, security_issues = validate_content(file_content, file_ext)
            
            if not is_safe:
                # Remove dangerous file immediately
                os.unlink(temp_input.name)
                current_app.logger.error(
                    f'Malicious file detected in API: {filename}, '
                    f'issues: {", ".join(security_issues)}, IP: {request.remote_addr}'
                )
                return jsonify({
                    'success': False, 
                    'error': 'File failed security validation.'
                }), 400
        except Exception as validation_error:
            # Remove file if validation fails
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            current_app.logger.error(
                f'API file validation error: {validation_error}, file: {filename}'
            )
            return jsonify({
                'success': False,
                'error': 'File validation failed. Please try again.'
            }), 400

        try:
            # Get file info
            processor = HEICProcessor()
            file_info = processor.get_heic_info(temp_input.name)
            
            # Add file size and format info
            file_info['size'] = os.path.getsize(temp_input.name)
            file_info['dimensions'] = f"{file_info['width']} × {file_info['height']}"
            
            # Clean up temp file
            os.unlink(temp_input.name)
            
            # NEW: Security logging for successful API operation
            current_app.logger.info(
                f'HEIC info API success: {filename}, size: {file_info["size"]} bytes, '
                f'dimensions: {file_info["dimensions"]}, IP: {request.remote_addr}'
            )
            
            return jsonify({
                'success': True,
                'info': file_info
            })
            
        except Exception as e:
            # NEW: Enhanced error handling with security logging
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            
            current_app.logger.error(
                f'HEIC info API processing error: {e}, file: {filename}, '
                f'IP: {request.remote_addr}'
            )
            
            return jsonify({
                'success': False,
                'error': 'File processing failed. Please try again.'
            }), 500
            
    except Exception as e:
        # NEW: Enhanced general error handling
        current_app.logger.error(
            f'HEIC info API general error: {e}, IP: {request.remote_addr}'
        )
        return jsonify({
            'success': False,
            'error': 'API request failed. Please check your request and try again.'
        }), 500

@api_bp.route('/heic-convert', methods=['POST'])
# UNIVERSAL SECURITY FRAMEWORK - Enhanced API Security for HEIC Conversion
@rate_limit(requests_per_minute=20, per_user=False)  # NEW: Stricter rate limit for conversion
@validate_file_upload(  # NEW: Comprehensive file validation for conversion
    allowed_types=['heic', 'heif', 'jpg', 'jpeg', 'png'],
    max_size_mb=50,
    scan_malware=True
)
def heic_convert():
    """API endpoint for HEIC conversion"""
    try:
        # Check if HEIC support is available
        if not HEICProcessor.is_heic_supported():
            return jsonify({
                'success': False,
                'error': 'HEIC support is not available. Please install pillow-heif library.'
            }), 400

        # NEW: Enhanced parameter validation and sanitization
        raw_conversion_type = request.form.get('conversion_type', 'heic_to_jpg')
        raw_quality = request.form.get('quality', '95')
        raw_output_format = request.form.get('output_format', 'jpeg')
        raw_preserve_metadata = request.form.get('preserve_metadata', 'false')
        
        # NEW: Validate and sanitize parameters
        conversion_valid, conversion_errors = validate_user_input(raw_conversion_type, 'general')
        if not conversion_valid:
            current_app.logger.warning(
                f'Invalid conversion type in API: {raw_conversion_type}, IP: {request.remote_addr}'
            )
            return jsonify({
                'success': False,
                'error': f'Invalid conversion type: {", ".join(conversion_errors)}'
            }), 400
        
        format_valid, format_errors = validate_user_input(raw_output_format, 'general')
        if not format_valid:
            current_app.logger.warning(
                f'Invalid output format in API: {raw_output_format}, IP: {request.remote_addr}'
            )
            return jsonify({
                'success': False,
                'error': f'Invalid output format: {", ".join(format_errors)}'
            }), 400
        
        # NEW: Sanitize parameters
        conversion_type = sanitize_user_input(raw_conversion_type)
        output_format = sanitize_user_input(raw_output_format)
        
        # NEW: Safe quality parameter handling
        try:
            quality = int(raw_quality)
        except (ValueError, TypeError):
            current_app.logger.warning(
                f'Invalid quality parameter in API: {raw_quality}, IP: {request.remote_addr}'
            )
            return jsonify({
                'success': False,
                'error': 'Invalid quality parameter. Must be a number.'
            }), 400
        
        preserve_metadata = raw_preserve_metadata.lower() == 'true'

        # Validate quality
        if not 50 <= quality <= 100:
            return jsonify({
                'success': False,
                'error': 'Quality must be between 50 and 100'
            }), 400

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

        # Validate file
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}')
        file.save(temp_input.name)
        temp_input.close()

        # Check file size
        if os.path.getsize(temp_input.name) > MAX_FILE_SIZE:
            os.unlink(temp_input.name)
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB'
            }), 400

        try:
            # Initialize processor
            processor = HEICProcessor()
            input_size = os.path.getsize(temp_input.name)
            
            # Convert file based on type
            if conversion_type == 'heic_to_jpg':
                if output_format.lower() == 'png':
                    output_path = processor.convert_heic_with_metadata(temp_input.name, 'PNG', quality)
                else:
                    output_path = processor.heic_to_jpg(temp_input.name, quality)
                conversion_desc = 'HEIC → JPG'
            elif conversion_type == 'jpg_to_heic':
                output_path = processor.jpg_to_heic(temp_input.name, quality)
                conversion_desc = 'JPG → HEIC'
            else:
                raise ValueError(f'Invalid conversion type: {conversion_type}')

            # Clean up temp input file
            os.unlink(temp_input.name)

            # Get output file info
            output_filename = os.path.basename(output_path)
            output_size = os.path.getsize(output_path)
            
            # Calculate compression ratio
            compression_ratio = f"{((input_size - output_size) / input_size * 100):.1f}%" if input_size > 0 else "N/A"
            
            return jsonify({
                'success': True,
                'message': f'Successfully converted {filename}',
                'download_url': f'/heic-jpg/download/{output_filename}',
                'stats': {
                    'output_format': output_format.upper(),
                    'converted_size': f"{output_size / (1024*1024):.2f} MB",
                    'processing_time': '< 1s',  # Would be calculated in real implementation
                    'compression_ratio': compression_ratio
                },
                'converted_info': {
                    'filename': output_filename,
                    'size': output_size
                }
            })

        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_input.name):
                try:
                    os.unlink(temp_input.name)
                except:
                    pass

            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/preview-converted/<filename>')
# UNIVERSAL SECURITY FRAMEWORK - Enhanced API Security for File Preview
@rate_limit(requests_per_minute=60, per_user=False)  # NEW: Rate limiting for preview requests
def preview_converted(filename):
    """API endpoint for previewing converted files"""
    try:
        # NEW: Enhanced filename validation and sanitization
        if not filename or not validate_filename(filename):
            current_app.logger.warning(
                f'Invalid filename in preview API: {filename}, IP: {request.remote_addr}'
            )
            return jsonify({
                'success': False, 
                'error': 'Invalid filename.'
            }), 400
        
        # NEW: Sanitize filename with security framework
        safe_filename = sanitize_filename(filename)
        filename = secure_filename(safe_filename)
        
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, filename)
        
        # NEW: Path traversal prevention
        real_upload_folder = os.path.realpath(upload_folder)
        real_file_path = os.path.realpath(file_path)
        
        if not real_file_path.startswith(real_upload_folder):
            current_app.logger.error(
                f'Path traversal attempt blocked in preview API: {filename}, IP: {request.remote_addr}'
            )
            return jsonify({
                'success': False, 
                'error': 'Access denied.'
            }), 403
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Check if it's a directly previewable image file
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            # Return base64 encoded image for preview
            with open(file_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Get file extension for mime type
            ext = filename.lower().split('.')[-1]
            mime_type = f'image/{ext}' if ext in ['jpg', 'jpeg'] else f'image/{ext}'
            
            return jsonify({
                'success': True,
                'preview': f'data:{mime_type};base64,{image_data}',
                'format': ext.upper()
            })
        
        # Handle HEIC files by generating a JPG preview
        elif filename.lower().endswith(('.heic', '.heif')):
            try:
                # Check if HEIC support is available
                if not HEICProcessor.is_heic_supported():
                    return jsonify({
                        'success': False,
                        'error': 'HEIC preview not supported - pillow-heif not installed'
                    }), 400
                
                # Generate a JPG preview of the HEIC file
                processor = HEICProcessor()
                preview_path = processor.generate_preview(file_path)
                
                # Return the generated preview as base64
                with open(preview_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                # Clean up the temporary preview file
                try:
                    os.unlink(preview_path)
                except:
                    pass
                
                return jsonify({
                    'success': True,
                    'preview': f'data:image/jpeg;base64,{image_data}',
                    'format': 'HEIC'
                })
                
            except Exception as heic_error:
                return jsonify({
                    'success': False,
                    'error': f'Failed to generate HEIC preview: {str(heic_error)}'
                }), 500
        
        else:
            return jsonify({
                'success': False, 
                'error': 'File type not previewable'
            }), 400
            
    except Exception as e:
        # NEW: Enhanced error handling with security logging
        current_app.logger.error(
            f'Preview API general error: {e}, filename: {filename}, IP: {request.remote_addr}'
        )
        return jsonify({
            'success': False,
            'error': 'Preview request failed. Please try again.'
        }), 500


# UNIVERSAL SECURITY FRAMEWORK - Error Handlers for API Routes

@api_bp.errorhandler(RateLimitExceededError)
def handle_api_rate_limit_exceeded(e):
    """Handle rate limit exceeded for API routes"""
    current_app.logger.warning(
        f'API rate limit exceeded: IP={request.remote_addr}, '
        f'path={request.path}, error={str(e)}'
    )
    return jsonify({
        'success': False,
        'error': 'Too many requests. Please slow down.',
        'retry_after': 60
    }), 429


@api_bp.errorhandler(MalwareDetectedError)
def handle_api_malware_detected(e):
    """Handle malware detection in API uploads"""
    current_app.logger.error(
        f'Malware detected in API upload: IP={request.remote_addr}, '
        f'path={request.path}, error={str(e)}'
    )
    return jsonify({
        'success': False,
        'error': 'Security threat detected in uploaded file.'
    }), 403


@api_bp.errorhandler(InvalidFileTypeError)
def handle_api_invalid_file_type(e):
    """Handle invalid file type errors for API routes"""
    current_app.logger.warning(
        f'Invalid file type in API: IP={request.remote_addr}, '
        f'path={request.path}, error={str(e)}'
    )
    return jsonify({
        'success': False,
        'error': 'Invalid file type. Please upload a supported file.'
    }), 400


@api_bp.errorhandler(FileSizeExceededError)
def handle_api_file_size_exceeded(e):
    """Handle file size exceeded errors for API routes"""
    current_app.logger.warning(
        f'File size limit exceeded in API: IP={request.remote_addr}, '
        f'path={request.path}, error={str(e)}'
    )
    return jsonify({
        'success': False,
        'error': 'File too large. Please use a smaller file.'
    }), 413


@api_bp.errorhandler(SecurityViolationError)
def handle_api_security_violation(e):
    """Handle general security violations for API routes"""
    current_app.logger.error(
        f'Security violation in API: IP={request.remote_addr}, '
        f'path={request.path}, violation={str(e)}'
    )
    return jsonify({
        'success': False,
        'error': 'Security violation detected. Request blocked.'
    }), 403


# UNIVERSAL SECURITY FRAMEWORK - API Request Monitoring

@api_bp.after_request
def log_api_security_events(response):
    """Log security-relevant events for API routes"""
    
    # Log suspicious response codes
    if response.status_code >= 400:
        current_app.logger.warning(
            f'API security event: {request.method} {request.path} - '
            f'Status: {response.status_code}, IP: {request.remote_addr}, '
            f'User-Agent: {request.headers.get("User-Agent", "Unknown")}'
        )
    
    # Log successful API requests
    elif response.status_code == 200 and request.method == 'POST':
        current_app.logger.info(
            f'API request success: {request.method} {request.path} - '
            f'Status: {response.status_code}, IP: {request.remote_addr}'
        )
    
    # Monitor for large file uploads in API
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            try:
                file_size = len(file.read()) if hasattr(file, 'read') else 0
                file.seek(0)  # Reset file pointer
                
                # Log large API file uploads
                if file_size > 30 * 1024 * 1024:  # 30MB
                    current_app.logger.info(
                        f'Large API file upload: {file.filename}, '
                        f'size: {file_size} bytes, IP: {request.remote_addr}'
                    )
            except:
                pass  # Ignore file reading errors in monitoring
    
    # Monitor API usage patterns
    if request.path.startswith('/api/'):
        endpoint = request.path.replace('/api/', '')
        if response.status_code < 400:
            current_app.logger.debug(
                f'API usage: {endpoint}, IP: {request.remote_addr}, '
                f'Response: {response.status_code}'
            )
    
    return response
