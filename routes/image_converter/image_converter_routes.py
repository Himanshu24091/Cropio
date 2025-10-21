from flask import Blueprint, render_template, request, jsonify, send_file, current_app, session
import os
import tempfile
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import uuid
import traceback
from datetime import datetime
import shutil

# Import utility functions
from utils.image_converter.image_converter_utils import (
    process_image_conversion,
    validate_image_file,
    get_conversion_stats,
    cleanup_temp_files,
    create_conversion_summary
)

# Create blueprint
image_converter_bp = Blueprint('image_converter', __name__, url_prefix='/image-converter')

# Configuration constants
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB per file
MAX_FILES_PER_BATCH = 10
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'gif', 'webp'}
OUTPUT_FORMATS = {'jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff', 'gif'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    """Get file extension from filename"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

@image_converter_bp.route('/')
def index():
    """Render the Image Converter interface"""
    try:
        return render_template('image_converter/image_converter.html')
    except Exception as e:
        current_app.logger.error(f"Error rendering image converter template: {str(e)}")
        return jsonify({'error': 'Failed to load image converter interface'}), 500

@image_converter_bp.route('/convert', methods=['POST'])
def convert_images():
    """
    Convert uploaded images to specified format with optional processing
    Supports both single file and batch processing
    """
    session_id = str(uuid.uuid4())
    temp_dirs = []
    
    try:
        # Debug logging
        current_app.logger.info(f"Image conversion request received (session: {session_id})")
        current_app.logger.info(f"  Files: {list(request.files.keys())}")
        current_app.logger.info(f"  Form data: {dict(request.form)}")
        
        # Validate request
        if 'files' not in request.files:
            return jsonify({'error': 'No image files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or (len(files) == 1 and files[0].filename == ''):
            return jsonify({'error': 'No image files selected'}), 400
        
        # Check file count limit
        if len(files) > MAX_FILES_PER_BATCH:
            return jsonify({
                'error': f'Too many files. Maximum {MAX_FILES_PER_BATCH} images allowed per batch.'
            }), 400
        
        # Get conversion parameters
        output_format = request.form.get('output_format', '').lower()
        if not output_format:
            return jsonify({'error': 'Output format not specified'}), 400
        
        if output_format not in OUTPUT_FORMATS:
            return jsonify({'error': f'Unsupported output format: {output_format}'}), 400
        
        current_app.logger.info(f"  Target format: {output_format}")
        
        # Get processing options
        quality_mapping = {
            'high': 95,
            'medium': 85,
            'low': 70
        }
        quality_value = request.form.get('quality', 'medium')
        numeric_quality = quality_mapping.get(quality_value, 85)
        
        processing_options = {
            'quality': numeric_quality,
            'resize_percentage': request.form.get('resize_percentage'),
            'resize_width': request.form.get('resize_width'),
            'resize_height': request.form.get('resize_height'),
            'maintain_aspect_ratio': request.form.get('maintain_aspect_ratio') == 'on',
            'rotation': int(request.form.get('rotation', 0)),
            'convert_to_grayscale': request.form.get('convert_to_grayscale') == 'on',
            'preserve_metadata': request.form.get('preserve_metadata') == 'on'
        }
        
        # Validate and convert processing options
        try:
            if processing_options['resize_percentage']:
                processing_options['resize_percentage'] = int(processing_options['resize_percentage'])
                if processing_options['resize_percentage'] <= 0 or processing_options['resize_percentage'] > 500:
                    return jsonify({'error': 'Resize percentage must be between 1-500%'}), 400
            
            if processing_options['resize_width']:
                processing_options['resize_width'] = int(processing_options['resize_width'])
                if processing_options['resize_width'] <= 0 or processing_options['resize_width'] > 10000:
                    return jsonify({'error': 'Width must be between 1-10000 pixels'}), 400
            
            if processing_options['resize_height']:
                processing_options['resize_height'] = int(processing_options['resize_height'])
                if processing_options['resize_height'] <= 0 or processing_options['resize_height'] > 10000:
                    return jsonify({'error': 'Height must be between 1-10000 pixels'}), 400
            
            if processing_options['quality'] < 1 or processing_options['quality'] > 100:
                processing_options['quality'] = 85  # Default quality
                
        except ValueError as e:
            return jsonify({'error': 'Invalid processing parameters'}), 400
        
        current_app.logger.info(f"  Processing options: {processing_options}")
        
        # Create temporary directories
        input_temp_dir = tempfile.mkdtemp(prefix=f'img_input_{session_id}_')
        output_temp_dir = tempfile.mkdtemp(prefix=f'img_output_{session_id}_')
        temp_dirs.extend([input_temp_dir, output_temp_dir])
        
        # Process each uploaded file
        processed_files = []
        conversion_stats = {
            'total_files': len(files),
            'successful_conversions': 0,
            'failed_conversions': 0,
            'total_input_size': 0,
            'total_output_size': 0,
            'errors': []
        }
        
        for file_index, file in enumerate(files):
            try:
                current_app.logger.info(f"  Processing file {file_index + 1}/{len(files)}: {file.filename}")
                
                # Validate file
                if not file or file.filename == '':
                    conversion_stats['failed_conversions'] += 1
                    conversion_stats['errors'].append(f"Empty file at index {file_index}")
                    continue
                
                if not allowed_file(file.filename):
                    conversion_stats['failed_conversions'] += 1
                    conversion_stats['errors'].append(f"Invalid file type: {file.filename}")
                    continue
                
                # Check file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    conversion_stats['failed_conversions'] += 1
                    conversion_stats['errors'].append(f"File too large: {file.filename} ({file_size // (1024*1024)}MB)")
                    continue
                
                conversion_stats['total_input_size'] += file_size
                
                # Save uploaded file
                filename = secure_filename(file.filename)
                if not filename:
                    filename = f"image_{file_index + 1}.{get_file_extension(file.filename)}"
                
                input_path = os.path.join(input_temp_dir, filename)
                file.save(input_path)
                
                # Validate image file content
                if not validate_image_file(input_path):
                    conversion_stats['failed_conversions'] += 1
                    conversion_stats['errors'].append(f"Invalid image file: {filename}")
                    continue
                
                # Generate output filename
                base_name = os.path.splitext(filename)[0]
                output_filename = f"{base_name}.{output_format}"
                output_path = os.path.join(output_temp_dir, output_filename)
                
                # Convert the image with detailed logging
                current_app.logger.info(f"    Starting conversion: {input_path} -> {output_path}")
                
                try:
                    # Simple PIL conversion for debugging
                    from PIL import Image
                    with Image.open(input_path) as img:
                        # Convert to RGB if needed
                        if output_format.lower() in ['jpg', 'jpeg'] and img.mode in ['RGBA', 'LA']:
                            # Create white background
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = background
                        
                        # Save the image
                        save_params = {}
                        if output_format.lower() in ['jpg', 'jpeg']:
                            save_params['format'] = 'JPEG'
                            save_params['quality'] = processing_options.get('quality', 85)
                        elif output_format.lower() == 'png':
                            save_params['format'] = 'PNG'
                        elif output_format.lower() == 'webp':
                            save_params['format'] = 'WEBP'
                            save_params['quality'] = processing_options.get('quality', 85)
                        
                        img.save(output_path, **save_params)
                        
                        current_app.logger.info(f"    Image saved successfully to {output_path}")
                        success = True
                        error_msg = None
                        
                except Exception as conv_error:
                    success = False
                    error_msg = str(conv_error)
                    current_app.logger.error(f"    Conversion failed: {error_msg}")
                    current_app.logger.error(traceback.format_exc())
                
                if success:
                    # Get output file size
                    if os.path.exists(output_path):
                        output_size = os.path.getsize(output_path)
                        conversion_stats['total_output_size'] += output_size
                        
                        processed_files.append({
                            'original_name': filename,
                            'output_name': output_filename,
                            'output_path': output_path,
                            'input_size': file_size,
                            'output_size': output_size
                        })
                        conversion_stats['successful_conversions'] += 1
                        
                        current_app.logger.info(f"    Converted: {filename} -> {output_filename}")
                    else:
                        conversion_stats['failed_conversions'] += 1
                        conversion_stats['errors'].append(f"Output file not created: {filename}")
                else:
                    conversion_stats['failed_conversions'] += 1
                    conversion_stats['errors'].append(f"Conversion failed for {filename}: {error_msg}")
                    current_app.logger.error(f"    Failed: {filename} - {error_msg}")
                
            except Exception as e:
                conversion_stats['failed_conversions'] += 1
                error_msg = f"Error processing {file.filename}: {str(e)}"
                conversion_stats['errors'].append(error_msg)
                current_app.logger.error(f"    Exception: {error_msg}")
                current_app.logger.error(traceback.format_exc())
        
        # Debug: Log final conversion stats
        current_app.logger.info(f"Conversion completed - Success: {conversion_stats['successful_conversions']}, Failed: {conversion_stats['failed_conversions']}")
        current_app.logger.info(f"Processed files count: {len(processed_files)}")
        
        # Check if any conversions were successful
        if conversion_stats['successful_conversions'] == 0:
            error_messages = conversion_stats['errors'][:3]  # Show first 3 errors
            if len(conversion_stats['errors']) > 3:
                error_messages.append(f"... and {len(conversion_stats['errors']) - 3} more errors")
            
            current_app.logger.error(f"All conversions failed. Errors: {conversion_stats['errors']}")
            return jsonify({
                'error': f'All conversions failed. Errors: {"; ".join(error_messages)}'
            }), 400
        
        # Always return the first converted file directly (no ZIP for multiple files)
        if len(processed_files) >= 1:
            # Return the first successfully converted file
            file_info = processed_files[0]
            
            # Determine proper MIME type based on format
            mime_types = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg', 
                'png': 'image/png',
                'webp': 'image/webp',
                'bmp': 'image/bmp',
                'tiff': 'image/tiff',
                'gif': 'image/gif'
            }
            
            mimetype = mime_types.get(output_format.lower(), 'application/octet-stream')
            
            response = send_file(
                file_info['output_path'],
                as_attachment=True,
                download_name=file_info['output_name'],
                mimetype=mimetype
            )
            
            # Schedule cleanup after response with delay
            import threading
            import time
            
            def delayed_cleanup():
                time.sleep(5)  # Wait 5 seconds before cleanup
                cleanup_temp_files(temp_dirs)
                # Use standard logging instead of Flask's current_app.logger in thread
                import logging
                logging.info(f"Cleaned up temp files for session {session_id}")
            
            cleanup_thread = threading.Thread(target=delayed_cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
            if len(processed_files) > 1:
                current_app.logger.info(f"Multiple files converted, returning first file: {file_info['output_name']} (Note: Only first file downloaded)")
            else:
                current_app.logger.info(f"Single file conversion completed: {file_info['output_name']}")
            
            return response
        else:
            # This should not happen since we check for processed_files >= 1 above
            cleanup_temp_files(temp_dirs)
            return jsonify({'error': 'No files were successfully converted'}), 500
    
    except RequestEntityTooLarge:
        cleanup_temp_files(temp_dirs)
        return jsonify({'error': 'File size too large. Maximum 25MB per file.'}), 413
    
    except Exception as e:
        cleanup_temp_files(temp_dirs)
        current_app.logger.error(f"Unexpected error in image conversion: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred during conversion. Please try again.'}), 500

@image_converter_bp.route('/supported-formats')
def supported_formats():
    """Return list of supported input and output formats"""
    return jsonify({
        'input_formats': list(ALLOWED_EXTENSIONS),
        'output_formats': list(OUTPUT_FORMATS),
        'max_file_size': MAX_FILE_SIZE,
        'max_files_per_batch': MAX_FILES_PER_BATCH
    })

@image_converter_bp.route('/format-info/<format_name>')
def format_info(format_name):
    """Get information about a specific image format"""
    format_name = format_name.lower()
    
    format_details = {
        'jpg': {
            'name': 'JPEG',
            'description': 'Joint Photographic Experts Group format, best for photographs',
            'supports_transparency': False,
            'compression': 'Lossy',
            'best_for': 'Photographs, images with many colors',
            'file_size': 'Small to medium',
            'quality_options': True
        },
        'jpeg': {
            'name': 'JPEG',
            'description': 'Joint Photographic Experts Group format, best for photographs',
            'supports_transparency': False,
            'compression': 'Lossy',
            'best_for': 'Photographs, images with many colors',
            'file_size': 'Small to medium',
            'quality_options': True
        },
        'png': {
            'name': 'PNG',
            'description': 'Portable Network Graphics format, supports transparency',
            'supports_transparency': True,
            'compression': 'Lossless',
            'best_for': 'Graphics, logos, images with transparency',
            'file_size': 'Medium to large',
            'quality_options': False
        },
        'webp': {
            'name': 'WebP',
            'description': 'Modern format with superior compression',
            'supports_transparency': True,
            'compression': 'Lossy/Lossless',
            'best_for': 'Web images, modern browsers',
            'file_size': 'Very small',
            'quality_options': True
        },
        'bmp': {
            'name': 'BMP',
            'description': 'Bitmap format, uncompressed',
            'supports_transparency': False,
            'compression': 'None',
            'best_for': 'Simple graphics, exact pixel data',
            'file_size': 'Very large',
            'quality_options': False
        },
        'tiff': {
            'name': 'TIFF',
            'description': 'Tagged Image File Format, high quality archival',
            'supports_transparency': True,
            'compression': 'Lossless',
            'best_for': 'Professional photography, archival',
            'file_size': 'Large',
            'quality_options': False
        },
        'gif': {
            'name': 'GIF',
            'description': 'Graphics Interchange Format, supports animation',
            'supports_transparency': True,
            'compression': 'Lossless (limited colors)',
            'best_for': 'Simple animations, graphics with few colors',
            'file_size': 'Small to medium',
            'quality_options': False
        }
    }
    
    if format_name in format_details:
        return jsonify(format_details[format_name])
    else:
        return jsonify({'error': 'Format not supported'}), 404

@image_converter_bp.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test temp directory creation
        test_dir = tempfile.mkdtemp(prefix='health_check_')
        os.rmdir(test_dir)
        
        return jsonify({
            'status': 'healthy',
            'service': 'Image Converter',
            'timestamp': datetime.now().isoformat(),
            'supported_formats': len(OUTPUT_FORMATS),
            'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
            'max_batch_size': MAX_FILES_PER_BATCH
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Error handlers specific to image converter
@image_converter_bp.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    """Handle file too large error"""
    return jsonify({
        'error': f'File size too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB per file.'
    }), 413

@image_converter_bp.errorhandler(404)
def handle_not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Image converter endpoint not found'}), 404

@image_converter_bp.errorhandler(500)
def handle_internal_error(e):
    """Handle 500 errors"""
    current_app.logger.error(f"Internal server error in image converter: {str(e)}")
    return jsonify({'error': 'Internal server error occurred during image conversion'}), 500