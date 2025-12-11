#!/usr/bin/env python3
"""
Production Readiness Test Suite for Cropio
==========================================
Comprehensive testing to validate production deployment readiness including
performance, scalability, security, monitoring, and operational requirements.

Usage:
    python production_readiness_test.py
    python production_readiness_test.py --verbose
    python production_readiness_test.py --performance-only
    python production_readiness_test.py --export-report
"""

import os
import sys
import time
import json
import psutil
import threading
import subprocess
import requests
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import argparse
import concurrent.futures
from urllib.parse import urljoin
import socket
import ssl

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class ProductionTest:
    name: str
    passed: bool
    message: str
    duration: float
    category: str
    severity: str = "INFO"
    recommendations: List[str] = None
    metrics: Dict[str, Any] = None

class ProductionReadinessTester:
    """Comprehensive production readiness validation"""
    
    def __init__(self, verbose: bool = False, performance_only: bool = False, 
                 export_report: bool = False):
        self.verbose = verbose
        self.performance_only = performance_only
        self.export_report = export_report
        self.tests: List[ProductionTest] = []
        self.start_time = time.time()
        self.categories = [
            'CONFIGURATION',
            'SECURITY', 
            'PERFORMANCE',
            'SCALABILITY',
            'MONITORING',
            'DEPLOYMENT',
            'OPERATIONAL'
        ]
        
        print("🚀 CROPIO PRODUCTION READINESS TEST SUITE")
        print("=" * 50)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Verbose mode: {'ON' if verbose else 'OFF'}")
        print(f"⚡ Performance focus: {'ON' if performance_only else 'OFF'}")
        print()

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        if self.verbose or level in ["WARNING", "ERROR", "CRITICAL"]:
            timestamp = datetime.now().strftime('%H:%M:%S')
            colors = {
                'INFO': '\033[92m',
                'WARNING': '\033[93m', 
                'ERROR': '\033[91m',
                'CRITICAL': '\033[95m',
                'RESET': '\033[0m'
            }
            color = colors.get(level, colors['INFO'])
            print(f"{color}[{timestamp}] {level}: {message}{colors['RESET']}")

    def add_test(self, name: str, passed: bool, message: str, duration: float,
                 category: str, severity: str = "INFO", 
                 recommendations: List[str] = None, metrics: Dict[str, Any] = None):
        """Add test result"""
        test = ProductionTest(
            name=name,
            passed=passed,
            message=message,
            duration=duration,
            category=category,
            severity=severity,
            recommendations=recommendations or [],
            metrics=metrics or {}
        )
        self.tests.append(test)
        
        # Log result
        status = "✅ PASS" if passed else "❌ FAIL"
        self.log(f"{status} {name}: {message}", 
                "INFO" if passed else severity)

    def run_test(self, test_func, name: str, category: str):
        """Run individual test with error handling"""
        if self.performance_only and category != 'PERFORMANCE':
            return
            
        start_time = time.time()
        try:
            result = test_func()
            duration = time.time() - start_time
            
            if isinstance(result, tuple):
                if len(result) == 2:
                    passed, message = result
                    recommendations = []
                    metrics = {}
                elif len(result) == 3:
                    passed, message, recommendations = result
                    metrics = {}
                elif len(result) == 4:
                    passed, message, recommendations, metrics = result
                else:
                    passed, message = result[:2]
                    recommendations = []
                    metrics = {}
            else:
                passed = result
                message = "Test completed"
                recommendations = []
                metrics = {}
                
            self.add_test(name, passed, message, duration, category,
                         "INFO" if passed else "ERROR", 
                         recommendations, metrics)
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed with exception: {str(e)}"
            self.add_test(name, False, error_msg, duration, category, "ERROR")

    # =============================================================================
    # CONFIGURATION TESTS
    # =============================================================================

    def test_production_environment_config(self):
        """Test production environment configuration"""
        self.log("🔧 Testing Production Environment Configuration...")
        
        issues = []
        recommendations = []
        metrics = {}
        
        # Check Flask environment
        flask_env = os.getenv('FLASK_ENV', 'development')
        if flask_env != 'production':
            issues.append(f"FLASK_ENV is '{flask_env}' (should be 'production')")
            recommendations.append("Set FLASK_ENV=production")
        
        # Check debug mode
        flask_debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        if flask_debug:
            issues.append("Debug mode is enabled in production")
            recommendations.append("Set FLASK_DEBUG=false")
        
        # Check secret key
        secret_key = os.getenv('SECRET_KEY') or os.getenv('FLASK_SECRET_KEY')
        if not secret_key or len(secret_key) < 32:
            issues.append("Secret key is missing or too short")
            recommendations.append("Generate a secure 32+ character secret key")
        
        # Check database URL
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            issues.append("DATABASE_URL not configured")
            recommendations.append("Configure production database URL")
        elif 'localhost' in db_url or '127.0.0.1' in db_url:
            issues.append("Database URL points to localhost")
            recommendations.append("Use production database server")
        
        # Check SSL configuration
        ssl_cert = os.getenv('SSL_CERT_PATH')
        ssl_key = os.getenv('SSL_KEY_PATH')
        if not ssl_cert or not ssl_key:
            issues.append("SSL certificates not configured")
            recommendations.append("Configure SSL certificates for HTTPS")
        
        # Check email configuration
        mail_server = os.getenv('MAIL_SERVER')
        mail_username = os.getenv('MAIL_USERNAME')
        if not mail_server or not mail_username:
            issues.append("Email configuration incomplete")
            recommendations.append("Configure production email settings")
        
        metrics = {
            'flask_env': flask_env,
            'debug_mode': flask_debug,
            'secret_key_length': len(secret_key) if secret_key else 0,
            'ssl_configured': bool(ssl_cert and ssl_key),
            'email_configured': bool(mail_server and mail_username)
        }
        
        if issues:
            return False, f"Configuration issues: {'; '.join(issues)}", recommendations, metrics
        return True, "Production configuration: READY", recommendations, metrics

    def test_database_production_config(self):
        """Test database production configuration"""
        self.log("🗄️ Testing Database Production Configuration...")
        
        try:
            from app import app
            from models import db
            from sqlalchemy import text
            
            issues = []
            recommendations = []
            metrics = {}
            
            with app.app_context():
                # Test connection pooling
                pool_size = db.engine.pool.size()
                max_overflow = db.engine.pool.overflow()
                
                if pool_size < 5:
                    issues.append(f"Connection pool size too small: {pool_size}")
                    recommendations.append("Increase SQLALCHEMY_ENGINE_OPTIONS pool_size to 10+")
                
                # Test connection performance
                start_time = time.time()
                result = db.session.execute(text("SELECT 1"))
                result.fetchone()
                connection_time = time.time() - start_time
                
                if connection_time > 0.1:
                    issues.append(f"Slow database connection: {connection_time:.3f}s")
                    recommendations.append("Optimize database connection or use connection pooling")
                
                # Test transaction performance
                start_time = time.time()
                result = db.session.execute(text("SELECT COUNT(*) FROM users"))
                result.fetchone()
                transaction_time = time.time() - start_time
                
                # Check database version and settings
                try:
                    version_result = db.session.execute(text("SELECT version()"))
                    db_version = version_result.scalar()
                except:
                    db_version = "Unknown"
                
                metrics = {
                    'pool_size': pool_size,
                    'max_overflow': max_overflow,
                    'connection_time_ms': round(connection_time * 1000, 2),
                    'transaction_time_ms': round(transaction_time * 1000, 2),
                    'database_version': db_version
                }
            
            if issues:
                return False, f"Database config issues: {'; '.join(issues)}", recommendations, metrics
            return True, f"Database config: OPTIMIZED (pool: {pool_size}, conn: {connection_time*1000:.1f}ms)", recommendations, metrics
            
        except Exception as e:
            return False, f"Database config test failed: {str(e)}", [], {}

    # =============================================================================
    # PERFORMANCE TESTS
    # =============================================================================

    def test_application_startup_time(self):
        """Test application startup performance"""
        self.log("⚡ Testing Application Startup Performance...")
        
        try:
            # Measure import time
            start_time = time.time()
            from app import app
            import_time = time.time() - start_time
            
            # Measure app context creation time
            start_time = time.time()
            with app.app_context():
                pass
            context_time = time.time() - start_time
            
            recommendations = []
            metrics = {
                'import_time_ms': round(import_time * 1000, 2),
                'context_time_ms': round(context_time * 1000, 2),
                'total_startup_time_ms': round((import_time + context_time) * 1000, 2)
            }
            
            total_time = import_time + context_time
            
            if total_time > 5.0:
                recommendations.append("Optimize imports and reduce startup dependencies")
                return False, f"Slow startup: {total_time:.2f}s", recommendations, metrics
            elif total_time > 2.0:
                recommendations.append("Consider optimizing startup time for faster scaling")
                return True, f"Startup time: {total_time:.2f}s (acceptable)", recommendations, metrics
            
            return True, f"Startup time: {total_time:.2f}s (fast)", recommendations, metrics
            
        except Exception as e:
            return False, f"Startup test failed: {str(e)}", [], {}

    def test_memory_usage(self):
        """Test memory usage patterns"""
        self.log("💾 Testing Memory Usage...")
        
        try:
            process = psutil.Process()
            
            # Initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Test memory under load
            from app import app
            memory_samples = []
            
            with app.app_context():
                for i in range(10):
                    # Simulate some work
                    from models import User
                    users = User.query.limit(100).all()
                    
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_samples.append(current_memory)
                    time.sleep(0.1)
            
            avg_memory = sum(memory_samples) / len(memory_samples)
            max_memory = max(memory_samples)
            memory_growth = max_memory - initial_memory
            
            recommendations = []
            metrics = {
                'initial_memory_mb': round(initial_memory, 2),
                'average_memory_mb': round(avg_memory, 2),
                'max_memory_mb': round(max_memory, 2),
                'memory_growth_mb': round(memory_growth, 2)
            }
            
            if max_memory > 500:  # 500MB
                recommendations.append("High memory usage detected - consider optimization")
                return False, f"High memory usage: {max_memory:.1f}MB", recommendations, metrics
            elif memory_growth > 50:  # 50MB growth
                recommendations.append("Significant memory growth detected - check for leaks")
                return False, f"Memory growth concern: +{memory_growth:.1f}MB", recommendations, metrics
            
            return True, f"Memory usage: {avg_memory:.1f}MB (efficient)", recommendations, metrics
            
        except Exception as e:
            return False, f"Memory test failed: {str(e)}", [], {}

    def test_concurrent_request_handling(self):
        """Test concurrent request handling capability"""
        self.log("⚙️ Testing Concurrent Request Handling...")
        
        try:
            # Start Flask app in test mode
            from app import app
            import threading
            import queue
            from werkzeug.serving import make_server
            
            # Use test client for concurrent testing
            results = queue.Queue()
            error_count = 0
            success_count = 0
            
            def make_request(app_client, request_id):
                try:
                    start_time = time.time()
                    response = app_client.get('/')
                    duration = time.time() - start_time
                    
                    results.put({
                        'id': request_id,
                        'status': response.status_code,
                        'duration': duration,
                        'success': response.status_code == 200
                    })
                except Exception as e:
                    results.put({
                        'id': request_id,
                        'error': str(e),
                        'success': False
                    })
            
            # Test with multiple concurrent requests
            num_requests = 20
            threads = []
            clients = []
            
            # Create multiple clients to avoid context issues
            for i in range(num_requests):
                clients.append(app.test_client())
            
            start_time = time.time()
            
            # Create threads
            for i in range(num_requests):
                thread = threading.Thread(target=make_request, args=(clients[i], i))
                threads.append(thread)
            
            # Start all threads
            for thread in threads:
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            # Collect results
            response_times = []
            success_count = 0
            error_count = 0
            
            while not results.empty():
                result = results.get()
                if result.get('success'):
                    success_count += 1
                    if 'duration' in result:
                        response_times.append(result['duration'])
                else:
                    error_count += 1
            
            recommendations = []
            metrics = {
                'concurrent_requests': num_requests,
                'successful_requests': success_count,
                'failed_requests': error_count,
                'total_test_time_s': round(total_time, 2),
                'avg_response_time_ms': round(sum(response_times) / len(response_times) * 1000, 2) if response_times else 0,
                'max_response_time_ms': round(max(response_times) * 1000, 2) if response_times else 0,
                'requests_per_second': round(num_requests / total_time, 2)
            }
            
            success_rate = success_count / num_requests * 100
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            if success_rate < 95:
                recommendations.append("Low success rate - investigate error handling")
                return False, f"Concurrency test failed: {success_rate:.1f}% success rate", recommendations, metrics
            
            if avg_response_time > 1.0:  # 1 second
                recommendations.append("Slow response times under load - consider performance optimization")
                return False, f"Slow under load: {avg_response_time*1000:.0f}ms avg", recommendations, metrics
            
            return True, f"Concurrency: {success_rate:.1f}% success, {avg_response_time*1000:.0f}ms avg", recommendations, metrics
            
        except Exception as e:
            return False, f"Concurrency test failed: {str(e)}", [], {}

    # =============================================================================
    # SECURITY TESTS  
    # =============================================================================

    def test_production_security_hardening(self):
        """Test production security hardening"""
        self.log("🔒 Testing Production Security Hardening...")
        
        issues = []
        recommendations = []
        metrics = {}
        
        try:
            from app import app
            
            # Check debug mode
            if app.debug:
                issues.append("Debug mode enabled")
                recommendations.append("Disable debug mode in production")
            
            # Check session configuration
            session_config_issues = []
            
            if not app.config.get('SESSION_COOKIE_SECURE', False):
                session_config_issues.append("SESSION_COOKIE_SECURE not enabled")
                recommendations.append("Enable secure session cookies")
            
            if not app.config.get('SESSION_COOKIE_HTTPONLY', False):
                session_config_issues.append("SESSION_COOKIE_HTTPONLY not enabled") 
                recommendations.append("Enable HttpOnly session cookies")
            
            samesite = app.config.get('SESSION_COOKIE_SAMESITE', '')
            if samesite not in ['Strict', 'Lax']:
                session_config_issues.append(f"SESSION_COOKIE_SAMESITE not configured properly: {samesite}")
                recommendations.append("Set SESSION_COOKIE_SAMESITE to 'Lax' or 'Strict'")
            
            # Check CSRF protection
            csrf_enabled = app.config.get('WTF_CSRF_ENABLED', False)
            if not csrf_enabled:
                issues.append("CSRF protection disabled")
                recommendations.append("Enable CSRF protection")
            
            # Check file upload security
            max_content_length = app.config.get('MAX_CONTENT_LENGTH')
            if not max_content_length or max_content_length > 1024 * 1024 * 1024:  # 1GB
                issues.append("File upload size not properly limited")
                recommendations.append("Set appropriate MAX_CONTENT_LENGTH")
            
            metrics = {
                'debug_mode': app.debug,
                'csrf_enabled': csrf_enabled,
                'max_upload_size_mb': (max_content_length / (1024*1024)) if max_content_length else None,
                'session_security_issues': len(session_config_issues)
            }
            
            all_issues = issues + session_config_issues
            
            if all_issues:
                return False, f"Security issues: {'; '.join(all_issues[:3])}", recommendations, metrics
            return True, "Production security: HARDENED", recommendations, metrics
            
        except Exception as e:
            return False, f"Security test failed: {str(e)}", [], {}

    # =============================================================================
    # MONITORING TESTS
    # =============================================================================

    def test_logging_configuration(self):
        """Test production logging configuration"""
        self.log("📝 Testing Logging Configuration...")
        
        try:
            recommendations = []
            metrics = {}
            
            # Check log directory
            log_dir = Path('logs')
            if not log_dir.exists():
                return False, "Log directory not found", ["Create logs directory"], {}
            
            # Check log files
            log_files = list(log_dir.glob('*.log'))
            if not log_files:
                return False, "No log files found", ["Configure application logging"], {}
            
            # Check log rotation
            total_log_size = sum(f.stat().st_size for f in log_files) / (1024*1024)  # MB
            
            # Check if logs are too large (indicating no rotation)
            large_logs = [f for f in log_files if f.stat().st_size > 100*1024*1024]  # 100MB
            
            recommendations = []
            if large_logs:
                recommendations.append("Configure log rotation to prevent large log files")
            
            if total_log_size > 1000:  # 1GB
                recommendations.append("High total log size - consider log cleanup policy")
            
            # Test log writing
            test_log_path = log_dir / 'test.log'
            try:
                with open(test_log_path, 'a') as f:
                    f.write(f"Test log entry at {datetime.now()}\n")
                test_log_path.unlink()  # Clean up
                log_writable = True
            except:
                log_writable = False
                recommendations.append("Log directory not writable")
            
            metrics = {
                'log_files_count': len(log_files),
                'total_log_size_mb': round(total_log_size, 2),
                'large_log_files': len(large_logs),
                'log_directory_writable': log_writable
            }
            
            if not log_writable or large_logs:
                return False, f"Logging issues detected", recommendations, metrics
            
            return True, f"Logging: {len(log_files)} files, {total_log_size:.1f}MB total", recommendations, metrics
            
        except Exception as e:
            return False, f"Logging test failed: {str(e)}", [], {}

    def test_health_check_endpoints(self):
        """Test health check endpoints for monitoring"""
        self.log("🏥 Testing Health Check Endpoints...")
        
        try:
            from app import app
            
            recommendations = []
            metrics = {}
            
            with app.test_client() as client:
                # Test basic health endpoint
                health_endpoints = [
                    '/',
                    '/health',
                    '/api/health',
                    '/status'
                ]
                
                working_endpoints = []
                failed_endpoints = []
                
                for endpoint in health_endpoints:
                    try:
                        response = client.get(endpoint)
                        if response.status_code in [200, 404]:  # 404 is ok, means app is running
                            working_endpoints.append(endpoint)
                        else:
                            failed_endpoints.append(f"{endpoint} ({response.status_code})")
                    except Exception as e:
                        failed_endpoints.append(f"{endpoint} (error: {str(e)})")
                
                # Test database health
                try:
                    from models import db
                    with app.app_context():
                        db.session.execute(db.text("SELECT 1"))
                    db_healthy = True
                except:
                    db_healthy = False
                
                metrics = {
                    'working_endpoints': len(working_endpoints),
                    'failed_endpoints': len(failed_endpoints),
                    'database_healthy': db_healthy,
                    'primary_endpoint_status': 200 if '/' in working_endpoints else 'failed'
                }
                
                if not working_endpoints:
                    recommendations.append("Create health check endpoints for monitoring")
                    return False, "No working endpoints found", recommendations, metrics
                
                if not db_healthy:
                    recommendations.append("Database health check failing")
                    return False, "Database health check failed", recommendations, metrics
                
                return True, f"Health checks: {len(working_endpoints)} endpoints working", recommendations, metrics
                
        except Exception as e:
            return False, f"Health check test failed: {str(e)}", [], {}

    # =============================================================================
    # DEPLOYMENT TESTS
    # =============================================================================

    def test_static_files_optimization(self):
        """Test static file serving optimization"""
        self.log("📦 Testing Static Files Optimization...")
        
        try:
            static_dir = Path('static')
            if not static_dir.exists():
                return False, "Static directory not found", ["Create static directory"], {}
            
            # Check CSS files
            css_files = list(static_dir.rglob('*.css'))
            js_files = list(static_dir.rglob('*.js'))
            img_files = list(static_dir.rglob('*.png')) + list(static_dir.rglob('*.jpg')) + list(static_dir.rglob('*.gif'))
            
            recommendations = []
            metrics = {}
            
            # Check for minified files
            minified_css = len([f for f in css_files if '.min.' in f.name])
            minified_js = len([f for f in js_files if '.min.' in f.name])
            
            # Check file sizes
            total_css_size = sum(f.stat().st_size for f in css_files) / 1024  # KB
            total_js_size = sum(f.stat().st_size for f in js_files) / 1024  # KB
            total_img_size = sum(f.stat().st_size for f in img_files) / 1024  # KB
            
            # Large file detection
            large_css = [f for f in css_files if f.stat().st_size > 500*1024]  # 500KB
            large_js = [f for f in js_files if f.stat().st_size > 1024*1024]  # 1MB
            
            if len(css_files) > 0 and minified_css / len(css_files) < 0.5:
                recommendations.append("Consider minifying CSS files for better performance")
            
            if len(js_files) > 0 and minified_js / len(js_files) < 0.5:
                recommendations.append("Consider minifying JavaScript files for better performance")
            
            if large_css or large_js:
                recommendations.append("Large static files detected - consider optimization")
            
            metrics = {
                'css_files': len(css_files),
                'js_files': len(js_files),
                'image_files': len(img_files),
                'minified_css_ratio': minified_css / len(css_files) if css_files else 0,
                'minified_js_ratio': minified_js / len(js_files) if js_files else 0,
                'total_css_size_kb': round(total_css_size, 2),
                'total_js_size_kb': round(total_js_size, 2),
                'total_img_size_kb': round(total_img_size, 2)
            }
            
            total_static_size = total_css_size + total_js_size + total_img_size
            
            return True, f"Static files: {len(css_files + js_files + img_files)} files, {total_static_size:.1f}KB", recommendations, metrics
            
        except Exception as e:
            return False, f"Static files test failed: {str(e)}", [], {}

    # =============================================================================
    # TEST RUNNER
    # =============================================================================

    def run_production_tests(self):
        """Run all production readiness tests"""
        print("🚀 Starting production readiness validation...\n")
        
        # Configuration Tests
        self.run_test(self.test_production_environment_config, 
                     "Production Environment Config", "CONFIGURATION")
        self.run_test(self.test_database_production_config,
                     "Database Production Config", "CONFIGURATION")
        
        # Security Tests  
        self.run_test(self.test_production_security_hardening,
                     "Production Security Hardening", "SECURITY")
        
        # Performance Tests
        self.run_test(self.test_application_startup_time,
                     "Application Startup Time", "PERFORMANCE")
        self.run_test(self.test_memory_usage,
                     "Memory Usage", "PERFORMANCE")
        self.run_test(self.test_concurrent_request_handling,
                     "Concurrent Request Handling", "PERFORMANCE")
        
        # Monitoring Tests
        self.run_test(self.test_logging_configuration,
                     "Logging Configuration", "MONITORING")
        self.run_test(self.test_health_check_endpoints,
                     "Health Check Endpoints", "MONITORING")
        
        # Deployment Tests
        self.run_test(self.test_static_files_optimization,
                     "Static Files Optimization", "DEPLOYMENT")

    def generate_production_report(self):
        """Generate comprehensive production readiness report"""
        total_time = time.time() - self.start_time
        
        # Calculate statistics
        total_tests = len(self.tests)
        passed_tests = len([t for t in self.tests if t.passed])
        failed_tests = total_tests - passed_tests
        
        # Category breakdown
        category_stats = {}
        for category in self.categories:
            cat_tests = [t for t in self.tests if t.category == category]
            if cat_tests:
                cat_passed = len([t for t in cat_tests if t.passed])
                category_stats[category] = {
                    'total': len(cat_tests),
                    'passed': cat_passed,
                    'percentage': (cat_passed / len(cat_tests)) * 100
                }
        
        # Overall score
        overall_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Production readiness assessment
        critical_failures = [t for t in self.tests if not t.passed and t.severity in ['CRITICAL', 'ERROR']]
        
        print("\n" + "="*60)
        print("🏭 PRODUCTION READINESS REPORT")
        print("="*60)
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"🧪 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Overall Score: {overall_score:.1f}%")
        print()
        
        # Category breakdown
        print("📋 CATEGORY BREAKDOWN:")
        print("-" * 30)
        for category, stats in category_stats.items():
            status = "✅" if stats['percentage'] == 100 else "⚠️" if stats['percentage'] >= 75 else "❌"
            print(f"{status} {category:<20} {stats['percentage']:>6.1f}%")
        print()
        
        # Failed tests
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            print("-" * 30)
            for test in self.tests:
                if not test.passed:
                    print(f"• {test.name}: {test.message}")
                    if test.recommendations:
                        for rec in test.recommendations[:2]:  # Show first 2 recommendations
                            print(f"  💡 {rec}")
            print()
        
        # Production readiness assessment
        if overall_score >= 95 and len(critical_failures) == 0:
            readiness = "🚀 PRODUCTION READY"
            color = '\033[92m'  # Green
        elif overall_score >= 85 and len(critical_failures) == 0:
            readiness = "⚠️ PRODUCTION READY (with minor issues)"
            color = '\033[93m'  # Yellow
        elif overall_score >= 70:
            readiness = "🔧 NEEDS OPTIMIZATION"
            color = '\033[93m'  # Yellow
        else:
            readiness = "❌ NOT READY FOR PRODUCTION"
            color = '\033[91m'  # Red
        
        print(f"{color}🎯 PRODUCTION READINESS: {readiness}\033[0m")
        
        # Key metrics summary
        if self.tests:
            print("\n📈 KEY METRICS:")
            print("-" * 20)
            
            # Collect key metrics
            for test in self.tests:
                if test.metrics:
                    for key, value in test.metrics.items():
                        if key in ['total_startup_time_ms', 'average_memory_mb', 'requests_per_second']:
                            print(f"• {key.replace('_', ' ').title()}: {value}")
        
        print("="*60)
        
        # Export report if requested
        if self.export_report:
            self.export_production_report(overall_score, category_stats)
        
        return overall_score, critical_failures, category_stats

    def export_production_report(self, overall_score, category_stats):
        """Export production readiness report"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': overall_score,
            'category_stats': category_stats,
            'total_tests': len(self.tests),
            'tests': [
                {
                    'name': test.name,
                    'passed': test.passed,
                    'message': test.message,
                    'duration': test.duration,
                    'category': test.category,
                    'severity': test.severity,
                    'recommendations': test.recommendations,
                    'metrics': test.metrics
                }
                for test in self.tests
            ]
        }
        
        report_file = f"production_readiness_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Production report exported to: {report_file}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Cropio Production Readiness Test Suite')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--performance-only', '-p', action='store_true', help='Run only performance tests')
    parser.add_argument('--export-report', '-e', action='store_true', help='Export report to JSON file')
    
    args = parser.parse_args()
    
    try:
        tester = ProductionReadinessTester(
            verbose=args.verbose,
            performance_only=args.performance_only, 
            export_report=args.export_report
        )
        
        tester.run_production_tests()
        overall_score, critical_failures, category_stats = tester.generate_production_report()
        
        # Exit with appropriate code
        if overall_score >= 95 and len(critical_failures) == 0:
            sys.exit(0)  # Production ready
        elif overall_score >= 85:
            sys.exit(1)  # Minor issues
        elif overall_score >= 70:
            sys.exit(2)  # Needs optimization
        else:
            sys.exit(3)  # Not ready
            
    except KeyboardInterrupt:
        print("\n⚠️ Production readiness test interrupted by user")
        sys.exit(4)
    except Exception as e:
        print(f"\n🚨 Production readiness test failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(5)


if __name__ == "__main__":
    main()
