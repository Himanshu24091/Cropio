"""
RAW ⇄ JPG Converter Routes
Professional camera RAW image format conversion endpoints
"""

from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
from datetime import datetime
import mimetypes
import traceback
from pathlib import Path

# Import the RAW processor utility
from utils.image.raw_processor import RAWProcessor

# Create blueprint
raw_jpg_bp = Blueprint('raw_jpg', __name__, url_prefix='/raw-jpg')

# Configuration
ALLOWED_EXTENSIONS = {
    # RAW formats
    'cr2', 'cr3', 'nef', 'arw', 'dng', 'raf', 'rw2', 'orf', 'pef', 'srw', 
    'x3f', '3fr', 'fff', 'mef', 'mos', 'raw',
    # Standard image formats
    'jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp'
}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB for RAW files

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(filepath):
    """Get file size in MB"""
    return os.path.getsize(filepath) / (1024 * 1024)

@raw_jpg_bp.route('/')
@login_required
def raw_jpg_converter():
    """Main RAW ⇄ JPG converter page"""
    try:
        # Check if RAW support is available
        raw_available = RAWProcessor.is_raw_supported()
        
        # Check for unavailability to match template expectations
        raw_unavailable = not raw_available
        
        # TODO: Add usage tracking integration
        usage = None  # This would integrate with your usage tracking system
        quota_exceeded = False  # This would check actual quota status
        
        return render_template(
            'image/raw_jpg.html',  # Use the existing template name
            raw_unavailable=raw_unavailable,
            raw_available=raw_available,
            max_file_size_mb=MAX_FILE_SIZE // (1024 * 1024),
            supported_formats=RAWProcessor.get_supported_formats() if raw_available else [],
            format_info=RAWProcessor.get_format_info() if raw_available else {},
            usage=usage,
            quota_exceeded=quota_exceeded
        )
    except Exception as e:
        flash(f'Error loading converter: {str(e)}', 'error')
        return render_template('image/raw_jpg.html', raw_unavailable=True, raw_available=False)

@raw_jpg_bp.route('/convert', methods=['POST'])
def convert_raw_jpg():
    """Convert single RAW file to JPG/PNG or single image file to RAW"""
    try:
        # Check if RAW support is available
        if not RAWProcessor.is_raw_supported():
            return jsonify({
                'success': False,
                'error': 'RAW processing support is not available. Please install rawpy library.'
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

        # Get conversion parameters
        output_format = request.form.get('output_format', 'JPEG')
        quality = int(request.form.get('quality', 95))
        preserve_metadata = request.form.get('preserve_metadata', 'true') == 'true'

        # Advanced processing parameters
        processing_params = {}
        if request.form.get('auto_white_balance') == 'true':
            processing_params['use_camera_wb'] = True
        if request.form.get('auto_brightness') == 'true':
            processing_params['auto_bright_thr'] = 0.01
        
        # Get brightness, contrast adjustments
        brightness = float(request.form.get('brightness', 1.0))
        contrast = float(request.form.get('contrast', 1.0))
        saturation = float(request.form.get('saturation', 1.0))
        sharpness = float(request.form.get('sharpness', 1.0))
        temperature_shift = int(request.form.get('temperature_shift', 0))
        
        if brightness != 1.0:
            processing_params['bright'] = brightness
        
        # Validate parameters
        if not 50 <= quality <= 100:
            return jsonify({
                'success': False,
                'error': 'Quality must be between 50 and 100'
            }), 400

        # Validate file
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(sorted(ALLOWED_EXTENSIONS))}'
            }), 400

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, 
                                               suffix=f'_{filename}')
        file.save(temp_input.name)
        temp_input.close()

        # Check file size
        if os.path.getsize(temp_input.name) > MAX_FILE_SIZE:
            os.unlink(temp_input.name)
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB'
            }), 400

        # Initialize processor with upload folder from app config
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        processor = RAWProcessor(upload_folder)
        
        try:
            # Get original file size BEFORE processing
            original_size = get_file_size_mb(temp_input.name)
            
            # Use smart conversion to automatically detect file type and route appropriately
            conversion_result = processor.smart_convert(
                temp_input.name,
                output_format=output_format,
                quality=quality,
                preserve_metadata=preserve_metadata,
                processing_params=processing_params
            )
            
            if not conversion_result['success']:
                error_msg = conversion_result['error']
                format_check = conversion_result.get('format_check')
                
                # Provide helpful suggestions based on the detected format
                if format_check and format_check.get('suggestion') == 'use_image_to_raw':
                    detected_format = format_check.get('detected_format', 'unknown')
                    error_msg += f"\n\nSuggestion: This appears to be a {detected_format} image file with a RAW extension. "
                    error_msg += "Please switch to 'JPG/PNG to RAW' conversion mode to convert this file."
                
                raise Exception(error_msg)
            
            output_path = conversion_result['output_path']
            conversion_type = conversion_result['conversion_type']

            # Get converted file size
            converted_size = get_file_size_mb(output_path)
            
            # Clean up temp input file
            os.unlink(temp_input.name)
            
            # Get output filename and create download URL
            output_filename = os.path.basename(output_path)
            
            # Create download URL
            download_url = url_for('raw_jpg.download_converted_file', filename=output_filename, _external=True)
            
            return jsonify({
                'success': True,
                'message': f'Successfully converted {filename}',
                'download': {
                    'filename': output_filename,
                    'url': download_url,
                    'size': converted_size * 1024 * 1024  # Convert back to bytes for consistency
                },
                'stats': {
                    'original_size': f'{original_size:.2f} MB' if original_size > 0 else 'Unknown',
                    'converted_size': f'{converted_size:.2f} MB',
                    'processing_time': '< 1 second',  # Could be measured if needed
                    'output_format': output_format
                },
                'conversion_type': conversion_type
            })

        except Exception as e:
            # Clean up temp file
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            raise e

    except Exception as e:
        error_details = str(e)
        print(f"RAW conversion error: {error_details}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': f'Conversion failed: {error_details}'
        }), 500

@raw_jpg_bp.route('/download/<filename>')
def download_converted_file(filename):
    """Download converted file"""
    try:
        # Secure the filename
        filename = secure_filename(filename)
        
        # Get the upload folder from app config or use default
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        
        file_path = os.path.join(upload_folder, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            flash('File not found', 'error')
            return redirect(url_for('raw_jpg.raw_jpg_converter'))
        
        # Determine the correct mimetype
        mimetype = mimetypes.guess_type(file_path)[0]
        if not mimetype:
            # Set appropriate mimetype for RAW files
            ext = filename.lower().split('.')[-1]
            if ext in ['cr2', 'cr3', 'nef', 'arw', 'dng', 'raf', 'rw2', 'orf', 'pef', 'srw']:
                mimetype = 'application/octet-stream'
            else:
                mimetype = 'application/octet-stream'
        
        # Track analytics for logged-in users
        if current_user.is_authenticated:
            try:
                from utils.analytics_tracker import track_feature
                
                # Determine conversion direction based on file extension
                ext = filename.lower().split('.')[-1]
                if ext in ['cr2', 'cr3', 'nef', 'arw', 'dng', 'raf', 'rw2', 'orf', 'pef', 'srw']:
                    feature_name = 'jpg_to_raw'
                else:
                    feature_name = 'raw_to_jpg'
                
                track_feature(
                    feature_name=feature_name,
                    feature_category='image_conversion',
                    extra_metadata={'file_type': ext, 'filename': filename},
                    success=True
                )
                print(f"[ANALYTICS] Tracked: {feature_name}")
            except Exception as e:
                print(f"[ANALYTICS] Error: {e}")
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('raw_jpg.raw_jpg_converter'))

@raw_jpg_bp.route('/preview/<filename>')
def preview_file(filename):
    """Preview converted file (for images)"""
    try:
        filename = secure_filename(filename)
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Check if it's an image file that can be previewed
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.tif')):
            return send_file(file_path, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'File type not previewable'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@raw_jpg_bp.route('/create-preview', methods=['POST'])
def create_raw_preview():
    """Create a preview/thumbnail of a RAW file or image file"""
    try:
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
                'error': 'Invalid file type'
            }), 400

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}')
        file.save(temp_input.name)
        temp_input.close()

        try:
            # Use smart file detection to determine actual file type
            format_check = RAWProcessor.check_file_format(temp_input.name)
            file_ext = filename.lower().split('.')[-1]
            
            print(f"🔍 Preview generation for {filename}:")
            print(f"   Extension: .{file_ext}")
            print(f"   Detected format: {format_check.get('detected_format', 'unknown')}")
            print(f"   Is RAW: {format_check['is_raw']}")
            print(f"   Is Image: {format_check['is_image']}")
            
            if format_check['is_raw']:
                # Handle true RAW file preview
                if not RAWProcessor.is_raw_supported():
                    return jsonify({
                        'success': False,
                        'error': 'RAW processing support not available'
                    }), 400

                # Create RAW preview
                upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
                processor = RAWProcessor(upload_folder)
                preview_path = processor.create_preview(temp_input.name)
                preview_filename = os.path.basename(preview_path)
                
                # Clean up temp input file
                os.unlink(temp_input.name)
                
                return jsonify({
                    'success': True,
                    'preview_filename': preview_filename,
                    'preview_path': preview_path,
                    'file_type': 'raw',
                    'detected_format': format_check.get('detected_format', 'RAW')
                })
                
            elif format_check['is_image']:
                # Handle image file preview (same as api/preview-image endpoint)
                from PIL import Image
                import base64
                from io import BytesIO
                
                detected_format = format_check.get('detected_format', 'IMAGE')
                print(f"✅ Creating preview for {detected_format} image file")
                
                # Create thumbnail
                with Image.open(temp_input.name) as img:
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Create thumbnail while preserving aspect ratio
                    img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                    
                    # Save thumbnail to bytes
                    thumb_io = BytesIO()
                    img.save(thumb_io, format='JPEG', quality=85)
                    thumb_io.seek(0)
                    
                    # Encode as base64 for display
                    thumb_base64 = base64.b64encode(thumb_io.getvalue()).decode('utf-8')
                    preview_data_url = f'data:image/jpeg;base64,{thumb_base64}'

                # Clean up temp file
                os.unlink(temp_input.name)

                return jsonify({
                    'success': True,
                    'preview': preview_data_url,
                    'file_type': 'image',
                    'detected_format': detected_format,
                    'suggestion': 'This is an image file. You can preview it or convert it to RAW format using the JPG/PNG to RAW mode.'
                })
            else:
                # File is neither RAW nor standard image
                error_msg = f"Cannot create preview for '{filename}'. "
                if format_check.get('suggestion') == 'file_corrupted_or_unsupported':
                    error_msg += "The file appears to be corrupted or in an unsupported format."
                else:
                    error_msg += f"Error: {format_check.get('error', 'Unknown error')}"
                raise ValueError(error_msg)

        except Exception as e:
            # Clean up temp file
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raw_jpg_bp.route('/metadata/<filename>')
def get_raw_metadata(filename):
    """Get comprehensive metadata from a RAW file"""
    try:
        filename = secure_filename(filename)
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Check if RAW support is available
        if not RAWProcessor.is_raw_supported():
            return jsonify({'error': 'RAW processing support not available'}), 400
        
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        processor = RAWProcessor(upload_folder)
        metadata = processor.get_raw_metadata(file_path)
        
        return jsonify({
            'success': True,
            'metadata': metadata
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raw_jpg_bp.route('/batch-convert', methods=['POST'])
def batch_convert_raw():
    """Batch convert multiple RAW files"""
    try:
        # Check if RAW support is available
        if not RAWProcessor.is_raw_supported():
            return jsonify({
                'success': False,
                'error': 'RAW processing support is not available'
            }), 400

        # Get parameters
        output_format = request.form.get('output_format', 'JPEG')
        quality = int(request.form.get('quality', 95))
        preserve_metadata = request.form.get('preserve_metadata', 'true') == 'true'
        
        # Get files - try both 'files[]' and 'files' for compatibility
        files = request.files.getlist('files[]') or request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'success': False,
                'error': 'No files uploaded'
            }), 400
        
        # Initialize processor with upload folder from app config
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        processor = RAWProcessor(upload_folder)
        
        results = {
            'converted': [],
            'failed': [],
            'total_processed': len(files),
            'success_count': 0,
            'failure_count': 0
        }
        
        # Process each file
        for file in files:
            if file.filename == '':
                continue
                
            try:
                # Validate file
                if not allowed_file(file.filename):
                    results['failed'].append({
                        'filename': file.filename,
                        'error': f'Invalid file type. Allowed: {", ".join(sorted(ALLOWED_EXTENSIONS))}',
                        'status': 'failed'
                    })
                    results['failure_count'] += 1
                    continue

                # Save uploaded file temporarily
                filename = secure_filename(file.filename)
                temp_input = tempfile.NamedTemporaryFile(delete=False, 
                                                       suffix=f'_{filename}')
                file.save(temp_input.name)
                temp_input.close()

                # Check file size
                if os.path.getsize(temp_input.name) > MAX_FILE_SIZE:
                    os.unlink(temp_input.name)
                    results['failed'].append({
                        'filename': filename,
                        'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB',
                        'status': 'failed'
                    })
                    results['failure_count'] += 1
                    continue

                # Determine conversion type based on file extension
                file_ext = filename.lower().split('.')[-1]
                raw_extensions = ['cr2', 'cr3', 'nef', 'arw', 'dng', 'raf', 'rw2', 'orf', 'pef', 'srw', 'x3f', '3fr', 'fff', 'mef', 'mos', 'raw']
                
                if file_ext in raw_extensions:
                    # RAW to Image conversion
                    output_path = processor.raw_to_jpg(
                        temp_input.name, 
                        output_format=output_format,
                        quality=quality, 
                        preserve_metadata=preserve_metadata
                    )
                    conversion_type = f'RAW → {output_format}'
                else:
                    # Image to RAW conversion
                    raw_format = request.form.get('raw_format', 'DNG')
                    output_path = processor.png_to_raw(
                        temp_input.name,
                        output_format=raw_format,
                        quality=quality,
                        preserve_metadata=preserve_metadata
                    )
                    conversion_type = f'{file_ext.upper()} → {raw_format}'

                # Clean up temp input file
                os.unlink(temp_input.name)

                # Get output filename and create download URL
                output_filename = os.path.basename(output_path)
                download_url = url_for('raw_jpg.download_converted_file', filename=output_filename, _external=True)
                
                results['converted'].append({
                    'filename': output_filename,
                    'original_filename': filename,
                    'download_url': download_url,
                    'output_format': output_format,
                    'size': get_file_size_mb(output_path),
                    'conversion_type': conversion_type,
                    'status': 'success'
                })
                results['success_count'] += 1

            except Exception as e:
                # Clean up temp file if it exists
                if 'temp_input' in locals() and os.path.exists(temp_input.name):
                    try:
                        os.unlink(temp_input.name)
                    except:
                        pass

                results['failed'].append({
                    'filename': file.filename,
                    'error': str(e),
                    'status': 'failed'
                })
                results['failure_count'] += 1

        # Return results
        if results['success_count'] == 0:
            return jsonify({
                'success': False,
                'error': 'No files were converted successfully',
                'details': results
            }), 400
        
        return jsonify({
            'success': True,
            'message': f'Successfully converted {results["success_count"]} of {results["total_processed"]} files',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raw_jpg_bp.route('/enhance', methods=['POST'])
def enhance_image():
    """Apply enhancements to processed image"""
    try:
        # Get parameters
        filename = request.form.get('filename')
        if not filename:
            return jsonify({
                'success': False,
                'error': 'No filename provided'
            }), 400
        
        filename = secure_filename(filename)
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Get enhancement parameters
        brightness = float(request.form.get('brightness', 1.0))
        contrast = float(request.form.get('contrast', 1.0))
        saturation = float(request.form.get('saturation', 1.0))
        sharpness = float(request.form.get('sharpness', 1.0))
        temperature_shift = int(request.form.get('temperature_shift', 0))
        
        # Apply enhancements
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        processor = RAWProcessor(upload_folder)
        enhanced_path = processor.enhance_image(
            file_path,
            brightness=brightness,
            contrast=contrast,
            saturation=saturation,
            sharpness=sharpness,
            temperature_shift=temperature_shift
        )
        
        enhanced_filename = os.path.basename(enhanced_path)
        
        return jsonify({
            'success': True,
            'enhanced_filename': enhanced_filename,
            'enhanced_path': enhanced_path
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raw_jpg_bp.route('/check-support')
def check_raw_support():
    """Check if RAW processing support is available"""
    try:
        supported = RAWProcessor.is_raw_supported()
        formats = RAWProcessor.get_supported_formats() if supported else []
        format_info = RAWProcessor.get_format_info() if supported else {}
        
        return jsonify({
            'supported': supported,
            'formats': formats,
            'format_info': format_info,
            'message': 'RAW processing support available' if supported else 'RAW processing support not available - install rawpy'
        })
        
    except Exception as e:
        return jsonify({
            'supported': False,
            'error': str(e)
        }), 500

@raw_jpg_bp.route('/estimate-time')
def estimate_processing_time():
    """Estimate processing time for file size"""
    try:
        file_size_mb = float(request.args.get('size', 0))
        estimate = RAWProcessor.estimate_processing_time(file_size_mb)
        
        return jsonify({
            'success': True,
            'estimate': estimate,
            'file_size_mb': file_size_mb
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API endpoints with names expected by the template
@raw_jpg_bp.route('/api/convert', methods=['POST'])
def api_convert_raw():
    """API endpoint for RAW conversion (alias to /convert)"""
    return convert_raw_jpg()

@raw_jpg_bp.route('/api/analyze', methods=['POST'])
def api_analyze_raw():
    """API endpoint for smart file analysis (now supports both RAW and image files)"""
    try:
        if not RAWProcessor.is_raw_supported():
            return jsonify({
                'success': False,
                'error': 'RAW processing support not available'
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
                'error': 'Invalid file type'
            }), 400

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}')
        file.save(temp_input.name)
        temp_input.close()

        try:
            # Perform smart file format analysis
            format_check = RAWProcessor.check_file_format(temp_input.name)
            file_ext = filename.lower().split('.')[-1]
            file_size = os.path.getsize(temp_input.name)
            
            print(f"🔍 Smart analysis for {filename}:")
            print(f"   Extension: .{file_ext}")
            print(f"   Detected format: {format_check.get('detected_format', 'unknown')}")
            print(f"   Is RAW: {format_check['is_raw']}")
            print(f"   Is Image: {format_check['is_image']}")
            print(f"   Suggestion: {format_check.get('suggestion', 'none')}")
            
            if format_check['is_raw']:
                # True RAW file - get RAW metadata
                try:
                    upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
                    processor = RAWProcessor(upload_folder)
                    metadata = processor.get_raw_metadata(temp_input.name)
                    
                    # Clean up temp file
                    os.unlink(temp_input.name)
                    
                    return jsonify({
                        'success': True,
                        'metadata': metadata,
                        'file_type': 'raw',
                        'detected_format': format_check.get('detected_format', 'RAW')
                    })
                except Exception as e:
                    raise Exception(f"Failed to extract RAW metadata: {str(e)}")
                    
            elif format_check['is_image']:
                # Image file (including ones with wrong RAW extensions)
                detected_format = format_check.get('detected_format', 'IMAGE')
                
                # Get image metadata using PIL
                from PIL import Image
                from PIL.ExifTags import TAGS
                
                with Image.open(temp_input.name) as img:
                    width, height = img.size
                    format_name = img.format or file_ext.upper()
                    mode = img.mode
                    
                    # Extract EXIF data if available
                    exif_data = {}
                    if hasattr(img, '_getexif') and img._getexif():
                        exif = img._getexif()
                        for tag, value in exif.items():
                            tag_name = TAGS.get(tag, tag)
                            exif_data[tag_name] = str(value) if not isinstance(value, (str, int, float)) else value

                # Build metadata response for image file
                metadata = {
                    'filename': filename,
                    'filesize': file_size,
                    'format': detected_format,
                    'dimensions': {
                        'width': width,
                        'height': height
                    },
                    'megapixels': round((width * height) / 1000000, 1),
                    'color_mode': mode,
                    'exif_data': exif_data,
                    'brand': exif_data.get('Make', 'Unknown')
                }
                
                # Add helpful message for files with wrong extensions
                analysis_message = None
                if file_ext in ['dng', 'cr2', 'cr3', 'nef', 'arw'] and not format_check['is_raw']:
                    analysis_message = f"This file has a .{file_ext.upper()} extension but is actually a {detected_format} image file. Switch to 'JPG/PNG to RAW' mode to convert it to DNG format."
                
                # Clean up temp file
                os.unlink(temp_input.name)
                
                return jsonify({
                    'success': True,
                    'metadata': metadata,
                    'file_type': 'image',
                    'detected_format': detected_format,
                    'analysis_message': analysis_message,
                    'suggestion': format_check.get('suggestion')
                })
            else:
                # Neither RAW nor image
                error_msg = f"Cannot analyze file '{filename}'. "
                if format_check.get('suggestion') == 'file_corrupted_or_unsupported':
                    error_msg += "The file appears to be corrupted or in an unsupported format."
                else:
                    error_msg += f"Error: {format_check.get('error', 'Unknown error')}"
                raise ValueError(error_msg)

        except Exception as e:
            # Clean up temp file
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raw_jpg_bp.route('/api/preview', methods=['POST'])
def api_create_preview():
    """API endpoint for RAW preview creation (alias to /create-preview)"""
    return create_raw_preview()

@raw_jpg_bp.route('/api/batch-convert', methods=['POST'])
def api_batch_convert():
    """API endpoint for batch RAW conversion (alias to /batch-convert)"""
    return batch_convert_raw()

@raw_jpg_bp.route('/api/convert-png-to-raw', methods=['POST'])
def api_convert_png_to_raw():
    """API endpoint for PNG to RAW conversion"""
    # Modify the conversion mode to handle PNG to RAW specifically
    return convert_raw_jpg()

@raw_jpg_bp.route('/api/batch-convert-png-to-raw', methods=['POST'])
def api_batch_convert_png_to_raw():
    """API endpoint for batch PNG to RAW conversion"""
    # Modify the conversion mode to handle PNG to RAW specifically
    return batch_convert_raw()

@raw_jpg_bp.route('/api/analyze-image', methods=['POST'])
def api_analyze_image():
    """API endpoint for image file analysis (EXIF, metadata)"""
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

        # Validate file
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type'
            }), 400

        # Check if it's an image file
        filename = secure_filename(file.filename)
        file_ext = filename.lower().split('.')[-1]
        image_extensions = ['jpg', 'jpeg', 'png', 'tiff', 'tif', 'bmp', 'webp']
        
        if file_ext not in image_extensions:
            return jsonify({
                'success': False,
                'error': f'Analysis is only available for image files. File extension \'{file_ext.upper()}\' is not a supported image format.'
            }), 400

        # Save uploaded file temporarily
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}')
        file.save(temp_input.name)
        temp_input.close()

        try:
            # Get image metadata using PIL/Pillow
            from PIL import Image
            from PIL.ExifTags import TAGS
            import os

            # Open image and get basic info
            with Image.open(temp_input.name) as img:
                width, height = img.size
                format_name = img.format or file_ext.upper()
                mode = img.mode
                
                # Extract EXIF data if available
                exif_data = {}
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    for tag, value in exif.items():
                        tag_name = TAGS.get(tag, tag)
                        exif_data[tag_name] = str(value) if not isinstance(value, (str, int, float)) else value

            # Get file stats
            file_size = os.path.getsize(temp_input.name)
            megapixels = (width * height) / 1000000

            # Build metadata response
            metadata = {
                'filename': filename,
                'filesize': file_size,
                'format': format_name,
                'dimensions': {
                    'width': width,
                    'height': height
                },
                'megapixels': round(megapixels, 1),
                'color_mode': mode,
                'exif_data': exif_data
            }

            # Add brand info from EXIF if available
            metadata['brand'] = exif_data.get('Make', 'Unknown')

            # Clean up temp file
            os.unlink(temp_input.name)

            return jsonify({
                'success': True,
                'metadata': metadata
            })

        except Exception as e:
            # Clean up temp file
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raw_jpg_bp.route('/api/preview-image', methods=['POST'])
def api_create_image_preview():
    """API endpoint for image file preview/thumbnail creation"""
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

        # Validate file
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type'
            }), 400

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}')
        file.save(temp_input.name)
        temp_input.close()

        try:
            from PIL import Image
            import base64
            from io import BytesIO
            
            # Create thumbnail
            with Image.open(temp_input.name) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail while preserving aspect ratio
                img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                
                # Save thumbnail to bytes
                thumb_io = BytesIO()
                img.save(thumb_io, format='JPEG', quality=85)
                thumb_io.seek(0)
                
                # Encode as base64 for display
                thumb_base64 = base64.b64encode(thumb_io.getvalue()).decode('utf-8')
                preview_data_url = f'data:image/jpeg;base64,{thumb_base64}'

            # Clean up temp file
            os.unlink(temp_input.name)

            return jsonify({
                'success': True,
                'preview': preview_data_url
            })

        except Exception as e:
            # Clean up temp file
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raw_jpg_bp.route('/api/formats')
def get_supported_formats():
    """Get supported formats information"""
    try:
        supported = RAWProcessor.is_raw_supported()
        formats = RAWProcessor.get_supported_formats() if supported else []
        format_info = RAWProcessor.get_format_info() if supported else {}
        
        return jsonify({
            'success': True,
            'supported': supported,
            'formats': formats,
            'format_info': format_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@raw_jpg_bp.route('/api/smart-analyze', methods=['POST'])
def api_smart_analyze():
    """Smart file analysis that detects actual format regardless of extension"""
    try:
        if not RAWProcessor.is_raw_supported():
            return jsonify({
                'success': False,
                'error': 'RAW processing support not available'
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
                'error': 'Invalid file type'
            }), 400

        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}')
        file.save(temp_input.name)
        temp_input.close()

        try:
            # Perform smart file format analysis
            format_check = RAWProcessor.check_file_format(temp_input.name)
            file_ext = filename.lower().split('.')[-1]
            file_size = os.path.getsize(temp_input.name)
            
            print(f"🔍 Smart analysis for {filename}:")
            print(f"   Extension: .{file_ext}")
            print(f"   Detected format: {format_check.get('detected_format', 'unknown')}")
            print(f"   Is RAW: {format_check['is_raw']}")
            print(f"   Is Image: {format_check['is_image']}")
            print(f"   Suggestion: {format_check.get('suggestion', 'none')}")
            
            analysis_result = {
                'filename': filename,
                'file_extension': file_ext.upper(),
                'file_size': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'detected_format': format_check.get('detected_format', 'unknown'),
                'is_raw': format_check['is_raw'],
                'is_image': format_check['is_image'],
                'suggestion': format_check.get('suggestion', 'unknown'),
                'recommended_action': None
            }
            
            # Add specific recommendations based on detection
            if format_check['is_raw']:
                analysis_result['recommended_action'] = 'Use RAW to JPG/PNG conversion'
                # Try to get RAW metadata if it's a true RAW file
                try:
                    upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
                    processor = RAWProcessor(upload_folder)
                    metadata = processor.get_raw_metadata(temp_input.name)
                    analysis_result['raw_metadata'] = metadata
                except Exception as meta_error:
                    analysis_result['metadata_error'] = str(meta_error)
                    
            elif format_check['is_image']:
                detected_format = format_check.get('detected_format', 'IMAGE')
                if file_ext in ['dng', 'cr2', 'cr3', 'nef', 'arw']:
                    analysis_result['recommended_action'] = f'Switch to JPG/PNG to RAW conversion (file is actually {detected_format})'
                else:
                    analysis_result['recommended_action'] = 'Use regular image conversion or JPG/PNG to RAW conversion'
                
                # Get basic image info
                try:
                    from PIL import Image
                    with Image.open(temp_input.name) as img:
                        analysis_result['image_info'] = {
                            'dimensions': f'{img.size[0]} x {img.size[1]}',
                            'mode': img.mode,
                            'format': img.format
                        }
                except Exception as img_error:
                    analysis_result['image_error'] = str(img_error)
            else:
                analysis_result['recommended_action'] = 'File format not supported or corrupted'
                analysis_result['error_details'] = format_check.get('error', 'Unknown error')

            # Clean up temp file
            os.unlink(temp_input.name)

            return jsonify({
                'success': True,
                'analysis': analysis_result
            })

        except Exception as e:
            # Clean up temp file
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            raise e

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
