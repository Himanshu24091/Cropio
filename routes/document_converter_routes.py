# routes/document_converter_routes.py
import os
from io import BytesIO
from flask import Blueprint, render_template, request, flash, redirect, send_file, current_app
from docx import Document
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file

document_converter_bp = Blueprint('document_converter', __name__)

@document_converter_bp.route('/document-converter', methods=['GET', 'POST'])
def document_converter():
    from config import ALLOWED_CONVERTER_EXTENSIONS
    
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
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
