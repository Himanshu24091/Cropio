"""
Universal Security Framework - Access Control
Role-based access control and permission management
"""
from functools import wraps
from flask import request, jsonify
from flask_login import current_user
from security.core.exceptions import AuthorizationException, AdminSecurityException
from security.logging import security_logger

def require_admin_role(f):
    """Require admin role for access"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            raise AuthorizationException("Authentication required")
        
        if not current_user.is_admin:
            raise AdminSecurityException("Admin privileges required")
        
        return f(*args, **kwargs)
    return wrapper

def require_user_management_role(f):
    """Require user management permissions"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            raise AuthorizationException("Authentication required")
        
        if not (current_user.is_admin or hasattr(current_user, 'can_manage_users')):
            raise AdminSecurityException("User management privileges required")
        
        return f(*args, **kwargs)
    return wrapper

def log_admin_action(action_name):
    """Log administrative actions"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            security_logger.info(f"Admin action '{action_name}' by {current_user.username if current_user.is_authenticated else 'Anonymous'}")
            return f(*args, **kwargs)
        return wrapper
    return decorator