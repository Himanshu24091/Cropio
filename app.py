# app.py
import os
import uuid
import time
import json
from datetime import datetime, timedelta
from io import BytesIO

from apscheduler.schedulers.background import BackgroundScheduler
from docx import Document
from flask import (Flask, jsonify, redirect, render_template, request,
                   send_from_directory, flash, url_for, send_file)
from pdf2docx import Converter
from PIL import Image
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
import pandas as pd

# ==============================================================================
# App Initialization & Configuration
# ==============================================================================
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_default_secret_key_for_development')
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

# --- Folder Setup for Render's Persistent Disk ---
RENDER_DISK_PATH = '/var/data'
if os.path.exists(RENDER_DISK_PATH):
    BASE_DIR = RENDER_DISK_PATH
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['COMPRESSED_FOLDER'] = os.path.join(BASE_DIR, 'compressed')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['COMPRESSED_FOLDER'], exist_ok=True)

# --- Allowed File Extensions ---
ALLOWED_CONVERTER_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'},
    'pdf': {'pdf'},
    'doc': {'docx'},
    'excel': {'xlsx', 'xls'}
}
ALLOWED_COMPRESS_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
ALLOWED_CROP_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
ALLOWED_PDF_EDITOR_EXTENSIONS = {'pdf'}

# ==============================================================================
# Helper Functions
# ==============================================================================
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def compress_image(input_path, output_path, level):
    try:
        with Image.open(input_path) as img:
            file_format = img.format
            quality_map = {'low': 40, 'medium': 65, 'high': 85}
            quality = quality_map.get(level, 75)
            if file_format == 'PNG': img.save(output_path, 'PNG', optimize=True)
            elif file_format in ['JPEG', 'JPG']: img.save(output_path, 'JPEG', quality=quality, optimize=True)
            elif file_format == 'WEBP': img.save(output_path, 'WEBP', quality=quality)
            else: img.convert('RGB').save(output_path, 'JPEG', quality=quality, optimize=True)
        return True
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False

def compress_pdf(input_path, output_path, level):
    try:
        garbage_map = {'low': 1, 'medium': 2, 'high': 4}
        garbage = garbage_map.get(level, 2)
        doc = fitz.open(input_path)
        doc.save(output_path, garbage=garbage, deflate=True, clean=True)
        doc.close()
        return True
    except Exception as e:
        print(f"Error compressing PDF: {e}")
        return False

# ==============================================================================
# Background Scheduler for File Cleanup
# ==============================================================================
def cleanup_files():
    with app.app_context():
        now = time.time()
        cutoff = now - 3600
        for folder_key in ['UPLOAD_FOLDER', 'COMPRESSED_FOLDER']:
            folder = app.config[folder_key]
            try:
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff:
                        os.remove(file_path)
                        print(f"Deleted old file: {filename}")
            except Exception as e:
                print(f"Error during cleanup in {folder}: {e}")

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(cleanup_files, 'interval', minutes=30)
scheduler.start()

# ==============================================================================
# Main and Converter Routes
# ==============================================================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image-converter', methods=['GET', 'POST'])
def image_converter():
    allowed_extensions = ALLOWED_CONVERTER_EXTENSIONS['image']
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename, allowed_extensions):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            output_format = request.form.get('format')
            try:
                img = Image.open(filepath)
                output_buffer = BytesIO()
                output_filename = f"{filename.rsplit('.', 1)[0]}.{output_format.lower()}"

                if output_format.lower() in ['jpeg', 'jpg', 'bmp', 'pdf'] and img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                if output_format.lower() == 'ico':
                    img.save(output_buffer, format='ICO', sizes=[(32,32)])
                else:
                    img.save(output_buffer, format=output_format.upper())
                
                output_buffer.seek(0)
                flash(f"Successfully converted to {output_format.upper()}!", 'success')
                return send_file(output_buffer, as_attachment=True, download_name=output_filename)
            except Exception as e:
                flash(f"Error converting image: {e}", 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type for image conversion.', 'error')
            return redirect(request.url)

    accept_string = ",".join(['.' + ext for ext in allowed_extensions])
    return render_template('image_converter.html', accept_string=accept_string)

@app.route('/pdf-converter', methods=['GET', 'POST'])
def pdf_converter():
    allowed_extensions = ALLOWED_CONVERTER_EXTENSIONS['pdf']
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename, allowed_extensions):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            output_format = request.form.get('format')
            try:
                if output_format == 'docx':
                    docx_file = f"{filepath.rsplit('.', 1)[0]}.docx"
                    cv = Converter(filepath)
                    cv.convert(docx_file, start=0, end=None)
                    cv.close()
                    flash('Successfully converted to DOCX!', 'success')
                    return send_file(docx_file, as_attachment=True)
                elif output_format == 'csv':
                    doc = fitz.open(filepath)
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    df = pd.DataFrame([x.split() for x in text.split('\n') if x.strip()])
                    csv_buffer = BytesIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    flash('Successfully converted to CSV!', 'success')
                    return send_file(csv_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}.csv")

            except Exception as e:
                flash(f"Error converting PDF: {e}", 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a PDF file.', 'error')
            return redirect(request.url)
    
    return render_template('pdf_converter.html')

@app.route('/document-converter', methods=['GET', 'POST'])
def document_converter():
    allowed_extensions = ALLOWED_CONVERTER_EXTENSIONS['doc']
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename, allowed_extensions):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            output_format = request.form.get('format')
            try:
                if output_format == 'pdf':
                    flash('DOCX to PDF conversion is not supported in this version.', 'error')
                    return redirect(request.url)
                elif output_format == 'txt':
                    doc = Document(filepath)
                    full_text = [para.text for para in doc.paragraphs]
                    text = '\n'.join(full_text)
                    txt_buffer = BytesIO(text.encode('utf-8'))
                    flash('Successfully converted to TXT!', 'success')
                    return send_file(txt_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}.txt")

            except Exception as e:
                flash(f"Error converting Document: {e}", 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a DOCX file.', 'error')
            return redirect(request.url)
    
    return render_template('document_converter.html')

@app.route('/excel-converter', methods=['GET', 'POST'])
def excel_converter():
    allowed_extensions = ALLOWED_CONVERTER_EXTENSIONS['excel']
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename, allowed_extensions):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            output_format = request.form.get('format')
            try:
                df = pd.read_excel(filepath)
                if output_format == 'csv':
                    csv_buffer = BytesIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    flash('Successfully converted to CSV!', 'success')
                    return send_file(csv_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}.csv")
                elif output_format == 'json':
                    json_buffer = BytesIO(df.to_json(orient='records').encode('utf-8'))
                    flash('Successfully converted to JSON!', 'success')
                    return send_file(json_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}.json")
            except Exception as e:
                flash(f"Error converting Excel: {e}", 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload an Excel file (XLSX, XLS).', 'error')
            return redirect(request.url)
            
    return render_template('excel_converter.html')

# ==============================================================================
# Compressor Routes
# ==============================================================================
@app.route('/compressor')
def compressor_page():
    return render_template('compressor.html')

@app.route('/compress', methods=['POST'])
def compress_files_route():
    try:
        files = request.files.getlist('files[]')
        level = request.form.get('level', 'medium')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400

        results = []
        for file in files:
            if not allowed_file(file.filename, ALLOWED_COMPRESS_EXTENSIONS):
                results.append({'filename': file.filename, 'error': 'File type not supported'})
                continue

            try:
                unique_id = uuid.uuid4().hex
                original_ext = file.filename.rsplit('.', 1)[1].lower()
                original_filename = f"{unique_id}.{original_ext}"
                input_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
                file.save(input_path)

                original_size = os.path.getsize(input_path)
                compressed_filename = f"compressed_{original_filename}"
                output_path = os.path.join(app.config['COMPRESSED_FOLDER'], compressed_filename)
                is_image = original_ext != 'pdf'
                success = compress_image(input_path, output_path, level) if is_image else compress_pdf(input_path, output_path, level)

                if success:
                    compressed_size = os.path.getsize(output_path)
                    reduction_percent = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0
                    results.append({
                        'filename': file.filename, 'original_size': original_size, 'compressed_size': compressed_size,
                        'reduction_percent': round(reduction_percent, 2), 'download_url': f'/download/{compressed_filename}',
                        'preview_url': f'/preview/{compressed_filename}' if is_image else None
                    })
                else:
                    results.append({'filename': file.filename, 'error': 'Failed to compress file'})
            
            except Exception as e:
                print(f"Error processing {file.filename}: {e}")
                results.append({'filename': file.filename, 'error': 'An error occurred during processing'})

        return jsonify({'results': results})

    except Exception as e:
        print(f"An unexpected error occurred in /compress route: {e}")
        return jsonify({'error': 'An internal server error occurred. Please try again later.'}), 500

# ==============================================================================
# Image Cropper Routes
# ==============================================================================
@app.route('/image-cropper')
def cropper_page():
    return render_template('cropper.html')

@app.route('/pdf-to-image-preview', methods=['POST'])
def pdf_to_image_preview():
    if 'file' not in request.files:
        return jsonify({'error': 'No file received'}), 400
    file = request.files['file']
    if file.filename == '' or not allowed_file(file.filename, {'pdf'}):
        return jsonify({'error': 'Invalid file type, PDF required'}), 400
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=150)
        unique_id = uuid.uuid4().hex
        preview_filename = f"preview_{unique_id}.png"
        preview_path = os.path.join(app.config['UPLOAD_FOLDER'], preview_filename)
        pix.save(preview_path)
        doc.close()
        return jsonify({'preview_url': f'/preview/{preview_filename}'})
    except Exception as e:
        print(f"Error converting PDF to preview: {e}")
        return jsonify({'error': 'Failed to generate PDF preview'}), 500

@app.route('/crop-image', methods=['POST'])
def crop_image_route():
    try:
        if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename, ALLOWED_CROP_EXTENSIONS):
            return jsonify({'error': 'Invalid file or file type not allowed'}), 400

        crop_data = json.loads(request.form.get('crop_data'))
        output_format = request.form.get('output_format', 'jpeg').lower()

        if output_format not in ['jpeg', 'png', 'webp', 'pdf']:
            return jsonify({'error': 'Invalid output format specified'}), 400

        source_is_pdf = file.filename.rsplit('.', 1)[1].lower() == 'pdf'
        if source_is_pdf:
            doc = fitz.open(stream=file.read(), filetype="pdf")
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
        else:
            img = Image.open(file.stream)

        x, y, width, height = int(crop_data['x']), int(crop_data['y']), int(crop_data['width']), int(crop_data['height'])
        cropped_img = img.crop((x, y, x + width, y + height))

        output_buffer = BytesIO()
        
        if output_format == 'pdf':
            if cropped_img.mode in ('RGBA', 'LA', 'P'):
                cropped_img = cropped_img.convert('RGB')
            cropped_img.save(output_buffer, format='PDF', resolution=100.0)
            mimetype = 'application/pdf'
        else:
            save_format = 'JPEG' if output_format == 'jpeg' else output_format.upper()
            if save_format == 'JPEG' and cropped_img.mode in ('RGBA', 'LA', 'P'):
                cropped_img = cropped_img.convert('RGB')
            cropped_img.save(output_buffer, format=save_format)
            mimetype = f'image/{output_format}'

        output_buffer.seek(0)
        
        original_name = secure_filename(file.filename).rsplit('.', 1)[0]
        download_filename = f"{original_name}_cropped.{output_format}"
        return send_file(output_buffer, mimetype=mimetype, as_attachment=True, download_name=download_filename)

    except Exception as e:
        print(f"An error occurred in /crop-image: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

# ==============================================================================
# PDF Editor Routes
# ==============================================================================
@app.route('/pdf-editor')
def pdf_editor_page():
    """Renders the new PDF Editor page."""
    return render_template('pdf_editor.html')

# ==============================================================================
# File Serving Routes (Consolidated)
# ==============================================================================
@app.route('/download/<filename>')
def download_file(filename):
    """Serves compressed files for download."""
    return send_from_directory(app.config['COMPRESSED_FOLDER'], filename, as_attachment=True)

@app.route('/preview/<filename>')
def preview_file(filename):
    """Serves temporary preview images from the uploads folder."""
    if 'preview_' in filename:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        return send_from_directory(app.config['COMPRESSED_FOLDER'], filename)

# ==============================================================================
# Main Execution
# ==============================================================================
if __name__ == '__main__':
    app.run(debug=True)
