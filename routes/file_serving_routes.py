# routes/file_serving_routes.py
from flask import Blueprint, send_from_directory, current_app, abort
import os
from werkzeug.utils import secure_filename

file_serving_bp = Blueprint('file_serving', __name__)

@file_serving_bp.route('/download/<filename>')
def download_file(filename):
    """Serves files for download from multiple possible locations."""
    original_filename = filename
    filename = secure_filename(filename)
    
    current_app.logger.info(f"Download request - Original: {original_filename}, Secured: {filename}")
    
    # Check multiple folders in order of priority
    folders_to_check = [
        current_app.config.get('OUTPUT_FOLDER'),
        current_app.config.get('COMPRESSED_FOLDER'),
        current_app.config.get('UPLOAD_FOLDER')
    ]
    
    for folder in folders_to_check:
        if folder:
            file_path = os.path.join(folder, filename)
            current_app.logger.info(f"Checking: {file_path}")
            if os.path.exists(file_path):
                current_app.logger.info(f"Found file at: {file_path}")
                try:
                    return send_from_directory(folder, filename, as_attachment=True, download_name=original_filename)
                except Exception as e:
                    current_app.logger.error(f"Error serving file: {e}")
                    abort(500)
    
    # Debug: List files in OUTPUT_FOLDER
    output_folder = current_app.config.get('OUTPUT_FOLDER')
    if output_folder and os.path.exists(output_folder):
        files = os.listdir(output_folder)
        current_app.logger.error(f"File {filename} not found. Files in OUTPUT_FOLDER: {files[-5:]}")
    
    # If file not found in any folder
    current_app.logger.error(f"File not found: {filename}")
    abort(404)

@file_serving_bp.route('/preview/<filename>')
def preview_file(filename):
    """Serves temporary preview images from the uploads folder."""
    if 'preview_' in filename or 'thumb_' in filename:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    else:
        return send_from_directory(current_app.config['COMPRESSED_FOLDER'], filename)

@file_serving_bp.route('/serve/<filename>')
def serve_file(filename):
    """Serves files from uploads folder (including PDFs)."""
    # Secure the filename to prevent directory traversal
    filename = secure_filename(filename)
    
    # Check if file exists
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        abort(404)
    
    # Determine if it should be served as attachment or inline
    # PDFs and images are served inline, others as attachment
    _, ext = os.path.splitext(filename.lower())
    if ext in ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp']:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=False)
    else:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# Support for uploads via /uploads/ path for backward compatibility
@file_serving_bp.route('/uploads/<filename>')
def serve_upload_file(filename):
    """Alternative route for serving uploaded files."""
    return serve_file(filename)
