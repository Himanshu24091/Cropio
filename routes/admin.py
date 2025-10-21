"""
Admin Dashboard Routes - Phase 2
Administrative interface for user management and system oversight
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from models import User, UsageTracking, ConversionHistory, UserRole, UserSession, db
from utils.email_service import send_admin_notification
from utils.permissions import admin_required, user_management_required, analytics_required, system_management_required
from forms import AdminUserManagementForm
import os
import json

# Universal Security Framework imports
from security.core.rate_limiter import rate_limit
from security.core.validators import validate_admin_input, validate_user_id, validate_pagination, validate_json_request
from security.core.sanitizers import sanitize_search_query, sanitize_admin_params, sanitize_filename
from security.core.exceptions import SecurityException, AdminSecurityException, InvalidUserIdException, ValidationException
from security.core.access_control import require_admin_role, require_user_management_role, log_admin_action
from security.logging import security_logger
from security.core.error_handlers import handle_admin_security_error, handle_validation_error
from security.core.crypto import secure_hash
from security.core.audit import audit_admin_action

# Create admin blueprint
admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/')
@rate_limit(key='admin_dashboard', limit=20, per_minute=True)
@login_required
@require_admin_role
@audit_admin_action('dashboard_access')
def dashboard():
    """Admin dashboard overview"""
    try:
        # Log admin dashboard access
        security_logger.info(f"Admin dashboard accessed by {current_user.username} from {request.remote_addr}")
        
        # Validate admin permissions
        if not current_user.is_admin:
            security_logger.warning(f"Non-admin user {current_user.username} attempted dashboard access")
            raise AdminSecurityException("Insufficient permissions")
        
        # Get system statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(email_verified=True).count()
        premium_users = User.query.filter_by(subscription_tier='premium').count()
        
        # Get recent activity (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_conversions = ConversionHistory.query.filter(
            ConversionHistory.created_at >= thirty_days_ago
        ).count()
        
        new_users_month = User.query.filter(
            User.created_at >= thirty_days_ago
        ).count()
        
        # Get recent users (last 10)
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        
        # Get system storage usage
        storage_stats = get_storage_statistics()
        
        # Get popular tools
        popular_tools = get_popular_tools()
        
        return render_template('admin/dashboard.html',
                             total_users=total_users,
                             active_users=active_users,
                             premium_users=premium_users,
                             recent_conversions=recent_conversions,
                             new_users_month=new_users_month,
                             recent_users=recent_users,
                             storage_stats=storage_stats,
                             popular_tools=popular_tools)
        
    except AdminSecurityException as e:
        security_logger.error(f"Admin security violation in dashboard: {e} - User: {current_user.username}")
        return handle_admin_security_error(e)
    except Exception as e:
        security_logger.error(f"Admin dashboard error: {e} - User: {current_user.username}")
        current_app.logger.error(f"Admin dashboard error: {e}")
        flash('Error loading admin dashboard', 'error')
        return redirect(url_for('main.index'))

@admin.route('/users')
@rate_limit(key='admin_users', limit=30, per_minute=True)
@login_required
@require_admin_role
@audit_admin_action('user_list_access')
def users():
    """User management interface"""
    try:
        # Validate pagination and search parameters
        page = validate_pagination(request.args.get('page', 1, type=int))
        search = sanitize_search_query(request.args.get('search', '', type=str))
        filter_type = validate_admin_input(request.args.get('filter', 'all', type=str), 
                                         allowed_values=['all', 'active', 'inactive', 'premium', 'banned'])
        
        # Log user management access
        security_logger.info(f"Admin users page accessed by {current_user.username} - Search: '{search}', Filter: '{filter_type}'")
        
        # Base query
        query = User.query
        
        # Apply search filter
        if search:
            query = query.filter(
                User.username.contains(search) |
                User.email.contains(search)
            )
        
        # Apply type filter - using placeholder logic since User model doesn't have these fields yet
        if filter_type == 'active':
            query = query.filter_by(email_verified=True)
        elif filter_type == 'inactive':
            query = query.filter_by(email_verified=False)
        elif filter_type == 'premium':
            query = query.filter_by(subscription_tier='premium')
        elif filter_type == 'banned':
            # User model doesn't have is_banned field yet, skip for now
            pass
        
        # Pagination
        users_pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
        return render_template('admin/users.html',
                             users=users_pagination.items,
                             pagination=users_pagination,
                             search=search,
                             filter_type=filter_type)
        
    except ValidationException as e:
        security_logger.warning(f"Admin users validation error: {e} - User: {current_user.username}")
        return handle_validation_error(e)
    except AdminSecurityException as e:
        security_logger.error(f"Admin users security violation: {e} - User: {current_user.username}")
        return handle_admin_security_error(e)
    except Exception as e:
        security_logger.error(f"Admin users page error: {e} - User: {current_user.username}")
        current_app.logger.error(f"Admin users page error: {e}")
        flash('Error loading users list', 'error')
        return redirect(url_for('admin.dashboard'))

@admin.route('/users/<int:user_id>')
@rate_limit(key='admin_user_detail', limit=50, per_minute=True)
@login_required
@require_admin_role
@audit_admin_action('user_detail_access')
def user_detail(user_id):
    """Detailed user information and management"""
    try:
        # Validate user ID
        validate_user_id(user_id)
        
        # Log user detail access
        security_logger.info(f"Admin user detail accessed by {current_user.username} for user_id: {user_id}")
        
        user = User.query.get_or_404(user_id)
        
        # Get user statistics
        user_stats = get_user_statistics(user)
        
        # Get recent activity
        recent_conversions = ConversionHistory.query.filter_by(
            user_id=user_id
        ).order_by(ConversionHistory.created_at.desc()).limit(10).all()
        
        # Get usage history (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        usage_history = UsageTracking.query.filter(
            UsageTracking.user_id == user_id,
            UsageTracking.date >= thirty_days_ago.date()
        ).order_by(UsageTracking.date.desc()).all()
        
        return render_template('admin/user_detail.html',
                             user=user,
                             user_stats=user_stats,
                             recent_conversions=recent_conversions,
                             usage_history=usage_history)
        
    except InvalidUserIdException as e:
        security_logger.warning(f"Admin user detail invalid ID: {e} - User: {current_user.username}")
        return handle_validation_error(e)
    except AdminSecurityException as e:
        security_logger.error(f"Admin user detail security violation: {e} - User: {current_user.username}")
        return handle_admin_security_error(e)
    except Exception as e:
        security_logger.error(f"Admin user detail error: {e} - User: {current_user.username}")
        current_app.logger.error(f"Admin user detail error: {e}")
        flash('Error loading user details', 'error')
        return redirect(url_for('admin.users'))

@admin.route('/users/<int:user_id>/ban', methods=['POST'])
@rate_limit(key='admin_ban_user', limit=10, per_minute=True)
@login_required
@require_admin_role
@audit_admin_action('user_ban_action')
def ban_user(user_id):
    """Ban or unban a user"""
    try:
        # Validate user ID and JSON request
        validate_user_id(user_id)
        validate_json_request(request)
        
        user = User.query.get_or_404(user_id)
        action = validate_admin_input(request.json.get('action', 'ban'), 
                                    allowed_values=['ban', 'unban'])
        reason = sanitize_admin_params(request.json.get('reason', ''))
        
        # Prevent self-banning
        if user.id == current_user.id:
            security_logger.warning(f"Admin {current_user.username} attempted to ban themselves")
            raise AdminSecurityException("Cannot ban yourself")
        
        # Prevent banning other admins without super admin privileges
        if user.is_admin and not current_user.is_super_admin:
            security_logger.warning(f"Admin {current_user.username} attempted to ban admin user {user.username}")
            raise AdminSecurityException("Cannot ban admin users")
        
        if action == 'ban':
            user.is_banned = True
            user.ban_reason = reason
            user.banned_at = datetime.utcnow()
            user.banned_by = current_user.id
            
            # Log security action
            security_logger.warning(f"User BANNED: {user.username} by {current_user.username} - Reason: {reason}")
            
            # Send notification
            send_admin_notification(
                f"User Banned: {user.username}",
                f"User {user.username} ({user.email}) has been banned by {current_user.username}. Reason: {reason}"
            )
            
            flash(f'User {user.username} has been banned', 'success')
            
        elif action == 'unban':
            user.is_banned = False
            user.ban_reason = None
            user.banned_at = None
            user.banned_by = None
            
            # Log security action
            security_logger.info(f"User UNBANNED: {user.username} by {current_user.username}")
            
            flash(f'User {user.username} has been unbanned', 'success')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User status updated'})
        
    except InvalidUserIdException as e:
        security_logger.warning(f"Admin ban user invalid ID: {e} - User: {current_user.username}")
        return jsonify({'success': False, 'error': 'Invalid user ID'}), 400
    except ValidationException as e:
        security_logger.warning(f"Admin ban user validation error: {e} - User: {current_user.username}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except AdminSecurityException as e:
        security_logger.error(f"Admin ban user security violation: {e} - User: {current_user.username}")
        return jsonify({'success': False, 'error': str(e)}), 403
    except Exception as e:
        security_logger.error(f"Admin ban user error: {e} - User: {current_user.username}")
        current_app.logger.error(f"Admin ban user error: {e}")
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500

@admin.route('/users/<int:user_id>/subscription', methods=['POST'])
@rate_limit(key='admin_subscription', limit=20, per_minute=True)
@login_required
@require_admin_role
@audit_admin_action('subscription_management')
def manage_subscription(user_id):
    """Manage user subscription"""
    try:
        # Validate user ID and JSON request
        validate_user_id(user_id)
        validate_json_request(request)
        
        user = User.query.get_or_404(user_id)
        action = validate_admin_input(request.json.get('action'), 
                                    allowed_values=['upgrade_premium', 'downgrade_free', 'extend_subscription'])
        
        # Log subscription management action
        security_logger.info(f"Subscription management by {current_user.username} for user {user.username}: {action}")
        
        if action == 'upgrade_premium':
            user.subscription_type = 'premium'
            user.subscription_start = datetime.utcnow()
            user.subscription_end = datetime.utcnow() + timedelta(days=30)
            flash(f'{user.username} upgraded to Premium', 'success')
            
        elif action == 'downgrade_free':
            user.subscription_type = 'free'
            user.subscription_start = None
            user.subscription_end = None
            flash(f'{user.username} downgraded to Free', 'success')
            
        elif action == 'extend_subscription':
            days = validate_admin_input(request.json.get('days', 30), data_type='int', min_val=1, max_val=365)
            if user.subscription_end:
                user.subscription_end += timedelta(days=days)
            else:
                user.subscription_end = datetime.utcnow() + timedelta(days=days)
            flash(f'{user.username} subscription extended by {days} days', 'success')
        
        db.session.commit()
        
        # Send notification
        send_admin_notification(
            f"Subscription Modified: {user.username}",
            f"Subscription for {user.username} ({user.email}) has been modified by {current_user.username}. Action: {action}"
        )
        
        return jsonify({'success': True, 'message': 'Subscription updated'})
        
    except InvalidUserIdException as e:
        security_logger.warning(f"Admin subscription invalid ID: {e} - User: {current_user.username}")
        return jsonify({'success': False, 'error': 'Invalid user ID'}), 400
    except ValidationException as e:
        security_logger.warning(f"Admin subscription validation error: {e} - User: {current_user.username}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except AdminSecurityException as e:
        security_logger.error(f"Admin subscription security violation: {e} - User: {current_user.username}")
        return jsonify({'success': False, 'error': str(e)}), 403
    except Exception as e:
        security_logger.error(f"Admin subscription management error: {e} - User: {current_user.username}")
        current_app.logger.error(f"Admin subscription management error: {e}")
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500

@admin.route('/analytics')
@rate_limit(key='admin_analytics', limit=10, per_minute=True)
@login_required
@require_admin_role
@audit_admin_action('analytics_access')
def analytics():
    """System analytics and reports"""
    try:
        # Validate date range parameter
        days = validate_admin_input(request.args.get('days', 30, type=int), 
                                  data_type='int', min_val=1, max_val=365)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Log analytics access
        security_logger.info(f"Admin analytics accessed by {current_user.username} for {days} days")
        
        # User growth analytics
        user_growth = get_user_growth_data(start_date)
        
        # Conversion analytics
        conversion_data = get_conversion_analytics(start_date)
        
        # Storage analytics
        storage_data = get_storage_analytics(start_date)
        
        # Revenue analytics (if applicable)
        revenue_data = get_revenue_analytics(start_date)
        
        return render_template('admin/analytics.html',
                             user_growth=user_growth,
                             conversion_data=conversion_data,
                             storage_data=storage_data,
                             revenue_data=revenue_data,
                             days=days)
        
    except Exception as e:
        current_app.logger.error(f"Admin analytics error: {e}")
        flash('Error loading analytics', 'error')
        return redirect(url_for('admin.dashboard'))

@admin.route('/system')
@rate_limit(key='admin_system', limit=5, per_minute=True)
@login_required
@require_admin_role
@audit_admin_action('system_access')
def system():
    """System information and settings"""
    try:
        # Log system access - this is sensitive information
        security_logger.warning(f"Admin system information accessed by {current_user.username}")
        
        # Get system information
        system_info = get_system_info()
        
        # Get configuration
        config_info = get_config_info()
        
        # Get logs (last 100 lines)
        recent_logs = get_recent_logs()
        
        return render_template('admin/system.html',
                             system_info=system_info,
                             config_info=config_info,
                             recent_logs=recent_logs)
        
    except Exception as e:
        current_app.logger.error(f"Admin system page error: {e}")
        flash('Error loading system information', 'error')
        return redirect(url_for('admin.dashboard'))

@admin.route('/cleanup')
@rate_limit(key='admin_cleanup_view', limit=10, per_minute=True)
@login_required
@require_admin_role
@audit_admin_action('cleanup_view')
def cleanup():
    """System cleanup and maintenance"""
    try:
        # Get cleanup statistics
        cleanup_stats = get_cleanup_statistics()
        
        return render_template('admin/cleanup.html',
                             cleanup_stats=cleanup_stats)
        
    except Exception as e:
        current_app.logger.error(f"Admin cleanup page error: {e}")
        flash('Error loading cleanup page', 'error')
        return redirect(url_for('admin.dashboard'))

@admin.route('/cleanup/run', methods=['POST'])
@rate_limit(key='admin_cleanup_run', limit=3, per_minute=True)  # Very restrictive
@login_required
@require_admin_role
@audit_admin_action('cleanup_execution')
def run_cleanup():
    """Execute system cleanup"""
    try:
        # Validate JSON request and cleanup type
        validate_json_request(request)
        cleanup_type = validate_admin_input(request.json.get('type', 'temp_files'), 
                                          allowed_values=['temp_files', 'old_conversions', 'unused_uploads'])
        
        # Log critical system operation
        security_logger.warning(f"CRITICAL: System cleanup '{cleanup_type}' initiated by {current_user.username}")
        
        if cleanup_type == 'temp_files':
            result = cleanup_temp_files()
        elif cleanup_type == 'old_conversions':
            result = cleanup_old_conversions()
        elif cleanup_type == 'unused_uploads':
            result = cleanup_unused_uploads()
        else:
            return jsonify({'success': False, 'error': 'Invalid cleanup type'}), 400
        
        # Send admin notification
        send_admin_notification(
            f"System Cleanup: {cleanup_type}",
            f"Cleanup operation '{cleanup_type}' completed by {current_user.username}. {result['message']}"
        )
        
        return jsonify({'success': True, 'result': result})
        
    except Exception as e:
        current_app.logger.error(f"Admin cleanup execution error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Helper functions
def get_storage_statistics():
    """Get storage usage statistics"""
    try:
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
                    file_count += 1
        
        return {
            'total_size_gb': round(total_size / (1024**3), 2),
            'file_count': file_count,
            'avg_file_size_mb': round((total_size / file_count) / (1024**2), 2) if file_count > 0 else 0
        }
    except:
        return {'total_size_gb': 0, 'file_count': 0, 'avg_file_size_mb': 0}

def get_popular_tools():
    """Get most popular conversion tools"""
    try:
        from sqlalchemy import func
        popular = ConversionHistory.query.with_entities(
            ConversionHistory.tool_used,
            func.count(ConversionHistory.id).label('count')
        ).group_by(ConversionHistory.tool_used).order_by(
            func.count(ConversionHistory.id).desc()
        ).limit(10).all()
        
        return [{'tool': tool, 'count': count} for tool, count in popular]
    except:
        return []

def get_user_statistics(user):
    """Get detailed statistics for a user"""
    try:
        total_conversions = ConversionHistory.query.filter_by(user_id=user.id).count()
        
        # Calculate total storage used
        total_storage = 0
        usage_records = UsageTracking.query.filter_by(user_id=user.id).all()
        for record in usage_records:
            total_storage += record.storage_used
        
        # Get last activity
        last_conversion = ConversionHistory.query.filter_by(
            user_id=user.id
        ).order_by(ConversionHistory.created_at.desc()).first()
        
        return {
            'total_conversions': total_conversions,
            'total_storage_mb': round(total_storage / (1024**2), 2),
            'last_activity': last_conversion.created_at if last_conversion else None,
            'account_age_days': (datetime.utcnow() - user.created_at).days
        }
    except:
        return {'total_conversions': 0, 'total_storage_mb': 0, 'last_activity': None, 'account_age_days': 0}

def get_user_growth_data(start_date):
    """Get user growth data for analytics"""
    try:
        from sqlalchemy import func, extract
        
        daily_signups = User.query.with_entities(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('signups')
        ).filter(
            User.created_at >= start_date
        ).group_by(
            func.date(User.created_at)
        ).order_by(
            func.date(User.created_at)
        ).all()
        
        return [{'date': str(date), 'signups': signups} for date, signups in daily_signups]
    except:
        return []

def get_conversion_analytics(start_date):
    """Get conversion analytics data"""
    try:
        from sqlalchemy import func
        
        daily_conversions = ConversionHistory.query.with_entities(
            func.date(ConversionHistory.created_at).label('date'),
            func.count(ConversionHistory.id).label('conversions')
        ).filter(
            ConversionHistory.created_at >= start_date
        ).group_by(
            func.date(ConversionHistory.created_at)
        ).order_by(
            func.date(ConversionHistory.created_at)
        ).all()
        
        return [{'date': str(date), 'conversions': conversions} for date, conversions in daily_conversions]
    except:
        return []

def get_storage_analytics(start_date):
    """Get storage analytics data"""
    try:
        from sqlalchemy import func
        
        daily_storage = UsageTracking.query.with_entities(
            UsageTracking.date,
            func.sum(UsageTracking.storage_used).label('storage')
        ).filter(
            UsageTracking.date >= start_date.date()
        ).group_by(
            UsageTracking.date
        ).order_by(
            UsageTracking.date
        ).all()
        
        return [{'date': str(date), 'storage_mb': round(storage / (1024**2), 2)} for date, storage in daily_storage]
    except:
        return []

def get_revenue_analytics(start_date):
    """Get revenue analytics (placeholder for future implementation)"""
    # This would integrate with payment processing
    return []

def get_system_info():
    """Get system information"""
    try:
        import psutil
        import platform
        
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
    except ImportError:
        return {
            'platform': 'Information not available',
            'python_version': 'Unknown',
            'cpu_usage': 0,
            'memory_usage': 0,
            'disk_usage': 0
        }

def get_config_info():
    """Get configuration information"""
    return {
        'debug_mode': current_app.debug,
        'testing': current_app.testing,
        'mail_configured': bool(current_app.config.get('MAIL_USERNAME')),
        'database_url': current_app.config.get('DATABASE_URL', 'Not configured')[:50] + '...' if current_app.config.get('DATABASE_URL') else 'Not configured',
        'upload_folder': current_app.config.get('UPLOAD_FOLDER', 'uploads'),
        'max_content_length': current_app.config.get('MAX_CONTENT_LENGTH', 'Not set')
    }

def get_recent_logs():
    """Get recent log entries (placeholder)"""
    # This would read from log files
    return [
        {'timestamp': datetime.utcnow(), 'level': 'INFO', 'message': 'Admin dashboard accessed'},
        {'timestamp': datetime.utcnow() - timedelta(minutes=5), 'level': 'INFO', 'message': 'User login successful'},
    ]

def get_cleanup_statistics():
    """Get cleanup statistics"""
    try:
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        temp_files = []
        old_files = []
        
        # Check for temporary files
        for root, dirs, files in os.walk(upload_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    stat = os.stat(file_path)
                    age_days = (datetime.now().timestamp() - stat.st_mtime) / 86400
                    
                    if file.startswith('temp_') or file.endswith('.tmp'):
                        temp_files.append(file)
                    elif age_days > 30:  # Files older than 30 days
                        old_files.append(file)
        
        return {
            'temp_files_count': len(temp_files),
            'old_files_count': len(old_files),
            'old_conversions_count': ConversionHistory.query.filter(
                ConversionHistory.created_at < datetime.utcnow() - timedelta(days=90)
            ).count()
        }
    except:
        return {'temp_files_count': 0, 'old_files_count': 0, 'old_conversions_count': 0}

def cleanup_temp_files():
    """Clean up temporary files"""
    try:
        upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        cleaned_count = 0
        
        for root, dirs, files in os.walk(upload_dir):
            for file in files:
                if file.startswith('temp_') or file.endswith('.tmp'):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                    except:
                        pass
        
        return {'message': f'Cleaned {cleaned_count} temporary files', 'count': cleaned_count}
    except Exception as e:
        return {'message': f'Error during cleanup: {str(e)}', 'count': 0}

def cleanup_old_conversions():
    """Clean up old conversion records"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        old_conversions = ConversionHistory.query.filter(
            ConversionHistory.created_at < cutoff_date
        )
        
        count = old_conversions.count()
        old_conversions.delete()
        
        return {'message': f'Cleaned {count} old conversion records', 'count': count}
    except Exception as e:
        return {'message': f'Error during cleanup: {str(e)}', 'count': 0}

def cleanup_unused_uploads():
    """Clean up unused uploaded files"""
    try:
        # This would check for files not referenced in the database
        # Implementation depends on how files are tracked
        return {'message': 'Unused files cleanup not implemented', 'count': 0}
    except Exception as e:
        return {'message': f'Error during cleanup: {str(e)}', 'count': 0}


# Admin Security Error Handlers
@admin.errorhandler(SecurityException)
def handle_admin_security_exception(e):
    """Handle admin security exceptions"""
    security_logger.error(f"Admin security exception: {e} - User: {current_user.username if current_user.is_authenticated else 'Anonymous'}")
    return jsonify({
        'success': False, 
        'error': 'Security violation detected',
        'details': 'Your request has been logged for review'
    }), 403

@admin.errorhandler(AdminSecurityException)
def handle_admin_security_violation(e):
    """Handle admin-specific security violations"""
    security_logger.critical(f"ADMIN SECURITY VIOLATION: {e} - User: {current_user.username if current_user.is_authenticated else 'Anonymous'}")
    return jsonify({
        'success': False, 
        'error': 'Administrative security violation',
        'details': 'This incident has been logged and will be investigated'
    }), 403

@admin.errorhandler(ValidationException)
def handle_admin_validation_error(e):
    """Handle admin validation errors"""
    security_logger.warning(f"Admin validation error: {e} - User: {current_user.username if current_user.is_authenticated else 'Anonymous'}")
    return jsonify({
        'success': False, 
        'error': 'Invalid input provided',
        'details': str(e)
    }), 400

@admin.errorhandler(InvalidUserIdException)
def handle_admin_invalid_user_id(e):
    """Handle invalid user ID errors"""
    security_logger.warning(f"Admin invalid user ID: {e} - User: {current_user.username if current_user.is_authenticated else 'Anonymous'}")
    return jsonify({
        'success': False, 
        'error': 'Invalid user identifier',
        'details': 'The specified user could not be found'
    }), 404

@admin.errorhandler(429)
def handle_admin_rate_limit(e):
    """Handle admin rate limit exceeded"""
    security_logger.warning(f"Admin rate limit exceeded - User: {current_user.username if current_user.is_authenticated else 'Anonymous'}")
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded', 
        'details': 'Too many admin requests. Please wait before trying again.'
    }), 429


# Role Management Routes
@admin.route('/roles')
@rate_limit(key='admin_roles', limit=15, per_minute=True)
@login_required
@require_admin_role
@audit_admin_action('role_management_access')
def roles():
    """Role management interface"""
    try:
        roles = UserRole.query.order_by(UserRole.name).all()
        
        # Get user count for each role
        role_stats = {}
        for role in roles:
            role_stats[role.id] = User.query.filter_by(role_id=role.id).count()
        
        return render_template('admin/roles.html', 
                             roles=roles, 
                             role_stats=role_stats)
        
    except Exception as e:
        current_app.logger.error(f"Admin roles page error: {e}")
        flash('Error loading roles', 'error')
        return redirect(url_for('admin.dashboard'))


@admin.route('/users/<int:user_id>/role', methods=['POST'])
@rate_limit(key='admin_assign_role', limit=10, per_minute=True)
@login_required
@require_user_management_role
@audit_admin_action('role_assignment')
def assign_user_role(user_id):
    """Assign role to user"""
    try:
        # Validate user ID and JSON request
        validate_user_id(user_id)
        validate_json_request(request)
        
        user = User.query.get_or_404(user_id)
        new_role_name = sanitize_admin_params(request.json.get('role'))
        
        if not new_role_name:
            return jsonify({'success': False, 'error': 'Role name required'}), 400
        
        # Check if role exists
        role = UserRole.query.filter_by(name=new_role_name).first()
        if not role:
            return jsonify({'success': False, 'error': 'Invalid role'}), 400
        
        # Prevent self-demotion from admin
        if user.id == current_user.id and current_user.is_admin and new_role_name != 'admin':
            return jsonify({'success': False, 'error': 'Cannot demote yourself from admin'}), 400
        
        # Log role assignment attempt
        old_role = user.get_role_name()
        security_logger.warning(f"ROLE CHANGE: {user.username} from {old_role} to {new_role_name} by {current_user.username}")
        
        # Assign the role
        success = user.assign_role(new_role_name)
        
        if success:
            db.session.commit()
            
            # Send notification
            send_admin_notification(
                f"Role Changed: {user.username}",
                f"User {user.username} ({user.email}) role changed from {old_role} to {new_role_name} by {current_user.username}"
            )
            
            return jsonify({
                'success': True, 
                'message': f'Role updated to {role.display_name}',
                'old_role': old_role,
                'new_role': new_role_name
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to assign role'}), 500
        
    except Exception as e:
        current_app.logger.error(f"Role assignment error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin.route('/sessions')
@rate_limit(key='admin_sessions', limit=10, per_minute=True)
@login_required
@require_admin_role
@audit_admin_action('session_management_access')
def sessions():
    """Session management interface"""
    try:
        # Get all active sessions
        active_sessions = UserSession.query.filter_by(is_active=True).filter(
            UserSession.expires_at > datetime.utcnow()
        ).order_by(UserSession.last_activity.desc()).all()
        
        # Clean up expired sessions
        expired_count = UserSession.cleanup_expired()
        
        if expired_count > 0:
            flash(f'Cleaned up {expired_count} expired sessions', 'info')
        
        return render_template('admin/sessions.html', 
                             active_sessions=active_sessions)
        
    except Exception as e:
        current_app.logger.error(f"Admin sessions page error: {e}")
        flash('Error loading sessions', 'error')
        return redirect(url_for('admin.dashboard'))


@admin.route('/sessions/<int:session_id>/invalidate', methods=['POST'])
@rate_limit(key='admin_invalidate_session', limit=20, per_minute=True)
@login_required
@require_admin_role
@audit_admin_action('session_invalidation')
def invalidate_session(session_id):
    """Invalidate a specific session"""
    try:
        session_obj = UserSession.query.get_or_404(session_id)
        
        # Prevent self-session invalidation
        if session_obj.user_id == current_user.id:
            return jsonify({'success': False, 'error': 'Cannot invalidate your own session'}), 400
        
        session_obj.invalidate()
        
        # Send notification
        send_admin_notification(
            f"Session Invalidated: {session_obj.user.username}",
            f"Session for {session_obj.user.username} from {session_obj.ip_address} invalidated by {current_user.username}"
        )
        
        return jsonify({'success': True, 'message': 'Session invalidated'})
        
    except Exception as e:
        current_app.logger.error(f"Session invalidation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin.route('/users/<int:user_id>/sessions/invalidate-all', methods=['POST'])
@rate_limit(key='admin_invalidate_all_sessions', limit=5, per_minute=True)
@login_required
@require_user_management_role
@audit_admin_action('bulk_session_invalidation')
def invalidate_all_user_sessions(user_id):
    """Invalidate all sessions for a user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent self-session invalidation
        if user_id == current_user.id:
            return jsonify({'success': False, 'error': 'Cannot invalidate your own sessions'}), 400
        
        # Get all active sessions for this user
        active_sessions = UserSession.get_active_sessions(user_id)
        
        for session_obj in active_sessions:
            session_obj.invalidate()
        
        # Send notification
        send_admin_notification(
            f"All Sessions Invalidated: {user.username}",
            f"All sessions for {user.username} ({len(active_sessions)} sessions) invalidated by {current_user.username}"
        )
        
        return jsonify({
            'success': True, 
            'message': f'Invalidated {len(active_sessions)} sessions for {user.username}'
        })
        
    except Exception as e:
        current_app.logger.error(f"Bulk session invalidation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
