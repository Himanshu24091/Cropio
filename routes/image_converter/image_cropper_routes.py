# routes/image_converter/image-cropper.py - IMAGE CROPPER ROUTES
# Dedicated routes for image cropping functionality
from flask import Blueprint, request, render_template, jsonify, current_app, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
import shutil
import tempfile
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple

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

# Import Image cropping utilities
from utils.image_converter.image_cropper_utils import ImageCropper

# Create Image cropper blueprint
image_cropper_bp = Blueprint('image_cropper', __name__, url_prefix='/crop/images')

# Configuration
IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'webp', 'gif'}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB per image
MAX_FILES = 10  # Maximum 10 images per request
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

@image_cropper_bp.route('/', methods=['GET'])
def image_cropper():
    """Image cropper page"""
    try:
        return render_template('image_converter/image_cropper.html')
    except Exception as e:
        logger.error(f'Error rendering image cropper page: {e}')
        return render_template('errors/500.html'), 500

@image_cropper_bp.route('/', methods=['POST'])
@rate_limit(requests_per_minute=15, per_user=False)  # Rate limit for cropping
@validate_file_upload(
    allowed_types=['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'webp', 'gif'],
    max_size_mb=25,
    scan_malware=True
)
def crop_images():
    """Handle image cropping requests"""
    try:
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files uploaded'
            }), 400

        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400

        # Limit number of files
        if len(files) > MAX_FILES:
            return jsonify({
                'success': False,
                'error': f'Too many files. Maximum {MAX_FILES} images allowed.'
            }), 400

        # Validate all files first
        validated_files = []
        for file in files:
            if not file or file.filename == '':
                continue
                
            # Validate file extension
            if not allowed_file(file.filename, IMAGE_EXTENSIONS):
                return jsonify({
                    'success': False,
                    'error': f'Invalid file type: {file.filename}. Only image files are allowed.'
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
            
            validated_files.append((file, filename))

        if not validated_files:
            return jsonify({
                'success': False,
                'error': 'No valid image files found'
            }), 400

        # Create temporary directory for this cropping session
        temp_dir = tempfile.mkdtemp(prefix='image_cropper_')
        temp_files = []

        try:
            # Save and validate all uploaded files
            for file, filename in validated_files:
                temp_input = os.path.join(temp_dir, f'input_{filename}')
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
                
                temp_files.append((temp_input, filename))

            # Process cropping
            result = crop_images_internal(temp_files, temp_dir, request.form)

            if result['success']:
                # Log successful cropping
                logger.info(f'Successful image cropping: {len(temp_files)} images, IP: {request.remote_addr}')
                
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
            logger.error(f'Cropping processing error: {processing_error}, files: {[f[1] for f in validated_files]}')
            return jsonify({
                'success': False,
                'error': 'File processing failed. Please try again.'
            }), 500

    except SecurityViolationError as sve:
        logger.warning(f'Security violation in image cropping: {sve}, IP: {request.remote_addr}')
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
        logger.error(f'General image cropping error: {e}, IP: {request.remote_addr}')
        return jsonify({
            'success': False,
            'error': 'Cropping request failed. Please check your request and try again.'
        }), 500

def crop_images_internal(temp_files: List[Tuple[str, str]], temp_dir: str, form_data) -> Dict:
    """Crop images internally"""
    try:
        # Debug logging of form data
        logger.info(f"Crop form data received: {dict(form_data)}")
        
        # Get cropping parameters
        crop_mode = form_data.get('crop_mode', 'free')
        aspect_ratio = form_data.get('aspect_ratio', '1:1')
        crop_shape = form_data.get('crop_shape', 'rectangle')
        custom_width = form_data.get('custom_width')
        custom_height = form_data.get('custom_height')
        maintain_aspect = form_data.get('maintain_aspect') == 'on'
        center_crop = form_data.get('center_crop') == 'on'
        output_format = form_data.get('output_format', 'jpg')
        quality = int(form_data.get('quality', 85))
        crop_data_json = form_data.get('crop_data')
        
        # Parse crop data from frontend if available
        crop_data = None
        if crop_data_json:
            try:
                crop_data = json.loads(crop_data_json)
            except json.JSONDecodeError:
                logger.warning("Invalid crop data JSON")
        
        # Enhanced debug logging
        logger.info(f"Parsed parameters - Mode: '{crop_mode}', Aspect: '{aspect_ratio}', Shape: '{crop_shape}'")
        logger.info(f"Custom dimensions: {custom_width}x{custom_height}, Quality: {quality}%")
        logger.info(f"Options - Maintain aspect: {maintain_aspect}, Center crop: {center_crop}")
        if crop_data:
            logger.info(f"Crop data: {crop_data}")
        
        # Validate parameters
        if crop_mode not in ['free', 'aspect', 'shape']:
            logger.warning(f"Invalid crop mode '{crop_mode}', defaulting to free")
            crop_mode = 'free'
            
        if output_format not in ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff', 'gif']:
            logger.warning(f"Invalid output format '{output_format}', defaulting to jpg")
            output_format = 'jpg'

        # Initialize cropper
        cropper = ImageCropper()
        
        # Check if the requested format is available
        if not cropper.is_format_supported(output_format):
            logger.error(f"{output_format.upper()} format not supported")
            return {
                'success': False,
                'error': f'{output_format.upper()} format is not supported'
            }
        
        # Process cropping
        if len(temp_files) == 1:
            # Single image cropping
            input_path, original_filename = temp_files[0]
            base_name = os.path.splitext(original_filename)[0]
            
            # Set appropriate file extension based on format
            extensions = {
                'jpg': '.jpg', 'jpeg': '.jpg',
                'png': '.png', 'webp': '.webp',
                'bmp': '.bmp', 'tiff': '.tiff', 'gif': '.gif'
            }
            
            output_filename = f"{base_name}_cropped{extensions.get(output_format, '.jpg')}"
            output_path = os.path.join(temp_dir, output_filename)

            # Prepare cropping options
            crop_options = {
                'crop_mode': crop_mode,
                'aspect_ratio': aspect_ratio,
                'crop_shape': crop_shape,
                'custom_width': int(custom_width) if custom_width else None,
                'custom_height': int(custom_height) if custom_height else None,
                'maintain_aspect': maintain_aspect,
                'center_crop': center_crop,
                'output_format': output_format,
                'quality': quality,
                'crop_data': crop_data
            }

            # Perform cropping
            success = cropper.crop_image(
                input_path=input_path,
                output_path=output_path,
                **crop_options
            )

            if success and os.path.exists(output_path):
                # Determine MIME type based on format
                mime_types = {
                    'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                    'png': 'image/png', 'webp': 'image/webp',
                    'bmp': 'image/bmp', 'tiff': 'image/tiff', 'gif': 'image/gif'
                }
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'filename': output_filename,
                    'mimetype': mime_types.get(output_format, 'image/jpeg')
                }
            else:
                return {
                    'success': False,
                    'error': f'Image cropping to {output_format.upper()} failed'
                }
        
        else:
            # Multiple images cropping - return first cropped image
            results = []
            
            for input_path, original_filename in temp_files:
                base_name = os.path.splitext(original_filename)[0]
                extensions = {
                    'jpg': '.jpg', 'jpeg': '.jpg',
                    'png': '.png', 'webp': '.webp',
                    'bmp': '.bmp', 'tiff': '.tiff', 'gif': '.gif'
                }
                
                output_filename = f"{base_name}_cropped{extensions.get(output_format, '.jpg')}"
                output_path = os.path.join(temp_dir, output_filename)

                # Prepare cropping options
                crop_options = {
                    'crop_mode': crop_mode,
                    'aspect_ratio': aspect_ratio,
                    'crop_shape': crop_shape,
                    'custom_width': int(custom_width) if custom_width else None,
                    'custom_height': int(custom_height) if custom_height else None,
                    'maintain_aspect': maintain_aspect,
                    'center_crop': center_crop,
                    'output_format': output_format,
                    'quality': quality,
                    'crop_data': crop_data
                }

                # Perform cropping
                success = cropper.crop_image(
                    input_path=input_path,
                    output_path=output_path,
                    **crop_options
                )

                if success and os.path.exists(output_path):
                    results.append((output_path, output_filename))
                else:
                    logger.warning(f"Failed to crop {original_filename}")

            if results:
                # Return the first successfully cropped image
                output_path, output_filename = results[0]
                
                # Determine MIME type based on format
                mime_types = {
                    'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                    'png': 'image/png', 'webp': 'image/webp',
                    'bmp': 'image/bmp', 'tiff': 'image/tiff', 'gif': 'image/gif'
                }
                
                return {
                    'success': True,
                    'output_path': output_path,
                    'filename': output_filename,
                    'mimetype': mime_types.get(output_format, 'image/jpeg'),
                    'processed_count': len(results),
                    'total_count': len(temp_files)
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to crop any images'
                }

    except Exception as e:
        logger.error(f'Image cropping error: {e}')
        return {
            'success': False,
            'error': f'Cropping error: {str(e)}'
        }

@image_cropper_bp.route('/status', methods=['GET'])
def cropping_status():
    """Check cropping status and system health"""
    try:
        cropper = ImageCropper()
        status = {
            'service': 'online',
            'timestamp': datetime.now().isoformat(),
            'features': {
                'image_cropping': True,
                'batch_processing': True,
                'shape_cropping': cropper.is_shape_cropping_available(),
                'aspect_ratio_cropping': True
            },
            'limits': {
                'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
                'max_files_per_request': MAX_FILES,
                'supported_formats': {
                    'input': list(IMAGE_EXTENSIONS),
                    'output': ['jpg', 'png', 'webp', 'bmp', 'tiff', 'gif']
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

@image_cropper_bp.route('/formats', methods=['GET'])
def supported_formats():
    """Get list of supported input and output formats"""
    try:
        return jsonify({
            'input_formats': {
                'jpg': {
                    'name': 'JPEG Image',
                    'description': 'Joint Photographic Experts Group format',
                    'mime_type': 'image/jpeg',
                    'extensions': ['jpg', 'jpeg']
                },
                'png': {
                    'name': 'PNG Image',
                    'description': 'Portable Network Graphics format with transparency support',
                    'mime_type': 'image/png',
                    'extensions': ['png']
                },
                'webp': {
                    'name': 'WebP Image',
                    'description': 'Modern web image format with superior compression',
                    'mime_type': 'image/webp',
                    'extensions': ['webp']
                },
                'bmp': {
                    'name': 'Bitmap Image',
                    'description': 'Windows Bitmap format',
                    'mime_type': 'image/bmp',
                    'extensions': ['bmp']
                },
                'tiff': {
                    'name': 'TIFF Image',
                    'description': 'Tagged Image File Format for high quality images',
                    'mime_type': 'image/tiff',
                    'extensions': ['tiff', 'tif']
                },
                'gif': {
                    'name': 'GIF Image',
                    'description': 'Graphics Interchange Format with animation support',
                    'mime_type': 'image/gif',
                    'extensions': ['gif']
                }
            },
            'output_formats': {
                'jpg': {
                    'name': 'JPEG Image',
                    'description': 'Lossy compression, small file size, good for photos',
                    'mime_type': 'image/jpeg'
                },
                'png': {
                    'name': 'PNG Image',
                    'description': 'Lossless compression, supports transparency',
                    'mime_type': 'image/png'
                },
                'webp': {
                    'name': 'WebP Image',
                    'description': 'Modern format with excellent compression',
                    'mime_type': 'image/webp'
                },
                'bmp': {
                    'name': 'Bitmap Image',
                    'description': 'Uncompressed format, large file size',
                    'mime_type': 'image/bmp'
                },
                'tiff': {
                    'name': 'TIFF Image',
                    'description': 'High quality format, large file size',
                    'mime_type': 'image/tiff'
                },
                'gif': {
                    'name': 'GIF Image',
                    'description': 'Limited colors, supports animation',
                    'mime_type': 'image/gif'
                }
            }
        })
    except Exception as e:
        logger.error(f'Formats endpoint error: {e}')
        return jsonify({
            'error': 'Failed to retrieve format information'
        }), 500

@image_cropper_bp.route('/crop-modes', methods=['GET'])
def crop_modes():
    """Get list of available crop modes and options"""
    try:
        return jsonify({
            'crop_modes': {
                'free': {
                    'name': 'Free Crop',
                    'description': 'Freely adjustable crop area with no restrictions',
                    'options': []
                },
                'aspect': {
                    'name': 'Fixed Aspect Ratio',
                    'description': 'Crop with fixed width-to-height ratio',
                    'options': [
                        {'value': '1:1', 'name': 'Square (1:1)'},
                        {'value': '4:3', 'name': 'Standard (4:3)'},
                        {'value': '16:9', 'name': 'Widescreen (16:9)'},
                        {'value': '3:2', 'name': 'Photo (3:2)'}
                    ]
                },
                'shape': {
                    'name': 'Shape Crop',
                    'description': 'Crop to specific shapes',
                    'options': [
                        {'value': 'rectangle', 'name': 'Rectangle'},
                        {'value': 'circle', 'name': 'Circle'},
                        {'value': 'rounded', 'name': 'Rounded Corners'}
                    ]
                }
            }
        })
    except Exception as e:
        logger.error(f'Crop modes endpoint error: {e}')
        return jsonify({
            'error': 'Failed to retrieve crop mode information'
        }), 500

@image_cropper_bp.errorhandler(413)
def file_too_large(e):
    """Handle file size exceeded errors"""
    return jsonify({
        'success': False,
        'error': f'File size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit per image'
    }), 413

@image_cropper_bp.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@image_cropper_bp.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f'Internal server error in image cropper: {e}')
    return render_template('errors/500.html'), 500