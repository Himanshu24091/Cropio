"""
PowerBI to PDF Converter Routes
Handles basic and advanced PowerBI file conversion to PDF
"""

import os
import tempfile
import uuid
from datetime import datetime
from flask import Blueprint, request, render_template, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from utils.pdf_converters.powerbi_utils import PowerBIConverter
import logging

logger = logging.getLogger(__name__)

# Create blueprint
powerbi_bp = Blueprint('powerbi_converter', __name__)
# Export with expected name for app.py
powerbi_converter_bp = powerbi_bp

ALLOWED_EXTENSIONS = {'pbix'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_size(file):
    """Validate file size"""
    # Get file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    return size <= MAX_FILE_SIZE

@powerbi_bp.route('/convert/powerbi-to-pdf/', methods=['GET'])
@powerbi_bp.route('/powerbi-converter', methods=['GET'])
def powerbi_converter():
    """Display PowerBI converter page"""
    try:
        return render_template('pdf_converters/powerbi_converter.html')
    except Exception as e:
        logger.error(f"Error loading PowerBI converter page: {str(e)}")
        return jsonify({'error': 'Failed to load converter page'}), 500

@powerbi_bp.route('/convert/powerbi-to-pdf/', methods=['POST'])
@powerbi_bp.route('/powerbi-converter', methods=['POST'])
def convert_powerbi():
    """Handle PowerBI file conversion"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate file
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only .pbix files are allowed'}), 400

        if not validate_file_size(file):
            return jsonify({'error': 'File size exceeds 50MB limit'}), 400

        # Get conversion parameters
        action = request.form.get('action', 'basic')
        
        # Basic parameters
        pdf_quality = request.form.get('pdf_quality', 'high')
        page_format = request.form.get('page_format', 'A4')
        
        # Advanced parameters
        export_all = request.form.get('export_all') == 'on'
        page_range = request.form.get('page_range', '') if not export_all else ''
        resolution = int(request.form.get('resolution', '300'))
        compression = request.form.get('compression', 'medium')
        
        # Watermark parameters
        add_watermark = request.form.get('add_watermark') == 'on'
        watermark_text = request.form.get('watermark_text', '') if add_watermark else ''
        watermark_opacity = float(request.form.get('watermark_opacity', '0.2')) if add_watermark else 0.2
        
        # Password parameters
        add_password = request.form.get('add_password') == 'on'
        pdf_password = request.form.get('pdf_password', '') if add_password else ''

        # Create temporary directories
        input_dir = tempfile.mkdtemp(prefix='powerbi_input_')
        output_dir = tempfile.mkdtemp(prefix='powerbi_output_')
        
        try:
            # Save uploaded file
            filename = secure_filename(file.filename)
            input_path = os.path.join(input_dir, filename)
            file.save(input_path)
            
            # Create output filename
            output_filename = filename.rsplit('.', 1)[0] + '_converted.pdf'
            output_path = os.path.join(output_dir, output_filename)
            
            # Initialize converter
            converter = PowerBIConverter(
                quality=pdf_quality,
                page_format=page_format,
                resolution=resolution,
                compression=compression
            )
            
            # Prepare conversion options
            conversion_options = {
                'export_all': export_all,
                'page_range': page_range,
                'add_watermark': add_watermark,
                'watermark_text': watermark_text,
                'watermark_opacity': watermark_opacity,
                'add_password': add_password,
                'pdf_password': pdf_password,
                'action': action
            }
            
            logger.info(f"Converting PowerBI file: {filename} with action: {action}")
            
            # Convert PowerBI to PDF
            success = converter.convert_to_pdf(input_path, output_path, conversion_options)
            
            if success and os.path.exists(output_path):
                # Return the PDF file
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=output_filename,
                    mimetype='application/pdf'
                )
            else:
                logger.error(f"Conversion failed for file: {filename}")
                return jsonify({'error': 'Conversion failed. Please check your PowerBI file.'}), 500
                
        finally:
            # Clean up temporary files
            try:
                import shutil
                if os.path.exists(input_dir):
                    shutil.rmtree(input_dir)
                if os.path.exists(output_dir):
                    shutil.rmtree(output_dir, ignore_errors=True)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary files: {cleanup_error}")

    except Exception as e:
        logger.error(f"Error in PowerBI conversion: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@powerbi_bp.route('/api/powerbi/validate', methods=['POST'])
def validate_powerbi_file():
    """Validate PowerBI file before conversion"""
    try:
        if 'file' not in request.files:
            return jsonify({'valid': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'valid': False, 'error': 'No file selected'}), 400

        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'valid': False, 
                'error': 'Invalid file type. Only .pbix files are allowed'
            }), 400

        # Check file size
        if not validate_file_size(file):
            return jsonify({
                'valid': False, 
                'error': 'File size exceeds 50MB limit'
            }), 400

        # Basic file structure validation
        try:
            converter = PowerBIConverter()
            is_valid = converter.validate_pbix_file(file)
            
            if is_valid:
                return jsonify({
                    'valid': True,
                    'message': 'PowerBI file is valid',
                    'filename': file.filename,
                    'size': file.content_length or 0
                })
            else:
                return jsonify({
                    'valid': False,
                    'error': 'Invalid or corrupted PowerBI file'
                })
                
        except Exception as validation_error:
            logger.warning(f"File validation error: {validation_error}")
            return jsonify({
                'valid': False,
                'error': 'Unable to validate PowerBI file structure'
            })

    except Exception as e:
        logger.error(f"Error validating PowerBI file: {str(e)}")
        return jsonify({'valid': False, 'error': 'Validation failed'}), 500

@powerbi_bp.route('/api/powerbi/info', methods=['POST'])
def get_powerbi_info():
    """Get basic information about PowerBI file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if not allowed_file(file.filename) or not validate_file_size(file):
            return jsonify({'error': 'Invalid file'}), 400

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.pbix', delete=False) as temp_file:
            file.save(temp_file.name)
            
            try:
                converter = PowerBIConverter()
                info = converter.get_file_info(temp_file.name)
                
                return jsonify({
                    'success': True,
                    'info': info
                })
                
            finally:
                # Clean up
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

    except Exception as e:
        logger.error(f"Error getting PowerBI info: {str(e)}")
        return jsonify({'error': 'Failed to get file information'}), 500

# Error handlers
@powerbi_bp.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({'error': 'File size exceeds maximum limit of 50MB'}), 413

@powerbi_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request error"""
    return jsonify({'error': 'Bad request'}), 400

@powerbi_bp.errorhandler(500)
def internal_error(error):
    """Handle internal server error"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error occurred'}), 500