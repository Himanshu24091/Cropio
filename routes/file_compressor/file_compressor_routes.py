from flask import Blueprint, render_template, request, jsonify, send_file, current_app, session
import os
import tempfile
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import uuid
import traceback
from datetime import datetime
import shutil
import zipfile

# Import utility functions
from utils.file_compressor.file_compressor_utils import (
    process_file_compression,
    validate_compression_file,
    get_compression_stats,
    cleanup_temp_files,
    create_compression_summary,
    estimate_compression_time,
    apply_quality_based_compression,
    apply_target_size_compression
)

# Create blueprint
file_compressor_bp = Blueprint('file_compressor', __name__, url_prefix='/file-compressor')

# Configuration constants
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1GB per file
MAX_FILES_PER_BATCH = 50
ALLOWED_EXTENSIONS = {
    'images': {'jpg', 'jpeg', 'png', 'webp'},
    'documents': {'pdf', 'docx', 'pptx'},
    'videos': {'mp4', 'avi', 'mkv'},
    'archives': {'zip', 'rar'}
}

# Compression modes
COMPRESSION_MODES = {
    'quality_based': 'Quality-Based Compression',
    'target_size': 'Target Size Compression'
}

# Quality levels
QUALITY_LEVELS = {
    'high': 90,
    'medium': 75,
    'low': 50,
    'custom': None  # Will use custom_quality value
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    all_extensions = set()
    for ext_set in ALLOWED_EXTENSIONS.values():
        all_extensions.update(ext_set)
    
    return extension in all_extensions

def get_file_extension(filename):
    """Get file extension from filename"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def get_file_category(filename):
    """Determine file category based on extension"""
    if '.' not in filename:
        return None
    
    extension = filename.rsplit('.', 1)[1].lower()
    
    for category, extensions in ALLOWED_EXTENSIONS.items():
        if extension in extensions:
            return category.rstrip('s')  # Remove plural 's'
    
    return 'file'

@file_compressor_bp.route('/')
def index():
    """Render the File Compressor interface"""
    try:
        return render_template('file_compressor/file_compressor.html')
    except Exception as e:
        current_app.logger.error(f"Error rendering file compressor template: {str(e)}")
        return jsonify({'error': 'Failed to load file compressor interface'}), 500

@file_compressor_bp.route('/compress', methods=['POST'])
def compress_files():
    """
    Compress uploaded files using specified compression settings
    Supports both quality-based and target size compression
    """
    session_id = str(uuid.uuid4())
    temp_dirs = []
    
    try:
        # Debug logging
        current_app.logger.info(f"File compression request received (session: {session_id})")
        current_app.logger.info(f"  Files: {list(request.files.keys())}")
        current_app.logger.info(f"  Form data: {dict(request.form)}")
        
        # Validate request
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided', 'success': False}), 400
        
        files = request.files.getlist('files')
        if not files or (len(files) == 1 and files[0].filename == ''):
            return jsonify({'error': 'No files selected', 'success': False}), 400
        
        # Check file count limit
        if len(files) > MAX_FILES_PER_BATCH:
            return jsonify({
                'error': f'Too many files. Maximum {MAX_FILES_PER_BATCH} files allowed per batch.',
                'success': False
            }), 400
        
        # Get compression parameters
        compression_mode = request.form.get('compression_mode', 'quality_based')
        if compression_mode not in COMPRESSION_MODES:
            return jsonify({'error': 'Invalid compression mode', 'success': False}), 400
        
        current_app.logger.info(f"  Compression mode: {compression_mode}")
        
        # Get compression options (support both 'on' and 'true'/'false' formats)
        def parse_checkbox_value(value):
            """Parse checkbox value from different formats"""
            if value is None:
                return False
            value_str = str(value).lower()
            return value_str in ('on', 'true', '1', 'yes')
        
        compression_options = {
            'mode': compression_mode,
            'ai_optimization': parse_checkbox_value(request.form.get('ai_optimization')),
            'remove_metadata': parse_checkbox_value(request.form.get('remove_metadata')),
            'lossless_mode': parse_checkbox_value(request.form.get('lossless_mode')),
            'password_protection': parse_checkbox_value(request.form.get('password_protection')),
            'compression_password': request.form.get('compression_password') or request.form.get('password', ''),
        }
        
        # Quality-based compression options
        if compression_mode == 'quality_based':
            quality_level = request.form.get('quality_level', 'high')
            if quality_level == 'custom':
                try:
                    custom_quality = int(request.form.get('custom_quality', 85))
                    compression_options['quality'] = max(10, min(100, custom_quality))
                except (ValueError, TypeError):
                    compression_options['quality'] = 85
            else:
                compression_options['quality'] = QUALITY_LEVELS.get(quality_level, 90)
        
        # Target size compression options
        elif compression_mode == 'target_size':
            try:
                target_size = float(request.form.get('target_size', 10))
                size_unit = request.form.get('size_unit', 'MB')
                max_iterations = int(request.form.get('max_iterations', 5))
                
                # Convert to bytes
                unit_multipliers = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
                target_size_bytes = target_size * unit_multipliers.get(size_unit, 1024**2)
                
                compression_options.update({
                    'target_size': target_size_bytes,
                    'max_iterations': max(1, min(10, max_iterations))
                })
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid target size parameters', 'success': False}), 400
        
        current_app.logger.info(f"  Compression options: {compression_options}")
        
        # Create temporary directories
        input_temp_dir = tempfile.mkdtemp(prefix=f'compress_input_{session_id}_')
        output_temp_dir = tempfile.mkdtemp(prefix=f'compress_output_{session_id}_')
        temp_dirs.extend([input_temp_dir, output_temp_dir])
        
        # Process each uploaded file
        processed_files = []
        compression_stats = {
            'total_files': len(files),
            'successful_compressions': 0,
            'failed_compressions': 0,
            'total_input_size': 0,
            'total_output_size': 0,
            'processing_time': 0,
            'errors': []
        }
        
        start_time = datetime.now()
        
        for file_index, file in enumerate(files):
            try:
                current_app.logger.info(f"  Processing file {file_index + 1}/{len(files)}: {file.filename}")
                
                # Validate file
                if not file or file.filename == '':
                    compression_stats['failed_compressions'] += 1
                    compression_stats['errors'].append(f"Empty file at index {file_index}")
                    continue
                
                if not allowed_file(file.filename):
                    compression_stats['failed_compressions'] += 1
                    compression_stats['errors'].append(f"Invalid file type: {file.filename}")
                    continue
                
                # Check file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    compression_stats['failed_compressions'] += 1
                    compression_stats['errors'].append(f"File too large: {file.filename} ({file_size // (1024**3)}GB)")
                    continue
                
                compression_stats['total_input_size'] += file_size
                
                # Save uploaded file
                filename = secure_filename(file.filename)
                if not filename:
                    filename = f"file_{file_index + 1}.{get_file_extension(file.filename)}"
                
                input_path = os.path.join(input_temp_dir, filename)
                file.save(input_path)
                
                # Validate file content
                if not validate_compression_file(input_path):
                    compression_stats['failed_compressions'] += 1
                    compression_stats['errors'].append(f"Invalid or corrupted file: {filename}")
                    continue
                
                # Generate output filename
                base_name = os.path.splitext(filename)[0]
                file_extension = get_file_extension(filename)
                output_filename = f"{base_name}_compressed.{file_extension}"
                output_path = os.path.join(output_temp_dir, output_filename)
                
                # Compress the file
                current_app.logger.info(f"    Starting compression: {input_path} -> {output_path}")
                
                compression_result = process_file_compression(
                    input_path, 
                    output_path, 
                    compression_options
                )
                
                if compression_result['success']:
                    # Verify output file exists and has reasonable size
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        output_size = os.path.getsize(output_path)
                        compression_stats['total_output_size'] += output_size
                        compression_stats['successful_compressions'] += 1
                        
                        # Include password protection info if applicable
                        file_info = {
                            'original_filename': file.filename,
                            'compressed_filename': output_filename,
                            'original_size': file_size,
                            'compressed_size': output_size,
                            'compression_ratio': ((file_size - output_size) / file_size) * 100,
                            'file_category': get_file_category(file.filename)
                        }
                        
                        # Add password protection details if present
                        if compression_result.get('password_protected'):
                            file_info['password_protected'] = True
                            file_info['protection_method'] = compression_result.get('protection_method', 'Password protected')
                            if compression_result.get('password_hint'):
                                file_info['password_hint'] = compression_result.get('password_hint')
                        
                        # Add any additional notes
                        if compression_result.get('note'):
                            file_info['note'] = compression_result.get('note')
                        
                        processed_files.append(file_info)
                        
                        current_app.logger.info(f"    Compression successful: {file_size} -> {output_size} bytes")
                    else:
                        compression_stats['failed_compressions'] += 1
                        compression_stats['errors'].append(f"Compression failed to produce output: {filename}")
                else:
                    compression_stats['failed_compressions'] += 1
                    compression_stats['errors'].append(f"Compression failed: {filename} - {compression_result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                current_app.logger.error(f"Error processing file {file.filename}: {str(e)}")
                compression_stats['failed_compressions'] += 1
                compression_stats['errors'].append(f"Processing error: {file.filename} - {str(e)}")
                continue
        
        # Calculate processing time
        end_time = datetime.now()
        compression_stats['processing_time'] = (end_time - start_time).total_seconds()
        
        # Check if any files were processed successfully
        if compression_stats['successful_compressions'] == 0:
            return jsonify({
                'error': 'No files could be compressed successfully',
                'success': False,
                'stats': compression_stats
            }), 400
        
        # Create downloadable archive if multiple files, or single file download
        if len(processed_files) > 1:
            # Create ZIP archive
            archive_filename = f'compressed_files_{session_id[:8]}.zip'
            archive_path = os.path.join(output_temp_dir, archive_filename)
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for processed_file in processed_files:
                    file_path = os.path.join(output_temp_dir, processed_file['compressed_filename'])
                    if os.path.exists(file_path):
                        zipf.write(file_path, processed_file['compressed_filename'])
            
            download_filename = archive_filename
            download_path = archive_path
        else:
            # Single file download
            processed_file = processed_files[0]
            download_filename = processed_file['compressed_filename']
            download_path = os.path.join(output_temp_dir, download_filename)
        
        # Store download information in a JSON file for more reliable access
        import json
        download_info = {
            'session_id': session_id,
            'temp_dir': output_temp_dir,
            'filename': download_filename,
            'file_path': download_path,
            'created_at': datetime.now().isoformat()
        }
        
        # Save download info to a file
        info_file_path = os.path.join(output_temp_dir, f'download_info_{session_id}.json')
        with open(info_file_path, 'w') as f:
            json.dump(download_info, f)
        
        current_app.logger.info(f"Download info saved for session: {session_id}")
        
        # Calculate final statistics
        if compression_stats['total_input_size'] > 0:
            overall_compression_ratio = ((compression_stats['total_input_size'] - compression_stats['total_output_size']) / compression_stats['total_input_size']) * 100
        else:
            overall_compression_ratio = 0
        
        # Clean up input files
        try:
            shutil.rmtree(input_temp_dir, ignore_errors=True)
        except Exception:
            pass
        
        current_app.logger.info(f"Compression completed: {compression_stats}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully compressed {compression_stats["successful_compressions"]} file(s)',
            'stats': {
                'files_processed': compression_stats['successful_compressions'],
                'original_size': compression_stats['total_input_size'],
                'compressed_size': compression_stats['total_output_size'],
                'compression_ratio': round(overall_compression_ratio, 1),
                'processing_time': round(compression_stats['processing_time'], 2),
                'space_saved': compression_stats['total_input_size'] - compression_stats['total_output_size']
            },
            'download_url': f'/file-compressor/download/{session_id}',
            'processed_files': processed_files,
            'session_id': session_id
        })
        
    except RequestEntityTooLarge:
        return jsonify({
            'error': 'File too large. Maximum file size is 1GB per file.',
            'success': False
        }), 413
        
    except Exception as e:
        current_app.logger.error(f"Error during compression: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Clean up temporary directories on error
        for temp_dir in temp_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        return jsonify({
            'error': f'Compression failed: {str(e)}',
            'success': False
        }), 500

@file_compressor_bp.route('/download/<session_id>')
def download_compressed(session_id):
    """Download compressed file(s) for a specific session"""
    try:
        import json
        current_app.logger.info(f"Download request for session: {session_id}")
        
        # Look for the download info file in temp directories
        temp_base = tempfile.gettempdir()
        info_file_path = None
        download_info = None
        
        # Search for the info file in temp directories
        for temp_dir in os.listdir(temp_base):
            if temp_dir.startswith(f'compress_output_{session_id}_'):
                potential_info_file = os.path.join(temp_base, temp_dir, f'download_info_{session_id}.json')
                if os.path.exists(potential_info_file):
                    info_file_path = potential_info_file
                    break
        
        if not info_file_path:
            current_app.logger.warning(f"Download info file not found for session: {session_id}")
            return jsonify({'error': 'Session expired or invalid'}), 404
        
        # Read download information
        try:
            with open(info_file_path, 'r') as f:
                download_info = json.load(f)
        except Exception as e:
            current_app.logger.error(f"Error reading download info: {e}")
            return jsonify({'error': 'Session expired or invalid'}), 404
        
        download_path = download_info.get('file_path')
        download_filename = download_info.get('filename')
        
        if not download_path or not download_filename or not os.path.exists(download_path):
            current_app.logger.warning(f"Download file not found: {download_path}")
            return jsonify({'error': 'Download file not found'}), 404
        
        # Determine mime type
        if download_filename.endswith('.zip'):
            mimetype = 'application/zip'
        else:
            # Determine based on file extension
            extension = get_file_extension(download_filename)
            mime_types = {
                'pdf': 'application/pdf',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'webp': 'image/webp',
                'mp4': 'video/mp4',
                'avi': 'video/x-msvideo',
                'mkv': 'video/x-matroska',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            }
            mimetype = mime_types.get(extension, 'application/octet-stream')
        
        current_app.logger.info(f"Serving download: {download_filename} ({os.path.getsize(download_path)} bytes)")
        
        return send_file(
            download_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        current_app.logger.error(f"Error serving download: {str(e)}")
        return jsonify({'error': 'Download failed'}), 500

@file_compressor_bp.route('/api/estimate-time', methods=['POST'])
def estimate_compression_time():
    """API endpoint to estimate compression time for uploaded files"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files selected'}), 400
        
        # Get compression options
        compression_mode = request.form.get('compression_mode', 'quality_based')
        quality_level = request.form.get('quality_level', 'high')
        
        total_size = 0
        file_types = {}
        
        for file in files:
            if file.filename:
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                total_size += file_size
                file_category = get_file_category(file.filename)
                file_types[file_category] = file_types.get(file_category, 0) + 1
        
        # Estimate compression time based on file size and types
        estimated_time = estimate_compression_time(total_size, file_types, compression_mode, quality_level)
        
        return jsonify({
            'success': True,
            'estimated_time_seconds': estimated_time,
            'estimated_time_readable': format_time_duration(estimated_time),
            'total_size': total_size,
            'file_count': len(files),
            'file_types': file_types
        })
        
    except Exception as e:
        current_app.logger.error(f"Error estimating compression time: {str(e)}")
        return jsonify({'error': 'Failed to estimate compression time'}), 500

@file_compressor_bp.route('/api/supported-formats')
def get_supported_formats():
    """API endpoint to get supported file formats"""
    return jsonify({
        'formats': ALLOWED_EXTENSIONS,
        'max_file_size': MAX_FILE_SIZE,
        'max_files_per_batch': MAX_FILES_PER_BATCH,
        'compression_modes': COMPRESSION_MODES,
        'quality_levels': QUALITY_LEVELS
    })

@file_compressor_bp.route('/api/compression-presets')
def get_compression_presets():
    """API endpoint to get predefined compression presets"""
    presets = {
        'web_optimized': {
            'name': 'Web Optimized',
            'description': 'Optimized for web usage with balanced quality and size',
            'quality': 75,
            'remove_metadata': True,
            'ai_optimization': True
        },
        'maximum_compression': {
            'name': 'Maximum Compression',
            'description': 'Smallest file size with acceptable quality',
            'quality': 50,
            'remove_metadata': True,
            'ai_optimization': True
        },
        'high_quality': {
            'name': 'High Quality',
            'description': 'Maintain high quality with moderate compression',
            'quality': 90,
            'remove_metadata': False,
            'ai_optimization': True
        },
        'archive_friendly': {
            'name': 'Archive Friendly',
            'description': 'Optimized for long-term storage and archiving',
            'quality': 80,
            'remove_metadata': False,
            'ai_optimization': True,
            'lossless_mode': False
        }
    }
    
    return jsonify({'presets': presets})

def format_time_duration(seconds):
    """Format time duration in a human-readable format"""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        if remaining_seconds > 0:
            return f"{minutes}m {remaining_seconds}s"
        return f"{minutes} minutes"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours} hours"

# Cleanup function for old session files
def cleanup_old_sessions(max_age_hours=24):
    """Clean up old session files and directories"""
    try:
        temp_dir = tempfile.gettempdir()
        current_time = datetime.now()
        
        for item in os.listdir(temp_dir):
            if item.startswith(('compress_input_', 'compress_output_')):
                item_path = os.path.join(temp_dir, item)
                if os.path.isdir(item_path):
                    try:
                        # Check if directory is older than max_age_hours
                        creation_time = datetime.fromtimestamp(os.path.getctime(item_path))
                        age_hours = (current_time - creation_time).total_seconds() / 3600
                        
                        if age_hours > max_age_hours:
                            shutil.rmtree(item_path, ignore_errors=True)
                            current_app.logger.info(f"Cleaned up old session directory: {item}")
                    except Exception as e:
                        current_app.logger.warning(f"Failed to cleanup {item}: {str(e)}")
                        
    except Exception as e:
        current_app.logger.error(f"Error during session cleanup: {str(e)}")

# Register cleanup function to run periodically
@file_compressor_bp.before_app_request
def before_request():
    """Run cleanup periodically"""
    # This would ideally be run by a background job scheduler
    # For now, we'll run it occasionally during requests
    import random
    if random.random() < 0.01:  # 1% chance to run cleanup on each request
        try:
            cleanup_old_sessions()
        except Exception:
            pass

# Export the blueprint
file_compressor = file_compressor_bp