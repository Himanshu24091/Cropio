# utils/auth_decorators.py
# Authentication Decorators for Access Control

from functools import wraps
from flask import flash, redirect, url_for, request, session
from flask_login import current_user


def login_required_for_free_tools(f):
    """
    Decorator to require login for free tools access
    This decorator checks if user is authenticated before allowing access to free tools
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access this free tool. Create a free account to get started!', 'info')
            # Store the originally requested URL so we can redirect back after login
            session['next_url'] = request.url
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def premium_required(f):
    """
    Decorator to require premium subscription for premium tools
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access premium features.', 'warning')
            session['next_url'] = request.url
            return redirect(url_for('auth.login'))
        
        if not current_user.is_premium():
            flash('This feature requires a premium subscription. Upgrade to access all advanced tools!', 'warning')
            return redirect(url_for('auth.profile'))  # or upgrade page
        
        return f(*args, **kwargs)
    return decorated_function


def free_tool_with_limits(conversion_limit=10, daily_limit=50):
    """
    Decorator for free tools with usage limits
    Args:
        conversion_limit: Number of conversions per session for non-logged users
        daily_limit: Daily conversion limit for free users
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # If user is not authenticated, apply session limits
            if not current_user.is_authenticated:
                session_conversions = session.get('conversion_count', 0)
                if session_conversions >= conversion_limit:
                    flash(f'You have reached the limit of {conversion_limit} conversions. Please login for more!', 'warning')
                    return redirect(url_for('auth.login'))
                
                # Increment session counter
                session['conversion_count'] = session_conversions + 1
            
            # For authenticated free users, check daily limits
            elif not current_user.is_premium():
                # Here you could add daily limit checking logic
                # For now, we'll allow unlimited for logged-in free users
                pass
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
