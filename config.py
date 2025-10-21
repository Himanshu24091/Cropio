# config.py - Professional Configuration Management
import os
import secrets
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration validation and utilities
class ConfigError(Exception):
    """Configuration validation error"""
    pass

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> str:
    """Get environment variable with validation"""
    value = os.environ.get(key, default)
    if required and not value:
        raise ConfigError(f"Required environment variable '{key}' is not set")
    return value

def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean environment variable"""
    return get_env_var(key, str(default)).lower() in ('true', '1', 'yes', 'on')

def get_env_int(key: str, default: int = 0) -> int:
    """Get integer environment variable"""
    try:
        return int(get_env_var(key, str(default)))
    except ValueError:
        raise ConfigError(f"Environment variable '{key}' must be an integer")

def generate_secret_key() -> str:
    """Generate a secure secret key"""
    return secrets.token_hex(32)

def validate_database_url(url: str) -> None:
    """Validate database URL format"""
    if not url or not url.startswith(('postgresql://', 'mysql://', 'sqlite://')):
        raise ConfigError(f"Invalid database URL format: {url}")

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
    'text': {'txt', 'md', 'html', 'xml', 'json', 'yaml', 'yml', 'css'}
}
ALLOWED_COMPRESS_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
ALLOWED_CROP_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
ALLOWED_PDF_EDITOR_EXTENSIONS = {'pdf'}

# --- GIF Converter Configuration ---
GIF_CONVERTER_CONFIG = {
    'max_file_size': 50 * 1024 * 1024,  # 50MB
    'max_frames': 500,  # Maximum frames per conversion
    'supported_input_formats': {
        'gif_to_png': ['gif'],
        'png_to_gif': ['png', 'jpg', 'jpeg']
    },
    'default_settings': {
        'frame_duration': 100,  # milliseconds
        'loop_count': 0,  # 0 = infinite
        'optimize': True,
        'dithering': False,
        'preserve_timing': True,
        'optimize_png': True
    },
    'quality_levels': {
        'low': {'colors': 64, 'optimize': True},
        'medium': {'colors': 128, 'optimize': True},
        'high': {'colors': 256, 'optimize': True}
    },
    'usage_limits': {
        'free_daily': 20,
        'premium_daily': 1000,
        'max_concurrent': 5
    }
}

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
    app.config['OUTPUT_FOLDER'] = os.path.join(base_dir, 'outputs')
    app.config['ALLOWED_CROP_EXTENSIONS'] = ALLOWED_CROP_EXTENSIONS
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['COMPRESSED_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)


# --- Professional Configuration Classes ---
class BaseConfig:
    """Base configuration with validation"""
    
    def __init__(self):
        self.validate_config()
    
    # Security Configuration
    SECRET_KEY = get_env_var('FLASK_SECRET_KEY', required=False) or generate_secret_key()
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Database Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    # Session Configuration
    SESSION_TIMEOUT = get_env_int('SESSION_TIMEOUT', 3600)
    PERMANENT_SESSION_LIFETIME = SESSION_TIMEOUT
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = get_env_int('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)  # 500MB default
    
    # JSON Request Configuration (for large document API requests)
    MAX_JSON_LENGTH = get_env_int('MAX_JSON_LENGTH', 50 * 1024 * 1024)  # 50MB for large documents
    
    # Request Timeout Configuration (for large LaTeX documents)
    REQUEST_TIMEOUT = get_env_int('REQUEST_TIMEOUT', 120)  # 2 minutes for large documents
    SEND_FILE_MAX_AGE = get_env_int('SEND_FILE_MAX_AGE', 31536000)  # Cache compiled PDFs
    
    # Email Configuration
    MAIL_SERVER = get_env_var('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = get_env_int('MAIL_PORT', 587)
    MAIL_USE_TLS = get_env_bool('MAIL_USE_TLS', True)
    MAIL_USE_SSL = get_env_bool('MAIL_USE_SSL', False)
    MAIL_USERNAME = get_env_var('MAIL_USERNAME')
    MAIL_PASSWORD = get_env_var('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = get_env_var('MAIL_DEFAULT_SENDER') or get_env_var('MAIL_USERNAME')
    
    # Site Configuration
    SITE_NAME = get_env_var('SITE_NAME', 'Cropio')
    SUPPORT_EMAIL = get_env_var('SUPPORT_EMAIL', 'support@cropio.com')
    
    # Logging Configuration
    LOG_LEVEL = get_env_var('LOG_LEVEL', 'INFO')
    LOG_FILE = get_env_var('LOG_FILE', 'cropio.log')
    LOG_MAX_BYTES = get_env_int('LOG_MAX_BYTES', 10485760)  # 10MB
    LOG_BACKUP_COUNT = get_env_int('LOG_BACKUP_COUNT', 5)
    LOG_DIR = get_env_var('LOG_DIR', 'logs')
    
    # Security Headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = get_env_var('REDIS_URL', 'redis://localhost:6379/1')
    RATELIMIT_HEADERS_ENABLED = True
    
    # Payment Configuration (Optional)
    RAZORPAY_KEY_ID = get_env_var('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = get_env_var('RAZORPAY_KEY_SECRET')
    STRIPE_PUBLIC_KEY = get_env_var('STRIPE_PUBLIC_KEY')
    STRIPE_SECRET_KEY = get_env_var('STRIPE_SECRET_KEY')
    
    # Monitoring (Optional)
    SENTRY_DSN = get_env_var('SENTRY_DSN')
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate critical configuration"""
        errors = []
        
        # Check secret key strength
        secret_key = get_env_var('FLASK_SECRET_KEY')
        if secret_key and len(secret_key) < 32:
            errors.append("SECRET_KEY must be at least 32 characters long")
        
        # Validate email configuration if provided
        mail_username = get_env_var('MAIL_USERNAME')
        mail_password = get_env_var('MAIL_PASSWORD')
        if mail_username and not mail_password:
            errors.append("MAIL_PASSWORD is required when MAIL_USERNAME is set")
        
        if errors:
            raise ConfigError("; ".join(errors))
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """Get configuration summary for logging"""
        return {
            'environment': get_env_var('FLASK_ENV', 'development'),
            'debug': cls.DEBUG if hasattr(cls, 'DEBUG') else False,
            'database_configured': bool(get_env_var('DATABASE_URL')),
            'email_configured': bool(get_env_var('MAIL_USERNAME')),
            'redis_configured': bool(get_env_var('REDIS_URL')),
            'sentry_configured': bool(get_env_var('SENTRY_DSN')),
        }


class DevelopmentConfig(BaseConfig):
    """Development configuration with debug features"""
    DEBUG = True
    TESTING = False
    
    # Development database - use environment or default
    SQLALCHEMY_DATABASE_URI = get_env_var('DATABASE_URL', 
        'postgresql://postgres:root@localhost:5432/cropio_dev')
    
    # Relaxed security for development
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    WTF_CSRF_ENABLED = get_env_bool('WTF_CSRF_ENABLED', True)
    
    # Development logging
    LOG_LEVEL = get_env_var('LOG_LEVEL', 'DEBUG')
    
    @classmethod
    def validate_config(cls) -> None:
        """Development-specific validation"""
        super().validate_config()
        
        # Warn about development database
        db_url = get_env_var('DATABASE_URL')
        if db_url and 'localhost' in db_url:
            print("WARNING: Using local development database")


class ProductionConfig(BaseConfig):
    """Production configuration with enhanced security"""
    DEBUG = False
    TESTING = False
    
    # Production database - must be set via environment
    SQLALCHEMY_DATABASE_URI = get_env_var('DATABASE_URL', required=True)
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True  # HTTPS only
    WTF_CSRF_ENABLED = True
    
    # Production logging
    LOG_LEVEL = get_env_var('LOG_LEVEL', 'WARNING')
    
    # Production-specific settings
    PREFERRED_URL_SCHEME = 'https'
    
    @classmethod
    def validate_config(cls) -> None:
        """Production-specific validation"""
        super().validate_config()
        
        errors = []
        
        # Ensure secure secret key in production
        secret_key = get_env_var('FLASK_SECRET_KEY')
        if not secret_key:
            errors.append("FLASK_SECRET_KEY environment variable is required in production")
        elif secret_key == 'dev-secret-key-change-in-production':
            errors.append("Default development secret key cannot be used in production")
        
        # Validate database URL
        db_url = get_env_var('DATABASE_URL')
        if db_url:
            validate_database_url(db_url)
            if 'localhost' in db_url:
                errors.append("Production database should not use localhost")
        
        if errors:
            raise ConfigError("; ".join(errors))


class TestingConfig(BaseConfig):
    """Testing configuration for unit tests"""
    TESTING = True
    DEBUG = True
    
    # In-memory database for fast tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable features that interfere with testing
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    
    # Fast testing settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': False,
        'pool_recycle': -1,
    }
    
    # Testing-specific logging
    LOG_LEVEL = 'ERROR'
    
    @classmethod
    def validate_config(cls) -> None:
        """Minimal validation for testing"""
        pass  # Skip most validation in testing


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def setup_flask_config(app, config_name=None):
    """Setup Flask app configuration"""
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Setup directories
    setup_directories(app)
    
    print(f"[CONFIG] Flask configured for: {config_name}")
    print(f"[DATABASE] {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"[UPLOAD] Upload folder: {app.config['UPLOAD_FOLDER']}")
    
    return app
