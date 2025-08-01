# routes/file_serving_routes.py
from flask import Blueprint, send_from_directory, current_app

file_serving_bp = Blueprint('file_serving', __name__)

@file_serving_bp.route('/download/<filename>')
def download_file(filename):
    """Serves compressed files for download."""
    return send_from_directory(current_app.config['COMPRESSED_FOLDER'], filename, as_attachment=True)

@file_serving_bp.route('/preview/<filename>')
def preview_file(filename):
    """Serves temporary preview images from the uploads folder."""
    if 'preview_' in filename:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    else:
        return send_from_directory(current_app.config['COMPRESSED_FOLDER'], filename)
