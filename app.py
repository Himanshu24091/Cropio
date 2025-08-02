# app_new.py
import os
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

# Import configuration and utilities
from config import setup_directories
from utils.helpers import cleanup_files

# Import all route blueprints
from routes.main_routes import main_bp
from routes.image_converter_routes import image_converter_bp
from routes.pdf_converter_routes import pdf_converter_bp
from routes.document_converter_routes import document_converter_bp
from routes.excel_converter_routes import excel_converter_bp
from routes.compressor_routes import compressor_bp
from routes.cropper_routes import cropper_bp
from routes.pdf_editor_routes import pdf_editor_bp
from routes.file_serving_routes import file_serving_bp
from routes.reverse_converter_routes import reverse_converter_bp
from routes.text_ocr_routes import text_ocr_bp
from routes.secure_pdf_routes import secure_pdf_bp
from routes.pdf_merge_routes import pdf_merge_bp
from routes.pdf_signature_routes import pdf_signature_bp
# from routes.universal_converter_routes import universal_converter_bp  # Commented out due to missing dependencies

def create_app():
    """Application factory function"""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    if app.config['SECRET_KEY'] == 'dev-secret-key-change-in-production':
        print("Warning: Using default SECRET_KEY. Set SECRET_KEY environment variable in production.")
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024
    
    # Setup directories
    setup_directories(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(image_converter_bp)
    app.register_blueprint(pdf_converter_bp)
    app.register_blueprint(document_converter_bp)
    app.register_blueprint(excel_converter_bp)
    app.register_blueprint(compressor_bp)
    app.register_blueprint(cropper_bp)
    app.register_blueprint(pdf_editor_bp)
    app.register_blueprint(file_serving_bp)
    app.register_blueprint(reverse_converter_bp)
    app.register_blueprint(text_ocr_bp)
    app.register_blueprint(secure_pdf_bp)
    app.register_blueprint(pdf_merge_bp)
    app.register_blueprint(pdf_signature_bp)
    
    return app

# Create the app
app = create_app()

# Background Scheduler for File Cleanup
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(cleanup_files, 'interval', minutes=30)
scheduler.start()

if __name__ == '__main__':
    # Bind to all network interfaces to allow mobile access
    app.run(host='0.0.0.0', port=5000, debug=True)
