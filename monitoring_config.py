# monitoring_config.py - Production Monitoring Configuration
"""
Production monitoring setup for Cropio application
Includes logging, health checks, metrics, and alerting configuration.
"""

import os
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import psutil

class ProductionMonitoring:
    """Production monitoring and logging configuration"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize monitoring for Flask app"""
        self.setup_production_logging(app)
        self.setup_health_monitoring(app)
        self.setup_performance_monitoring(app)
    
    def setup_production_logging(self, app):
        """Configure production-grade logging"""
        
        # Create logs directory
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.WARNING)
        
        # Application logger
        app_logger = logging.getLogger('cropio')
        app_logger.setLevel(logging.INFO if app.debug else logging.WARNING)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'cropio.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'cropio_errors.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # Security log handler
        security_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'cropio_security.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=20,  # Keep more security logs
            encoding='utf-8'
        )
        security_handler.setLevel(logging.WARNING)
        
        # Performance log handler
        performance_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'cropio_performance.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s '
            '[in %(pathname)s:%(lineno)d] [PID:%(process)d]'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        
        security_formatter = logging.Formatter(
            '%(asctime)s [SECURITY] [%(levelname)s] %(message)s '
            '[IP:%(clientip)s] [User:%(userid)s]'
        )
        
        # Set formatters
        file_handler.setFormatter(detailed_formatter)
        error_handler.setFormatter(detailed_formatter)
        security_handler.setFormatter(security_formatter)
        performance_handler.setFormatter(simple_formatter)
        
        # Add handlers
        app_logger.addHandler(file_handler)
        app_logger.addHandler(error_handler)
        app_logger.addHandler(security_handler)
        app_logger.addHandler(performance_handler)
        
        # Console handler for development
        if app.debug:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(simple_formatter)
            app_logger.addHandler(console_handler)
        
        app.logger.info("Production logging configured")
    
    def setup_health_monitoring(self, app):
        """Setup health monitoring endpoints and checks"""
        
        @app.route('/api/metrics')
        def metrics():
            """Prometheus-style metrics endpoint"""
            from flask import jsonify
            from models import db, User
            
            try:
                # System metrics
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                process = psutil.Process()
                
                # Application metrics
                with app.app_context():
                    user_count = User.query.count()
                    active_users = User.query.filter_by(is_active=True).count()
                
                metrics = {
                    'system': {
                        'memory_used_percent': memory.percent,
                        'memory_available_mb': memory.available / (1024*1024),
                        'disk_used_percent': disk.used / disk.total * 100,
                        'disk_free_gb': disk.free / (1024**3),
                        'cpu_percent': psutil.cpu_percent(interval=1),
                        'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
                    },
                    'application': {
                        'process_memory_mb': process.memory_info().rss / (1024*1024),
                        'process_cpu_percent': process.cpu_percent(),
                        'total_users': user_count,
                        'active_users': active_users,
                        'uptime_seconds': time.time() - process.create_time()
                    },
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                return jsonify(metrics), 200
                
            except Exception as e:
                app.logger.error(f"Metrics collection failed: {e}")
                return jsonify({'error': 'Metrics unavailable'}), 503
        
        app.logger.info("Health monitoring endpoints configured")
    
    def setup_performance_monitoring(self, app):
        """Setup performance monitoring"""
        
        @app.before_request
        def before_request_monitoring():
            """Track request start time"""
            from flask import g
            import time
            g.start_time = time.time()
        
        @app.after_request
        def after_request_monitoring(response):
            """Log performance metrics"""
            from flask import g, request
            
            if hasattr(g, 'start_time'):
                duration = time.time() - g.start_time
                
                # Log slow requests
                if duration > 1.0:  # Requests taking longer than 1 second
                    app.logger.warning(
                        f"Slow request: {request.method} {request.path} "
                        f"took {duration:.3f}s",
                        extra={
                            'duration': duration,
                            'method': request.method,
                            'path': request.path,
                            'status_code': response.status_code
                        }
                    )
                
                # Log to performance log
                perf_logger = logging.getLogger('cropio.performance')
                perf_logger.info(
                    f"{request.method} {request.path} {response.status_code} {duration:.3f}s"
                )
            
            return response
        
        app.logger.info("Performance monitoring configured")

# Error tracking integration
class ErrorTracking:
    """Error tracking and alerting"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize error tracking"""
        self.setup_sentry_integration(app)
        self.setup_error_handlers(app)
    
    def setup_sentry_integration(self, app):
        """Setup Sentry error tracking"""
        sentry_dsn = os.getenv('SENTRY_DSN')
        if sentry_dsn:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.flask import FlaskIntegration
                from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
                
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[
                        FlaskIntegration(auto_enabling=True),
                        SqlalchemyIntegration(),
                    ],
                    traces_sample_rate=0.1,  # 10% of transactions
                    environment=os.getenv('FLASK_ENV', 'production'),
                    release=os.getenv('APP_VERSION', '1.0.0')
                )
                
                app.logger.info("Sentry error tracking configured")
                
            except ImportError:
                app.logger.warning("Sentry SDK not installed, skipping error tracking setup")
        else:
            app.logger.warning("SENTRY_DSN not configured, skipping Sentry setup")
    
    def setup_error_handlers(self, app):
        """Setup custom error handlers with logging"""
        
        @app.errorhandler(500)
        def internal_error(error):
            from flask import render_template, request
            
            app.logger.error(
                f"Internal server error on {request.path}",
                extra={
                    'url': request.url,
                    'method': request.method,
                    'user_agent': request.headers.get('User-Agent'),
                    'remote_addr': request.remote_addr
                },
                exc_info=True
            )
            
            return render_template('errors/500.html'), 500
        
        @app.errorhandler(404)
        def not_found_error(error):
            from flask import render_template, request
            
            app.logger.warning(
                f"404 error: {request.path}",
                extra={
                    'url': request.url,
                    'method': request.method,
                    'remote_addr': request.remote_addr
                }
            )
            
            return render_template('errors/404.html'), 404

# Security monitoring
class SecurityMonitoring:
    """Security event monitoring and alerting"""
    
    def __init__(self, app=None):
        self.failed_logins = {}
        self.suspicious_ips = set()
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security monitoring"""
        
        @app.before_request
        def security_monitoring():
            """Monitor requests for security issues"""
            from flask import request
            import re
            
            # Check for common attack patterns
            suspicious_patterns = [
                r'<script',
                r'javascript:',
                r'<iframe',
                r'\.\./\.\.',
                r'union\s+select',
                r'drop\s+table'
            ]
            
            query_string = request.query_string.decode('utf-8', errors='ignore')
            
            for pattern in suspicious_patterns:
                if re.search(pattern, query_string, re.IGNORECASE):
                    security_logger = logging.getLogger('cropio.security')
                    security_logger.warning(
                        f"Suspicious request pattern detected: {pattern}",
                        extra={
                            'clientip': request.remote_addr,
                            'userid': 'unknown',
                            'pattern': pattern,
                            'query': query_string[:100]  # Limit logged data
                        }
                    )
                    break
        
        app.logger.info("Security monitoring configured")

# Initialize monitoring
def init_production_monitoring(app):
    """Initialize all production monitoring components"""
    
    # Basic monitoring
    monitoring = ProductionMonitoring(app)
    
    # Error tracking
    error_tracking = ErrorTracking(app)
    
    # Security monitoring
    security_monitoring = SecurityMonitoring(app)
    
    app.logger.info("All production monitoring components initialized")
    
    return {
        'monitoring': monitoring,
        'error_tracking': error_tracking,
        'security_monitoring': security_monitoring
    }
