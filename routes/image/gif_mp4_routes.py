"""
GIF ⇄ MP4 Converter Routes
Fresh implementation with dedicated endpoints and advanced video processing
"""

from flask import Blueprint, request, render_template, jsonify, send_file, current_app, g
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
import tempfile
import logging
from datetime import datetime
import traceback
from pathlib import Path

# Import usage tracking decorators  
from middleware.usage_tracking import quota_required, track_conversion_result
from utils.video.gif_mp4_processor import GifMp4Processor

# Create blueprint with unique name
gif_mp4_bp = Blueprint('gif_mp4', __name__, url_prefix='/gif-mp4')

# Configuration
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB for video files
ALLOWED_EXTENSIONS = {
    'gif_to_mp4': {'gif'},
    'mp4_to_gif': {'mp4', 'mov', 'avi', 'mkv', 'webm'}
}

# Global storage for conversion results (in production, use Redis or database)
conversion_results = {}

# Setup logging
logger = logging.getLogger(__name__)


def allowed_file(filename, conversion_mode):
    """Check if file has allowed extension for specific conversion mode"""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(conversion_mode, set())


def get_file_size_mb(filepath):
    """Get file size in MB"""
    return os.path.getsize(filepath) / (1024 * 1024)


def cleanup_conversion_data(conversion_id):
    """Clean up conversion data and temporary files"""
    try:
        if conversion_id in conversion_results:
            result_data = conversion_results[conversion_id]
            
            # Clean up temporary files
            if 'temp_input_path' in result_data:
                temp_path = result_data['temp_input_path']
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
            if 'output_path' in result_data:
                output_path = result_data['output_path']
                if os.path.exists(output_path):
                    os.unlink(output_path)
            
            # Remove from results
            del conversion_results[conversion_id]
            
        logger.info(f"Cleaned up conversion {conversion_id}")
    except Exception as e:
        logger.error(f"Error cleaning up conversion {conversion_id}: {str(e)}")


@gif_mp4_bp.route('/')
@login_required
@quota_required(tool_name='gif_mp4_converter', check_file_size=True)
def gif_mp4_converter():
    """Main GIF ⇄ MP4 converter page"""
    try:
        # Check if FFmpeg is available
        try:
            processor = GifMp4Processor()
            ffmpeg_available = True
            ffmpeg_info = processor.validate_ffmpeg_installation()
            supported_formats = processor.get_supported_formats()
        except RuntimeError as e:
            ffmpeg_available = False
            ffmpeg_info = (False, str(e))
            supported_formats = None
        
        # Get usage information
        usage = None
        quota_exceeded = False
        if hasattr(g, 'usage_check') and g.usage_check:
            usage = {
                'conversions_used': g.usage_check.get('used', 0),
                'daily_limit': g.usage_check.get('limit', 20),
                'percentage': (g.usage_check.get('used', 0) / max(g.usage_check.get('limit', 20), 1)) * 100
            }
            quota_exceeded = usage['conversions_used'] >= usage['daily_limit']
        
        return render_template(
            'image/gif_mp4.html',
            ffmpeg_available=ffmpeg_available,
            ffmpeg_info=ffmpeg_info,
            max_file_size=MAX_FILE_SIZE // (1024 * 1024),
            supported_formats=supported_formats,
            usage=usage,
            quota_exceeded=quota_exceeded
        )
    except Exception as e:
        logger.error(f"Error loading converter page: {str(e)}")
        return render_template(
            'image/gif_mp4.html', 
            ffmpeg_available=False,
            ffmpeg_info=(False, "Error loading converter"),
            max_file_size=MAX_FILE_SIZE // (1024 * 1024)
        )


@gif_mp4_bp.route('/convert', methods=['POST'])
@quota_required(tool_name='gif_mp4_converter', check_file_size=True)
@track_conversion_result(tool_type='gif_mp4_converter')
def convert_gif_mp4():
    """Convert GIF to MP4 or MP4 to GIF"""
    try:
        # Initialize processor
        try:
            processor = GifMp4Processor()
        except RuntimeError as e:
            return jsonify({
                'success': False,
                'error': f'FFmpeg not available: {str(e)}'
            }), 400

        # Get conversion mode
        conversion_mode = request.form.get('conversion_mode', 'gif_to_mp4')
        if conversion_mode not in ['gif_to_mp4', 'mp4_to_gif']:
            return jsonify({
                'success': False,
                'error': 'Invalid conversion mode'
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

        # Validate file count
        if len(files) != 1:
            return jsonify({
                'success': False,
                'error': 'Please select exactly one file'
            }), 400

        file = files[0]
        
        # Validate file
        if not allowed_file(file.filename, conversion_mode):
            expected = list(ALLOWED_EXTENSIONS[conversion_mode])
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Expected: {", ".join(expected)}'
            }), 400

        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset position
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400

        # Generate unique conversion ID
        conversion_id = str(uuid.uuid4())
        
        # Create temporary directory for this conversion
        temp_dir = tempfile.mkdtemp(prefix=f'gif_mp4_{conversion_id}_')
        
        try:
            # Save uploaded file
            filename = secure_filename(file.filename)
            temp_input_path = os.path.join(temp_dir, filename)
            file.save(temp_input_path)
            
            # Set up for usage tracking
            g.input_file_path = temp_input_path
            
            # Get conversion parameters
            if conversion_mode == 'gif_to_mp4':
                quality = request.form.get('quality', 'high')
                fps = request.form.get('fps')
                fps = int(fps) if fps and fps.isdigit() else None
                scale = request.form.get('scale') or None
                optimize = request.form.get('optimize', 'true').lower() == 'true'
                
                # Convert GIF to MP4
                result = processor.gif_to_mp4(
                    input_path=temp_input_path,
                    quality=quality,
                    fps=fps,
                    scale=scale,
                    optimize=optimize
                )
                
                conversion_type = 'GIF → MP4'
                output_format = 'mp4'
                
            else:  # mp4_to_gif
                fps = int(request.form.get('fps', 15))
                scale = request.form.get('scale', '-1:480')
                start_time = request.form.get('start_time') or None
                duration = request.form.get('duration') or None
                palette_quality = request.form.get('palette_quality', 'high')
                loop_count = int(request.form.get('loop_count', 0))
                
                # Convert MP4 to GIF
                result = processor.mp4_to_gif(
                    input_path=temp_input_path,
                    fps=fps,
                    scale=scale,
                    start_time=start_time,
                    duration=duration,
                    palette_quality=palette_quality,
                    loop_count=loop_count
                )
                
                conversion_type = 'MP4 → GIF'
                output_format = 'gif'
            
            if not result['success']:
                cleanup_conversion_data(conversion_id)
                
                # Provide more user-friendly error messages
                error_msg = result['error']
                if 'height not divisible by 2' in error_msg or 'width not divisible by 2' in error_msg:
                    error_msg = 'Video dimensions are not compatible with MP4 format. This has been automatically fixed in the latest version.'
                elif 'timeout' in error_msg.lower():
                    error_msg = 'Conversion is taking too long. Please try with a smaller file or lower quality settings.'
                elif 'ffmpeg' in error_msg.lower():
                    error_msg = f'Video processing error: {error_msg}'
                
                return jsonify({
                    'success': False,
                    'error': error_msg
                }), 400
            
            # Store conversion results with cleanup info
            conversion_results[conversion_id] = {
                'result': result,
                'conversion_type': conversion_type,
                'output_format': output_format,
                'created_at': datetime.now(),
                'temp_dir': temp_dir,
                'temp_input_path': temp_input_path,
                'output_path': result['output_path'],
                'original_filename': filename
            }
            
            # Set up for usage tracking
            g.output_file_path = result['output_path']
            
            # Schedule cleanup after 10 minutes
            import threading
            import time
            
            def delayed_cleanup():
                time.sleep(600)  # 10 minutes
                cleanup_conversion_data(conversion_id)
            
            cleanup_thread = threading.Thread(target=delayed_cleanup, daemon=True)
            cleanup_thread.start()
            
            # Return success response
            response_data = {
                'success': True,
                'conversion_id': conversion_id,
                'conversion_type': conversion_type,
                'output_format': output_format,
                'input_size': result.get('input_size', file_size),
                'output_size': result.get('output_size', 0),
                'message': f'Successfully converted {filename} to {output_format.upper()}'
            }
            
            # Add format-specific information
            if conversion_mode == 'gif_to_mp4':
                response_data.update({
                    'compression_ratio': result.get('compression_ratio', 'N/A'),
                    'quality': result.get('quality', quality),
                    'fps': result.get('output_info', {}).get('fps', fps)
                })
            else:
                response_data.update({
                    'size_ratio': result.get('size_ratio', 'N/A'),
                    'fps': result.get('fps', fps),
                    'palette_quality': result.get('palette_quality', palette_quality),
                    'loop_count': result.get('loop_count', loop_count)
                })
            
            return jsonify(response_data)
            
        except Exception as e:
            # Clean up on error
            try:
                if 'temp_input_path' in locals() and os.path.exists(temp_input_path):
                    os.unlink(temp_input_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass
            raise e
            
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Internal server error during conversion'
        }), 500


@gif_mp4_bp.route('/download/<conversion_id>')
def download_converted_file(conversion_id):
    """Download converted file"""
    try:
        if conversion_id not in conversion_results:
            return jsonify({'error': 'Conversion not found or expired'}), 404
        
        conversion_data = conversion_results[conversion_id]
        result = conversion_data['result']
        output_path = result['output_path']
        
        if not os.path.exists(output_path):
            return jsonify({'error': 'Converted file not found'}), 404
        
        # Determine download filename
        original_filename = conversion_data.get('original_filename', 'converted')
        name_without_ext = os.path.splitext(original_filename)[0]
        output_format = conversion_data['output_format']
        download_filename = f"{name_without_ext}_converted.{output_format}"
        
        def cleanup_after_send():
            """Clean up after file is sent"""
            try:
                cleanup_conversion_data(conversion_id)
            except:
                pass
        
        # Schedule cleanup after download
        import threading
        cleanup_thread = threading.Thread(target=cleanup_after_send, daemon=True)
        cleanup_thread.start()
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype=f'video/mp4' if output_format == 'mp4' else 'image/gif'
        )
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Download failed'}), 500


@gif_mp4_bp.route('/preview/<conversion_id>')
def preview_converted_file(conversion_id):
    """Get preview information for converted file"""
    try:
        if conversion_id not in conversion_results:
            return jsonify({'error': 'Conversion not found or expired'}), 404
        
        conversion_data = conversion_results[conversion_id]
        result = conversion_data['result']
        output_path = result['output_path']
        
        if not os.path.exists(output_path):
            return jsonify({'error': 'Converted file not found'}), 404
        
        # Return file information for preview
        file_info = {
            'success': True,
            'conversion_type': conversion_data['conversion_type'],
            'output_format': conversion_data['output_format'],
            'file_size': os.path.getsize(output_path),
            'created_at': conversion_data['created_at'].isoformat()
        }
        
        # Add format-specific info
        if 'input_info' in result:
            file_info['input_info'] = result['input_info']
        if 'output_info' in result:
            file_info['output_info'] = result['output_info']
        
        return jsonify(file_info)
        
    except Exception as e:
        logger.error(f"Preview error: {str(e)}")
        return jsonify({'error': 'Preview failed'}), 500


@gif_mp4_bp.route('/status/<conversion_id>')
def get_conversion_status(conversion_id):
    """Get status of a conversion"""
    try:
        if conversion_id not in conversion_results:
            return jsonify({
                'success': False,
                'status': 'not_found',
                'error': 'Conversion not found or expired'
            }), 404
        
        conversion_data = conversion_results[conversion_id]
        
        return jsonify({
            'success': True,
            'status': 'completed',
            'conversion_type': conversion_data['conversion_type'],
            'output_format': conversion_data['output_format'],
            'created_at': conversion_data['created_at'].isoformat(),
            'ready_for_download': True
        })
        
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Status check failed'
        }), 500


@gif_mp4_bp.route('/info')
def converter_info():
    """Get converter information and capabilities"""
    try:
        processor = GifMp4Processor()
        ffmpeg_available = True
        ffmpeg_info = processor.validate_ffmpeg_installation()
        supported_formats = processor.get_supported_formats()
    except RuntimeError as e:
        ffmpeg_available = False
        ffmpeg_info = (False, str(e))
        supported_formats = None
    
    return jsonify({
        'success': True,
        'ffmpeg_available': ffmpeg_available,
        'ffmpeg_status': ffmpeg_info[1] if ffmpeg_info else 'Unknown',
        'supported_formats': supported_formats,
        'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
        'conversion_modes': ['gif_to_mp4', 'mp4_to_gif']
    })


# Error handlers specific to this blueprint
@gif_mp4_bp.errorhandler(413)
def handle_file_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'success': False,
        'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
    }), 413


@gif_mp4_bp.errorhandler(500)
def handle_internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal error in gif-mp4 converter: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error. Please try again.'
    }), 500


# Cleanup old conversions on startup
def cleanup_old_conversions():
    """Clean up old conversion data"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=1)
        to_cleanup = []
        
        for conversion_id, data in conversion_results.items():
            if data.get('created_at', datetime.now()) < cutoff_time:
                to_cleanup.append(conversion_id)
        
        for conversion_id in to_cleanup:
            cleanup_conversion_data(conversion_id)
            
        if to_cleanup:
            logger.info(f"Cleaned up {len(to_cleanup)} old conversions")
            
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")


# Schedule periodic cleanup
import atexit
from datetime import timedelta
atexit.register(cleanup_old_conversions)
