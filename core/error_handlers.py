"""
Professional Error Handling System for Cropio SaaS Platform
Implements global error handlers, error monitoring, and user-friendly error pages
"""
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Tuple
from flask import Flask, request, render_template, jsonify, current_app
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge, BadRequest
from werkzeug.http import HTTP_STATUS_CODES
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from core.logging_config import cropio_logger
import os


class ErrorTracker:
    """Track and manage application errors"""
    
    def __init__(self):
        self.error_count = {}
        self.recent_errors = []
    
    def log_error(self, error_id: str, error_type: str, message: str, 
                  user_id: int = None, request_info: Dict = None) -> None:
        """Log error with tracking"""
        
        # Update error count
        self.error_count[error_type] = self.error_count.get(error_type, 0) + 1
        
        # Store recent error (keep last 100)
        error_info = {
            'id': error_id,
            'type': error_type,
            'message': message,
            'timestamp': datetime.utcnow(),
            'user_id': user_id,
            'request_info': request_info
        }
        self.recent_errors.append(error_info)
        if len(self.recent_errors) > 100:
            self.recent_errors.pop(0)
        
        # Log to security logger for critical errors
        if error_type in ['SecurityError', 'IntegrityError', 'AuthenticationError']:
            cropio_logger.security_event(
                'error_occurred',
                f"Critical error: {error_type}",
                user_id=user_id,
                extra_data={
                    'error_id': error_id,
                    'error_type': error_type,
                    'message': message,
                    'request_info': request_info
                }
            )


# Global error tracker
error_tracker = ErrorTracker()


def generate_error_id() -> str:
    """Generate unique error ID for tracking"""
    return str(uuid.uuid4())[:8]


def get_client_info() -> Dict[str, Any]:
    """Extract client information from request"""
    return {
        'ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
        'user_agent': request.headers.get('User-Agent', ''),
        'referer': request.headers.get('Referer', ''),
        'method': request.method,
        'url': request.url,
        'endpoint': request.endpoint
    }


def handle_database_error(error: SQLAlchemyError) -> Tuple[str, int]:
    """Handle database-related errors"""
    error_id = generate_error_id()
    
    if isinstance(error, IntegrityError):
        message = "Data integrity constraint violation"
        user_message = "The operation couldn't be completed due to data conflicts. Please try again."
        status_code = 400
    elif isinstance(error, OperationalError):
        message = "Database operation failed"
        user_message = "Service temporarily unavailable. Please try again later."
        status_code = 503
    else:
        message = f"Database error: {str(error)}"
        user_message = "An unexpected error occurred. Please try again."
        status_code = 500
    
    # Log the error
    cropio_logger.error(
        message,
        exc_info=True,
        extra_data={
            'error_id': error_id,
            'error_type': type(error).__name__,
            'database_error': True,
            'request_info': get_client_info()
        }
    )
    
    error_tracker.log_error(
        error_id, 
        type(error).__name__, 
        message,
        request_info=get_client_info()
    )
    
    return error_id, status_code


def init_error_handlers(app: Flask) -> None:
    """Initialize comprehensive error handlers"""
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors"""
        error_id = generate_error_id()
        
        cropio_logger.warning(
            f"404 Not Found: {request.url}",
            extra_data={
                'error_id': error_id,
                'request_info': get_client_info(),
                'error_type': '404_not_found'
            }
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found.',
                'error_id': error_id,
                'status_code': 404
            }), 404
        
        return render_template(
            'errors/404.html',
            error_id=error_id
        ), 404
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 Forbidden errors"""
        error_id = generate_error_id()
        
        cropio_logger.security_event(
            'unauthorized_access',
            f"403 Forbidden access attempt: {request.url}",
            extra_data={
                'error_id': error_id,
                'request_info': get_client_info(),
                'error_type': '403_forbidden'
            }
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Forbidden',
                'message': 'You do not have permission to access this resource.',
                'error_id': error_id,
                'status_code': 403
            }), 403
        
        return render_template(
            'errors/403.html',
            error_id=error_id
        ), 403
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle 500 Internal Server errors"""
        error_id = generate_error_id()
        
        cropio_logger.error(
            "Internal server error occurred",
            exc_info=True,
            extra_data={
                'error_id': error_id,
                'request_info': get_client_info(),
                'error_type': '500_internal_error',
                'original_exception': str(error.original_exception) if hasattr(error, 'original_exception') else str(error)
            }
        )
        
        error_tracker.log_error(
            error_id,
            '500_internal_error',
            "Internal server error",
            request_info=get_client_info()
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred. Our team has been notified.',
                'error_id': error_id,
                'status_code': 500
            }), 500
        
        return render_template(
            'errors/500.html',
            error_id=error_id
        ), 500
    
    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(error):
        """Handle file size too large errors"""
        error_id = generate_error_id()
        
        max_size = app.config.get('MAX_CONTENT_LENGTH', 100 * 1024 * 1024)
        max_size_mb = max_size // (1024 * 1024)
        
        cropio_logger.warning(
            f"File upload too large: {request.url}",
            extra_data={
                'error_id': error_id,
                'request_info': get_client_info(),
                'error_type': 'file_too_large',
                'max_size': max_size,
                'max_size_mb': max_size_mb
            }
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'File Too Large',
                'message': f'Maximum file size allowed is {max_size_mb}MB.',
                'error_id': error_id,
                'status_code': 413,
                'max_size_mb': max_size_mb
            }), 413
        
        return render_template(
            'errors/413.html',
            error_id=error_id,
            max_size_mb=max_size_mb
        ), 413
    
    @app.errorhandler(BadRequest)
    def handle_bad_request(error):
        """Handle 400 Bad Request errors"""
        error_id = generate_error_id()
        
        cropio_logger.warning(
            f"Bad request: {error.description}",
            extra_data={
                'error_id': error_id,
                'request_info': get_client_info(),
                'error_type': 'bad_request',
                'description': error.description
            }
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Bad Request',
                'message': error.description or 'The request could not be processed.',
                'error_id': error_id,
                'status_code': 400
            }), 400
        
        return render_template(
            'errors/400.html',
            error_id=error_id,
            message=error.description
        ), 400
    
    @app.errorhandler(SQLAlchemyError)
    def handle_database_exception(error):
        """Handle database exceptions"""
        error_id, status_code = handle_database_error(error)
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Database Error',
                'message': 'A database error occurred. Please try again.',
                'error_id': error_id,
                'status_code': status_code
            }), status_code
        
        return render_template(
            'errors/500.html',
            error_id=error_id,
            message="A database error occurred. Please try again."
        ), status_code
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle any unexpected errors"""
        error_id = generate_error_id()
        
        cropio_logger.error(
            f"Unexpected error: {str(error)}",
            exc_info=True,
            extra_data={
                'error_id': error_id,
                'request_info': get_client_info(),
                'error_type': type(error).__name__,
                'unexpected_error': True
            }
        )
        
        error_tracker.log_error(
            error_id,
            type(error).__name__,
            str(error),
            request_info=get_client_info()
        )
        
        # Don't handle HTTP exceptions here
        if isinstance(error, HTTPException):
            return error
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Unexpected Error',
                'message': 'An unexpected error occurred. Our team has been notified.',
                'error_id': error_id,
                'status_code': 500
            }), 500
        
        return render_template(
            'errors/500.html',
            error_id=error_id
        ), 500
    
    # Add custom error pages for common HTTP status codes
    @app.errorhandler(429)
    def handle_rate_limit(error):
        """Handle rate limiting errors"""
        error_id = generate_error_id()
        
        cropio_logger.security_event(
            'rate_limit_exceeded',
            "Rate limit exceeded",
            extra_data={
                'error_id': error_id,
                'request_info': get_client_info(),
                'error_type': 'rate_limit_exceeded'
            }
        )
        
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({
                'error': 'Rate Limit Exceeded',
                'message': 'Too many requests. Please slow down and try again later.',
                'error_id': error_id,
                'status_code': 429,
                'retry_after': getattr(error, 'retry_after', 60)
            }), 429
        
        return render_template(
            'errors/429.html',
            error_id=error_id
        ), 429
    
    app.logger.info("Error handlers initialized successfully")


def create_error_monitoring_blueprint():
    """Create blueprint for error monitoring (admin only)"""
    from flask import Blueprint, request, jsonify
    from flask_login import login_required, current_user
    
    monitoring_bp = Blueprint('error_monitoring', __name__, url_prefix='/admin/monitoring')
    
    @monitoring_bp.before_request
    @login_required
    def require_admin():
        """Require admin access for monitoring endpoints"""
        if not (current_user.is_authenticated and current_user.username == 'admin'):
            return jsonify({'error': 'Admin access required'}), 403
    
    @monitoring_bp.route('/errors')
    def get_error_stats():
        """Get error statistics"""
        return jsonify({
            'error_counts': error_tracker.error_count,
            'recent_errors': [
                {
                    'id': err['id'],
                    'type': err['type'],
                    'message': err['message'],
                    'timestamp': err['timestamp'].isoformat(),
                    'user_id': err['user_id']
                }
                for err in error_tracker.recent_errors[-20:]  # Last 20 errors
            ],
            'total_errors': len(error_tracker.recent_errors)
        })
    
    @monitoring_bp.route('/health')
    def health_check():
        """Health check endpoint"""
        try:
            # Check database connection
            from models import db
            db.session.execute('SELECT 1')
            
            # Check log directory
            log_dir_exists = os.path.exists('logs')
            
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'logging': 'active' if log_dir_exists else 'warning',
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503
    
    return monitoring_bp
