# routes/cropper_routes.py
import os
import uuid
import json
from io import BytesIO
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
import fitz
from PIL import Image
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file

cropper_bp = Blueprint('cropper', __name__)

@cropper_bp.route('/image-cropper')
def cropper_page():
    return render_template('cropper.html')

@cropper_bp.route('/pdf-to-image-preview', methods=['POST'])
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
        preview_path = os.path.join(current_app.config['UPLOAD_FOLDER'], preview_filename)
        pix.save(preview_path)
        doc.close()
        return jsonify({'preview_url': f'/preview/{preview_filename}'})
    except Exception as e:
        print(f"Error converting PDF to preview: {e}")
        return jsonify({'error': 'Failed to generate PDF preview'}), 500

@cropper_bp.route('/crop-image', methods=['POST'])
def crop_image_route():
    try:
        if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename, current_app.config['ALLOWED_CROP_EXTENSIONS']):
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


