# routes/pdf_converter_routes.py
import os
from io import BytesIO
from flask import Blueprint, render_template, request, flash, redirect, send_file, current_app
import fitz
import pandas as pd
from pdf2docx import Converter
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file

pdf_converter_bp = Blueprint('pdf_converter', __name__)

@pdf_converter_bp.route('/pdf-converter', methods=['GET', 'POST'])
def pdf_converter():
    from config import ALLOWED_CONVERTER_EXTENSIONS

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
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
                current_app.logger.error(f"Error converting PDF: {e}")
                flash(f"Error converting PDF. Please try again.", 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a PDF file.', 'error')
            return redirect(request.url)
    
    return render_template('pdf_converter.html')

