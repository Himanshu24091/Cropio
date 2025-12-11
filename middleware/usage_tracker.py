"""
Usage Tracking Middleware - Phase 2
Track conversions, enforce quotas, and manage file size limits
"""
from functools import wraps
from flask import request, jsonify, current_app, g, flash, redirect, url_for
from flask_login import current_user
from datetime import datetime
import time
import os

from models import db, ConversionHistory, UsageTracking, SystemSettings


def track_conversion(conversion_type, tool_name):
    """Decorator to track conversions and enforce quotas"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated for quota enforcement
            if current_user.is_authenticated:
                # Check if user can convert (quota enforcement)
                if not current_user.can_convert():
                    if request.is_json:
                        return jsonify({
                            'error': 'Daily conversion limit reached',
                            'message': 'You have reached your daily conversion limit. Upgrade to Premium for unlimited conversions.',
                            'limit_reached': True
                        }), 429
                    else:
                        flash('Daily conversion limit reached. Upgrade to Premium for unlimited conversions.', 'warning')
                        return redirect(url_for('dashboard.subscription'))
            
            # Record start time for processing time calculation
            start_time = time.time()
            
            # Execute the original function
            try:
                result = f(*args, **kwargs)
                
                # Track successful conversion if user is authenticated
                if current_user.is_authenticated:
                    processing_time = time.time() - start_time
                    
                    # Get file size if available from request
                    file_size = 0
                    if 'file' in request.files:
                        uploaded_file = request.files['file']
                        if uploaded_file and uploaded_file.filename:
                            # Try to get file size from content length or seek
                            try:
                                uploaded_file.seek(0, 2)  # Seek to end
                                file_size = uploaded_file.tell()
                                uploaded_file.seek(0)  # Reset to beginning
                            except:
                                file_size = 0
                    
                    # Record conversion in history
                    record_conversion(
                        user_id=current_user.id,
                        conversion_type=conversion_type,
                        tool_used=tool_name,
                        processing_time=processing_time,
                        file_size=file_size,
                        status='completed'
                    )
                
                return result
                
            except Exception as e:
                # Track failed conversion
                if current_user.is_authenticated:
                    processing_time = time.time() - start_time
                    record_conversion(
                        user_id=current_user.id,
                        conversion_type=conversion_type,
                        tool_used=tool_name,
                        processing_time=processing_time,
                        file_size=0,
                        status='failed',
                        error_message=str(e)
                    )
                
                # Re-raise the exception
                raise e
        
        return decorated_function
    return decorator


def check_file_size_limit():
    """Middleware to check file size limits based on subscription"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' in request.files:
                uploaded_file = request.files['file']
                if uploaded_file and uploaded_file.filename:
                    # Get file size
                    try:
                        uploaded_file.seek(0, 2)  # Seek to end
                        file_size = uploaded_file.tell()
                        uploaded_file.seek(0)  # Reset to beginning
                    except:
                        file_size = 0
                    
                    # Get size limit based on user subscription
                    if current_user.is_authenticated:
                        max_size = int(SystemSettings.get_setting(
                            'max_file_size_premium' if current_user.is_premium() else 'max_file_size_free',
                            '5368709120' if current_user.is_premium() else '52428800'
                        ))
                        user_type = f"{'Premium' if current_user.is_premium() else 'Free'} user"
                    else:
                        # Guest users get free tier limits
                        max_size = int(SystemSettings.get_setting('max_file_size_free', '52428800'))
                        user_type = "Guest user"
                    
                    if file_size > max_size:
                        max_size_mb = round(max_size / (1024 * 1024))
                        file_size_mb = round(file_size / (1024 * 1024), 1)
                        
                        if request.is_json:
                            return jsonify({
                                'error': 'File too large',
                                'message': f'{user_type} file size limit is {max_size_mb}MB. Your file is {file_size_mb}MB.',
                                'file_size_exceeded': True,
                                'max_size_mb': max_size_mb,
                                'file_size_mb': file_size_mb
                            }), 413
                        else:
                            flash(f'{user_type} file size limit is {max_size_mb}MB. Your file is {file_size_mb}MB.', 'error')
                            return redirect(request.referrer or url_for('main.index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def record_conversion(user_id, conversion_type, tool_used, processing_time=0, 
                     file_size=0, original_filename=None, original_format=None, 
                     target_format=None, status='completed', error_message=None):
    """Record a conversion in the database"""
    try:
        # Create conversion history entry
        conversion = ConversionHistory(
            user_id=user_id,
            original_filename=original_filename or 'unknown',
            original_format=original_format or 'unknown',
            target_format=target_format or 'unknown',
            file_size=file_size,
            conversion_type=conversion_type,
            tool_used=tool_used,
            processing_time=processing_time,
            status=status,
            error_message=error_message,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow() if status == 'completed' else None
        )
        
        db.session.add(conversion)
        
        # Update daily usage tracking
        if status == 'completed':
            today_usage = UsageTracking.get_or_create_today(user_id)
            today_usage.increment_usage(conversion_type, processing_time, file_size)
        
        db.session.commit()
        current_app.logger.info(f"Conversion tracked: {tool_used} for user {user_id}")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error tracking conversion: {e}")


def get_usage_stats(user_id, days=30):
    """Get usage statistics for a user over specified days"""
    from datetime import date, timedelta
    
    start_date = date.today() - timedelta(days=days-1)
    
    usage_data = UsageTracking.query.filter(
        UsageTracking.user_id == user_id,
        UsageTracking.date >= start_date
    ).order_by(UsageTracking.date).all()
    
    total_conversions = sum(u.conversions_count for u in usage_data)
    total_storage = sum(u.storage_used for u in usage_data)
    total_processing_time = sum(u.processing_time for u in usage_data)
    
    return {
        'total_conversions': total_conversions,
        'total_storage_used': total_storage,
        'total_processing_time': total_processing_time,
        'usage_data': usage_data
    }


def enforce_rate_limiting():
    """Rate limiting middleware for API endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Implement simple rate limiting based on IP
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', ''))
            
            # For now, just log the request
            current_app.logger.info(f"API request from {client_ip} to {request.endpoint}")
            
            # TODO: Implement Redis-based rate limiting in future
            return f(*args, **kwargs)
        return decorated_function
    return decorator


class UsageMiddleware:
    """Usage tracking middleware class"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Store request start time"""
        g.start_time = time.time()
        g.request_logged = False
    
    def after_request(self, response):
        """Log request completion"""
        try:
            # Only log for file processing endpoints
            if (hasattr(g, 'start_time') and 
                current_user.is_authenticated and 
                request.endpoint and 
                any(endpoint in request.endpoint for endpoint in [
                    'image_converter', 'pdf_converter', 'document_converter',
                    'excel_converter', 'file_compressor', 'cropper', 'pdf_editor',
                    'text_ocr', 'notebook_converter'
                ])):
                
                processing_time = time.time() - g.start_time
                
                # Log request for analytics
                current_app.logger.info(
                    f"Request processed: {request.endpoint} "
                    f"by user {current_user.username} "
                    f"in {processing_time:.2f}s"
                )
        
        except Exception as e:
            current_app.logger.error(f"Error in usage middleware: {e}")
        
        return response


# Helper functions for quota management
def get_daily_quota_remaining(user):
    """Get remaining conversions for today"""
    if user.is_premium():
        return 'unlimited'
    
    today_usage = user.get_daily_usage()
    daily_limit = int(SystemSettings.get_setting('free_daily_limit', '5'))
    
    if today_usage:
        remaining = max(0, daily_limit - today_usage.conversions_count)
    else:
        remaining = daily_limit
    
    return remaining


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"


def calculate_savings_percentage(original_size, compressed_size):
    """Calculate compression savings percentage"""
    if original_size == 0:
        return 0
    return round(((original_size - compressed_size) / original_size) * 100, 2)
