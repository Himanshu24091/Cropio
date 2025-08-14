from flask import Blueprint, request, render_template, flash, send_file, current_app, jsonify, redirect, url_for
import os
import json
import uuid
import subprocess
import tempfile
from werkzeug.utils import secure_filename
from datetime import datetime
import nbformat
from nbconvert import HTMLExporter, MarkdownExporter, PDFExporter
from nbconvert.preprocessors import TagRemovePreprocessor
import pypandoc

notebook_converter_bp = Blueprint('notebook_converter', __name__)

ALLOWED_EXTENSIONS = {'ipynb'}
SUPPORTED_FORMATS = {
    'html': {'extension': '.html', 'mime_type': 'text/html'},
    'markdown': {'extension': '.md', 'mime_type': 'text/markdown'},
    'pdf': {'extension': '.pdf', 'mime_type': 'application/pdf'},
    'docx': {'extension': '.docx', 'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'},
    'txt': {'extension': '.txt', 'mime_type': 'text/plain'},
    'latex': {'extension': '.tex', 'mime_type': 'application/x-latex'},
    'rst': {'extension': '.rst', 'mime_type': 'text/x-rst'}
}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_notebook(file_path):
    """Validate if the uploaded file is a valid Jupyter notebook"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            notebook = nbformat.read(f, as_version=4)
        return True, notebook
    except Exception as e:
        return False, str(e)

def convert_notebook_nbconvert(notebook_path, output_format, output_path):
    """Convert notebook using nbconvert"""
    try:
        if output_format == 'html':
            exporter = HTMLExporter()
            exporter.template_name = 'classic'
        elif output_format == 'markdown':
            exporter = MarkdownExporter()
        elif output_format == 'pdf':
            # Check if XeLaTeX is available before attempting PDF conversion
            import shutil
            if not shutil.which('xelatex'):
                return False, "PDF conversion requires XeLaTeX. Please install a TeX distribution like MiKTeX or TeX Live. Alternatively, try converting to HTML first."
            exporter = PDFExporter()
        elif output_format == 'latex':
            from nbconvert import LatexExporter
            exporter = LatexExporter()
        else:
            return False, f"Format {output_format} not supported by nbconvert"
        
        (body, resources) = exporter.from_filename(notebook_path)
        
        with open(output_path, 'w' if output_format != 'pdf' else 'wb', 
                 encoding='utf-8' if output_format != 'pdf' else None) as f:
            f.write(body)
        
        return True, "Conversion successful"
    except Exception as e:
        # Provide more helpful error messages for common issues
        error_msg = str(e)
        if 'xelatex not found' in error_msg.lower():
            return False, "PDF conversion requires XeLaTeX. Please install MiKTeX or TeX Live for Windows. Alternatively, try converting to HTML first."
        elif 'pandoc' in error_msg.lower():
            return False, "Pandoc is required for this conversion. Please install Pandoc from https://pandoc.org/installing.html"
        else:
            return False, f"Conversion error: {error_msg}"

def convert_notebook_pypandoc(notebook_path, output_format, output_path):
    """Convert notebook using pypandoc"""
    try:
        # First convert to markdown using nbconvert
        from nbconvert import MarkdownExporter
        md_exporter = MarkdownExporter()
        (md_body, resources) = md_exporter.from_filename(notebook_path)
        
        # Create temporary markdown file
        temp_md = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
        temp_md.write(md_body)
        temp_md.close()
        
        try:
            if output_format == 'docx':
                pypandoc.convert_file(temp_md.name, 'docx', outputfile=output_path)
            elif output_format == 'txt':
                pypandoc.convert_file(temp_md.name, 'plain', outputfile=output_path)
            elif output_format == 'rst':
                pypandoc.convert_file(temp_md.name, 'rst', outputfile=output_path)
            else:
                return False, f"Format {output_format} not supported by pypandoc"
            
            return True, "Conversion successful"
        finally:
            # Clean up temporary file
            os.unlink(temp_md.name)
            
    except Exception as e:
        return False, str(e)

@notebook_converter_bp.route('/notebook-converter')
def notebook_converter():
    """Display the notebook converter page"""
    return render_template('notebook_converter.html', formats=SUPPORTED_FORMATS)

@notebook_converter_bp.route('/notebook-converter', methods=['POST'])
def convert_notebook():
    """Handle notebook conversion"""
    try:
        # Check if file was uploaded
        if 'notebook_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('notebook_converter.notebook_converter'))
        
        file = request.files['notebook_file']
        output_format = request.form.get('output_format', 'html')
        
        # Validate file
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('notebook_converter.notebook_converter'))
        
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload a .ipynb file', 'error')
            return redirect(url_for('notebook_converter.notebook_converter'))
        
        if output_format not in SUPPORTED_FORMATS:
            flash('Invalid output format selected', 'error')
            return redirect(url_for('notebook_converter.notebook_converter'))
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        base_name = os.path.splitext(filename)[0]
        
        # Save uploaded file
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(upload_path)
        
        # Validate notebook
        is_valid, notebook_or_error = validate_notebook(upload_path)
        if not is_valid:
            os.remove(upload_path)
            flash(f'Invalid notebook file: {notebook_or_error}', 'error')
            return redirect(url_for('notebook_converter.notebook_converter'))
        
        # Prepare output file path
        output_extension = SUPPORTED_FORMATS[output_format]['extension']
        output_filename = f"{base_name}_{unique_id}{output_extension}"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        
        # Convert notebook
        success = False
        error_message = ""
        
        # Try nbconvert first for supported formats
        if output_format in ['html', 'markdown', 'pdf', 'latex']:
            success, message = convert_notebook_nbconvert(upload_path, output_format, output_path)
            if not success:
                error_message = f"nbconvert failed: {message}"
        
        # Try pypandoc for other formats or as fallback
        if not success and output_format in ['docx', 'txt', 'rst']:
            success, message = convert_notebook_pypandoc(upload_path, output_format, output_path)
            if not success:
                error_message = f"pypandoc failed: {message}"
        
        # Clean up uploaded file
        os.remove(upload_path)
        
        if not success:
            flash(f'Conversion failed: {error_message}', 'error')
            return redirect(url_for('notebook_converter.notebook_converter'))
        
        # Return success response with download link
        flash(f'Notebook successfully converted to {output_format.upper()}', 'success')
        return render_template('notebook_converter.html', 
                             formats=SUPPORTED_FORMATS,
                             download_file=output_filename,
                             download_format=output_format)
        
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('notebook_converter.notebook_converter'))

@notebook_converter_bp.route('/notebook-download/<filename>')
def download_file(filename):
    """Download converted file"""
    try:
        file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            flash('File not found', 'error')
            return redirect(url_for('notebook_converter.notebook_converter'))
        
        # Determine mime type from filename
        file_extension = os.path.splitext(filename)[1].lower()
        mime_type = 'application/octet-stream'  # default
        
        for format_info in SUPPORTED_FORMATS.values():
            if format_info['extension'] == file_extension:
                mime_type = format_info['mime_type']
                break
        
        return send_file(file_path, 
                        as_attachment=True,
                        download_name=filename,
                        mimetype=mime_type)
        
    except Exception as e:
        flash(f'Download failed: {str(e)}', 'error')
        return redirect(url_for('notebook_converter.notebook_converter'))

@notebook_converter_bp.route('/api/convert', methods=['POST'])
def api_convert():
    """API endpoint for notebook conversion"""
    try:
        if 'notebook_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['notebook_file']
        output_format = request.form.get('output_format', 'html')
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        if output_format not in SUPPORTED_FORMATS:
            return jsonify({'error': 'Invalid output format'}), 400
        
        # Process conversion (similar to above but return JSON)
        unique_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        base_name = os.path.splitext(filename)[0]
        
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(upload_path)
        
        is_valid, notebook_or_error = validate_notebook(upload_path)
        if not is_valid:
            os.remove(upload_path)
            return jsonify({'error': f'Invalid notebook: {notebook_or_error}'}), 400
        
        output_extension = SUPPORTED_FORMATS[output_format]['extension']
        output_filename = f"{base_name}_{unique_id}{output_extension}"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        
        # Convert
        success = False
        if output_format in ['html', 'markdown', 'pdf', 'latex']:
            success, message = convert_notebook_nbconvert(upload_path, output_format, output_path)
        
        if not success and output_format in ['docx', 'txt', 'rst']:
            success, message = convert_notebook_pypandoc(upload_path, output_format, output_path)
        
        os.remove(upload_path)
        
        if not success:
            return jsonify({'error': f'Conversion failed: {message}'}), 500
        
        return jsonify({
            'success': True,
            'download_url': url_for('notebook_converter.download_file', filename=output_filename),
            'filename': output_filename,
            'format': output_format
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
