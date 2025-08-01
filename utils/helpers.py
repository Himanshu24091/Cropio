# utils/helpers.py
import time
import os
from flask import current_app
from PIL import Image
import fitz

def allowed_file(filename, allowed_extensions):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def compress_image(input_path, output_path, level):
    """Compress image files"""
    try:
        with Image.open(input_path) as img:
            file_format = img.format
            quality_map = {'low': 40, 'medium': 65, 'high': 85}
            quality = quality_map.get(level, 75)
            if file_format == 'PNG': 
                img.save(output_path, 'PNG', optimize=True)
            elif file_format in ['JPEG', 'JPG']: 
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
            elif file_format == 'WEBP': 
                img.save(output_path, 'WEBP', quality=quality)
            else: 
                img.convert('RGB').save(output_path, 'JPEG', quality=quality, optimize=True)
        return True
    except Exception as e:
        current_app.logger.error(f"Error compressing image: {e}")
        return False

def compress_pdf(input_path, output_path, level):
    """Compress PDF files"""
    try:
        garbage_map = {'low': 1, 'medium': 2, 'high': 4}
        garbage = garbage_map.get(level, 2)
        doc = fitz.open(input_path)
        doc.save(output_path, garbage=garbage, deflate=True, clean=True)
        doc.close()
        return True
    except Exception as e:
        current_app.logger.error(f"Error compressing PDF: {e}")
        return False

def cleanup_files():
    """Background cleanup function for old files"""
    with current_app.app_context():
        now = time.time()
        cutoff = now - 3600  # 1 hour
        for folder_key in ['UPLOAD_FOLDER', 'COMPRESSED_FOLDER']:
            folder = current_app.config[folder_key]
            try:
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff:
                        os.remove(file_path)
                        print(f"Deleted old file: {filename}")
            except Exception as e:
                current_app.logger.error(f"Error during cleanup in {folder}: {e}")
