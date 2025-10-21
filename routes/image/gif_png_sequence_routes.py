# routes/image/gif_png_sequence_routes.py
# Fresh GIF ⇄ PNG Sequence Converter Routes

import os
import uuid
import zipfile
import tempfile
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, send_file, current_app, g
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from PIL import Image

# Import middleware and utilities
from middleware.usage_tracking import quota_required, track_conversion_result
from utils.image.gif_processor import GIFProcessor
from config import GIF_CONVERTER_CONFIG


# Create blueprint
gif_png_sequence_bp = Blueprint(
    'gif_png_sequence', 
    __name__, 
    url_prefix='/gif-png-sequence'
)

# Global storage for conversion results
conversion_results = {}


def threaded_cleanup_with_context(conversion_id: str, app, delay_seconds: int = 5):
    """Thread-safe cleanup function that properly handles Flask app context"""
    import threading
    import time
    
    def cleanup_with_context():
        try:
            # Wait for specified delay
            time.sleep(delay_seconds)
            
            # Use the Flask app context for proper logging
            with app.app_context():
                cleanup_conversion_data(conversion_id, app)
        except Exception as e:
            # Fallback logging if Flask context fails
            logging.getLogger(__name__).error(
                f"Error in threaded cleanup for conversion {conversion_id}: {str(e)}"
            )
    
    thread = threading.Thread(target=cleanup_with_context, daemon=True)
    thread.start()


def cleanup_conversion_data(conversion_id: str, app=None):
    """Clean up conversion data and temporary files"""
    # Setup logger - use standard logging if no Flask app context available
    try:
        if app and hasattr(app, 'logger'):
            logger = app.logger
        else:
            try:
                # Try to use Flask's current_app if in context
                logger = current_app.logger
            except RuntimeError:
                # Fallback to standard Python logging when outside Flask context
                logger = logging.getLogger(__name__)
        
        if conversion_id in conversion_results:
            result_data = conversion_results[conversion_id]
            
            # Clean up temporary directories
            if 'temp_dir' in result_data:
                temp_dir = result_data['temp_dir']
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            
            if 'output_dir' in result_data:
                output_dir = result_data['output_dir']
                if os.path.exists(output_dir):
                    shutil.rmtree(output_dir, ignore_errors=True)
            
            # Remove from results
            del conversion_results[conversion_id]
            
        logger.info(f"Cleaned up conversion {conversion_id}")
    except Exception as e:
        # Use standard logging as last resort for error reporting
        try:
            if app and hasattr(app, 'logger'):
                app.logger.error(f"Error cleaning up conversion {conversion_id}: {str(e)}")
            else:
                try:
                    current_app.logger.error(f"Error cleaning up conversion {conversion_id}: {str(e)}")
                except RuntimeError:
                    # Final fallback to standard logging
                    logging.getLogger(__name__).error(f"Error cleaning up conversion {conversion_id}: {str(e)}")
        except Exception:
            # Ultimate fallback - just use standard logging
            logging.getLogger(__name__).error(f"Error cleaning up conversion {conversion_id}: {str(e)}")


def validate_file_upload(file, conversion_mode: str):
    """Validate uploaded file based on conversion mode"""
    if not file or file.filename == '':
        return False, "No file selected"
    
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset position
    
    if size > GIF_CONVERTER_CONFIG['max_file_size']:
        return False, f"File too large. Maximum size: {GIF_CONVERTER_CONFIG['max_file_size'] // (1024*1024)}MB"
    
    # Validate file extension based on mode
    if conversion_mode == 'gif_to_png':
        if file_ext not in GIF_CONVERTER_CONFIG['supported_input_formats']['gif_to_png']:
            return False, "Only GIF files are supported for GIF to PNG conversion"
    elif conversion_mode == 'png_to_gif':
        if file_ext not in GIF_CONVERTER_CONFIG['supported_input_formats']['png_to_gif']:
            return False, "Only PNG, JPG, and JPEG files are supported for PNG to GIF conversion"
    
    return True, "File is valid"


@gif_png_sequence_bp.route('/')
@login_required
@quota_required(tool_name='gif_converter', check_file_size=True)
def converter_page():
    """Main GIF ⇄ PNG Sequence converter page"""
    try:
        # Get usage information for display
        usage_info = None
        if hasattr(g, 'usage_check') and g.usage_check:
            usage_info = {
                'conversions_used': g.usage_check.get('used', 0),
                'daily_limit': g.usage_check.get('limit', 20),
                'percentage': (g.usage_check.get('used', 0) / max(g.usage_check.get('limit', 20), 1)) * 100
            }
        
        return render_template(
            'image/gif_png_sequence.html',
            title="GIF ⇄ PNG Sequence Converter",
            usage=usage_info,
            config=GIF_CONVERTER_CONFIG
        )
    except Exception as e:
        current_app.logger.error(f"Error loading converter page: {str(e)}")
        return render_template('errors/500.html'), 500


@gif_png_sequence_bp.route('/convert/gif-to-png', methods=['POST'])
@quota_required(tool_name='gif_converter', check_file_size=True)
@track_conversion_result(tool_type='gif_converter')
def convert_gif_to_png():
    """API endpoint for converting GIF to PNG sequence"""
    try:
        # Validate file upload
        if 'gif_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['gif_file']
        is_valid, message = validate_file_upload(file, 'gif_to_png')
        if not is_valid:
            return jsonify({'success': False, 'error': message}), 400
        
        # Get conversion settings
        settings = {
            'preserve_timing': request.form.get('preserve_timing', 'true').lower() == 'true',
            'optimize_png': request.form.get('optimize_png', 'true').lower() == 'true'
        }
        
        # Create unique conversion ID and temp directory
        conversion_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp(prefix=f'gif_convert_{conversion_id}_')
        
        # Save uploaded file
        input_filename = secure_filename(file.filename)
        input_path = os.path.join(temp_dir, input_filename)
        file.save(input_path)
        
        # Set up for usage tracking
        g.input_file_path = input_path
        
        # Initialize GIF processor
        processor = GIFProcessor()
        
        # Convert GIF to PNG sequence
        output_dir = os.path.join(temp_dir, 'frames')
        result = processor.gif_to_png_sequence(
            gif_path=input_path,
            output_dir=output_dir,
            preserve_timing=settings['preserve_timing'],
            optimize=settings['optimize_png']
        )
        
        if not result['success']:
            cleanup_conversion_data(conversion_id)
            return jsonify({
                'success': False,
                'error': f"Conversion failed: {result['message']}"
            }), 500
        
        # Create ZIP file with all frames
        zip_filename = f"gif_frames_{conversion_id}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for frame_path in result['frames']:
                frame_filename = os.path.basename(frame_path)
                zip_file.write(frame_path, frame_filename)
            
            # Add timing information if preserving timing
            if settings['preserve_timing'] and result.get('timing_info'):
                import json
                timing_data = {
                    'frame_durations': result['timing_info'],
                    'total_duration': result['total_duration'],
                    'frame_count': result['frame_count'],
                    'average_duration': result['average_duration']
                }
                zip_file.writestr('timing_info.json', json.dumps(timing_data, indent=2))
        
        # Store conversion results
        conversion_results[conversion_id] = {
            'type': 'gif_to_png',
            'input_file': input_filename,
            'result': result,
            'settings': settings,
            'created_at': datetime.now(),
            'temp_dir': temp_dir,
            'output_dir': output_dir,
            'zip_path': zip_path,
            'zip_filename': zip_filename
        }
        
        # Set up for usage tracking
        g.output_file_path = zip_path
        
        return jsonify({
            'success': True,
            'conversion_id': conversion_id,
            'frame_count': result['frame_count'],
            'output_format': 'png',
            'zip_filename': zip_filename,
            'file_size': os.path.getsize(zip_path),
            'timing_info': result.get('timing_info', []),
            'message': f"Successfully extracted {result['frame_count']} frames from GIF"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in GIF to PNG conversion: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error during conversion'
        }), 500


@gif_png_sequence_bp.route('/convert/png-to-gif', methods=['POST'])
@quota_required(tool_name='gif_converter', check_file_size=True)
@track_conversion_result(tool_type='gif_converter')
def convert_png_to_gif():
    """API endpoint for converting PNG sequence to GIF"""
    try:
        # Validate file uploads
        if 'image_files' not in request.files:
            return jsonify({'success': False, 'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('image_files')
        if not files or len(files) == 0:
            return jsonify({'success': False, 'error': 'No files selected'}), 400
        
        # Validate each file
        for file in files:
            is_valid, message = validate_file_upload(file, 'png_to_gif')
            if not is_valid:
                return jsonify({'success': False, 'error': f"File {file.filename}: {message}"}), 400
        
        if len(files) > GIF_CONVERTER_CONFIG['max_frames']:
            return jsonify({
                'success': False,
                'error': f"Too many files. Maximum: {GIF_CONVERTER_CONFIG['max_frames']}"
            }), 400
        
        # Get conversion settings
        settings = {
            'frame_duration': int(request.form.get('frame_duration', 100)),
            'loop_count': int(request.form.get('loop_count', 0)),
            'optimize': request.form.get('optimize', 'true').lower() == 'true',
            'dithering': request.form.get('dithering', 'false').lower() == 'true',
            'quality': request.form.get('quality', 'medium')
        }
        
        # Create unique conversion ID and temp directory
        conversion_id = str(uuid.uuid4())
        temp_dir = tempfile.mkdtemp(prefix=f'png_convert_{conversion_id}_')
        
        input_dir = os.path.join(temp_dir, 'inputs')
        os.makedirs(input_dir)
        
        # Save uploaded files
        input_paths = []
        total_size = 0
        for i, file in enumerate(files):
            filename = f"frame_{i:04d}_{secure_filename(file.filename)}"
            input_path = os.path.join(input_dir, filename)
            file.save(input_path)
            input_paths.append(input_path)
            total_size += os.path.getsize(input_path)
        
        # Set up for usage tracking (use first file)
        g.input_file_path = input_paths[0] if input_paths else None
        
        # Initialize GIF processor
        processor = GIFProcessor()
        
        # Convert PNG sequence to GIF
        output_path = os.path.join(temp_dir, f'converted_{conversion_id}.gif')
        result = processor.png_sequence_to_gif(
            image_paths=input_paths,
            output_path=output_path,
            frame_duration=settings['frame_duration'],
            loop_count=settings['loop_count'],
            optimize=settings['optimize'],
            dithering=settings['dithering'],
            quality_settings=GIF_CONVERTER_CONFIG['quality_levels'][settings['quality']]
        )
        
        if not result['success']:
            cleanup_conversion_data(conversion_id)
            return jsonify({
                'success': False,
                'error': f"Conversion failed: {result['message']}"
            }), 500
        
        # Store conversion results
        conversion_results[conversion_id] = {
            'type': 'png_to_gif',
            'input_files': [secure_filename(f.filename) for f in files],
            'result': result,
            'settings': settings,
            'created_at': datetime.now(),
            'temp_dir': temp_dir,
            'input_dir': input_dir,
            'output_path': output_path
        }
        
        # Set up for usage tracking
        g.output_file_path = output_path
        
        return jsonify({
            'success': True,
            'conversion_id': conversion_id,
            'frame_count': len(files),
            'output_format': 'gif',
            'file_size': result.get('file_size', 0),
            'output_filename': os.path.basename(output_path),
            'message': f"Successfully created GIF from {len(files)} frames"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in PNG to GIF conversion: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error during conversion'
        }), 500


@gif_png_sequence_bp.route('/download/<conversion_id>/<result_type>')
def download_result(conversion_id, result_type):
    """Download conversion results"""
    try:
        if conversion_id not in conversion_results:
            return jsonify({'error': 'Conversion not found'}), 404
        
        result_data = conversion_results[conversion_id]
        
        if result_type == 'zip' and result_data['type'] == 'gif_to_png':
            # Download ZIP file of PNG frames
            zip_path = result_data.get('zip_path')
            if zip_path and os.path.exists(zip_path):
                # Schedule cleanup in thread with proper Flask context
                threaded_cleanup_with_context(conversion_id, current_app._get_current_object())
                
                return send_file(
                    zip_path, 
                    as_attachment=True, 
                    download_name=f"gif_frames_{conversion_id}.zip",
                    mimetype='application/zip'
                )
        
        elif result_type == 'gif' and result_data['type'] == 'png_to_gif':
            # Download GIF file
            gif_path = result_data.get('output_path')
            if gif_path and os.path.exists(gif_path):
                # Schedule cleanup in thread with proper Flask context
                threaded_cleanup_with_context(conversion_id, current_app._get_current_object())
                
                return send_file(
                    gif_path,
                    as_attachment=True,
                    download_name=f"converted_{conversion_id}.gif",
                    mimetype='image/gif'
                )
        
        return jsonify({'error': 'File not found'}), 404
        
    except Exception as e:
        current_app.logger.error(f"Error downloading result: {str(e)}")
        return jsonify({'error': 'Download failed'}), 500


@gif_png_sequence_bp.route('/preview/<conversion_id>')
def preview_conversion(conversion_id):
    """Get preview data for conversion result"""
    try:
        if conversion_id not in conversion_results:
            return jsonify({'error': 'Conversion not found'}), 404
        
        result_data = conversion_results[conversion_id]
        
        preview_data = {
            'conversion_id': conversion_id,
            'type': result_data['type'],
            'created_at': result_data['created_at'].isoformat(),
            'settings': result_data['settings']
        }
        
        if result_data['type'] == 'gif_to_png':
            # Get frame information
            frames_info = []
            if 'output_dir' in result_data and os.path.exists(result_data['output_dir']):
                for filename in sorted(os.listdir(result_data['output_dir'])):
                    if filename.lower().endswith('.png'):
                        frame_path = os.path.join(result_data['output_dir'], filename)
                        frames_info.append({
                            'filename': filename,
                            'size': os.path.getsize(frame_path)
                        })
            
            preview_data.update({
                'frame_count': len(frames_info),
                'frames': frames_info[:10],  # Limit to first 10 frames
                'timing_info': result_data['result'].get('timing_info', [])
            })
        
        elif result_data['type'] == 'png_to_gif':
            gif_path = result_data.get('output_path', '')
            if os.path.exists(gif_path):
                preview_data.update({
                    'file_size': os.path.getsize(gif_path),
                    'frame_count': result_data['result'].get('frame_count', 0),
                    'output_filename': os.path.basename(gif_path)
                })
        
        return jsonify({
            'success': True,
            'preview': preview_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting preview: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get preview'
        }), 500


@gif_png_sequence_bp.route('/cleanup', methods=['POST'])
def cleanup_temp():
    """Clean up temporary files"""
    try:
        conversion_id = request.json.get('conversion_id') if request.json else None
        if conversion_id:
            cleanup_conversion_data(conversion_id)
            return jsonify({'success': True, 'message': 'Cleanup completed'})
        else:
            return jsonify({'success': False, 'error': 'No conversion ID provided'}), 400
    except Exception as e:
        current_app.logger.error(f"Error during cleanup: {str(e)}")
        return jsonify({'success': False, 'error': 'Cleanup failed'}), 500


# Cleanup old conversions periodically
@gif_png_sequence_bp.before_app_request
def cleanup_old_conversions():
    """Clean up conversions older than 1 hour"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=1)
        expired_conversions = []
        
        for conversion_id, data in conversion_results.items():
            if data['created_at'] < cutoff_time:
                expired_conversions.append(conversion_id)
        
        for conversion_id in expired_conversions:
            cleanup_conversion_data(conversion_id)
            
    except Exception as e:
        current_app.logger.error(f"Error cleaning up old conversions: {str(e)}")


# Error handlers
@gif_png_sequence_bp.errorhandler(413)
def file_too_large(e):
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size: {GIF_CONVERTER_CONFIG["max_file_size"] // (1024*1024)}MB'
    }), 413


@gif_png_sequence_bp.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded. Please try again later.'
    }), 429
