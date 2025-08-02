# routes/compressor_routes.py
import os
import uuid
import time
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from utils.helpers import allowed_file, compress_image, compress_pdf, batch_compress_files, create_zip_archive

compressor_bp = Blueprint('compressor', __name__)

@compressor_bp.route('/compressor')
def compressor_page():
    return render_template('compressor.html')

@compressor_bp.route('/compress', methods=['POST'])
def compress_files_route():
    from config import ALLOWED_COMPRESS_EXTENSIONS
    
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
                input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], original_filename)
                file.save(input_path)

                original_size = os.path.getsize(input_path)
                compressed_filename = f"compressed_{original_filename}"
                output_path = os.path.join(current_app.config['COMPRESSED_FOLDER'], compressed_filename)
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
