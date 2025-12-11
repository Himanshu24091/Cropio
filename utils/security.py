"""
Security Enhancements for Cropio SaaS Platform
Implements CSRF protection, secure headers, rate limiting, and file validation
"""
from flask import request, current_app, g
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import RequestEntityTooLarge
from datetime import datetime, timedelta
import hashlib
import re
import os
from functools import wraps
from collections import defaultdict
import time

# Try to import python-magic, fall back to filetype if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except (ImportError, OSError):
    MAGIC_AVAILABLE = False
    import filetype

# Initialize CSRF protection
csrf = CSRFProtect()

# Rate limiting storage (in production, use Redis)
rate_limit_storage = defaultdict(list)

def init_security(app):
    """Initialize security features for the application"""
    # Configure CSRF protection - Always enabled for security
    app.config['WTF_CSRF_ENABLED'] = True  # Always enable CSRF protection
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit for CSRF tokens
    
    # Enable CSRF protection
    csrf.init_app(app)
    
    # Exempt certain routes from CSRF protection
    csrf.exempt('main.index')  # Homepage
    csrf.exempt('file_serving.serve_file')  # File downloads
    csrf.exempt('file_serving.preview_file')  # File previews
    # Note: compressor.compress_files_route is exempted using @csrf.exempt decorator
    
    # Configure security headers
    @app.after_request
    def set_security_headers(response):
        """Set security headers for all responses"""
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Force HTTPS in production
        if not app.debug:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy - Secure policy for production
        csp = {
            'default-src': ["'self'"],
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", 'https://cdn.tailwindcss.com', 'https://cdn.jsdelivr.net', 'https://cdnjs.cloudflare.com'],
            'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.tailwindcss.com', 'https://fonts.googleapis.com', 'https://cdn.jsdelivr.net', 'https://cdnjs.cloudflare.com'],
            'img-src': ["'self'", 'data:', 'https:', 'blob:'],
            'font-src': ["'self'", 'https://fonts.gstatic.com', 'https://cdnjs.cloudflare.com'],
            'connect-src': ["'self'", 'https:'],
            'object-src': ["'self'"],
            'media-src': ["'self'", 'blob:', 'data:'],
            'child-src': ["'self'", 'blob:'],
            'frame-src': ["'self'", 'blob:'],
            'frame-ancestors': ["'self'"],
            'worker-src': ["'self'", 'blob:']
        }
        
        csp_string = '; '.join([f"{key} {' '.join(value)}" for key, value in csp.items()])
        response.headers['Content-Security-Policy'] = csp_string
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy (formerly Feature Policy)
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response
    
    # Add request size limit handler
    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(e):
        """Handle file size exceeded errors"""
        from flask import flash, redirect, url_for
        flash('File size too large. Maximum allowed size is 100MB.', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    app.logger.info("Security features initialized")

def validate_password_strength(password):
    """
    Validate password strength
    Returns (is_valid, error_messages)
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Check for common passwords
    common_passwords = ['password', '12345678', 'qwerty', 'abc123', 'password123']
    if password.lower() in common_passwords:
        errors.append("Password is too common. Please choose a stronger password")
    
    return len(errors) == 0, errors

def validate_file_upload(file, allowed_extensions, max_size_mb=100):
    """
    Validate uploaded file for security
    Returns (is_valid, error_message)
    """
    if not file or not file.filename:
        return False, "No file selected"
    
    # Check file extension
    filename = file.filename.lower()
    ext = filename.rsplit('.', 1)[1] if '.' in filename else ''
    
    if ext not in allowed_extensions:
        return False, f"File type '.{ext}' is not allowed"
    
    # Check file size
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > max_size_mb * 1024 * 1024:
        return False, f"File size exceeds {max_size_mb}MB limit"
    
    # Check MIME type
    try:
        if MAGIC_AVAILABLE:
            file_mime = magic.from_buffer(file.read(2048), mime=True)
            file.seek(0)
        else:
            # Use filetype as fallback
            file_data = file.read(2048)
            file.seek(0)
            kind = filetype.guess(file_data)
            file_mime = kind.mime if kind else 'application/octet-stream'
        
        # Define allowed MIME types for each extension
        mime_map = {
            'pdf': ['application/pdf'],
            'png': ['image/png'],
            'jpg': ['image/jpeg'],
            'jpeg': ['image/jpeg'],
            'gif': ['image/gif'],
            'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'doc': ['application/msword'],
            'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
            'xls': ['application/vnd.ms-excel'],
            'txt': ['text/plain'],
            'csv': ['text/csv', 'text/plain']
        }
        
        allowed_mimes = mime_map.get(ext, [])
        if file_mime not in allowed_mimes and not file_mime.startswith('text/'):
            return False, f"File content does not match extension (detected: {file_mime})"
    
    except Exception as e:
        current_app.logger.warning(f"MIME type check failed: {e}")
    
    # Check for malicious content patterns
    file_content = file.read(1024)
    file.seek(0)
    
    # Check for PHP tags, script tags, etc.
    dangerous_patterns = [
        b'<?php',
        b'<script',
        b'<iframe',
        b'javascript:',
        b'onerror=',
        b'onclick='
    ]
    
    for pattern in dangerous_patterns:
        if pattern in file_content.lower():
            return False, "File contains potentially malicious content"
    
    return True, None

def rate_limit(max_attempts=60, window_seconds=60, scope='global'):
    """
    Rate limiting decorator
    Args:
        max_attempts: Maximum number of attempts allowed
        window_seconds: Time window in seconds
        scope: 'global', 'user', or 'ip'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine client identifier based on scope
            if scope == 'user' and hasattr(g, 'current_user') and g.current_user.is_authenticated:
                client_id = f"user:{g.current_user.id}"
            elif scope == 'ip':
                client_id = f"ip:{request.remote_addr}"
            else:
                client_id = f"global:{request.endpoint}"
            
            now = time.time()
            
            # Clean old entries
            rate_limit_storage[client_id] = [
                timestamp for timestamp in rate_limit_storage[client_id]
                if timestamp > now - window_seconds
            ]
            
            # Check rate limit
            if len(rate_limit_storage[client_id]) >= max_attempts:
                from flask import jsonify
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window_seconds
                }), 429
            
            # Add current request
            rate_limit_storage[client_id].append(now)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def login_rate_limit(max_attempts=5, lockout_duration=300):
    """
    Special rate limiting for login attempts
    Args:
        max_attempts: Maximum login attempts allowed
        lockout_duration: Lockout duration in seconds
    """
    login_attempts = defaultdict(list)
    locked_accounts = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            identifier = request.form.get('username_or_email', '').lower()
            ip_address = request.remote_addr
            key = f"{identifier}:{ip_address}"
            
            # Check if account is locked
            if key in locked_accounts:
                lock_time = locked_accounts[key]
                if time.time() - lock_time < lockout_duration:
                    remaining = int(lockout_duration - (time.time() - lock_time))
                    from flask import flash, render_template
                    flash(f'Account temporarily locked. Try again in {remaining} seconds.', 'error')
                    return render_template('auth/login.html'), 429
                else:
                    # Unlock account
                    del locked_accounts[key]
                    login_attempts[key] = []
            
            # Execute login function
            result = f(*args, **kwargs)
            
            # Check if login failed (assuming failed login redirects back to login page)
            if request.method == 'POST' and hasattr(result, 'status_code') and result.status_code != 302:
                # Record failed attempt
                login_attempts[key].append(time.time())
                
                # Keep only recent attempts
                login_attempts[key] = [
                    t for t in login_attempts[key]
                    if time.time() - t < 3600  # Within last hour
                ]
                
                # Check if should lock account
                if len(login_attempts[key]) >= max_attempts:
                    locked_accounts[key] = time.time()
                    from flask import flash
                    flash(f'Too many failed attempts. Account locked for {lockout_duration} seconds.', 'error')
            elif request.method == 'POST':
                # Successful login, clear attempts
                login_attempts.pop(key, None)
            
            return result
        
        return decorated_function
    return decorator

def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal and other attacks
    """
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|', '\x00']
    for char in dangerous_chars:
        filename = filename.replace(char, '')
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    # Ensure extension is lowercase
    ext = ext.lower()
    
    # Generate unique filename to prevent overwrites
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = hashlib.md5(f"{filename}{timestamp}".encode()).hexdigest()[:8]
    
    return f"{name}_{unique_id}{ext}"

def generate_secure_token(length=32):
    """Generate a cryptographically secure random token"""
    return hashlib.sha256(os.urandom(length)).hexdigest()

def is_safe_url(target):
    """
    Check if a URL is safe for redirection
    Prevents open redirect vulnerabilities
    """
    from urllib.parse import urlparse, urljoin
    from flask import request
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

# Audit logging functionality
class AuditLogger:
    """Simple audit logging for security-relevant events"""
    
    @staticmethod
    def log_event(event_type, user_id=None, details=None, ip_address=None):
        """Log security-relevant events"""
        from models import db
        
        log_entry = {
            'timestamp': datetime.utcnow(),
            'event_type': event_type,
            'user_id': user_id or (current_user.id if hasattr(g, 'current_user') and g.current_user.is_authenticated else None),
            'ip_address': ip_address or request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'details': details or {}
        }
        
        # In production, this would be saved to a database table
        current_app.logger.info(f"AUDIT: {log_entry}")
        
        return log_entry
    
    @staticmethod
    def log_login(user, success=True):
        """Log login attempts"""
        AuditLogger.log_event(
            'login_success' if success else 'login_failed',
            user_id=user.id if success and user else None,
            details={'username': user.username if user else request.form.get('username_or_email')}
        )
    
    @staticmethod
    def log_file_upload(user, filename, file_size):
        """Log file uploads"""
        AuditLogger.log_event(
            'file_upload',
            user_id=user.id,
            details={'filename': filename, 'size': file_size}
        )
    
    @staticmethod
    def log_permission_denied(user, resource):
        """Log unauthorized access attempts"""
        AuditLogger.log_event(
            'permission_denied',
            user_id=user.id if user else None,
            details={'resource': resource}
        )
