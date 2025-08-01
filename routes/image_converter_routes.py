# routes/image_converter_routes.py
import os
from io import BytesIO
from flask import Blueprint, render_template, request, flash, redirect, send_file, current_app
from PIL import Image
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file

image_converter_bp = Blueprint('image_converter', __name__)

@image_converter_bp.route('/image-converter', methods=['GET', 'POST'])
def image_converter():
    from config import ALLOWED_CONVERTER_EXTENSIONS
    
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
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
                current_app.logger.error(f"Error converting image: {e}")
                flash(f"Error converting image. Please try again.", 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type for image conversion.', 'error')
            return redirect(request.url)

    accept_string = ",".join(['.' + ext for ext in allowed_extensions])
    return render_template('image_converter.html', accept_string=accept_string)
