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
    
    return app

# Create the app
app = create_app()

# Background Scheduler for File Cleanup
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(cleanup_files, 'interval', minutes=30)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)
