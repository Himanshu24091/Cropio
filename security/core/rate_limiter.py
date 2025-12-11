"""
Universal Security Framework - Rate Limiter
Advanced rate limiting with user-specific and IP-based tracking
"""
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
from datetime import datetime, timedelta
import redis
import json
from collections import defaultdict

# In-memory fallback for development
rate_limit_store = defaultdict(list)

def get_rate_limit_key(key, user_id=None, ip_address=None):
    """Generate unique rate limit key"""
    if user_id:
        return f"rate_limit:{key}:user:{user_id}"
    elif ip_address:
        return f"rate_limit:{key}:ip:{ip_address}"
    else:
        return f"rate_limit:{key}:global"

def rate_limit(key, limit=100, per_minute=True, per_user=True):
    """
    Rate limiting decorator with advanced tracking
    
    Args:
        key (str): Unique identifier for the rate limit
        limit (int): Maximum requests allowed
        per_minute (bool): If True, limit per minute, else per hour
        per_user (bool): If True, apply per-user limits
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                # Determine rate limit key
                if per_user and current_user.is_authenticated:
                    rate_key = get_rate_limit_key(key, user_id=current_user.id)
                else:
                    rate_key = get_rate_limit_key(key, ip_address=request.remote_addr)
                
                # Get current time window
                now = datetime.utcnow()
                window_size = timedelta(minutes=1 if per_minute else 60)
                window_start = now - window_size
                
                # Clean old entries and count current requests
                rate_limit_store[rate_key] = [
                    timestamp for timestamp in rate_limit_store[rate_key]
                    if datetime.fromisoformat(timestamp) > window_start
                ]
                
                # Check if limit exceeded
                if len(rate_limit_store[rate_key]) >= limit:
                    current_app.logger.warning(
                        f"Rate limit exceeded for {rate_key}: "
                        f"{len(rate_limit_store[rate_key])}/{limit} requests"
                    )
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'limit': limit,
                        'window': '1 minute' if per_minute else '1 hour',
                        'retry_after': 60 if per_minute else 3600
                    }), 429
                
                # Add current request timestamp
                rate_limit_store[rate_key].append(now.isoformat())
                
                return f(*args, **kwargs)
                
            except Exception as e:
                current_app.logger.error(f"Rate limiter error: {e}")
                # Allow request to proceed if rate limiter fails
                return f(*args, **kwargs)
        
        return wrapper
    return decorator

def get_rate_limit_info(key, user_id=None, ip_address=None):
    """Get current rate limit status"""
    rate_key = get_rate_limit_key(key, user_id=user_id, ip_address=ip_address)
    return {
        'key': rate_key,
        'current_requests': len(rate_limit_store.get(rate_key, [])),
        'requests': rate_limit_store.get(rate_key, [])
    }

def reset_rate_limit(key, user_id=None, ip_address=None):
    """Reset rate limit for a specific key"""
    rate_key = get_rate_limit_key(key, user_id=user_id, ip_address=ip_address)
    if rate_key in rate_limit_store:
        del rate_limit_store[rate_key]
        return True
    return False

def cleanup_expired_limits():
    """Clean up expired rate limit entries"""
    now = datetime.utcnow()
    cleaned_count = 0
    
    for key in list(rate_limit_store.keys()):
        # Keep only entries from last hour
        cutoff = now - timedelta(hours=1)
        old_count = len(rate_limit_store[key])
        
        rate_limit_store[key] = [
            timestamp for timestamp in rate_limit_store[key]
            if datetime.fromisoformat(timestamp) > cutoff
        ]
        
        # Remove empty entries
        if not rate_limit_store[key]:
            del rate_limit_store[key]
            cleaned_count += 1
    
    return cleaned_count