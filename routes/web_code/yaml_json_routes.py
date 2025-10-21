"""
YAML ⇄ JSON Converter Routes
Flask routes for bidirectional YAML/JSON conversion with file upload, real-time conversion, and download.
"""

from flask import Blueprint, request, render_template, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import traceback
import tempfile
from typing import Dict, Any, Optional

# Import usage tracking decorators
from middleware.usage_tracking import quota_required, track_conversion_result

# Import the YAML/JSON processor
from utils.web_code.yaml_processor import YamlJsonProcessor, create_sample_yaml, create_sample_json

# Import core utilities
from core.logging_config import cropio_logger

# Create blueprint
yaml_json_bp = Blueprint('yaml_json', __name__)

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {
    'yaml': {'yaml', 'yml', 'txt'},
    'json': {'json', 'txt'}
}

@yaml_json_bp.route('/yaml-json')
def yaml_json_redirect():
    """Redirect old URL to new URL"""
    from flask import redirect, url_for
    return redirect(url_for('yaml_json.yaml_json_converter'), code=301)

@yaml_json_bp.route('/yaml-json-converter')
@login_required
def yaml_json_converter():
    """Main YAML ⇄ JSON converter page"""
    # Get user conversion statistics if logged in
    stats = {
        'total_conversions': 0,
        'success_rate': 100,
        'avg_file_size': '0 KB'
    }
    
    # You can add database queries here to get actual stats
    if current_user.is_authenticated:
        # Example: Get stats from database
        # stats = get_user_conversion_stats(current_user.id, 'yaml_json')
        pass
    
    return render_template(
        'web_code/yaml_json.html',
        stats=stats
    )

@yaml_json_bp.route('/api/yaml-json/convert', methods=['POST'])
@quota_required(tool_name='yaml_json_converter', check_file_size=False)
@track_conversion_result(tool_type='yaml_json_converter')
def api_convert():
    """API endpoint for YAML/JSON conversion"""
    try:
        data = request.get_json(force=True, cache=False)
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        content = data.get('content', '').strip()
        mode = data.get('mode', 'yaml-to-json')
        options = data.get('options', {})
        
        cropio_logger.info(f"YAML/JSON conversion request - Mode: {mode}, Content length: {len(content)}")
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'No content provided'
            }), 400
        
        if mode not in ['yaml-to-json', 'json-to-yaml']:
            return jsonify({
                'success': False,
                'error': 'Invalid conversion mode'
            }), 400
        
        # Create processor instance
        processor = YamlJsonProcessor()
        
        # Store metadata for usage tracking
        from flask import g
        g.input_content_size = len(content)
        
        # Perform conversion
        start_time = datetime.now()
        
        if mode == 'yaml-to-json':
            result = processor.yaml_to_json(
                content, 
                pretty=options.get('pretty', True),
                sort_keys=options.get('sort_keys', False)
            )
        else:
            result = processor.json_to_yaml(
                content,
                flow_style=options.get('flow_style', False),
                sort_keys=options.get('sort_keys', False)
            )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Store output size for usage tracking
        if result.get('success'):
            g.estimated_output_size = len(result.get('output', ''))
        
        cropio_logger.info(f"YAML/JSON conversion result - Success: {result['success']}, Output length: {len(result.get('output', '')) if result.get('success') else 'N/A'}")
        
        if not result['success']:
            return jsonify(result), 400
        
        # Add processing time to result
        result['processing_time'] = processing_time
        result['stats']['processing_time'] = f"{processing_time:.3f}s"
        
        # Log conversion if user is authenticated
        if current_user.is_authenticated:
            try:
                # Here you would typically log the conversion to database
                # log_conversion(current_user.id, mode, len(content), processing_time)
                pass
            except Exception as e:
                cropio_logger.warning(f"Error logging conversion: {e}")
        
        return jsonify(result)
        
    except Exception as e:
        cropio_logger.error(f"API conversion error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@yaml_json_bp.route('/api/yaml-json/validate', methods=['POST'])
def api_validate():
    """API endpoint for content validation"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        content = data.get('content', '')
        content_type = data.get('type', 'yaml')
        
        # Create processor instance
        processor = YamlJsonProcessor()
        
        # Validate based on content type
        if content_type == 'yaml':
            result = processor.validate_yaml(content)
        elif content_type == 'json':
            result = processor.validate_json(content)
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid content type'
            }), 400
        
        return jsonify({
            'success': True,
            'validation': result
        })
        
    except Exception as e:
        cropio_logger.error(f"Validation error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Validation failed: {str(e)}'
        }), 500

@yaml_json_bp.route('/api/yaml-json/format', methods=['POST'])
def api_format():
    """API endpoint for content formatting"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        content = data.get('content', '')
        content_type = data.get('type', 'yaml')
        options = data.get('options', {})
        
        # Create processor instance
        processor = YamlJsonProcessor()
        
        # Format based on content type
        if content_type == 'yaml':
            result = processor.format_yaml(
                content,
                indent=options.get('indent', 2),
                flow_style=options.get('flow_style', False)
            )
        elif content_type == 'json':
            result = processor.format_json(
                content,
                indent=options.get('indent', 2),
                sort_keys=options.get('sort_keys', False)
            )
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid content type'
            }), 400
        
        return jsonify(result)
        
    except Exception as e:
        cropio_logger.error(f"Formatting error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Formatting failed: {str(e)}'
        }), 500

@yaml_json_bp.route('/api/yaml-json/upload', methods=['POST'])
@login_required
@quota_required(tool_name='yaml_json_upload', check_file_size=True)
@track_conversion_result(tool_type='yaml_json_upload')
def api_upload_file():
    """API endpoint for file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check file size
        if file.content_length and file.content_length > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': 'File size exceeds 10MB limit'
            }), 400
        
        # Check file extension
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        
        if (file_ext not in ALLOWED_EXTENSIONS['yaml'] and 
            file_ext not in ALLOWED_EXTENSIONS['json']):
            return jsonify({
                'success': False,
                'error': f'Unsupported file type: {file_ext}'
            }), 400
        
        # Read file content
        content = file.read().decode('utf-8')
        
        # Store file info for usage tracking
        from flask import g
        g.input_file_size = len(content) / (1024 * 1024)  # Convert to MB
        g.input_filename = filename
        
        # Detect content type based on file extension
        if file_ext in ALLOWED_EXTENSIONS['yaml']:
            suggested_mode = 'yaml-to-json'
            content_type = 'yaml'
        else:
            suggested_mode = 'json-to-yaml'
            content_type = 'json'
        
        # Validate content
        processor = YamlJsonProcessor()
        if content_type == 'yaml':
            validation = processor.validate_yaml(content)
        else:
            validation = processor.validate_json(content)
        
        return jsonify({
            'success': True,
            'content': content,
            'filename': filename,
            'suggested_mode': suggested_mode,
            'content_type': content_type,
            'file_size': len(content),
            'validation': validation,
            'stats': {
                'lines': content.count('\n') + 1,
                'words': len(content.split()) if content.strip() else 0,
                'characters': len(content)
            }
        })
        
    except UnicodeDecodeError:
        return jsonify({
            'success': False,
            'error': 'File contains invalid characters. Please ensure it\'s a valid text file.'
        }), 400
    except Exception as e:
        cropio_logger.error(f"File upload error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'File upload failed: {str(e)}'
        }), 500

@yaml_json_bp.route('/api/yaml-json/download', methods=['POST'])
def api_download():
    """API endpoint for downloading converted content"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        content = data.get('content', '')
        filename = data.get('filename', 'converted')
        file_type = data.get('type', 'json')
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'No content to download'
            }), 400
        
        # Determine file extension and MIME type
        if file_type == 'yaml':
            ext = 'yaml'
            mimetype = 'application/x-yaml'
        elif file_type == 'json':
            ext = 'json'
            mimetype = 'application/json'
        else:
            ext = 'txt'
            mimetype = 'text/plain'
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{ext}', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Generate download filename
        download_filename = f"{filename}.{ext}"
        
        return send_file(
            tmp_file_path,
            as_attachment=True,
            download_name=download_filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        cropio_logger.error(f"Download error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }), 500

@yaml_json_bp.route('/api/yaml-json/sample/<content_type>')
def api_get_sample(content_type):
    """API endpoint to get sample content"""
    try:
        if content_type == 'yaml':
            content = create_sample_yaml()
        elif content_type == 'json':
            content = create_sample_json()
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid content type'
            }), 400
        
        return jsonify({
            'success': True,
            'content': content,
            'type': content_type
        })
        
    except Exception as e:
        cropio_logger.error(f"Sample content error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to generate sample: {str(e)}'
        }), 500

# Error handlers for this blueprint
@yaml_json_bp.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 10MB.'
    }), 413

@yaml_json_bp.errorhandler(400)
def bad_request(e):
    return jsonify({
        'success': False,
        'error': 'Bad request. Please check your input.'
    }), 400

@yaml_json_bp.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error. Please try again later.'
    }), 500

def allowed_file(filename: str, file_type: str) -> bool:
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(file_type, set())

def get_file_size_formatted(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"
