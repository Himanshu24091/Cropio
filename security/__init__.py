"""
Universal Security Framework for Cropio SaaS Platform
Version 1.0.0 - Comprehensive security implementation

This module provides a centralized, robust, and reusable security framework
that protects against common web vulnerabilities, malicious file uploads,
and other security threats.

Key Features:
- File upload validation and sanitization
- Content-based malware detection
- CSRF protection
- Rate limiting
- Session security
- Input validation and sanitization

Usage:
    from security import validate_file_upload, rate_limit, csrf_required
    
    @validate_file_upload(['jpg', 'png'], max_size_mb=10, sanitize=True)
    @rate_limit(limit=5, per_minute=True)
    @csrf_required()
    def upload_image():
        # Your secure route logic here
        pass
"""

__version__ = "1.0.0"
__author__ = "Cropio Security Team"
__email__ = "security@cropio.com"

# Core security components
from .core.decorators import (
    validate_file_upload,
    rate_limit,
    require_csrf,
    require_authentication
)

from .core.validators import (
    validate_content,
    validate_filename,
    validate_user_input,
    validate_ip_address
)

from .core.sanitizers import (
    sanitize_filename,
    sanitize_content,
    sanitize_user_input,
    remove_script_tags
)

from .core.exceptions import (
    SecurityViolationError,
    MalwareDetectedError,
    RateLimitExceededError,
    InvalidFileTypeError,
    CSRFValidationError,
    FileSizeExceededError,
    ContentValidationError,
    AuthenticationError,
    AuthorizationError
)

# Configuration
from .config.security_config import SecurityConfig, SecurityLevel
from .config.constants import (
    DEFAULT_RATE_LIMITS,
    SECURITY_HEADERS,
    ALLOWED_MIME_TYPES
)

# Version info
VERSION_INFO = {
    'version': __version__,
    'build_date': '2025-09-17',
    'python_requires': '>=3.8',
    'dependencies': [
        'Flask>=2.0.0',
        'python-magic>=0.4.27',
        'bleach>=6.0.0',
        'defusedxml>=0.7.1',
        'validators>=0.20.0',
        'cryptography>=40.0.0'
    ]
}

# Quick security check function
def health_check():
    """
    Perform a quick security health check
    Returns dict with status of various security components
    """
    health_status = {
        'version': __version__,
        'core_modules': {
            'validators': False,
            'sanitizers': False,
            'decorators': False,
            'exceptions': False
        },
        'config': False,
        'overall_status': 'unknown'
    }
    
    try:
        # Test core validators
        from .core.validators import validate_content
        health_status['core_modules']['validators'] = True
        
        # Test core sanitizers
        from .core.sanitizers import sanitize_filename
        health_status['core_modules']['sanitizers'] = True
        
        # Test core decorators
        from .core.decorators import require_csrf
        health_status['core_modules']['decorators'] = True
        
        # Test exceptions
        from .core.exceptions import SecurityViolationError
        health_status['core_modules']['exceptions'] = True
        
        # Test configuration
        config = SecurityConfig()
        health_status['config'] = True
        
        # Overall status
        all_healthy = all(health_status['core_modules'].values()) and health_status['config']
        health_status['overall_status'] = 'healthy' if all_healthy else 'degraded'
        
    except ImportError as e:
        health_status['error'] = f"Missing dependencies: {str(e)}"
        health_status['overall_status'] = 'unhealthy'
    except Exception as e:
        health_status['error'] = f"Health check failed: {str(e)}"
        health_status['overall_status'] = 'unhealthy'
    
    return health_status

# Initialize security framework
def initialize_security(app, config=None):
    """
    Initialize the security framework with Flask app
    
    Args:
        app: Flask application instance
        config: SecurityConfig instance (optional)
        
    Returns:
        bool: True if initialization successful
    """
    try:
        if not app:
            return False
            
        # Use provided config or create default
        if config is None:
            config = SecurityConfig()
        
        # Store config in app for access by decorators
        app.security_config = config
        
        # Register error handlers for security exceptions
        @app.errorhandler(SecurityViolationError)
        def handle_security_violation(e):
            return {'error': str(e), 'type': 'security_violation'}, 400
            
        @app.errorhandler(RateLimitExceededError)
        def handle_rate_limit(e):
            return {'error': str(e), 'type': 'rate_limit_exceeded'}, 429
            
        @app.errorhandler(CSRFValidationError)
        def handle_csrf_error(e):
            return {'error': str(e), 'type': 'csrf_validation_failed'}, 400
            
        if hasattr(app, 'logger'):
            app.logger.info(f"Security framework v{__version__} initialized successfully")
        
        return True
            
    except Exception as e:
        if app and hasattr(app, 'logger'):
            app.logger.error(f"Security framework initialization failed: {str(e)}")
        return False

# Export main components for easy import
__all__ = [
    # Core decorators
    'validate_file_upload',
    'rate_limit', 
    'require_csrf',
    'require_authentication',
    
    # Validators
    'validate_content',
    'validate_filename',
    'validate_user_input',
    'validate_ip_address',
    
    # Sanitizers
    'sanitize_filename',
    'sanitize_content',
    'sanitize_user_input',
    'remove_script_tags',
    
    # Exceptions
    'SecurityViolationError',
    'MalwareDetectedError',
    'RateLimitExceededError',
    'InvalidFileTypeError',
    'CSRFValidationError',
    'FileSizeExceededError',
    'ContentValidationError',
    'AuthenticationError',
    'AuthorizationError',
    
    # Configuration
    'SecurityConfig',
    'SecurityLevel',
    'DEFAULT_RATE_LIMITS',
    'SECURITY_HEADERS',
    'ALLOWED_MIME_TYPES',
    
    # Framework functions
    'initialize_security',
    'health_check',
    'VERSION_INFO',
    '__version__',
    '__author__'
]