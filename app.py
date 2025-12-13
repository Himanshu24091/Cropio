#!/usr/bin/env python3
"""
Bootstrapping: ensure we run inside the project's virtual environment when
invoked as `python app.py`. If not already in a venv, re-exec using the local
venv interpreter so that all blueprints (e.g., markdown-html-converter) load
with the correct dependencies.
"""
import os as _os
import sys as _sys
from pathlib import Path as _Path

# Re-exec with venv Python if not already inside a virtual environment
if __name__ == '__main__':
    try:
        in_venv = hasattr(_sys, 'real_prefix') or (
            hasattr(_sys, 'base_prefix') and _sys.base_prefix != _sys.prefix
        )
        if not in_venv:
            project_root = _Path(__file__).resolve().parent
            candidates = [
                project_root / 'venv' / 'Scripts' / 'python.exe',   # Windows
                project_root / 'venv' / 'bin' / 'python'             # Unix/macOS
            ]
            for interp in candidates:
                if interp.exists():
                    # Re-exec current script with venv interpreter
                    _os.execv(str(interp), [str(interp), __file__])
            # If no venv found, continue with system Python (may be limited)
    except Exception:
        # Fail open: continue without re-exec to avoid blocking startup
        pass

# app.py - Cropio SaaS Platform
# Professional Grade Implementation with Security, Logging, and Error Handling
import os
import sys
from pathlib import Path
from flask import Flask, request, g
from security import initialize_security
from flask_login import LoginManager
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import time
from datetime import datetime

# Import configuration and utilities
from config import setup_flask_config
from utils.helpers import cleanup_files

# Import database models
from models import db, User, init_database

# Import email service
from utils.email_service import mail, init_mail

# Import middleware
from middleware import init_usage_tracking

# Import professional core systems
from core.logging_config import setup_logging, cropio_logger
from core.error_handlers import init_error_handlers, create_error_monitoring_blueprint

# Import all route blueprints
from routes.main_routes import main_bp
from routes.image_converter.image_converter_routes import image_converter_bp
from routes.pdf_converters.pdf_converter_routes import pdf_converter_bp
from routes.document_converter.document_converter_routes import document_converter_bp  # Old import
# from routes.document_converter.document_converter_routes import document_converter_bp  # New Document Converter
from routes.excel_converter.excel_converter_routes import excel_converter_bp
from routes.file_compressor.file_compressor_routes import file_compressor_bp
from routes.image_converter.image_cropper_routes import image_cropper_bp
from routes.pdf_converters.pdf_editor_routes import pdf_editor_bp
from routes.file_serving_routes import file_serving_bp
from routes.reverse_converter_routes import reverse_converter_bp
from routes.text_ocr_converters.text_ocr_routes import text_ocr_bp
from routes.pdf_converters.secure_pdf_routes import secure_pdf_bp
from routes.pdf_converters.pdf_merge_routes import pdf_merge_bp
from routes.pdf_converters.pdf_signature_routes import pdf_signature_bp
from routes.pdf_converters.pdf_page_delete_routes import pdf_page_delete_bp
from routes.notebook_converter.notebook_converter_routes import notebook_converter_bp
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.presentation_converter.presentation_converter_routes import presentation_converter_bp
from routes.pdf_converters.pdf_presentation_converter_routes import pdf_presentation_converter_bp
from routes.pdf_converters.powerbi_converter_routes import powerbi_converter_bp

# Import API routes
from routes.api_routes import api_bp

# Import admin routes
from routes.admin import admin  # Admin routes
from routes.health_routes import health_bp  # Health check endpoints
from routes.legal_routes import legal_bp  # Legal pages (Terms, Privacy)
from routes.analytics_routes import analytics_bp  # Usage Analytics
# from routes.universal_converter_routes import universal_converter_bp  # Commented out due to missing dependencies

# Phase 1.5 - New converter blueprints (with unique names to avoid conflicts)
try:
    from routes.latex_pdf_routes import latex_pdf_bp as latex_pdf_doc_bp
except:
    latex_pdf_doc_bp = None
    
try:
    from routes.document.markdown_html_converter_routes import markdown_html_converter_bp
except:
    markdown_html_converter_bp = None
    
try:
    from routes.image.heic_jpg_routes import heic_jpg_bp as heic_jpg_img_bp
except:
    heic_jpg_img_bp = None
    
try:
    from routes.image.raw_jpg_routes import raw_jpg_bp
except:
    raw_jpg_bp = None
    
try:
    from routes.image.gif_png_sequence_routes import gif_png_sequence_bp
except:
    gif_png_sequence_bp = None
    
try:
    from routes.image.gif_mp4_routes import gif_mp4_bp
except:
    gif_mp4_bp = None

try:
    from routes.web_code.html_pdf_snapshot_routes import html_pdf_snapshot_bp
except:
    html_pdf_snapshot_bp = None
    
    
try:
    from routes.web_code.yaml_json_routes import yaml_json_bp
except:
    yaml_json_bp = None

def setup_latex_environment():
    """Setup LaTeX environment for the application"""
    try:
        # Try to setup LaTeX environment if the script exists
        setup_script_path = Path(__file__).parent / "setup_latex_env.py"
        if setup_script_path.exists():
            import setup_latex_env
            setup_latex_env.setup_latex_env()
    except ImportError:
        # setup_latex_env.py doesn't exist or has issues
        print("WARNING: LaTeX environment setup script not found - LaTeX features may not work")
    except Exception as e:
        print(f"WARNING: LaTeX environment setup failed: {e}")

def create_app():
    """Application factory function with professional-grade initialization"""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Setup LaTeX environment before anything else
    setup_latex_environment()
    
    # Setup Flask configuration (includes database, directories, etc.)
    setup_flask_config(app)
    
    # Initialize professional logging system FIRST
    setup_logging(app)
    cropio_logger.info("Starting Cropio SaaS Platform initialization")
    
    # Initialize security features
    try:
        initialize_security(app)
        cropio_logger.info("Security features initialized successfully")
    except Exception as e:
        cropio_logger.error(f"Failed to initialize security features: {e}", exc_info=True)
        sys.exit(1)
    
    # Initialize error handlers
    try:
        init_error_handlers(app)
        cropio_logger.info("Error handlers initialized successfully")
    except Exception as e:
        cropio_logger.error(f"Failed to initialize error handlers: {e}", exc_info=True)
        # Continue without error handlers in emergency
    
    # Initialize database
    try:
        db.init_app(app)
        cropio_logger.info("Database connection initialized")
    except Exception as e:
        cropio_logger.error(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)
    
    # Setup Flask-Login with security enhancements
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'  # Enhanced session protection
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except Exception as e:
            cropio_logger.error(f"Error loading user {user_id}: {e}")
            return None
    
    # Initialize Flask-Mail
    try:
        init_mail(app)
        cropio_logger.info("Email service initialized")
    except Exception as e:
        cropio_logger.warning(f"Email service initialization failed: {e}")
    
    # Initialize usage tracking middleware
    try:
        init_usage_tracking(app)
        cropio_logger.info("Usage tracking middleware initialized")
    except Exception as e:
        cropio_logger.warning(f"Usage tracking initialization failed: {e}")
    
    # Setup database migrations
    migrate = Migrate(app, db)
    
    # Add detailed request logging middleware
    @app.before_request
    def before_request():
        g.start_time = time.time()
        g.request_id = request.headers.get('X-Request-ID', os.urandom(8).hex())
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Get client IP
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if client_ip and ',' in client_ip:
                client_ip = client_ip.split(',')[0].strip()
            
            # Format timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
            
            # Log all requests with detailed information
            log_message = f"{client_ip} - - [{datetime.now().strftime('%d/%b/%Y %H:%M:%S')}] \"{request.method} {request.path}"
            if request.query_string:
                log_message += f"?{request.query_string.decode()}"
            log_message += f" {request.environ.get('SERVER_PROTOCOL', 'HTTP/1.1')}\" {response.status_code} -"
            
            # Print to console with color (skip static files for cleaner logs)
            if not request.path.startswith('/static/'):
                if response.status_code >= 500:
                    print(f"\033[91m{timestamp} - werkzeug - INFO - {log_message}\033[0m")  # Red for errors
                elif response.status_code >= 400:
                    print(f"\033[93m{timestamp} - werkzeug - INFO - {log_message}\033[0m")  # Yellow for client errors
                elif response.status_code >= 300:
                    print(f"\033[94m{timestamp} - werkzeug - INFO - {log_message}\033[0m")  # Blue for redirects
                else:
                    print(f"\033[92m{timestamp} - werkzeug - INFO - {log_message}\033[0m")  # Green for success
            
            # Log slow requests separately
            if duration > 2.0:
                cropio_logger.performance_warning(
                    f"Slow request: {request.method} {request.path}",
                    duration=duration,
                    extra_data={
                        'request_id': getattr(g, 'request_id', ''),
                        'status_code': response.status_code
                    }
                )
        return response
    
    # Create database tables and initialize data
    with app.app_context():
        try:
            init_database()
            cropio_logger.info("Database initialized successfully")
        except Exception as e:
            cropio_logger.error(f"Database initialization error: {e}", exc_info=True)
            # Create tables anyway for development
            try:
                db.create_all()
                cropio_logger.info("Database tables created (fallback)")
            except Exception as create_error:
                cropio_logger.error(f"Failed to create database tables: {create_error}", exc_info=True)
                sys.exit(1)
    
    # Register blueprints
    try:
        app.register_blueprint(main_bp)
        app.register_blueprint(image_converter_bp)
        app.register_blueprint(pdf_converter_bp)
        app.register_blueprint(document_converter_bp)
        app.register_blueprint(excel_converter_bp)
        app.register_blueprint(file_compressor_bp)
        app.register_blueprint(image_cropper_bp)  # Image Cropper
        app.register_blueprint(pdf_editor_bp)
        app.register_blueprint(file_serving_bp)
        app.register_blueprint(reverse_converter_bp)
        app.register_blueprint(text_ocr_bp)
        app.register_blueprint(secure_pdf_bp)
        app.register_blueprint(pdf_merge_bp)
        app.register_blueprint(pdf_signature_bp)
        app.register_blueprint(pdf_page_delete_bp)
        app.register_blueprint(notebook_converter_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(presentation_converter_bp)  # PPTX to PDF Converter
        app.register_blueprint(pdf_presentation_converter_bp)  # PDF to PPTX Converter
        app.register_blueprint(powerbi_converter_bp)  # PowerBI to PDF Converter
        app.register_blueprint(api_bp)  # Global API routes
        app.register_blueprint(health_bp)  # Health check endpoints
        app.register_blueprint(admin)
        app.register_blueprint(legal_bp)  # Legal pages
        app.register_blueprint(analytics_bp)  # Usage Analytics
        
        # Register new organized converter blueprints
        if latex_pdf_doc_bp:
            app.register_blueprint(latex_pdf_doc_bp)  # Document LaTeX converter
        if heic_jpg_img_bp:
            app.register_blueprint(heic_jpg_img_bp)   # Image HEIC converter
        if yaml_json_bp:
            app.register_blueprint(yaml_json_bp)      # Web Code YAML/JSON converter
        if markdown_html_converter_bp:
            app.register_blueprint(markdown_html_converter_bp)
        if raw_jpg_bp:
            app.register_blueprint(raw_jpg_bp)
        if gif_png_sequence_bp:
            app.register_blueprint(gif_png_sequence_bp)
        if gif_mp4_bp:
            app.register_blueprint(gif_mp4_bp)
        if html_pdf_snapshot_bp:
            app.register_blueprint(html_pdf_snapshot_bp)  # Web Code HTML PDF Snapshot converter
        
        cropio_logger.info("All blueprints registered successfully")
        
        # Register monitoring blueprint for admin
        monitoring_bp = create_error_monitoring_blueprint()
        app.register_blueprint(monitoring_bp)
        
        cropio_logger.info("All blueprints registered successfully")
    except Exception as e:
        cropio_logger.error(f"Failed to register blueprints: {e}", exc_info=True)
        sys.exit(1)
    
    cropio_logger.info("Cropio SaaS Platform initialization completed successfully")
    return app

# Create the app
app = create_app()

# Background Scheduler for File Cleanup
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(cleanup_files, 'interval', minutes=30)
scheduler.start()

# Graceful shutdown handler
def shutdown_handler():
    """Gracefully shutdown the application"""
    try:
        if scheduler.running:
            scheduler.shutdown(wait=False)
            cropio_logger.info("Background scheduler shutdown complete")
    except Exception as e:
        cropio_logger.error(f"Error during scheduler shutdown: {e}")
    
    cropio_logger.info("Cropio SaaS Platform shutdown complete")

# Route to serve uploaded files
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Register shutdown handler
atexit.register(shutdown_handler)

if __name__ == '__main__':
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Enable debug mode ONLY in development (SECURITY FIX)
        app.debug = os.environ.get('FLASK_ENV') == 'development'
        
        # Get port from environment or use default 5000
        port = int(os.environ.get('PORT', 5000))
        
        # Print server startup information
        print("\033[92m[SERVER] Server ready to accept connections!\033[0m")
        print("=" * 50)
        print(f"* Serving Flask app 'app'")
        print(f"* Debug mode: on")
        print(f"* Running on all addresses (0.0.0.0)")
        print(f"* Running on http://127.0.0.1:{port}")
        print(f"* Running on http://192.168.1.4:{port}")
        print(f"\033[93m * Restarting with stat\033[0m")
        print(f"\033[93m * Debugger is active!\033[0m")
        print(f"\033[93m * Debugger PIN: xxx-xxx-xxx\033[0m")
        print(f"\033[94m2025-08-22 13:22:47,496 - werkzeug - INFO - Press CTRL+C to quit\033[0m")
        
        # Run the application
        is_dev = os.environ.get('FLASK_ENV') == 'development'
        app.run(
            host='0.0.0.0',  # This will make it accessible on all network interfaces
            port=port,
            debug=is_dev,  # Enable debug mode ONLY in development (SECURITY FIX)
            use_reloader=is_dev,  # Auto-reload on code changes (dev only)
            use_debugger=is_dev   # Enable debugger (dev only)
        )
    except KeyboardInterrupt:
        cropio_logger.info("Received shutdown signal")
        shutdown_handler()
        sys.exit(0)
    except Exception as e:
        cropio_logger.error(f"Fatal error during startup: {e}", exc_info=True)
        sys.exit(1)
