"""
Usage Tracking Middleware - Phase 2
Track conversions, enforce quotas, and collect analytics data
"""
from functools import wraps
from flask import request, jsonify, current_app, g, session, flash, redirect, url_for
from flask_login import current_user
from datetime import datetime, date, timedelta
from models import User, UsageTracking, ConversionHistory, db
from utils.email_service import send_usage_limit_notification, send_admin_notification
import os

# Subscription limits configuration
SUBSCRIPTION_LIMITS = {
    'free': {
        'daily_conversions': 20,
        'max_file_size_mb': 50,  # Increased for better UX
        'concurrent_uploads': 5,
        'storage_limit_mb': 200,
        'features': ['basic_conversion', 'pdf_merge', 'image_compress']
    },
    'premium': {
        'daily_conversions': 500,
        'max_file_size_mb': 200,  # Increased for premium users
        'concurrent_uploads': 20,
        'storage_limit_mb': 5000,
        'features': ['all']
    }
}

class UsageTracker:
    """Central usage tracking and quota management"""
    
    @staticmethod
    def get_user_limits(user=None):
        """Get current user's limits based on subscription"""
        if not user:
            user = current_user
        
        if user.is_authenticated:
            subscription_type = user.subscription_tier or 'free'
            
            # Check if premium subscription is expired
            if subscription_type == 'premium' and user.subscription_end:
                if user.subscription_end < datetime.utcnow().date():
                    subscription_type = 'free'
                    # Update user subscription status
                    user.subscription_tier = 'free'
                    user.subscription_end = None
                    db.session.commit()
        else:
            subscription_type = 'free'
        
        return SUBSCRIPTION_LIMITS.get(subscription_type, SUBSCRIPTION_LIMITS['free'])
    
    @staticmethod
    def get_daily_usage(user_id, target_date=None):
        """Get user's daily usage statistics"""
        if not target_date:
            target_date = date.today()
        
        usage_record = UsageTracking.query.filter_by(
            user_id=user_id,
            date=target_date
        ).first()
        
        if not usage_record:
            # Create new usage record
            usage_record = UsageTracking(
                user_id=user_id,
                date=target_date,
                conversions_count=0,
                storage_used=0
            )
            db.session.add(usage_record)
            db.session.commit()
        
        return usage_record
    
    @staticmethod
    def check_conversion_quota(user=None):
        """Check if user can perform more conversions today"""
        if not user:
            user = current_user
        
        if not user.is_authenticated:
            return {'allowed': True, 'remaining': float('inf'), 'limit': float('inf')}
        
        limits = UsageTracker.get_user_limits(user)
        usage = UsageTracker.get_daily_usage(user.id)
        
        remaining = limits['daily_conversions'] - usage.conversions_count
        allowed = remaining > 0
        
        return {
            'allowed': allowed,
            'remaining': max(0, remaining),
            'limit': limits['daily_conversions'],
            'used': usage.conversions_count
        }
    
    @staticmethod
    def check_file_size_limit(file_size_mb, user=None):
        """Check if file size is within user's limits"""
        if not user:
            user = current_user
        
        limits = UsageTracker.get_user_limits(user)
        return file_size_mb <= limits['max_file_size_mb']
    
    @staticmethod
    def check_storage_limit(additional_mb, user=None):
        """Check if additional storage would exceed user's limit"""
        if not user:
            user = current_user
        
        if not user.is_authenticated:
            return True
        
        limits = UsageTracker.get_user_limits(user)
        
        # Calculate current storage usage
        current_storage = db.session.query(
            db.func.sum(UsageTracking.storage_used)
        ).filter_by(user_id=user.id).scalar() or 0
        
        # Convert bytes to MB and ensure float type
        current_storage_mb = float(current_storage) / (1024 * 1024)
        additional_mb = float(additional_mb)
        
        return (current_storage_mb + additional_mb) <= limits['storage_limit_mb']
    
    @staticmethod
    def track_conversion(tool_type, input_file_path, output_file_path, user=None):
        """Track a successful conversion using current ConversionHistory schema"""
        if not user:
            user = current_user
        
        if not user.is_authenticated:
            return
        
        try:
            # Calculate file sizes and derive formats
            input_size = os.path.getsize(input_file_path) if os.path.exists(input_file_path) else 0
            output_size = os.path.getsize(output_file_path) if os.path.exists(output_file_path) else 0
            
            # If no output file exists (streamed response), check for estimated size
            if output_size == 0 and hasattr(g, 'estimated_output_size'):
                output_size = g.estimated_output_size
            
            # If still no output size, estimate based on input
            if output_size == 0 and input_size > 0:
                # Conservative estimate: most conversions produce similar or smaller files
                output_size = int(input_size * 0.8)
            
            original_filename = os.path.basename(input_file_path) if input_file_path else ''
            target_filename = os.path.basename(output_file_path) if output_file_path else ''
            
            # Try to infer target format from tool type if no output filename
            if not target_filename and tool_type:
                if 'pdf' in tool_type:
                    target_ext = 'pdf'
                elif 'image' in tool_type:
                    # Check form data for target format
                    target_ext = request.form.get('format', 'unknown').lower()
                elif 'document' in tool_type:
                    target_ext = request.form.get('format', 'unknown').lower()
                else:
                    target_ext = 'unknown'
            else:
                target_ext = (os.path.splitext(target_filename)[1].lstrip('.').lower() if target_filename else 'unknown')
            
            original_ext = (os.path.splitext(original_filename)[1].lstrip('.').lower() if original_filename else 'unknown')
            
            # Update daily usage
            usage = UsageTracker.get_daily_usage(user.id)
            usage.conversions_count += 1
            # Count at least the input size; if output exists use the larger as processed storage
            processed_bytes = max(output_size, input_size)
            usage.storage_used += processed_bytes
            
            # Update feature-specific counters
            if 'image' in tool_type:
                usage.image_conversions += 1
            elif 'pdf' in tool_type:
                usage.pdf_conversions += 1
            elif 'document' in tool_type:
                usage.document_conversions += 1
            
            # Create conversion history record (aligned to models.ConversionHistory)
            conversion = ConversionHistory(
                user_id=user.id,
                original_filename=original_filename or 'unknown',
                original_format=original_ext or 'unknown',
                target_format=target_ext or 'unknown',
                file_size=output_size or input_size,
                conversion_type=tool_type,
                tool_used=tool_type,
                status='completed',
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            db.session.add(conversion)
            db.session.commit()
            
            # Check if user is approaching limits
            limits = UsageTracker.get_user_limits(user)
            remaining = limits['daily_conversions'] - usage.conversions_count
            
            if 0 < remaining <= 2:
                # Send approaching limit notification
                try:
                    send_usage_limit_notification(user, 'approaching')
                except:
                    pass  # Don't fail conversion tracking if email fails
            elif remaining <= 0:
                # Send limit reached notification
                try:
                    send_usage_limit_notification(user, 'reached')
                except:
                    pass
            
            current_app.logger.info(f"Conversion tracked: {tool_type} for user {user.username}, size: {processed_bytes} bytes")
            
        except Exception as e:
            current_app.logger.error(f"Error tracking conversion: {e}")
            db.session.rollback()
    
    @staticmethod
    def track_failed_conversion(tool_type, error_message, user=None):
        """Track a failed conversion attempt using current schema"""
        if not user:
            user = current_user
        
        if not user.is_authenticated:
            return
        
        try:
            conversion = ConversionHistory(
                user_id=user.id,
                original_filename='',
                original_format='unknown',
                target_format='unknown',
                file_size=0,
                conversion_type=tool_type,
                tool_used=tool_type,
                status='failed',
                error_message=error_message,
                created_at=datetime.utcnow()
            )
            
            db.session.add(conversion)
            db.session.commit()
            
            current_app.logger.warning(f"Failed conversion tracked: {tool_type} for user {user.username}")
            
        except Exception as e:
            current_app.logger.error(f"Error tracking failed conversion: {e}")
            db.session.rollback()

def quota_required(tool_name=None, check_file_size=True):
    """Decorator to enforce quotas on conversion routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip quota checks for admin users
            # TODO: Add proper admin field to User model
            # if current_user.is_authenticated and current_user.is_admin:
            #     return f(*args, **kwargs)
            
            # Check conversion quota
            quota_check = UsageTracker.check_conversion_quota()
            if not quota_check['allowed']:
                if request.is_json or 'api' in request.path:
                    return jsonify({
                        'error': 'Daily conversion limit reached',
                        'limit': quota_check['limit'],
                        'used': quota_check['used'],
                        'upgrade_url': url_for('dashboard.subscription') if current_user.is_authenticated else None
                    }), 429
                else:
                    flash('Daily conversion limit reached. Upgrade to Premium for unlimited conversions!', 'error')
                    if current_user.is_authenticated:
                        return redirect(url_for('dashboard.subscription'))
                    else:
                        return redirect(url_for('auth.login'))
            
            # Check file size if file is uploaded
            if check_file_size and 'file' in request.files:
                file = request.files['file']
                if file and file.filename:
                    # Determine file size without persisting to disk
                    try:
                        file.seek(0, 2)
                        file_size_bytes = file.tell()
                        file.seek(0)
                        file_size_mb = file_size_bytes / (1024 * 1024)
                    except Exception:
                        file_size_mb = 0
                    
                    if not UsageTracker.check_file_size_limit(file_size_mb):
                        limits = UsageTracker.get_user_limits()
                        
                        if request.is_json or 'api' in request.path:
                            return jsonify({
                                'error': f'File size exceeds limit of {limits["max_file_size_mb"]}MB',
                                'limit_mb': limits['max_file_size_mb'],
                                'file_size_mb': round(file_size_mb, 2)
                            }), 413
                        else:
                            flash(f'File size exceeds limit of {limits["max_file_size_mb"]}MB. Upgrade to Premium for larger files!', 'error')
                            if current_user.is_authenticated:
                                return redirect(url_for('dashboard.subscription'))
                            else:
                                return redirect(url_for('auth.login'))
                    
                    # Check storage limit
                    if not UsageTracker.check_storage_limit(file_size_mb):
                        limits = UsageTracker.get_user_limits()
                        
                        if request.is_json or 'api' in request.path:
                            return jsonify({
                                'error': f'Storage limit of {limits["storage_limit_mb"]}MB would be exceeded',
                                'storage_limit_mb': limits['storage_limit_mb']
                            }), 507
                        else:
                            flash(f'Storage limit would be exceeded. Upgrade to Premium for more storage!', 'error')
                            if current_user.is_authenticated:
                                return redirect(url_for('dashboard.subscription'))
                            else:
                                return redirect(url_for('auth.login'))
                    
                    # Store size info for tracking
                    g.input_file_size = file_size_mb
            
            # Store tool name for tracking
            g.tool_name = tool_name or f.__name__
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def track_conversion_result(tool_type=None):
    """Decorator to track conversion results"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the original function
            result = f(*args, **kwargs)
            
            # Track the result if user is authenticated
            if current_user.is_authenticated:
                tool_name = tool_type or getattr(g, 'tool_name', f.__name__)
                
                try:
                    # Check if conversion was successful
                    if isinstance(result, tuple):
                        # Flask response tuple (response, status_code)
                        response_obj = result[0]
                        status_code = result[1] if len(result) > 1 else 200
                    else:
                        response_obj = result
                        status_code = 200
                    
                    # Check for JSON API responses (like LaTeX compilation)
                    is_json_success = False
                    if hasattr(response_obj, 'is_json') and response_obj.is_json:
                        try:
                            json_data = response_obj.get_json()
                            is_json_success = json_data.get('success', False) == True
                        except:
                            pass
                    
                    # Only track on successful POST requests
                    should_track = (
                        status_code == 200 and request.method == 'POST' and (
                            # File upload conversions
                            (hasattr(g, 'input_file_path') or ('file' in request.files and request.files['file'].filename)) or
                            # JSON API conversions (like LaTeX compilation)
                            (is_json_success and hasattr(g, 'output_file_path'))
                        )
                    )
                    
                    if should_track:
                        # Successful conversion
                        input_path = getattr(g, 'input_file_path', '')
                        output_path = getattr(g, 'output_file_path', '')
                        
                        # If no output path but we have a response object, try to estimate size
                        if not output_path and hasattr(response_obj, 'direct_passthrough'):
                            # For send_file responses with BytesIO
                            try:
                                # Store the estimated output size based on response
                                if hasattr(response_obj, 'content_length') and response_obj.content_length:
                                    g.estimated_output_size = response_obj.content_length
                                elif hasattr(g, 'input_file_size'):
                                    # Estimate output size based on input (conservative estimate)
                                    g.estimated_output_size = int(g.input_file_size * 1024 * 1024 * 0.8)  # 80% of input
                            except:
                                pass
                        
                        # Track even if output_path is not available (e.g., streamed response)
                        UsageTracker.track_conversion(
                            tool_name, input_path, output_path or ''
                        )
                    elif status_code != 200 and request.method == 'POST':
                        # Failed conversion
                        error_msg = f"HTTP {status_code}"
                        UsageTracker.track_failed_conversion(tool_name, error_msg)
                        
                except Exception as e:
                    current_app.logger.error(f"Error in conversion tracking: {e}")
            
            return result
        return decorated_function
    return decorator

def usage_analytics():
    """Middleware to collect anonymous usage analytics"""
    def before_request():
        """Collect request analytics"""
        g.request_start_time = datetime.utcnow()
        
        # Store basic analytics info
        g.user_agent = request.headers.get('User-Agent', '')
        g.ip_address = request.remote_addr
        g.path = request.path
        g.method = request.method
    
    def after_request(response):
        """Process and store analytics after request"""
        try:
            # Calculate request duration
            if hasattr(g, 'request_start_time'):
                duration_ms = (datetime.utcnow() - g.request_start_time).total_seconds() * 1000
                g.request_duration_ms = duration_ms
            
            # Log slow requests
            if hasattr(g, 'request_duration_ms') and g.request_duration_ms > 5000:  # 5 seconds
                current_app.logger.warning(
                    f"Slow request: {g.method} {g.path} took {g.request_duration_ms:.2f}ms"
                )
            
            # Store conversion tool usage statistics
            path = getattr(g, 'path', request.path)
            if '/convert' in path and current_user.is_authenticated:
                # This would be saved to analytics database in a production system
                current_app.logger.info(f"Tool usage: {path} by {current_user.username}")
            
        except Exception as e:
            current_app.logger.error(f"Error in usage analytics: {e}")
            # Ensure we don't break the request if analytics fails
        
        return response
    
    return before_request, after_request

def init_usage_tracking(app):
    """Initialize usage tracking middleware"""
    before_request, after_request = usage_analytics()
    
    app.before_request(before_request)
    app.after_request(after_request)
    
    # Add context processor for usage information
    @app.context_processor
    def inject_usage_info():
        """Inject usage information into templates"""
        if current_user.is_authenticated:
            quota_check = UsageTracker.check_conversion_quota()
            limits = UsageTracker.get_user_limits()
            
            return {
                'user_quota': quota_check,
                'user_limits': limits,
                'usage_tracker': UsageTracker
            }
        return {}
    
    app.logger.info("Usage tracking middleware initialized")

# Utility functions for cleanup and maintenance

def cleanup_old_usage_records(days_to_keep=90):
    """Clean up old usage tracking records"""
    try:
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        deleted_usage = UsageTracking.query.filter(
            UsageTracking.date < cutoff_date
        ).delete()
        
        deleted_history = ConversionHistory.query.filter(
            ConversionHistory.created_at < datetime.combine(cutoff_date, datetime.min.time())
        ).delete()
        
        db.session.commit()
        
        current_app.logger.info(f"Cleaned up {deleted_usage} usage records and {deleted_history} conversion history records")
        
        return {
            'usage_records_deleted': deleted_usage,
            'conversion_history_deleted': deleted_history
        }
        
    except Exception as e:
        current_app.logger.error(f"Error cleaning up usage records: {e}")
        db.session.rollback()
        return {'error': str(e)}

def generate_usage_report(user_id, days=30):
    """Generate detailed usage report for a user"""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get usage records
        usage_records = UsageTracking.query.filter(
            UsageTracking.user_id == user_id,
            UsageTracking.date >= start_date,
            UsageTracking.date <= end_date
        ).order_by(UsageTracking.date.desc()).all()
        
        # Get conversion history
        conversion_history = ConversionHistory.query.filter(
            ConversionHistory.user_id == user_id,
            ConversionHistory.created_at >= datetime.combine(start_date, datetime.min.time())
        ).order_by(ConversionHistory.created_at.desc()).all()
        
        # Calculate totals
        total_conversions = sum(record.conversions_count for record in usage_records)
        total_storage = sum(record.storage_used for record in usage_records)
        successful_conversions = len([c for c in conversion_history if c.status == 'completed'])
        failed_conversions = len([c for c in conversion_history if c.status == 'failed'])
        
        # Most used tools
        tool_usage = {}
        for conversion in conversion_history:
            if conversion.status == 'completed':
                tool_key = getattr(conversion, 'tool_used', None) or 'unknown'
                tool_usage[tool_key] = tool_usage.get(tool_key, 0) + 1
        
        return {
            'period': f"{start_date} to {end_date}",
            'total_conversions': total_conversions,
            'successful_conversions': successful_conversions,
            'failed_conversions': failed_conversions,
            'total_storage_bytes': total_storage,
            'total_storage_mb': round(total_storage / (1024 * 1024), 2),
            'daily_average': round(total_conversions / days, 2),
            'most_used_tools': sorted(tool_usage.items(), key=lambda x: x[1], reverse=True),
            'usage_by_day': [
                {
                    'date': record.date.strftime('%Y-%m-%d'),
                    'conversions': record.conversions_count,
                    'storage_mb': round(record.storage_used / (1024 * 1024), 2)
                }
                for record in usage_records
            ]
        }
        
    except Exception as e:
        current_app.logger.error(f"Error generating usage report: {e}")
        return {'error': str(e)}

# Rate limiting decorator for API endpoints
def rate_limit(requests_per_minute=60):
    """Simple rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple in-memory rate limiting (would use Redis in production)
            client_id = current_user.id if current_user.is_authenticated else request.remote_addr
            
            # This is a simplified implementation
            # In production, you would use Redis or similar for distributed rate limiting
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
