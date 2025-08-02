# config.py
import os

# --- Allowed File Extensions ---
ALLOWED_CONVERTER_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff', 'tif', 'ico', 'heic', 'heif', 'raw', 'cr2', 'nef', 'arw', 'dng', 'svg'},
    'pdf': {'pdf'},
    'doc': {'docx', 'doc', 'odt', 'rtf', 'txt'},
    'excel': {'xlsx', 'xls', 'ods', 'csv'},
    'powerpoint': {'pptx', 'ppt', 'odp'},
    'video': {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'},
    'audio': {'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma'},
    'archive': {'zip', 'rar', '7z', 'tar', 'gz', 'bz2'},
    'text': {'txt', 'md', 'html', 'xml', 'json', 'yaml', 'yml', 'css', 'js', 'py', 'java', 'cpp', 'c', 'h'}
}
ALLOWED_COMPRESS_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
ALLOWED_CROP_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
ALLOWED_PDF_EDITOR_EXTENSIONS = {'pdf'}

# --- Folder Setup for Render's Persistent Disk ---
RENDER_DISK_PATH = '/var/data'

def get_base_dir():
    if os.path.exists(RENDER_DISK_PATH):
        return RENDER_DISK_PATH
    else:
        return os.path.dirname(os.path.abspath(__file__))

def setup_directories(app):
    """Setup upload and compressed directories"""
    base_dir = get_base_dir()
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')
    app.config['COMPRESSED_FOLDER'] = os.path.join(base_dir, 'compressed')
    app.config['ALLOWED_CROP_EXTENSIONS'] = ALLOWED_CROP_EXTENSIONS
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['COMPRESSED_FOLDER'], exist_ok=True)
