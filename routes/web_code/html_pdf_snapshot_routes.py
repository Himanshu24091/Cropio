"""
HTML PDF Snapshot Converter Routes
Professional-grade web page to PDF conversion with advanced features
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
import time

# Import the HTML PDF processor utility
from utils.web_code.html_pdf_snapshot_utils import HTMLPDFProcessor

# Create blueprint with unique name to avoid conflicts
html_pdf_snapshot_bp = Blueprint('html_pdf_snapshot', __name__, url_prefix='/html-pdf-snapshot')

# Configuration
ALLOWED_EXTENSIONS = {'html', 'htm'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB for direct HTML content
TIMEOUT_SECONDS = 30

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(filepath):
    """Get file size in MB"""
    return os.path.getsize(filepath) / (1024 * 1024)

@html_pdf_snapshot_bp.route('/')
@login_required
def html_pdf_snapshot_converter():
    """Main HTML PDF snapshot converter page"""
    try:
        # Check if PDF backend is available
        processor = HTMLPDFProcessor()
        backend_available = processor.is_backend_available()
        
        # Check for unavailability to match template expectations
        backend_unavailable = not backend_available
        
        # Get backend information
        backend_info = processor.get_backend_info()
        
        # TODO: Add usage tracking integration
        usage = None  # This would integrate with your usage tracking system
        quota_exceeded = False  # This would check actual quota status
        
        return render_template(
            'web_code/html_pdf_snapshot.html',
            backend_unavailable=backend_unavailable,
            backend_available=backend_available,
            backend_info=backend_info,
            max_file_size=MAX_FILE_SIZE // (1024 * 1024),
            max_content_size=MAX_CONTENT_SIZE // (1024 * 1024),
            timeout_seconds=TIMEOUT_SECONDS,
            usage=usage,
            quota_exceeded=quota_exceeded
        )
    except Exception as e:
        flash(f'Error loading converter: {str(e)}', 'error')
        return render_template('web_code/html_pdf_snapshot.html', 
                             backend_unavailable=True, 
                             backend_available=False)

@html_pdf_snapshot_bp.route('/convert', methods=['POST'])
def convert_html_to_pdf():
    """Convert HTML/URL to PDF"""
    try:
        # Check if PDF backend is available
        processor = HTMLPDFProcessor()
        if not processor.is_backend_available():
            return jsonify({
                'success': False,
                'error': 'PDF generation backend is not available. Please contact the administrator.'
            }), 400

        # Get conversion mode
        conversion_mode = request.form.get('conversion_mode', 'url')
        
        # Get settings
        page_size = request.form.get('page_size', 'A4')
        orientation = request.form.get('orientation', 'portrait')
        margin_top = float(request.form.get('margin_top', 2))
        margin_bottom = float(request.form.get('margin_bottom', 2))
        margin_left = float(request.form.get('margin_left', 2))
        margin_right = float(request.form.get('margin_right', 2))
        viewport_width = int(request.form.get('viewport_width', 1366))
        viewport_height = int(request.form.get('viewport_height', 768))
        full_page = request.form.get('full_page', 'true') == 'true'
        background_graphics = request.form.get('background_graphics', 'true') == 'true'
        wait_for_load = request.form.get('wait_for_load', 'false') == 'true'
        wait_time = int(request.form.get('wait_time', 3))
        scale_factor = float(request.form.get('scale_factor', 1.0))
        
        # Get optional custom CSS and HTML elements
        custom_css = request.form.get('custom_css', '').strip()
        header_html = request.form.get('header_html', '').strip()
        footer_html = request.form.get('footer_html', '').strip()

        # Validate settings
        if not 50 <= viewport_width <= 3840:
            return jsonify({
                'success': False,
                'error': 'Viewport width must be between 50 and 3840 pixels'
            }), 400

        settings = {
            'page_size': page_size,
            'orientation': orientation,
            'margin_top': margin_top,
            'margin_bottom': margin_bottom,
            'margin_left': margin_left,
            'margin_right': margin_right,
            'viewport_width': viewport_width,
            'viewport_height': viewport_height,
            'full_page': full_page,
            'background_graphics': background_graphics,
            'wait_for_load': wait_for_load,
            'wait_time': wait_time,
            'scale_factor': scale_factor,
            'custom_css': custom_css,
            'header_html': header_html,
            'footer_html': footer_html
        }

        # Start timing
        start_time = time.time()
        
        if conversion_mode == 'url':
            url = request.form.get('url', '').strip()
            if not url:
                return jsonify({
                    'success': False,
                    'error': 'URL is required for URL conversion mode'
                }), 400
            
            # Convert URL to PDF
            pdf_path = processor.url_to_pdf(url, settings)
            source_name = processor.get_domain_from_url(url) or 'webpage'
            
        elif conversion_mode == 'content':
            html_content = request.form.get('content', '').strip()
            if not html_content:
                return jsonify({
                    'success': False,
                    'error': 'HTML content is required for content conversion mode'
                }), 400
            
            # Check content size
            if len(html_content) > MAX_CONTENT_SIZE:
                return jsonify({
                    'success': False,
                    'error': f'HTML content exceeds {MAX_CONTENT_SIZE // (1024 * 1024)}MB limit'
                }), 400
            
            # Convert content to PDF
            pdf_path = processor.content_to_pdf(html_content, settings)
            source_name = 'html_content'
            
        elif conversion_mode == 'file':
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
            temp_input = tempfile.NamedTemporaryFile(delete=False, 
                                                   suffix=f'_{filename}')
            file.save(temp_input.name)
            temp_input.close()

            try:
                # Check file size
                if os.path.getsize(temp_input.name) > MAX_FILE_SIZE:
                    return jsonify({
                        'success': False,
                        'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB'
                    }), 400
                
                # Convert file to PDF
                pdf_path = processor.file_to_pdf(temp_input.name, settings)
                source_name = filename
                
            finally:
                # Clean up temp input file
                if os.path.exists(temp_input.name):
                    os.unlink(temp_input.name)
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid conversion mode'
            }), 400

        # Calculate processing time
        processing_time = round(time.time() - start_time, 2)
        
        # Get output filename for download
        output_filename = os.path.basename(pdf_path)
        
        # Get file size info
        pdf_size = get_file_size_mb(pdf_path)
        
        return jsonify({
            'success': True,
            'message': f'Successfully converted {source_name} to PDF',
            'download_url': f'/html-pdf-snapshot/download/{output_filename}',
            'stats': {
                'output_format': 'PDF',
                'converted_size': f"{pdf_size:.2f} MB",
                'processing_time': f'{processing_time}s',
                'backend': processor.get_current_backend()
            },
            'converted_info': {
                'filename': output_filename,
                'size': pdf_size,
                'processing_time': processing_time
            }
        })

    except Exception as e:
        error_details = str(e)
        print(f"HTML PDF conversion error: {error_details}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            'success': False,
            'error': f'Conversion failed: {error_details}'
        }), 500

@html_pdf_snapshot_bp.route('/download/<filename>')
def download_converted_file(filename):
    """Download converted PDF file"""
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
            return redirect(url_for('html_pdf_snapshot.html_pdf_snapshot_converter'))
        
        # Determine the correct mimetype
        mimetype = 'application/pdf'
        
        
        # Track analytics for logged-in users
        if current_user.is_authenticated:
            try:
                from utils.analytics_tracker import track_feature
                
                track_feature(
                    feature_name='html_to_pdf_snapshot',
                    feature_category='web_conversion',
                    extra_metadata={'filename': filename, 'download_mode': download_mode},
                    success=True
                )
                print(f"[ANALYTICS] Tracked: html_to_pdf_snapshot")
            except Exception as e:
                print(f"[ANALYTICS] Error: {e}")
        
        # Check if user wants to download or view in browser
        download_mode = request.args.get('download', 'false').lower() == 'true'
        
        if download_mode:
            # Force download
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype=mimetype
            )
        else:
            # Display in browser
            return send_file(
                file_path,
                as_attachment=False,
                mimetype=mimetype,
                conditional=True
            )
        
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('html_pdf_snapshot.html_pdf_snapshot_converter'))

@html_pdf_snapshot_bp.route('/preview', methods=['POST'])
def preview_url():
    """Preview URL before conversion"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
        
        url = data['url'].strip()
        
        # Initialize processor and get preview
        processor = HTMLPDFProcessor()
        preview_data = processor.get_url_preview(url)
        
        return jsonify({
            'success': True,
            'preview': preview_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@html_pdf_snapshot_bp.route('/validate', methods=['POST'])
def validate_content():
    """Validate HTML content"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        content = data.get('content', '').strip()
        content_type = data.get('type', 'html')
        
        processor = HTMLPDFProcessor()
        validation_result = processor.validate_html_content(content)
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@html_pdf_snapshot_bp.route('/backend-info')
def backend_info():
    """Get backend information for frontend"""
    try:
        processor = HTMLPDFProcessor()
        info = processor.get_backend_info()
        
        return jsonify({
            'success': True,
            'backend_info': info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to get backend information'
        }), 500

@html_pdf_snapshot_bp.route('/check-support')
def check_html_pdf_support():
    """Check if HTML PDF conversion support is available"""
    try:
        processor = HTMLPDFProcessor()
        supported = processor.is_backend_available()
        backend_info = processor.get_backend_info()
        
        return jsonify({
            'supported': supported,
            'backend_info': backend_info,
            'message': 'HTML PDF conversion available' if supported else 'PDF backend not available'
        })
        
    except Exception as e:
        return jsonify({
            'supported': False,
            'error': str(e)
        }), 500

# API routes for frontend compatibility
@html_pdf_snapshot_bp.route('/api/html-preview', methods=['POST'])
def api_html_preview():
    """API endpoint for HTML content preview (frontend compatibility)"""
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
                'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=f'_{filename}')
        file.save(temp_input.name)
        temp_input.close()

        try:
            # Check file size
            if os.path.getsize(temp_input.name) > MAX_FILE_SIZE:
                return jsonify({
                    'success': False,
                    'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB'
                }), 400

            # Initialize processor
            processor = HTMLPDFProcessor()
            
            # Get file preview/info
            file_info = processor.get_html_file_info(temp_input.name)
            
            # Clean up temp file
            os.unlink(temp_input.name)
            
            return jsonify({
                'success': True,
                'preview': file_info,
                'format': 'HTML'
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

@html_pdf_snapshot_bp.route('/api/html-convert', methods=['POST'])
def api_html_convert():
    """API endpoint for HTML conversion (frontend compatibility)"""
    try:
        # Check if PDF backend is available
        processor = HTMLPDFProcessor()
        if not processor.is_backend_available():
            return jsonify({
                'success': False,
                'error': 'PDF generation backend is not available.'
            }), 400

        # Get parameters
        conversion_type = request.form.get('conversion_type', 'url')
        page_size = request.form.get('page_size', 'A4')
        orientation = request.form.get('orientation', 'portrait')
        
        # Validate parameters
        if conversion_type not in ['url', 'content', 'file']:
            return jsonify({
                'success': False,
                'error': 'Invalid conversion type'
            }), 400

        settings = {
            'page_size': page_size,
            'orientation': orientation,
            'margin_top': float(request.form.get('margin_top', 2)),
            'margin_bottom': float(request.form.get('margin_bottom', 2)),
            'margin_left': float(request.form.get('margin_left', 2)),
            'margin_right': float(request.form.get('margin_right', 2)),
            'viewport_width': int(request.form.get('viewport_width', 1366)),
            'viewport_height': int(request.form.get('viewport_height', 768)),
            'full_page': request.form.get('full_page', 'true') == 'true',
            'background_graphics': request.form.get('background_graphics', 'true') == 'true',
            'wait_for_load': request.form.get('wait_for_load', 'false') == 'true',
            'wait_time': int(request.form.get('wait_time', 3)),
            'scale_factor': float(request.form.get('scale_factor', 1.0))
        }

        start_time = time.time()
        
        if conversion_type == 'url':
            url = request.form.get('url', '').strip()
            if not url:
                return jsonify({
                    'success': False,
                    'error': 'URL is required'
                }), 400
            
            # Convert URL to PDF
            pdf_path = processor.url_to_pdf(url, settings)
            source_name = processor.get_domain_from_url(url) or 'webpage'
            
        elif conversion_type == 'content':
            content = request.form.get('content', '').strip()
            if not content:
                return jsonify({
                    'success': False,
                    'error': 'HTML content is required'
                }), 400
            
            # Check content size
            if len(content) > MAX_CONTENT_SIZE:
                return jsonify({
                    'success': False,
                    'error': f'Content size exceeds {MAX_CONTENT_SIZE // (1024 * 1024)}MB limit'
                }), 400
            
            # Convert content to PDF
            pdf_path = processor.content_to_pdf(content, settings)
            source_name = 'html_content'
            
        elif conversion_type == 'file':
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

            try:
                # Check file size
                if os.path.getsize(temp_input.name) > MAX_FILE_SIZE:
                    return jsonify({
                        'success': False,
                        'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB'
                    }), 400
                
                # Convert file to PDF
                pdf_path = processor.file_to_pdf(temp_input.name, settings)
                source_name = filename
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_input.name):
                    os.unlink(temp_input.name)
        
        # Calculate processing time
        processing_time = round(time.time() - start_time, 2)
        
        # Get output file info
        output_filename = os.path.basename(pdf_path)
        pdf_size = get_file_size_mb(pdf_path)
        
        return jsonify({
            'success': True,
            'message': f'Successfully converted {source_name}',
            'download_url': f'/html-pdf-snapshot/download/{output_filename}',
            'stats': {
                'output_format': 'PDF',
                'converted_size': f"{pdf_size:.2f} MB",
                'processing_time': f'{processing_time}s',
                'backend': processor.get_current_backend()
            },
            'converted_info': {
                'filename': output_filename,
                'size': pdf_size
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@html_pdf_snapshot_bp.route('/batch-convert', methods=['POST'])
def batch_convert_html():
    """Batch convert multiple HTML files"""
    try:
        # Check if PDF backend is available
        processor = HTMLPDFProcessor()
        if not processor.is_backend_available():
            return jsonify({
                'success': False,
                'error': 'PDF generation backend is not available'
            }), 400

        # Get parameters
        page_size = request.form.get('page_size', 'A4')
        orientation = request.form.get('orientation', 'portrait')
        
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
                'error': 'No valid HTML files found'
            }), 400
        
        # Process batch conversion
        settings = {
            'page_size': page_size,
            'orientation': orientation,
            'margin_top': 2,
            'margin_bottom': 2,
            'margin_left': 2,
            'margin_right': 2
        }
        
        results = processor.batch_convert_html(temp_files, settings)
        
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
