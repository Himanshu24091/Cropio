"""
LaTeX ⇄ PDF Converter Routes
Professional LaTeX compilation and PDF text extraction endpoints
"""

from flask import Blueprint, request, render_template, jsonify, send_file, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import traceback
from datetime import datetime

# Import LaTeX utilities
from utils.latex_utils import LatexProcessor

# Create blueprint
latex_pdf_bp = Blueprint('latex_pdf', __name__)

# Initialize LaTeX processor
latex_processor = LatexProcessor()

# Configuration
ALLOWED_EXTENSIONS = {'tex', 'latex', 'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@latex_pdf_bp.route('/latex-pdf')
@login_required
def latex_pdf_converter():
    """Main LaTeX ⇄ PDF converter page"""
    try:
        # Get templates
        templates = latex_processor.get_latex_templates()
        
        return render_template(
            'document/latex_pdf.html',
            templates=templates,
            page_title='LaTeX ⇄ PDF Converter'
        )
    except Exception as e:
        print(f"Error loading LaTeX converter page: {e}")
        flash('Error loading converter page', 'error')
        return redirect(url_for('main.index'))


@latex_pdf_bp.route('/api/latex-pdf/compile', methods=['POST'])
@login_required
def api_compile():
    """API endpoint for compiling LaTeX to PDF"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        latex_content = data.get('latex', '')
        auto_wrap = data.get('auto_wrap', True)
        show_log = data.get('show_log', False)
        
        if not latex_content.strip():
            return jsonify({
                'success': False,
                'error': 'No LaTeX content provided'
            }), 400
        
        print(f"[DEBUG] Compiling LaTeX - Auto-wrap: {auto_wrap}, Show log: {show_log}")
        
        # Compile LaTeX to PDF
        start_time = datetime.now()
        result = latex_processor.compile_to_pdf(
            latex_content, 
            auto_wrap=auto_wrap, 
            include_log=show_log
        )
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        if result['success']:
            # Track analytics for logged-in users
            if current_user.is_authenticated:
                try:
                    from utils.analytics_tracker import track_feature
                    
                    track_feature(
                        feature_name='latex_to_pdf',
                        feature_category='document_conversion',
                        extra_metadata={
                            'auto_wrap': auto_wrap,
                            'content_size': len(latex_content)
                        },
                        processing_time=processing_time,
                        success=True
                    )
                    print(f"[ANALYTICS] Tracked: latex_to_pdf")
                except Exception as e:
                    print(f"[ANALYTICS] Error: {e}")
            
            return jsonify({
                'success': True,
                'pdf_url': result['pdf_url'],
                'pdf_path': os.path.basename(result['pdf_path']),
                'compilation_time': result['compilation_time'],
                'log': result.get('log')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Compilation failed'),
                'log': result.get('log')
            }), 400
            
    except Exception as e:
        print(f"LaTeX compilation error: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@latex_pdf_bp.route('/api/latex-pdf/validate', methods=['POST'])
@login_required
def api_validate():
    """API endpoint for validating LaTeX syntax"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        latex_content = data.get('latex', '')
        
        # Validate LaTeX
        results = latex_processor.validate_latex(latex_content)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        print(f"LaTeX validation error: {e}")
        return jsonify({
            'success': False,
            'error': f'Validation error: {str(e)}'
        }), 500


@latex_pdf_bp.route('/api/latex-pdf/extract-text', methods=['POST'])
@login_required
def api_extract_text():
    """API endpoint for extracting text from PDF"""
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
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Only PDF files are allowed.'
            }), 400
        
        # Save uploaded file temporarily
        from flask import current_app
        upload_folder = current_app.config['UPLOAD_FOLDER']
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Extract text from PDF
        start_time = datetime.now()
        result = latex_processor.extract_text_from_pdf(filepath)
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except:
            pass
        
        if result['success']:
            # Track analytics
            if current_user.is_authenticated:
                try:
                    from utils.analytics_tracker import track_feature
                    
                    track_feature(
                        feature_name='pdf_to_text_extraction',
                        feature_category='document_conversion',
                        extra_metadata={'filename': filename},
                        processing_time=processing_time,
                        success=True
                    )
                    print(f"[ANALYTICS] Tracked: pdf_to_text_extraction")
                except Exception as e:
                    print(f"[ANALYTICS] Error: {e}")
            
            return jsonify({
                'success': True,
                'text': result['text']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Text extraction failed')
            }), 400
            
    except Exception as e:
        print(f"PDF text extraction error: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500


@latex_pdf_bp.route('/api/latex-pdf/requirements', methods=['GET'])
@login_required
def api_requirements():
    """API endpoint for checking system requirements"""
    try:
        requirements = latex_processor.check_system_requirements()
        
        return jsonify({
            'success': True,
            'requirements': requirements
        })
        
    except Exception as e:
        print(f"Requirements check error: {e}")
        return jsonify({
            'success': False,
            'error': f'Error checking requirements: {str(e)}'
        }), 500


@latex_pdf_bp.route('/api/latex-pdf/templates', methods=['GET'])
@login_required
def api_templates():
    """API endpoint for getting LaTeX templates"""
    try:
        templates = latex_processor.get_latex_templates()
        
        # Convert templates to JSON-friendly format
        templates_list = []
        for key, template_data in templates.items():
            templates_list.append({
                'id': key,
                'name': template_data['name'],
                'description': template_data['description'],
                'content': template_data['content']
            })
        
        return jsonify({
            'success': True,
            'templates': templates_list
        })
        
    except Exception as e:
        print(f"Templates fetch error: {e}")
        return jsonify({
            'success': False,
            'error': f'Error fetching templates: {str(e)}'
        }), 500


@latex_pdf_bp.route('/api/latex-pdf/download/<filename>', methods=['GET'])
@login_required
def api_download(filename):
    """API endpoint for downloading compiled PDF"""
    try:
        # Secure the filename
        filename = secure_filename(filename)
        
        # Get the upload folder from app config
        from flask import current_app
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        file_path = os.path.join(upload_folder, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        # Track analytics for download
        if current_user.is_authenticated:
            try:
                from utils.analytics_tracker import track_feature
                
                track_feature(
                    feature_name='latex_pdf_download',
                    feature_category='document_conversion',
                    extra_metadata={'filename': filename},
                    success=True
                )
                print(f"[ANALYTICS] Tracked: latex_pdf_download")
            except Exception as e:
                print(f"[ANALYTICS] Error: {e}")
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Download error: {e}")
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }), 500


# Cleanup old files periodically (can be called via cron or scheduler)
@latex_pdf_bp.route('/api/latex-pdf/cleanup', methods=['POST'])
@login_required
def api_cleanup():
    """API endpoint for cleaning up old LaTeX PDF files"""
    try:
        # Only allow admin users to trigger cleanup
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Unauthorized'
            }), 403
        
        latex_processor.cleanup_old_files(max_age_hours=24)
        
        return jsonify({
            'success': True,
            'message': 'Cleanup completed successfully'
        })
        
    except Exception as e:
        print(f"Cleanup error: {e}")
        return jsonify({
            'success': False,
            'error': f'Cleanup failed: {str(e)}'
        }), 500
