"""
Markdown ⇄ HTML Converter Routes
Fresh implementation with dedicated endpoints and features
"""

from flask import Blueprint, request, render_template, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import traceback
import tempfile
import markdown
import html2text
from markdown.extensions import codehilite, tables, toc
import bleach
from typing import Dict, Any, Optional

# Import usage tracking decorators
from middleware.usage_tracking import quota_required, track_conversion_result

# Create blueprint
markdown_html_converter_bp = Blueprint('markdown_html_converter', __name__)

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {
    'markdown': {'md', 'markdown', 'txt'},
    'html': {'html', 'htm'}
}

# Allowed HTML tags and attributes for security - Enhanced for code highlighting
ALLOWED_HTML_TAGS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'hr', 'div', 'span',
    'strong', 'b', 'em', 'i', 'u', 's', 'del', 'ins',
    'a', 'img',
    'ul', 'ol', 'li',
    'blockquote', 'pre', 'code',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'tfoot',
    'dl', 'dt', 'dd',
    'sup', 'sub', 'small', 'mark', 'cite', 'abbr', 'dfn',
    'time', 'kbd', 'samp', 'var', 'q', 'address'
]

ALLOWED_HTML_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'code': ['class', 'data-highlighted'],
    'pre': ['class', 'data-highlighted'],
    'table': ['class'],
    'th': ['align'],
    'td': ['align'],
    'div': ['class', 'id'],
    'span': ['class', 'style'],  # Allow style for syntax highlighting
    '*': ['id', 'class']  # Allow basic attributes on all elements
}


class MarkdownHTMLProcessor:
    """Handles conversion between Markdown and HTML formats"""
    
    def __init__(self):
        # Configure markdown processor
        self.md = markdown.Markdown(extensions=[
            'extra',           # Tables, footnotes, etc.
            'codehilite',     # Syntax highlighting
            'toc',            # Table of contents
            'nl2br',          # New line to break
            'fenced_code',    # Fenced code blocks
            'tables'          # Tables
        ], extension_configs={
            'codehilite': {
                'css_class': 'highlight',
                'use_pygments': True
            },
            'toc': {
                'title': 'Table of Contents'
            }
        })
        
        # Configure HTML to text processor
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # Don't wrap lines
        self.h2t.unicode_snob = True
        self.h2t.escape_snob = True
    
    def markdown_to_html(self, markdown_content: str, sanitize: bool = True) -> Dict[str, Any]:
        """Convert Markdown to HTML"""
        try:
            if not markdown_content.strip():
                return {
                    'success': False,
                    'error': 'No content provided'
                }
            
            # Convert markdown to HTML
            html_content = self.md.convert(markdown_content)
            
            # Sanitize HTML if requested
            if sanitize:
                html_content = bleach.clean(
                    html_content,
                    tags=ALLOWED_HTML_TAGS,
                    attributes=ALLOWED_HTML_ATTRIBUTES,
                    strip=True
                )
            
            # Reset markdown instance for next use
            self.md.reset()
            
            return {
                'success': True,
                'output': html_content,
                'stats': {
                    'input_length': len(markdown_content),
                    'output_length': len(html_content),
                    'lines': html_content.count('\n') + 1
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Markdown conversion failed: {str(e)}'
            }
    
    def html_to_markdown(self, html_content: str, preserve_formatting: bool = False) -> Dict[str, Any]:
        """Convert HTML to Markdown"""
        try:
            if not html_content.strip():
                return {
                    'success': False,
                    'error': 'No content provided'
                }
            
            # Configure HTML2Text based on preferences
            if preserve_formatting:
                self.h2t.ignore_emphasis = True
                self.h2t.ignore_links = False
            else:
                self.h2t.ignore_emphasis = False
                self.h2t.ignore_links = False
            
            # Convert HTML to Markdown
            markdown_content = self.h2t.handle(html_content)
            
            # Clean up the output
            markdown_content = self._clean_markdown_output(markdown_content)
            
            return {
                'success': True,
                'output': markdown_content,
                'stats': {
                    'input_length': len(html_content),
                    'output_length': len(markdown_content),
                    'lines': markdown_content.count('\n') + 1
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'HTML conversion failed: {str(e)}'
            }
    
    def _clean_markdown_output(self, markdown_content: str) -> str:
        """Clean up the markdown output"""
        lines = markdown_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove excessive blank lines
            if line.strip() == '' and len(cleaned_lines) > 0 and cleaned_lines[-1].strip() == '':
                continue
            cleaned_lines.append(line)
        
        # Remove trailing whitespace and normalize line endings
        return '\n'.join(line.rstrip() for line in cleaned_lines).strip()


@markdown_html_converter_bp.route('/markdown-html')
def markdown_html_redirect():
    """Redirect old URL to new URL"""
    from flask import redirect, url_for
    return redirect(url_for('markdown_html_converter.markdown_html_converter'), code=301)

@markdown_html_converter_bp.route('/markdown-html-converter')
@login_required
def markdown_html_converter():
    """Main converter page"""
    # Get user conversion statistics if logged in
    stats = {
        'total_conversions': 0,
        'success_rate': 0,
        'avg_file_size': '0 KB'
    }
    
    # You can add database queries here to get actual stats
    if current_user.is_authenticated:
        # Example: Get stats from database
        # stats = get_user_conversion_stats(current_user.id)
        pass
    
    return render_template(
        'document/markdown_html_converter.html',
        stats=stats
    )


@markdown_html_converter_bp.route('/api/markdown-html/convert', methods=['POST'])
@quota_required(tool_name='markdown_html_converter', check_file_size=False)
@track_conversion_result(tool_type='markdown_html_converter')
def api_convert():
    """API endpoint for conversion"""
    try:
        data = request.get_json(force=True, cache=False)
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        content = data.get('content', '').strip()
        mode = data.get('mode', 'markdown-to-html')
        preserve_formatting = data.get('preserve_formatting', False)
        
        print(f"[DEBUG] Conversion request - Mode: {mode}, Content length: {len(content)}")
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'No content provided'
            }), 400
        
        if mode not in ['markdown-to-html', 'html-to-markdown']:
            return jsonify({
                'success': False,
                'error': 'Invalid conversion mode'
            }), 400
        
        # Create processor instance
        processor = MarkdownHTMLProcessor()
        
        # Store metadata for usage tracking
        from flask import g
        g.input_content_size = len(content)
        
        # Perform conversion
        start_time = datetime.now()
        
        if mode == 'markdown-to-html':
            result = processor.markdown_to_html(content)
        else:
            result = processor.html_to_markdown(content, preserve_formatting)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Store output size for usage tracking
        if result.get('success'):
            g.estimated_output_size = len(result.get('output', ''))
        
        print(f"[DEBUG] Conversion result - Success: {result['success']}, Output length: {len(result.get('output', '')) if result.get('success') else 'N/A'}")
        
        if not result['success']:
            return jsonify(result), 400
        
        # Add processing time to result
        result['processing_time'] = processing_time
        result['stats']['processing_time'] = f"{processing_time:.3f}s"
        
        
        # Track analytics for logged-in users
        if current_user.is_authenticated:
            try:
                from utils.analytics_tracker import track_feature
                import json
                
                # Determine feature name based on mode
                if mode == 'markdown-to-html':
                    feature_name = 'markdown_to_html'
                else:
                    feature_name = 'html_to_markdown'
                
                # Prepare metadata
                metadata = {
                    'mode': mode,
                    'content_size': len(content),
                    'output_size': len(result.get('output', '')),
                    'processing_time': processing_time
                }
                
                print(f"[ANALYTICS] Tracking conversion: {feature_name}, user: {current_user.username}")
                
                track_result = track_feature(
                    feature_name=feature_name,
                    feature_category='document_conversion',
                    extra_metadata=metadata,
                    processing_time=processing_time,
                    success=True
                )
                
                print(f"[ANALYTICS] Tracking successful: {track_result}")
                
            except Exception as e:
                print(f"[ANALYTICS] Tracking error: {e}")
                import traceback
                traceback.print_exc()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"API conversion error: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@markdown_html_converter_bp.route('/api/markdown-html/preview', methods=['POST'])
def api_preview():
    """API endpoint for live preview (Markdown to HTML only)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({
                'success': True,
                'html': '<p class="text-slate-500 text-center">Start typing to see preview...</p>'
            })
        
        # Create processor instance
        processor = MarkdownHTMLProcessor()
        
        # Convert markdown to HTML for preview
        result = processor.markdown_to_html(content)
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            'html': result['output']
        })
        
    except Exception as e:
        print(f"Preview error: {e}")
        return jsonify({
            'success': False,
            'error': f'Preview generation failed: {str(e)}'
        }), 500


@markdown_html_converter_bp.route('/api/markdown-html/upload', methods=['POST'])
@login_required
@quota_required(tool_name='markdown_html_upload', check_file_size=True)
@track_conversion_result(tool_type='markdown_html_upload')
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
        
        if file_ext not in ALLOWED_EXTENSIONS['markdown'] and file_ext not in ALLOWED_EXTENSIONS['html']:
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
        
        # Detect mode based on file extension
        if file_ext in ALLOWED_EXTENSIONS['html']:
            suggested_mode = 'html-to-markdown'
        else:
            suggested_mode = 'markdown-to-html'
        
        return jsonify({
            'success': True,
            'content': content,
            'filename': filename,
            'suggested_mode': suggested_mode,
            'file_size': len(content),
            'stats': {
                'lines': content.count('\n') + 1,
                'words': len(content.split()) if content.strip() else 0,
                'characters': len(content)
            }
        })
        
    except UnicodeDecodeError:
        return jsonify({
            'success': False,
            'error': 'File contains invalid characters. Please ensure it\'s a text file.'
        }), 400
    except Exception as e:
        print(f"File upload error: {e}")
        return jsonify({
            'success': False,
            'error': f'File upload failed: {str(e)}'
        }), 500


@markdown_html_converter_bp.route('/api/markdown-html/download', methods=['POST'])
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
        file_type = data.get('type', 'html')
        
        if not content:
            return jsonify({
                'success': False,
                'error': 'No content to download'
            }), 400
        
        # Determine file extension and MIME type
        if file_type == 'html':
            ext = 'html'
            mimetype = 'text/html'
            feature_name = 'markdown_to_html'
        elif file_type == 'markdown':
            ext = 'md'
            mimetype = 'text/markdown'
            feature_name = 'html_to_markdown'
        else:
            ext = 'txt'
            mimetype = 'text/plain'
            feature_name = 'markdown_html_converter'
        
        # Track analytics for logged-in users
        if current_user.is_authenticated:
            try:
                from utils.analytics_tracker import track_feature
                import json
                
                # Prepare metadata
                metadata = {
                    'file_type': file_type,
                    'content_size': len(content),
                    'filename': filename
                }
                
                print(f"[ANALYTICS] Tracking conversion: {feature_name}, user: {current_user.username}")
                
                result = track_feature(
                    feature_name=feature_name,
                    feature_category='document_conversion',
                    extra_metadata=metadata,
                    success=True
                )
                
                print(f"[ANALYTICS] Tracking result: {result}")
                
            except Exception as e:
                print(f"[ANALYTICS] Tracking error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[ANALYTICS] User not authenticated, skipping tracking")
        
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
        print(f"Download error: {e}")
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }), 500


@markdown_html_converter_bp.route('/api/markdown-html/validate', methods=['POST'])
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
        content_type = data.get('type', 'markdown')
        
        validation_result = {
            'success': True,
            'valid': True,
            'warnings': [],
            'errors': [],
            'stats': {
                'lines': content.count('\n') + 1 if content else 0,
                'words': len(content.split()) if content.strip() else 0,
                'characters': len(content),
                'paragraphs': len([p for p in content.split('\n\n') if p.strip()]) if content else 0
            }
        }
        
        if not content.strip():
            validation_result['warnings'].append('Content is empty')
        
        if content_type == 'markdown':
            # Basic Markdown validation
            if '```' in content and content.count('```') % 2 != 0:
                validation_result['errors'].append('Unmatched code block delimiters (```)')
                validation_result['valid'] = False
            
            # Check for common Markdown issues
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if line.strip().startswith('#') and not line.startswith('# ') and len(line.strip()) > 1:
                    validation_result['warnings'].append(f'Line {i}: Header should have space after #')
        
        elif content_type == 'html':
            # Basic HTML validation
            import re
            
            # Check for unclosed tags
            open_tags = re.findall(r'<([^/>\s]+)', content)
            close_tags = re.findall(r'</([^>\s]+)', content)
            
            for tag in open_tags:
                if tag.lower() not in ['br', 'hr', 'img', 'input', 'meta', 'link']:
                    if open_tags.count(tag) != close_tags.count(tag):
                        validation_result['warnings'].append(f'Potentially unclosed tag: <{tag}>')
        
        return jsonify(validation_result)
        
    except Exception as e:
        print(f"Validation error: {e}")
        return jsonify({
            'success': False,
            'error': f'Validation failed: {str(e)}'
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


# Error handlers for this blueprint
@markdown_html_converter_bp.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 10MB.'
    }), 413


@markdown_html_converter_bp.errorhandler(400)
def bad_request(e):
    return jsonify({
        'success': False,
        'error': 'Bad request. Please check your input.'
    }), 400


@markdown_html_converter_bp.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error. Please try again later.'
    }), 500
