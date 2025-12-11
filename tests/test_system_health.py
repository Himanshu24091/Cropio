#!/usr/bin/env python3
"""
Comprehensive System Health Test Suite for Cropio
==================================================
Production-level automated testing for system health, security, and functionality.

Usage:
    python test_system_health.py
    python test_system_health.py --verbose
    python test_system_health.py --security-only
"""

import os
import sys
import time
import json
import traceback
import subprocess
import importlib
import threading
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    duration: float
    severity: str = "INFO"  # INFO, WARNING, ERROR, CRITICAL
    category: str = "GENERAL"

class SystemHealthTester:
    """Comprehensive system health testing suite"""
    
    def __init__(self, verbose: bool = False, security_only: bool = False):
        self.verbose = verbose
        self.security_only = security_only
        self.results: List[TestResult] = []
        self.start_time = time.time()
        
        # Test categories
        self.categories = {
            'DEPENDENCIES': [],
            'ENVIRONMENT': [],
            'DATABASE': [],
            'SECURITY': [],
            'FUNCTIONALITY': [],
            'PERFORMANCE': [],
            'CONFIGURATION': []
        }
        
        print("🧪 CROPIO SYSTEM HEALTH TEST SUITE")
        print("=" * 50)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Verbose mode: {'ON' if verbose else 'OFF'}")
        print(f"🔒 Security only: {'ON' if security_only else 'OFF'}")
        print()

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        if self.verbose or level in ["WARNING", "ERROR", "CRITICAL"]:
            timestamp = datetime.now().strftime('%H:%M:%S')
            colors = {
                'INFO': '\033[92m',     # Green
                'WARNING': '\033[93m',  # Yellow
                'ERROR': '\033[91m',    # Red
                'CRITICAL': '\033[95m', # Magenta
                'RESET': '\033[0m'      # Reset
            }
            color = colors.get(level, colors['INFO'])
            print(f"{color}[{timestamp}] {level}: {message}{colors['RESET']}")

    def add_result(self, name: str, passed: bool, message: str, 
                   duration: float = 0.0, severity: str = "INFO", 
                   category: str = "GENERAL"):
        """Add test result"""
        result = TestResult(name, passed, message, duration, severity, category)
        self.results.append(result)
        self.categories[category].append(result)
        
        # Log result
        status = "✅ PASS" if passed else "❌ FAIL"
        self.log(f"{status} {name}: {message}", 
                "INFO" if passed else severity)

    def run_test(self, test_func, name: str, category: str = "GENERAL"):
        """Run individual test with error handling"""
        if self.security_only and category != 'SECURITY':
            return
            
        start_time = time.time()
        try:
            result = test_func()
            duration = time.time() - start_time
            
            if isinstance(result, tuple):
                passed, message = result
            else:
                passed, message = result, "Test completed"
                
            self.add_result(name, passed, message, duration, 
                          "INFO" if passed else "ERROR", category)
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Test failed with exception: {str(e)}"
            if self.verbose:
                error_msg += f"\n{traceback.format_exc()}"
            self.add_result(name, False, error_msg, duration, "ERROR", category)

    # =============================================================================
    # DEPENDENCY TESTS
    # =============================================================================

    def test_python_version(self):
        """Test Python version compatibility"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 8:
            return True, f"Python {version.major}.{version.minor}.{version.micro} (Compatible)"
        else:
            return False, f"Python {version.major}.{version.minor}.{version.micro} (Requires 3.8+)"

    def test_critical_dependencies(self):
        """Test all critical dependencies"""
        required_modules = {
            'flask': 'Flask web framework',
            'sqlalchemy': 'Database ORM',
            'PIL': 'Image processing (Pillow)',
            'werkzeug': 'WSGI utilities',
            'jinja2': 'Template engine',
            'wtforms': 'Form handling',
            'flask_sqlalchemy': 'Flask SQLAlchemy integration',
            'flask_login': 'Authentication',
            'flask_migrate': 'Database migrations',
            'bcrypt': 'Password hashing',
            'dotenv': 'Environment variables (python-dotenv)'
        }
        
        missing_modules = []
        for module, description in required_modules.items():
            try:
                importlib.import_module(module)
                self.log(f"✓ {module} - {description}")
            except ImportError:
                missing_modules.append(f"{module} ({description})")
        
        if missing_modules:
            return False, f"Missing critical modules: {', '.join(missing_modules)}"
        return True, f"All {len(required_modules)} critical dependencies available"

    def test_optional_dependencies(self):
        """Test optional dependencies for specific features"""
        optional_modules = {
            'rawpy': 'RAW image processing',
            'pillow_heif': 'HEIC image support',
            'weasyprint': 'HTML to PDF conversion',
            'selenium': 'Web automation',
            'opencv': 'Advanced image processing',
            'pandas': 'Data processing',
            'pymupdf': 'PDF processing',
            'reportlab': 'PDF generation'
        }
        
        available = []
        missing = []
        
        for module, description in optional_modules.items():
            try:
                if module == 'opencv':
                    importlib.import_module('cv2')
                elif module == 'pymupdf':
                    importlib.import_module('fitz')
                else:
                    importlib.import_module(module)
                available.append(f"{module} ({description})")
            except ImportError:
                missing.append(f"{module} ({description})")
        
        message = f"Available: {len(available)}/{len(optional_modules)} optional features"
        if missing and self.verbose:
            message += f" | Missing: {', '.join(missing)}"
        
        return len(missing) < len(optional_modules) // 2, message

    # =============================================================================
    # ENVIRONMENT TESTS
    # =============================================================================

    def test_environment_loading(self):
        """Test environment variable loading"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            return True, "Environment variables loaded successfully"
        except Exception as e:
            return False, f"Failed to load environment: {str(e)}"

    def test_critical_env_vars(self):
        """Test critical environment variables"""
        critical_vars = [
            'SECRET_KEY',
            'FLASK_SECRET_KEY', 
            'DATABASE_URL'
        ]
        
        missing_vars = []
        for var in critical_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            return False, f"Missing critical environment variables: {', '.join(missing_vars)}"
        return True, f"All {len(critical_vars)} critical environment variables set"

    def test_secret_key_strength(self):
        """Test secret key strength"""
        secret_key = os.getenv('SECRET_KEY') or os.getenv('FLASK_SECRET_KEY')
        if not secret_key:
            return False, "No secret key found"
        
        if len(secret_key) < 32:
            return False, f"Secret key too short: {len(secret_key)} chars (minimum 32)"
        
        if secret_key in ['dev', 'development', 'test', 'secret']:
            return False, "Secret key appears to be default/weak value"
        
        return True, f"Secret key strength: GOOD ({len(secret_key)} chars)"

    def test_file_permissions(self):
        """Test file and directory permissions"""
        issues = []
        
        # Check .env file
        env_file = Path('.env')
        if env_file.exists():
            # This is simplified for Windows - in production you'd check actual permissions
            if env_file.stat().st_size > 0:
                self.log("✓ .env file exists and has content")
            else:
                issues.append(".env file is empty")
        else:
            issues.append(".env file missing")
        
        # Check upload directories
        directories = ['uploads', 'outputs', 'compressed', 'logs']
        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                issues.append(f"Directory {directory} missing")
            elif not os.access(dir_path, os.W_OK):
                issues.append(f"Directory {directory} not writable")
        
        if issues:
            return False, f"File permission issues: {'; '.join(issues)}"
        return True, "File permissions: OK"

    # =============================================================================
    # DATABASE TESTS
    # =============================================================================

    def test_database_connection(self):
        """Test database connectivity"""
        try:
            from app import app
            from models import db
            
            with app.app_context():
                # Test basic connection
                with db.engine.connect() as connection:
                    result = connection.execute(db.text("SELECT 1"))
                    result.fetchone()
                return True, "Database connection: SUCCESSFUL"
                
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

    def test_database_tables(self):
        """Test database table structure"""
        try:
            from app import app
            from models import db, User, ConversionHistory, UsageTracking, UserSession
            from sqlalchemy import inspect
            
            with app.app_context():
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                
                expected_tables = ['users', 'conversion_history', 'usage_tracking', 'user_sessions', 'user_roles', 'system_settings']
                missing_tables = [table for table in expected_tables if table not in tables]
                
                if missing_tables:
                    return False, f"Missing database tables: {', '.join(missing_tables)}"
                
                return True, f"Database tables: {len(tables)} tables found, all required tables present"
                
        except Exception as e:
            return False, f"Database table check failed: {str(e)}"

    def test_database_operations(self):
        """Test basic database operations"""
        try:
            from app import app
            from models import db, User
            
            with app.app_context():
                # Test query
                user_count = User.query.count()
                
                # Test transaction
                test_user = User(
                    username=f"test_user_{int(time.time())}",
                    email=f"test_{int(time.time())}@test.com"
                )
                test_user.set_password("test_password")
                
                db.session.add(test_user)
                db.session.commit()
                
                # Clean up
                db.session.delete(test_user)
                db.session.commit()
                
                return True, f"Database operations: OK (Current users: {user_count})"
                
        except Exception as e:
            return False, f"Database operations failed: {str(e)}"

    def test_migrations(self):
        """Test migration system"""
        try:
            migrations_dir = Path('migrations')
            if not migrations_dir.exists():
                return False, "Migrations directory not found"
            
            # Check for migration files
            versions_dir = migrations_dir / 'versions'
            if versions_dir.exists():
                migration_files = list(versions_dir.glob('*.py'))
                status = f"Migration system: OK ({len(migration_files)} migration files)"
            else:
                status = "Migration system: Initialized but no migrations yet"
            
            return True, status
            
        except Exception as e:
            return False, f"Migration check failed: {str(e)}"

    # =============================================================================
    # SECURITY TESTS
    # =============================================================================

    def test_csrf_protection(self):
        """Test CSRF protection configuration"""
        try:
            from app import app
            
            csrf_enabled = app.config.get('WTF_CSRF_ENABLED', False)
            if not csrf_enabled:
                return False, "CSRF protection is disabled"
            
            csrf_timeout = app.config.get('WTF_CSRF_TIME_LIMIT', 3600)
            if csrf_timeout is not None and csrf_timeout > 86400:  # 24 hours
                return False, f"CSRF timeout too long: {csrf_timeout} seconds"
            
            timeout_str = f"{csrf_timeout}s" if csrf_timeout is not None else "None (no timeout)"
            return True, f"CSRF protection: ENABLED (timeout: {timeout_str})"
            
        except Exception as e:
            return False, f"CSRF check failed: {str(e)}"

    def test_session_security(self):
        """Test session security configuration"""
        try:
            from app import app
            
            issues = []
            
            # Check session cookie security
            if not app.config.get('SESSION_COOKIE_HTTPONLY', True):
                issues.append("HttpOnly cookies not enabled")
            
            if not app.config.get('SESSION_COOKIE_SECURE', False) and os.getenv('FLASK_ENV') == 'production':
                issues.append("Secure cookies not enabled in production")
            
            samesite = app.config.get('SESSION_COOKIE_SAMESITE', 'Lax')
            if samesite not in ['Strict', 'Lax']:
                issues.append(f"SameSite policy not secure: {samesite}")
            
            if issues:
                return False, f"Session security issues: {'; '.join(issues)}"
            
            return True, "Session security: CONFIGURED"
            
        except Exception as e:
            return False, f"Session security check failed: {str(e)}"

    def test_password_security(self):
        """Test password hashing and security"""
        try:
            from models import User
            import bcrypt
            
            # Test password hashing (generate secure test password)
            import secrets
            test_password = f"test_password_{secrets.token_hex(8)}"
            user = User()
            user.set_password(test_password)
            
            # Verify hash was created
            if not user.password_hash:
                return False, "Password hashing failed"
            
            # Verify password checking works
            if not user.check_password(test_password):
                return False, "Password verification failed"
            
            # Verify wrong password fails
            if user.check_password("wrong_password"):
                return False, "Password verification not working correctly"
            
            return True, "Password security: SECURE (bcrypt hashing)"
            
        except Exception as e:
            return False, f"Password security check failed: {str(e)}"

    def test_file_upload_security(self):
        """Test file upload security measures"""
        try:
            from config import ALLOWED_CONVERTER_EXTENSIONS
            from utils.helpers import allowed_file
            
            # Test that dangerous extensions are blocked
            dangerous_extensions = ['exe', 'bat', 'cmd', 'sh', 'php', 'asp', 'js']
            
            for ext in dangerous_extensions:
                if allowed_file(f"test.{ext}", ALLOWED_CONVERTER_EXTENSIONS.get('image', set())):
                    return False, f"Dangerous file extension allowed: {ext}"
            
            # Test that safe extensions are allowed
            safe_extensions = ['jpg', 'png', 'pdf', 'docx']
            allowed_count = 0
            for ext in safe_extensions:
                for category, extensions in ALLOWED_CONVERTER_EXTENSIONS.items():
                    if allowed_file(f"test.{ext}", extensions):
                        allowed_count += 1
                        break
            
            if allowed_count == 0:
                return False, "No safe file extensions are allowed"
            
            return True, f"File upload security: SECURE ({allowed_count}/{len(safe_extensions)} safe extensions allowed)"
            
        except Exception as e:
            return False, f"File upload security check failed: {str(e)}"

    def test_security_headers(self):
        """Test security headers configuration"""
        try:
            from config import BaseConfig
            
            headers = getattr(BaseConfig, 'SECURITY_HEADERS', {})
            
            required_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options', 
                'X-XSS-Protection',
                'Strict-Transport-Security'
            ]
            
            missing_headers = [header for header in required_headers if header not in headers]
            
            if missing_headers:
                return False, f"Missing security headers: {', '.join(missing_headers)}"
            
            return True, f"Security headers: {len(headers)} headers configured"
            
        except Exception as e:
            return False, f"Security headers check failed: {str(e)}"

    # =============================================================================
    # FUNCTIONALITY TESTS
    # =============================================================================

    def test_flask_app_startup(self):
        """Test Flask application startup"""
        try:
            from app import app
            
            # Test app creation
            if not app:
                return False, "Flask app creation failed"
            
            # Test configuration
            if not app.config:
                return False, "Flask app configuration missing"
            
            # Test blueprints
            blueprint_count = len(app.blueprints)
            if blueprint_count < 5:  # Should have multiple blueprints
                return False, f"Too few blueprints registered: {blueprint_count}"
            
            return True, f"Flask application: OK ({blueprint_count} blueprints)"
            
        except Exception as e:
            return False, f"Flask app startup failed: {str(e)}"

    def test_template_rendering(self):
        """Test template rendering system"""
        try:
            from app import app
            
            with app.test_client() as client:
                # Test main page
                response = client.get('/')
                if response.status_code != 200:
                    return False, f"Main page failed: HTTP {response.status_code}"
                
                # Check if response contains expected content
                if b'Cropio' not in response.data and b'converter' not in response.data.lower():
                    return False, "Main page content appears incorrect"
                
                return True, "Template rendering: OK"
                
        except Exception as e:
            return False, f"Template rendering failed: {str(e)}"

    def test_static_files(self):
        """Test static file serving"""
        try:
            from app import app
            
            static_folder = Path(app.static_folder)
            if not static_folder.exists():
                return False, "Static folder not found"
            
            # Count static files
            css_files = list(static_folder.glob('**/*.css'))
            js_files = list(static_folder.glob('**/*.js'))
            
            if len(css_files) == 0:
                return False, "No CSS files found"
            
            if len(js_files) == 0:
                return False, "No JavaScript files found"
            
            return True, f"Static files: OK ({len(css_files)} CSS, {len(js_files)} JS)"
            
        except Exception as e:
            return False, f"Static files check failed: {str(e)}"

    def test_file_processing_imports(self):
        """Test file processing module imports"""
        processing_modules = [
            'utils.helpers',
            'utils.image.raw_processor',
            'utils.image.heic_processor', 
            'utils.video.gif_mp4_processor',
            'utils.web_code.yaml_processor'
        ]
        
        available_modules = []
        failed_modules = []
        
        for module in processing_modules:
            try:
                importlib.import_module(module)
                available_modules.append(module)
            except ImportError as e:
                failed_modules.append(f"{module} ({str(e)})")
        
        if len(failed_modules) > len(processing_modules) // 2:
            return False, f"Too many processing modules failed: {', '.join(failed_modules)}"
        
        return True, f"Processing modules: {len(available_modules)}/{len(processing_modules)} available"

    # =============================================================================
    # PERFORMANCE TESTS
    # =============================================================================

    def test_memory_usage(self):
        """Test memory usage"""
        try:
            import psutil
            import gc
            
            # Force garbage collection
            gc.collect()
            
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Check if memory usage is reasonable (less than 500MB for basic startup)
            if memory_mb > 500:
                return False, f"High memory usage: {memory_mb:.1f} MB"
            
            return True, f"Memory usage: {memory_mb:.1f} MB (OK)"
            
        except ImportError:
            return True, "Memory test skipped (psutil not available)"
        except Exception as e:
            return False, f"Memory test failed: {str(e)}"

    def test_import_speed(self):
        """Test import speed"""
        start_time = time.time()
        try:
            from app import app
            import_time = time.time() - start_time
            
            if import_time > 10:  # More than 10 seconds is too slow
                return False, f"Slow imports: {import_time:.2f} seconds"
            
            return True, f"Import speed: {import_time:.2f} seconds (OK)"
            
        except Exception as e:
            return False, f"Import speed test failed: {str(e)}"

    # =============================================================================
    # CONFIGURATION TESTS
    # =============================================================================

    def test_gitignore_security(self):
        """Test .gitignore for security"""
        try:
            gitignore_path = Path('.gitignore')
            if not gitignore_path.exists():
                return False, ".gitignore file not found"
            
            content = gitignore_path.read_text()
            
            required_patterns = ['.env', '*.log', '__pycache__', 'uploads/', '*.db']
            missing_patterns = []
            
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)
            
            if missing_patterns:
                return False, f"Missing .gitignore patterns: {', '.join(missing_patterns)}"
            
            return True, f".gitignore security: OK ({len(required_patterns)} patterns found)"
            
        except Exception as e:
            return False, f".gitignore check failed: {str(e)}"

    def test_logging_configuration(self):
        """Test logging configuration"""
        try:
            from core.logging_config import cropio_logger
            
            # Test logger exists and is configured
            if not cropio_logger:
                return False, "Logger not configured"
            
            # Test log directory
            log_dir = Path('logs')
            if not log_dir.exists():
                return False, "Log directory not found"
            
            # Test log files
            log_files = list(log_dir.glob('*.log'))
            
            return True, f"Logging: OK ({len(log_files)} log files)"
            
        except Exception as e:
            return False, f"Logging check failed: {str(e)}"

    # =============================================================================
    # TEST RUNNER
    # =============================================================================

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting comprehensive system health tests...\n")
        
        # Dependency tests
        if not self.security_only:
            self.run_test(self.test_python_version, "Python Version Check", "DEPENDENCIES")
            self.run_test(self.test_critical_dependencies, "Critical Dependencies", "DEPENDENCIES")
            self.run_test(self.test_optional_dependencies, "Optional Dependencies", "DEPENDENCIES")
        
        # Environment tests
        self.run_test(self.test_environment_loading, "Environment Loading", "ENVIRONMENT")
        self.run_test(self.test_critical_env_vars, "Critical Environment Variables", "ENVIRONMENT")
        self.run_test(self.test_secret_key_strength, "Secret Key Strength", "ENVIRONMENT")
        self.run_test(self.test_file_permissions, "File Permissions", "ENVIRONMENT")
        
        # Database tests
        if not self.security_only:
            self.run_test(self.test_database_connection, "Database Connection", "DATABASE")
            self.run_test(self.test_database_tables, "Database Tables", "DATABASE")
            self.run_test(self.test_database_operations, "Database Operations", "DATABASE")
            self.run_test(self.test_migrations, "Migration System", "DATABASE")
        
        # Security tests
        self.run_test(self.test_csrf_protection, "CSRF Protection", "SECURITY")
        self.run_test(self.test_session_security, "Session Security", "SECURITY")
        self.run_test(self.test_password_security, "Password Security", "SECURITY")
        self.run_test(self.test_file_upload_security, "File Upload Security", "SECURITY")
        self.run_test(self.test_security_headers, "Security Headers", "SECURITY")
        
        # Functionality tests
        if not self.security_only:
            self.run_test(self.test_flask_app_startup, "Flask Application", "FUNCTIONALITY")
            self.run_test(self.test_template_rendering, "Template Rendering", "FUNCTIONALITY")
            self.run_test(self.test_static_files, "Static Files", "FUNCTIONALITY")
            self.run_test(self.test_file_processing_imports, "File Processing Modules", "FUNCTIONALITY")
        
        # Performance tests
        if not self.security_only:
            self.run_test(self.test_memory_usage, "Memory Usage", "PERFORMANCE")
            self.run_test(self.test_import_speed, "Import Speed", "PERFORMANCE")
        
        # Configuration tests
        self.run_test(self.test_gitignore_security, "GitIgnore Security", "CONFIGURATION")
        if not self.security_only:
            self.run_test(self.test_logging_configuration, "Logging Configuration", "CONFIGURATION")

    def generate_report(self):
        """Generate comprehensive test report"""
        total_time = time.time() - self.start_time
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        # Calculate scores by category
        category_scores = {}
        for category, results in self.categories.items():
            if results:
                passed = sum(1 for r in results if r.passed)
                category_scores[category] = (passed / len(results)) * 100
        
        # Overall score
        overall_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("📊 SYSTEM HEALTH TEST REPORT")
        print("="*60)
        print(f"⏱️  Total Time: {total_time:.2f} seconds")
        print(f"🧪 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Overall Score: {overall_score:.1f}%")
        print()
        
        # Category breakdown
        print("📋 CATEGORY BREAKDOWN:")
        print("-" * 30)
        for category, score in category_scores.items():
            status_icon = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            print(f"{status_icon} {category:15} {score:5.1f}%")
        print()
        
        # Failed tests details
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            print("-" * 30)
            for result in self.results:
                if not result.passed:
                    print(f"• {result.name}: {result.message}")
            print()
        
        # Critical issues
        critical_issues = [r for r in self.results if not r.passed and r.severity == "CRITICAL"]
        if critical_issues:
            print("🚨 CRITICAL ISSUES:")
            print("-" * 30)
            for issue in critical_issues:
                print(f"• {issue.name}: {issue.message}")
            print()
        
        # Security assessment
        security_results = self.categories.get('SECURITY', [])
        if security_results:
            security_passed = sum(1 for r in security_results if r.passed)
            security_score = (security_passed / len(security_results)) * 100
            security_status = "🔒 SECURE" if security_score >= 90 else "⚠️ NEEDS ATTENTION" if security_score >= 70 else "🚨 VULNERABLE"
            print(f"🛡️  SECURITY STATUS: {security_status} ({security_score:.1f}%)")
            print()
        
        # Production readiness
        if overall_score >= 95:
            readiness = "🚀 PRODUCTION READY"
        elif overall_score >= 85:
            readiness = "⚠️ NEEDS MINOR FIXES"
        elif overall_score >= 70:
            readiness = "🔧 NEEDS MAJOR FIXES"
        else:
            readiness = "❌ NOT PRODUCTION READY"
        
        print(f"🎯 PRODUCTION READINESS: {readiness}")
        print("="*60)
        
        return overall_score, category_scores, failed_tests


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Cropio System Health Test Suite')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--security-only', '-s', action='store_true', help='Run security tests only')
    
    args = parser.parse_args()
    
    try:
        tester = SystemHealthTester(verbose=args.verbose, security_only=args.security_only)
        tester.run_all_tests()
        overall_score, category_scores, failed_tests = tester.generate_report()
        
        # Exit with appropriate code
        if failed_tests == 0:
            sys.exit(0)  # Success
        elif overall_score >= 80:
            sys.exit(1)  # Minor issues
        else:
            sys.exit(2)  # Major issues
            
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"\n🚨 Test suite failed: {str(e)}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(4)


if __name__ == "__main__":
    main()
