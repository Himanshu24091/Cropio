"""
Universal Security Framework - Audit Trail
Comprehensive audit logging for administrative actions
"""
from functools import wraps
from flask import request
from flask_login import current_user
from security.logging import security_logger

def audit_admin_action(action_type):
    """Audit administrative actions"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = current_user.username if current_user.is_authenticated else 'Anonymous'
            ip = request.remote_addr
            
            security_logger.info(f"AUDIT: {action_type} - User: {user}, IP: {ip}")
            
            try:
                result = f(*args, **kwargs)
                security_logger.info(f"AUDIT SUCCESS: {action_type} - User: {user}")
                return result
            except Exception as e:
                security_logger.error(f"AUDIT FAILURE: {action_type} - User: {user}, Error: {e}")
                raise
        
        return wrapper
    return decorator