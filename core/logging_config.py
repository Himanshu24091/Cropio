"""
Professional Logging Configuration for Cropio SaaS Platform
Implements structured logging, log rotation, error tracking, and monitoring
"""
import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json
import traceback
from flask import request, current_app, has_request_context
from flask_login import current_user


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Create base log structure
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        if has_request_context():
            log_entry.update({
                'request': {
                    'method': request.method,
                    'url': request.url,
                    'endpoint': request.endpoint,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                }
            })
            
            # Add user context if authenticated
            if current_user.is_authenticated:
                log_entry['user'] = {
                    'id': current_user.id,
                    'username': current_user.username,
                    'email': current_user.email
                }
        
        # Add exception info if present
        if record.exc_info and record.exc_info != True:
            try:
                log_entry['exception'] = {
                    'type': record.exc_info[0].__name__,
                    'message': str(record.exc_info[1]),
                    'traceback': traceback.format_exception(*record.exc_info)
                }
            except (TypeError, AttributeError, IndexError):
                # Fallback if exc_info is malformed
                log_entry['exception'] = {
                    'type': 'UnknownException',
                    'message': str(record.exc_info) if record.exc_info else 'Exception info unavailable',
                    'traceback': []
                }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry, ensure_ascii=False)


class SecurityAuditFilter(logging.Filter):
    """Filter for security-related events"""
    
    SECURITY_EVENTS = [
        'login_attempt', 'login_success', 'login_failed',
        'password_change', 'account_locked', 'suspicious_activity',
        'unauthorized_access', 'file_upload', 'rate_limit_exceeded'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Only pass security-related log records"""
        return (
            hasattr(record, 'event_type') and 
            record.event_type in self.SECURITY_EVENTS
        )


def setup_logging(app) -> None:
    """Setup comprehensive logging for the application"""
    
    # Create logs directory
    log_dir = Path(app.config.get('LOG_DIR', 'logs'))
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Application log file with rotation
    app_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / app.config.get('LOG_FILE', 'cropio.log'),
        maxBytes=app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024),  # 10MB
        backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
    )
    app_handler.setFormatter(StructuredFormatter())
    app_handler.setLevel(logging.INFO)
    
    # Error log file
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'errors.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    error_handler.setFormatter(StructuredFormatter())
    error_handler.setLevel(logging.ERROR)
    
    # Security audit log
    security_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'security_audit.log',
        maxBytes=50 * 1024 * 1024,  # 50MB for security logs
        backupCount=20
    )
    security_handler.setFormatter(StructuredFormatter())
    security_handler.addFilter(SecurityAuditFilter())
    
    # Console handler for development
    if app.debug:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Add all handlers to root logger
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    
    # Create dedicated security logger
    security_logger = logging.getLogger('cropio.security')
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)
    
    # Performance logger for slow queries and requests
    perf_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / 'performance.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    perf_handler.setFormatter(StructuredFormatter())
    perf_logger = logging.getLogger('cropio.performance')
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.WARNING)
    
    # Suppress noisy third-party loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    app.logger.info("Logging system initialized successfully")


class CropioLogger:
    """Application-specific logger wrapper"""
    
    def __init__(self, name: str = 'cropio'):
        self.logger = logging.getLogger(name)
        self.security_logger = logging.getLogger('cropio.security')
        self.performance_logger = logging.getLogger('cropio.performance')
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log info level message"""
        record = self.logger.makeRecord(
            self.logger.name, logging.INFO, '', 0, message, None, None
        )
        if extra_data:
            record.extra_data = extra_data
        self.logger.handle(record)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log warning level message"""
        record = self.logger.makeRecord(
            self.logger.name, logging.WARNING, '', 0, message, None, None
        )
        if extra_data:
            record.extra_data = extra_data
        self.logger.handle(record)
    
    def error(self, message: str, exc_info: bool = False, 
              extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log error level message"""
        import sys
        exc_info_tuple = sys.exc_info() if exc_info and exc_info is True else exc_info
        
        record = self.logger.makeRecord(
            self.logger.name, logging.ERROR, '', 0, message, None, 
            exc_info_tuple if exc_info_tuple and exc_info_tuple != (None, None, None) else None
        )
        if extra_data:
            record.extra_data = extra_data
        self.logger.handle(record)
    
    def security_event(self, event_type: str, message: str, 
                      user_id: Optional[int] = None,
                      extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log security-related events"""
        data = extra_data or {}
        data.update({
            'event_type': event_type,
            'user_id': user_id
        })
        
        record = self.security_logger.makeRecord(
            self.security_logger.name, logging.INFO, '', 0, message, None, None
        )
        record.event_type = event_type
        record.extra_data = data
        self.security_logger.handle(record)
    
    def performance_warning(self, message: str, duration: float,
                           threshold: float = 1.0,
                           extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log performance issues"""
        if duration >= threshold:
            data = extra_data or {}
            data.update({
                'duration': duration,
                'threshold': threshold,
                'performance_issue': True
            })
            
            record = self.performance_logger.makeRecord(
                self.performance_logger.name, logging.WARNING, '', 0, 
                message, None, None
            )
            record.extra_data = data
            self.performance_logger.handle(record)


# Global logger instance
cropio_logger = CropioLogger()


def log_request_info():
    """Middleware to log request information"""
    if has_request_context():
        cropio_logger.info(
            f"{request.method} {request.path}",
            extra_data={
                'request_id': request.headers.get('X-Request-ID', ''),
                'user_agent': request.headers.get('User-Agent', ''),
                'referer': request.headers.get('Referer', '')
            }
        )


def log_database_error(error: Exception, query: str = '') -> None:
    """Log database-related errors"""
    cropio_logger.error(
        f"Database error: {str(error)}",
        exc_info=True,
        extra_data={
            'error_type': type(error).__name__,
            'query': query[:500],  # First 500 chars of query
            'database_error': True
        }
    )


def log_file_operation(operation: str, filename: str, 
                      user_id: Optional[int] = None,
                      file_size: Optional[int] = None,
                      success: bool = True) -> None:
    """Log file operations"""
    cropio_logger.info(
        f"File {operation}: {filename}",
        extra_data={
            'operation': operation,
            'filename': filename,
            'user_id': user_id,
            'file_size': file_size,
            'success': success,
            'file_operation': True
        }
    )


def log_conversion_metrics(tool: str, processing_time: float,
                         file_size: int, success: bool = True) -> None:
    """Log conversion performance metrics"""
    cropio_logger.info(
        f"Conversion completed: {tool}",
        extra_data={
            'tool': tool,
            'processing_time': processing_time,
            'file_size': file_size,
            'success': success,
            'conversion_metrics': True
        }
    )
