# routes/excel_converter_routes.py
import os
from io import BytesIO
from flask import Blueprint, render_template, request, flash, redirect, send_file, current_app
import pandas as pd
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file

excel_converter_bp = Blueprint('excel_converter', __name__)

@excel_converter_bp.route('/excel-converter', methods=['GET', 'POST'])
def excel_converter():
    from config import ALLOWED_CONVERTER_EXTENSIONS
    
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
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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
