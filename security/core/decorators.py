"""
Security Decorators Module

This module provides security decorators for Flask applications including
CSRF protection, rate limiting, file upload validation, and authentication.
"""

from functools import wraps
from flask import request, session, g, abort, jsonify, current_app
import time
from typing import List, Optional, Callable, Any

from .exceptions import (
    CSRFValidationError, RateLimitExceededError, InvalidFileTypeError,
    FileSizeExceededError, AuthenticationError, AuthorizationError,
    MalwareDetectedError
)


def require_csrf(token_field: str = 'csrf_token'):
    """
    Decorator to require CSRF token validation for protected endpoints.
    
    Args:
        token_field: Field name containing CSRF token (default: 'csrf_token')
        
    Returns:
        Decorated function that validates CSRF before execution
        
    Raises:
        CSRFValidationError: When CSRF token is invalid or missing
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip CSRF in debug mode if configured
            if current_app.debug and getattr(current_app.security_config, 'csrf_exempt_in_debug', False):
                return f(*args, **kwargs)
            
            # Get token from form, headers, or query params
            token = (
                request.form.get(token_field) or
                request.headers.get('X-CSRF-Token') or
                request.args.get(token_field)
            )
            
            if not token:
                raise CSRFValidationError("CSRF token is missing")
            
            # Validate token (mock validation for now)
            if not _validate_csrf_token(token):
                raise CSRFValidationError("CSRF token validation failed")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def rate_limit(requests_per_minute: int = 60, per_user: bool = True):
    """
    Decorator to apply rate limiting to endpoints.
    
    Args:
        requests_per_minute: Maximum requests per minute (default: 60)
        per_user: Apply limit per user vs globally (default: True)
        
    Returns:
        Decorated function with rate limiting applied
        
    Raises:
        RateLimitExceededError: When rate limit is exceeded
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip rate limiting if disabled
            if not getattr(current_app.security_config, 'rate_limit_enabled', True):
                return f(*args, **kwargs)
            
            # Determine rate limit key
            if per_user:
                user_id = getattr(g, 'user_id', None) or session.get('user_id', 'anonymous')
                key = f"rate_limit:{user_id}:{request.endpoint}"
            else:
                key = f"rate_limit:global:{request.endpoint}"
            
            # Check rate limit (mock implementation)
            if not _check_rate_limit(key, requests_per_minute):
                raise RateLimitExceededError(
                    f"Rate limit exceeded: {requests_per_minute} requests per minute"
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_file_upload(allowed_types: Optional[List[str]] = None, 
                        max_size_mb: int = 50, 
                        scan_malware: bool = True):
    """
    Decorator to validate file uploads comprehensively.
    
    Args:
        allowed_types: Allowed file extensions (default: None = all allowed)
        max_size_mb: Maximum file size in MB (default: 50)
        scan_malware: Enable malware scanning (default: True)
        
    Returns:
        Decorated function with file validation applied
        
    Raises:
        InvalidFileTypeError: When file type is not allowed
        FileSizeExceededError: When file exceeds size limit
        MalwareDetectedError: When malware is detected
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return f(*args, **kwargs)  # No file to validate
            
            file = request.files['file']
            if not file or file.filename == '':
                return f(*args, **kwargs)  # No actual file
            
            # Get file extension
            filename = file.filename.lower()
            file_ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
            
            # Validate file type
            if allowed_types and file_ext not in [ext.lower() for ext in allowed_types]:
                raise InvalidFileTypeError(
                    f"File type '{file_ext}' not allowed. Allowed types: {allowed_types}"
                )
            
            # Check file size
            file.seek(0, 2)  # Seek to end to get size
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            max_size_bytes = max_size_mb * 1024 * 1024
            if file_size > max_size_bytes:
                raise FileSizeExceededError(
                    f"File size {file_size} bytes exceeds maximum {max_size_bytes} bytes"
                )
            
            # Mock malware scanning
            if scan_malware and getattr(current_app.security_config, 'enable_malware_scanning', True):
                # Read file content for scanning
                content = file.read()
                file.seek(0)  # Reset for actual use
                
                if _mock_malware_scan(content, file_ext):
                    raise MalwareDetectedError("Malware detected in uploaded file")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_authentication(role: Optional[str] = None):
    """
    Decorator to require user authentication and optional role validation.
    
    Args:
        role: Required user role (optional)
        
    Returns:
        Decorated function that checks authentication
        
    Raises:
        AuthenticationError: When user is not authenticated
        AuthorizationError: When user lacks required role
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            user_id = getattr(g, 'user_id', None) or session.get('user_id')
            if not user_id:
                raise AuthenticationError("Authentication required")
            
            # Check role if specified
            if role:
                user_type = getattr(g, 'user_type', None) or session.get('user_type', 'basic')
                if not _check_user_role(user_type, role):
                    raise AuthorizationError(f"Role '{role}' required")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Helper functions (mock implementations)

def _validate_csrf_token(token: str) -> bool:
    """Mock CSRF token validation"""
    # In real implementation, this would validate against stored tokens
    return len(token) >= 16 and token.isalnum()


def _check_rate_limit(key: str, limit: int) -> bool:
    """Mock rate limit checking"""
    # In real implementation, this would use Redis or similar
    # For now, always allow (mock implementation)
    return True


def _mock_malware_scan(content: bytes, file_type: str) -> bool:
    """Mock malware scanning"""
    # Check for obvious malware patterns
    dangerous_patterns = [
        b'<script',
        b'javascript:',
        b'vbscript:',
        b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR',  # EICAR test string
    ]
    
    content_lower = content.lower()
    for pattern in dangerous_patterns:
        if pattern in content_lower:
            return True  # Malware detected
    
    return False  # Clean


def _check_user_role(user_type: str, required_role: str) -> bool:
    """Check if user has required role"""
    role_hierarchy = {
        'admin': ['admin', 'user', 'basic'],
        'user': ['user', 'basic'],
        'basic': ['basic']
    }
    
    allowed_roles = role_hierarchy.get(user_type, [])
    return required_role in allowed_roles