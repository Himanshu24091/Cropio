"""
HEIC ⇄ JPG Converter Routes
Professional-grade Apple HEIC image format conversion endpoints
"""

from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
from datetime import datetime
import mimetypes
import traceback
from pathlib import Path

# Import the HEIC processor utility
from utils.image.heic_processor import HEICProcessor

# Create blueprint with unique name to avoid conflicts
heic_jpg_bp = Blueprint('heic_jpg_img', __name__, url_prefix='/heic-jpg')

# Configuration
ALLOWED_EXTENSIONS = {'heic', 'heif', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(filepath):
    """Get file size in MB"""
    return os.path.getsize(filepath) / (1024 * 1024)

@heic_jpg_bp.route('/')
@login_required
def heic_jpg_converter():
    """Main HEIC ⇄ JPG converter page"""
    try:
        # Check if HEIC support is available
        heic_available = HEICProcessor.is_heic_supported()
        
        # Check for unavailability to match template expectations
        heic_unavailable = not heic_available
        
        # TODO: Add usage tracking integration
        usage = None  # This would integrate with your usage tracking system
        quota_exceeded = False  # This would check actual quota status
        
        return render_template(
            'image/heic_jpg.html',  # Use the existing template name
            heic_unavailable=heic_unavailable,
            heic_available=heic_available,
            max_file_size=MAX_FILE_SIZE // (1024 * 1024),
            supported_formats=HEICProcessor.get_supported_formats() if heic_available else None,
            usage=usage,
            quota_exceeded=quota_exceeded
        )
    except Exception as e:
        flash(f'Error loading converter: {str(e)}', 'error')
        return render_template('image/heic_jpg.html', heic_unavailable=True, heic_available=False)

@heic_jpg_bp.route('/convert', methods=['POST'])
def convert_heic_jpg():
    """Convert HEIC/HEIF files to JPG or vice versa"""
    try:
        # Check if HEIC support is available
        if not HEICProcessor.is_heic_supported():
            return jsonify({
                'success': False,
                'error': 'HEIC support is not available. Please install pillow-heif library.'
            }), 400

        # Get conversion mode
        conversion_mode = request.form.get('conversion_mode', 'heic_to_jpg')
        quality = int(request.form.get('quality', 95))
        preserve_metadata = request.form.get('preserve_metadata', 'true') == 'true'

        # Validate quality
        if not 50 <= quality <= 100:
            return jsonify({
                'success': False,
                'error': 'Quality must be between 50 and 100'
            }), 400

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

        # Initialize processor
        processor = HEICProcessor()
        
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
                        'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}',
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

                # Convert file based on mode
                if conversion_mode == 'heic_to_jpg':
                    output_path = processor.heic_to_jpg(temp_input.name, quality)
                    conversion_type = 'HEIC → JPG'
                elif conversion_mode == 'jpg_to_heic':
                    output_path = processor.jpg_to_heic(temp_input.name, quality)
                    conversion_type = 'JPG → HEIC'
                else:
                    raise ValueError(f'Invalid conversion mode: {conversion_mode}')

                # Clean up temp input file
                os.unlink(temp_input.name)

                # Get output filename for download
                output_filename = os.path.basename(output_path)
                
                results['converted'].append({
                    'filename': filename,
                    'output_filename': output_filename,
                    'output_path': output_path,
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
        error_details = str(e)
        print(f"HEIC conversion error: {error_details}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': f'Conversion failed: {error_details}'
        }), 500

@heic_jpg_bp.route('/download/<filename>')
def download_converted_file(filename):
    """Download converted file"""
    try:
        # Secure the filename
        filename = secure_filename(filename)
        
        # Get the upload folder from app config or use default
        from flask import current_app
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        
        file_path = os.path.join(upload_folder, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            flash('File not found', 'error')
            return redirect(url_for('heic_jpg_img.heic_jpg_converter'))
        
        # Determine the correct mimetype
        mimetype = mimetypes.guess_type(file_path)[0]
        if not mimetype:
            if filename.lower().endswith(('.heic', '.heif')):
                mimetype = 'image/heif'
            else:
                mimetype = 'application/octet-stream'
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('heic_jpg_img.heic_jpg_converter'))

@heic_jpg_bp.route('/preview/<filename>')
def preview_file(filename):
    """Preview converted file (for images)"""
    try:
        filename = secure_filename(filename)
        from flask import current_app
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Check if it's an image file that can be previewed
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return send_file(file_path, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'File type not previewable'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@heic_jpg_bp.route('/info/<filename>')
def get_file_info(filename):
    """Get information about a HEIC file"""
    try:
        filename = secure_filename(filename)
        from flask import current_app
        upload_folder = getattr(current_app.config, 'UPLOAD_FOLDER', 'uploads')
        file_path = os.path.join(upload_folder, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Check if HEIC support is available
        if not HEICProcessor.is_heic_supported():
            return jsonify({'error': 'HEIC support not available'}), 400
        
        processor = HEICProcessor()
        file_info = processor.get_heic_info(file_path)
        
        return jsonify({
            'success': True,
            'info': file_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@heic_jpg_bp.route('/batch-convert', methods=['POST'])
def batch_convert_heic():
    """Batch convert multiple HEIC files"""
    try:
        # Check if HEIC support is available
        if not HEICProcessor.is_heic_supported():
            return jsonify({
                'success': False,
                'error': 'HEIC support is not available'
            }), 400

        # Get parameters
        conversion_mode = request.form.get('conversion_mode', 'heic_to_jpg')
        quality = int(request.form.get('quality', 95))
        
        # Get files
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files uploaded'
            }), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({
                'success': False,
                'error': 'No files provided'
            }), 400
        
        # Save all files temporarily
        temp_files = []
        for file in files:
            if file.filename and allowed_file(file.filename):
                temp_file = tempfile.NamedTemporaryFile(delete=False, 
                                                      suffix=f'_{secure_filename(file.filename)}')
                file.save(temp_file.name)
                temp_file.close()
                temp_files.append(temp_file.name)
        
        if not temp_files:
            return jsonify({
                'success': False,
                'error': 'No valid files found'
            }), 400
        
        # Process batch conversion
        processor = HEICProcessor()
        
        if conversion_mode == 'heic_to_jpg':
            results = processor.batch_convert_heic(temp_files, 'JPEG', quality)
        else:
            # For individual processing when batch method for JPG→HEIC not available
            results = {
                'converted': [],
                'failed': [],
                'total_processed': len(temp_files),
                'success_count': 0,
                'failure_count': 0
            }
            
            for temp_file in temp_files:
                try:
                    output_path = processor.jpg_to_heic(temp_file, quality)
                    results['converted'].append({
                        'input': temp_file,
                        'output': output_path,
                        'status': 'success'
                    })
                    results['success_count'] += 1
                except Exception as e:
                    results['failed'].append({
                        'input': temp_file,
                        'error': str(e),
                        'status': 'failed'
                    })
                    results['failure_count'] += 1
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        # Clean up temp files on error
        if 'temp_files' in locals():
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except:
                    pass
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@heic_jpg_bp.route('/check-support')
def check_heic_support():
    """Check if HEIC support is available"""
    try:
        supported = HEICProcessor.is_heic_supported()
        formats = HEICProcessor.get_supported_formats() if supported else None
        
        return jsonify({
            'supported': supported,
            'formats': formats,
            'message': 'HEIC support available' if supported else 'HEIC support not available - install pillow-heif'
        })
        
    except Exception as e:
        return jsonify({
            'supported': False,
            'error': str(e)
        }), 500

# API routes for frontend compatibility
@heic_jpg_bp.route('/api/heic-info', methods=['POST'])
def api_heic_info():
    """API endpoint for getting HEIC file information (frontend compatibility)"""
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

        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}')
        file.save(temp_input.name)
        temp_input.close()

        try:
            # Get file info
            processor = HEICProcessor()
            file_info = processor.get_heic_info(temp_input.name)
            
            # Add file size and format info
            file_info['size'] = os.path.getsize(temp_input.name)
            file_info['dimensions'] = f"{file_info['width']} × {file_info['height']}"
            
            # Clean up temp file
            os.unlink(temp_input.name)
            
            return jsonify({
                'success': True,
                'info': file_info
            })
            
        except Exception as e:
            # Clean up temp file
            if os.path.exists(temp_input.name):
                os.unlink(temp_input.name)
            
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@heic_jpg_bp.route('/api/heic-preview', methods=['POST'])
def api_heic_preview():
    """API endpoint for generating HEIC preview (frontend compatibility)"""
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
            
            # Determine file type and generate appropriate preview
            file_ext = filename.lower().split('.')[-1]
            
            if file_ext in ['heic', 'heif']:
                # Generate web-compatible preview from HEIC file
                preview_path = processor.generate_preview(temp_input.name)
                
                # Read the preview as base64 for inline display
                import base64
                with open(preview_path, 'rb') as preview_file:
                    preview_data = base64.b64encode(preview_file.read()).decode('utf-8')
                
                # Clean up files
                os.unlink(temp_input.name)
                os.unlink(preview_path)
                
                return jsonify({
                    'success': True,
                    'preview': f'data:image/jpeg;base64,{preview_data}',
                    'format': 'HEIC'
                })
            else:
                # For JPG files, just return the file as-is
                import base64
                with open(temp_input.name, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                # Clean up temp file
                os.unlink(temp_input.name)
                
                return jsonify({
                    'success': True,
                    'preview': f'data:image/jpeg;base64,{img_data}',
                    'format': 'JPG'
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

@heic_jpg_bp.route('/api/heic-convert', methods=['POST'])
def api_heic_convert():
    """API endpoint for HEIC conversion (frontend compatibility)"""
    try:
        # Check if HEIC support is available
        if not HEICProcessor.is_heic_supported():
            return jsonify({
                'success': False,
                'error': 'HEIC support is not available. Please install pillow-heif library.'
            }), 400

        # Get parameters
        conversion_type = request.form.get('conversion_type', 'heic_to_jpg')
        quality = int(request.form.get('quality', 95))
        output_format = request.form.get('output_format', 'jpeg')
        preserve_metadata = request.form.get('preserve_metadata', 'false') == 'true'

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
