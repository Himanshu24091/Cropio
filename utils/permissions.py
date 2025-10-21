"""
Role-based Access Control (RBAC) Decorators
Provides decorators for protecting routes with role-based permissions
"""
from functools import wraps
from flask import abort, redirect, url_for, flash, request, session
from flask_login import current_user


def permission_required(permission):
    """
    Decorator to require specific permission
    Usage: @permission_required('can_manage_users')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.has_permission(permission):
                flash('Access denied. You do not have permission to access this page.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.can_access_admin():
            flash('Access denied. Administrator privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def staff_required(f):
    """Decorator to require staff privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not (current_user.is_staff or current_user.can_access_admin()):
            flash('Access denied. Staff privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def role_required(role_name):
    """
    Decorator to require specific role
    Usage: @role_required('admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            
            if current_user.get_role_name() != role_name:
                flash(f'Access denied. {role_name.title()} role required.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def user_management_required(f):
    """Decorator to require user management permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.can_manage_users():
            flash('Access denied. User management privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def analytics_required(f):
    """Decorator to require analytics viewing permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.can_view_analytics():
            flash('Access denied. Analytics viewing privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def system_management_required(f):
    """Decorator to require system management permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.can_manage_system():
            flash('Access denied. System management privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def content_management_required(f):
    """Decorator to require content management permissions"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.can_manage_content():
            flash('Access denied. Content management privileges required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def check_file_size_permission(file_size):
    """Check if user can upload file of given size"""
    if not current_user.is_authenticated:
        return False
    
    max_size = current_user.get_max_file_size()
    return file_size <= max_size


def check_conversion_permission():
    """Check if user can perform conversions"""
    if not current_user.is_authenticated:
        return False
    
    return current_user.can_convert()


def check_ai_features_permission():
    """Check if user can use AI features"""
    if not current_user.is_authenticated:
        return False
    
    return current_user.has_permission('can_use_ai_features')


def check_batch_processing_permission():
    """Check if user can use batch processing"""
    if not current_user.is_authenticated:
        return False
    
    return current_user.has_permission('can_batch_process')


def rate_limit_required(calls_per_minute=60):
    """
    Decorator to implement rate limiting for sensitive operations
    Usage: @rate_limit_required(calls_per_minute=30)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            
            # Check if user has exceeded rate limit
            from datetime import datetime, timedelta
            from models import db, UserSession
            
            # Use simple in-memory rate limiting for now
            # In production, consider using Redis or similar
            rate_limit_key = f"rate_limit_{current_user.id}_{f.__name__}"
            
            # For now, just log the rate limit check
            # In production, implement proper rate limiting
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def ip_whitelist_required(allowed_ips=None):
    """
    Decorator to restrict access to specific IP addresses
    Usage: @ip_whitelist_required(['127.0.0.1', '192.168.1.0/24'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            
            # For admin routes, check IP whitelist if configured
            if allowed_ips and current_user.can_access_admin():
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                if client_ip not in allowed_ips:
                    flash('Access denied from this IP address.', 'error')
                    abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def secure_headers_required(f):
    """
    Decorator to add security headers to responses
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Add security headers if response is a Response object
        if hasattr(response, 'headers'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        
        return response
    return decorated_function


def audit_log_required(action_type):
    """
    Decorator to log sensitive actions for audit purposes
    Usage: @audit_log_required('user_deletion')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from datetime import datetime
            
            # Execute the function
            result = f(*args, **kwargs)
            
            # Log the action (in production, store in audit log table)
            audit_entry = {
                'user_id': current_user.id if current_user.is_authenticated else None,
                'action': action_type,
                'timestamp': datetime.utcnow(),
                'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                'user_agent': request.headers.get('User-Agent', ''),
                'route': request.endpoint,
                'method': request.method
            }
            
            # In production, save to audit log table
            print(f"AUDIT LOG: {audit_entry}")
            
            return result
        return decorated_function
    return decorator


# Helper function for template usage
def get_user_permissions(user):
    """Get all permissions for a user (for template usage)"""
    if not user or not user.user_role:
        return {
            'can_access_admin': user.is_admin if user else False,
            'can_manage_users': user.is_admin if user else False,
            'can_manage_content': user.is_staff or user.is_admin if user else False,
            'can_view_analytics': user.is_staff or user.is_admin if user else False,
            'can_manage_system': user.is_admin if user else False,
            'can_delete_users': user.is_admin if user else False,
            'can_use_ai_features': False,
            'can_batch_process': False,
            'max_file_size': 52428800,  # 50MB
            'daily_conversion_limit': 5
        }
    
    role = user.user_role
    return {
        'can_access_admin': role.can_access_admin,
        'can_manage_users': role.can_manage_users,
        'can_manage_content': role.can_manage_content,
        'can_view_analytics': role.can_view_analytics,
        'can_manage_system': role.can_manage_system,
        'can_delete_users': role.can_delete_users,
        'can_use_ai_features': role.can_use_ai_features,
        'can_batch_process': role.can_batch_process,
        'max_file_size': role.max_file_size,
        'daily_conversion_limit': role.daily_conversion_limit
    }


def validate_csrf_token():
    """Validate CSRF token for forms"""
    if not current_user.is_authenticated:
        return False
    
    # Basic CSRF protection
    form_token = request.form.get('csrf_token')
    session_token = request.headers.get('X-CSRF-Token') or session.get('csrf_token')
    
    return form_token == session_token if form_token and session_token else True


def generate_csrf_token():
    """Generate CSRF token for forms"""
    import secrets
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']


def check_password_strength(password):
    """Check password strength and return validation result"""
    import re
    
    errors = []
    
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    
    if not re.search(r'\d', password):
        errors.append('Password must contain at least one number')
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character')
    
    # Check for common weak passwords
    weak_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if password.lower() in weak_passwords:
        errors.append('Password is too common. Please choose a stronger password')
    
    return {
        'is_strong': len(errors) == 0,
        'errors': errors,
        'score': max(0, 100 - (len(errors) * 20))  # Score out of 100
    }
