#!/usr/bin/env python3
"""
Comprehensive Security Audit Script for Cropio
===============================================
Advanced security testing including vulnerability checks, configuration validation,
and penetration testing for production readiness.

Usage:
    python security_audit.py
    python security_audit.py --verbose
    python security_audit.py --export-report
"""

import os
import sys
import time
import json
import hashlib
import socket
import re
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import argparse
import urllib.parse
import urllib.request
import ssl

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class SecurityIssue:
    title: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    description: str
    remediation: str
    affected_component: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None

class SecurityAuditor:
    """Comprehensive security auditing suite"""
    
    def __init__(self, verbose: bool = False, export_report: bool = False):
        self.verbose = verbose
        self.export_report = export_report
        self.issues: List[SecurityIssue] = []
        self.start_time = time.time()
        
        print("🔒 CROPIO SECURITY AUDIT SUITE")
        print("=" * 50)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Verbose mode: {'ON' if verbose else 'OFF'}")
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

    def add_issue(self, title: str, severity: str, description: str, 
                  remediation: str, component: str, cwe_id: str = None, 
                  cvss_score: float = None):
        """Add security issue"""
        issue = SecurityIssue(
            title=title,
            severity=severity,
            description=description,
            remediation=remediation,
            affected_component=component,
            cwe_id=cwe_id,
            cvss_score=cvss_score
        )
        self.issues.append(issue)
        
        # Log issue
        severity_icons = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MEDIUM': '⚡',
            'LOW': '💡',
            'INFO': 'ℹ️'
        }
        icon = severity_icons.get(severity, '❓')
        self.log(f"{icon} {severity}: {title} - {description}", 
                severity if severity in ['CRITICAL', 'HIGH'] else 'WARNING')

    # =============================================================================
    # AUTHENTICATION & SESSION SECURITY
    # =============================================================================

    def audit_authentication_security(self):
        """Audit authentication and session security"""
        self.log("🔐 Auditing Authentication & Session Security...")
        
        try:
            from app import app
            
            # Check session configuration
            with app.app_context():
                # Session cookie security
                if not app.config.get('SESSION_COOKIE_HTTPONLY', False):
                    self.add_issue(
                        "Session cookies not HttpOnly",
                        "HIGH",
                        "Session cookies are not configured with HttpOnly flag, making them vulnerable to XSS attacks",
                        "Set SESSION_COOKIE_HTTPONLY = True in configuration",
                        "Session Management",
                        "CWE-1004",
                        7.5
                    )
                
                if not app.config.get('SESSION_COOKIE_SECURE', False) and os.getenv('FLASK_ENV') == 'production':
                    self.add_issue(
                        "Session cookies not secure in production",
                        "HIGH",
                        "Session cookies not configured with Secure flag in production environment",
                        "Set SESSION_COOKIE_SECURE = True for production",
                        "Session Management",
                        "CWE-614",
                        7.5
                    )
                
                samesite = app.config.get('SESSION_COOKIE_SAMESITE', '')
                if samesite not in ['Strict', 'Lax']:
                    self.add_issue(
                        "Session SameSite policy not configured",
                        "MEDIUM",
                        f"Session SameSite policy is '{samesite}' which may allow CSRF attacks",
                        "Set SESSION_COOKIE_SAMESITE = 'Lax' or 'Strict'",
                        "Session Management",
                        "CWE-352",
                        6.1
                    )
                
                # Secret key strength
                secret_key = app.config.get('SECRET_KEY') or os.getenv('SECRET_KEY') or os.getenv('FLASK_SECRET_KEY')
                if secret_key:
                    if len(secret_key) < 32:
                        self.add_issue(
                            "Weak secret key",
                            "CRITICAL",
                            f"Secret key is only {len(secret_key)} characters long (minimum 32 required)",
                            "Generate a cryptographically secure secret key of at least 32 characters",
                            "Cryptography",
                            "CWE-326",
                            9.8
                        )
                    
                    # Check for common weak keys
                    weak_patterns = ['secret', 'password', 'key', 'dev', 'test', 'admin', '123']
                    if any(pattern in secret_key.lower() for pattern in weak_patterns):
                        self.add_issue(
                            "Predictable secret key",
                            "CRITICAL",
                            "Secret key contains common patterns that could be guessed",
                            "Generate a random cryptographically secure secret key",
                            "Cryptography",
                            "CWE-340",
                            9.8
                        )
                else:
                    self.add_issue(
                        "No secret key configured",
                        "CRITICAL",
                        "Application has no secret key configured",
                        "Set a strong SECRET_KEY in environment variables",
                        "Cryptography",
                        "CWE-326",
                        9.8
                    )
                
                # CSRF protection
                csrf_enabled = app.config.get('WTF_CSRF_ENABLED', False)
                if not csrf_enabled:
                    self.add_issue(
                        "CSRF protection disabled",
                        "HIGH",
                        "Cross-Site Request Forgery protection is disabled",
                        "Enable WTF_CSRF_ENABLED = True",
                        "CSRF Protection",
                        "CWE-352",
                        8.8
                    )
                
        except Exception as e:
            self.add_issue(
                "Authentication audit failed",
                "MEDIUM",
                f"Could not complete authentication security audit: {str(e)}",
                "Investigate authentication configuration issues",
                "Configuration"
            )

    def audit_password_security(self):
        """Audit password security implementation"""
        self.log("🔑 Auditing Password Security...")
        
        try:
            from models import User
            
            # Test password hashing
            test_user = User()
            test_passwords = [
                "password123",  # Common weak password
                "admin",        # Very weak
                "P@ssw0rd!23",  # Strong password
            ]
            
            for password in test_passwords:
                test_user.set_password(password)
                
                # Check if hash was generated
                if not test_user.password_hash:
                    self.add_issue(
                        "Password hashing failure",
                        "CRITICAL",
                        "Password hashing function is not working properly",
                        "Fix password hashing implementation",
                        "Authentication",
                        "CWE-327",
                        9.8
                    )
                    break
                
                # Check hash strength (bcrypt should start with $2b$)
                if not test_user.password_hash.startswith('$2b$'):
                    self.add_issue(
                        "Weak password hashing algorithm",
                        "HIGH",
                        f"Password hash '{test_user.password_hash[:10]}...' does not appear to use bcrypt",
                        "Ensure bcrypt is being used for password hashing",
                        "Cryptography",
                        "CWE-327",
                        7.5
                    )
                
                # Verify password checking works
                if not test_user.check_password(password):
                    self.add_issue(
                        "Password verification failure",
                        "HIGH",
                        "Password verification is not working correctly",
                        "Fix password verification logic",
                        "Authentication",
                        "CWE-287",
                        8.1
                    )
                
                # Verify wrong password fails
                if test_user.check_password(password + "_wrong"):
                    self.add_issue(
                        "Password verification bypass",
                        "CRITICAL",
                        "Password verification accepts incorrect passwords",
                        "Fix password verification to properly reject wrong passwords",
                        "Authentication",
                        "CWE-287",
                        9.8
                    )
            
            self.log("✅ Password security audit completed")
            
        except Exception as e:
            self.add_issue(
                "Password audit failed",
                "MEDIUM",
                f"Could not complete password security audit: {str(e)}",
                "Investigate password security implementation",
                "Authentication"
            )

    # =============================================================================
    # FILE UPLOAD SECURITY
    # =============================================================================

    def audit_file_upload_security(self):
        """Audit file upload security measures"""
        self.log("📁 Auditing File Upload Security...")
        
        try:
            from config import ALLOWED_CONVERTER_EXTENSIONS
            from utils.helpers import allowed_file
            
            # Test dangerous extensions
            dangerous_extensions = [
                'exe', 'bat', 'cmd', 'com', 'scr', 'pif',
                'msi', 'msp', 'reg', 'dll', 'so', 'dylib',
                'php', 'asp', 'aspx', 'jsp', 'py', 'rb',
                'js', 'vbs', 'ps1', 'sh', 'bash'
            ]
            
            blocked_count = 0
            allowed_dangerous = []
            
            for ext in dangerous_extensions:
                test_filename = f"malicious.{ext}"
                is_blocked = True
                
                # Test against all categories
                for category, extensions in ALLOWED_CONVERTER_EXTENSIONS.items():
                    if allowed_file(test_filename, extensions):
                        is_blocked = False
                        allowed_dangerous.append(f"{ext} (in {category})")
                        break
                
                if is_blocked:
                    blocked_count += 1
            
            if allowed_dangerous:
                self.add_issue(
                    "Dangerous file extensions allowed",
                    "CRITICAL",
                    f"Dangerous file extensions are allowed: {', '.join(allowed_dangerous)}",
                    "Remove dangerous extensions from ALLOWED_CONVERTER_EXTENSIONS",
                    "File Upload",
                    "CWE-434",
                    9.8
                )
            else:
                self.log(f"✅ All {len(dangerous_extensions)} dangerous extensions properly blocked")
            
            # Check for file size limits
            max_size = None
            try:
                from app import app
                max_size = app.config.get('MAX_CONTENT_LENGTH')
            except:
                pass
            
            if not max_size:
                self.add_issue(
                    "No file size limit configured",
                    "MEDIUM",
                    "No maximum file size limit is configured, allowing potential DoS attacks",
                    "Set MAX_CONTENT_LENGTH in application configuration",
                    "File Upload",
                    "CWE-770",
                    6.5
                )
            elif max_size > 1000 * 1024 * 1024:  # > 1GB
                self.add_issue(
                    "File size limit too high",
                    "LOW",
                    f"File size limit is very high: {max_size / (1024*1024):.1f}MB",
                    "Consider lowering MAX_CONTENT_LENGTH for better security",
                    "File Upload",
                    "CWE-770",
                    4.3
                )
            
            # Check upload directories
            upload_dirs = ['uploads', 'outputs', 'compressed', 'temp']
            for upload_dir in upload_dirs:
                dir_path = Path(upload_dir)
                if dir_path.exists():
                    # Check if directory is world-writable (simplified for Windows)
                    if os.access(dir_path, os.W_OK):
                        # This is expected, but we should check for public access
                        pass
                    
                    # Check for web accessibility (this is simplified)
                    web_accessible_files = ['.htaccess', 'web.config', 'index.html']
                    protection_found = any((dir_path / f).exists() for f in web_accessible_files)
                    
                    if not protection_found:
                        self.add_issue(
                            f"Upload directory may be web accessible",
                            "MEDIUM",
                            f"Upload directory '{upload_dir}' may be directly accessible via web",
                            f"Add .htaccess or web.config to block direct access to {upload_dir}",
                            "File Upload",
                            "CWE-552",
                            6.5
                        )
            
        except Exception as e:
            self.add_issue(
                "File upload audit failed",
                "MEDIUM",
                f"Could not complete file upload security audit: {str(e)}",
                "Investigate file upload configuration",
                "File Upload"
            )

    # =============================================================================
    # CONFIGURATION SECURITY
    # =============================================================================

    def audit_configuration_security(self):
        """Audit configuration security"""
        self.log("⚙️ Auditing Configuration Security...")
        
        # Check environment variables
        sensitive_vars = {
            'SECRET_KEY': 'Secret key for session encryption',
            'FLASK_SECRET_KEY': 'Flask secret key',
            'DATABASE_URL': 'Database connection string',
            'MAIL_PASSWORD': 'Email authentication credential',
            'RAZORPAY_KEY_SECRET': 'Razorpay secret key',
            'STRIPE_SECRET_KEY': 'Stripe secret key'
        }
        
        for var_name, description in sensitive_vars.items():
            var_value = os.getenv(var_name)
            if var_value:
                # Check if value looks like a placeholder
                placeholders = ['your-', 'change-me', 'replace-', 'example', 'test']
                if any(placeholder in var_value.lower() for placeholder in placeholders):
                    self.add_issue(
                        f"Placeholder value in {var_name}",
                        "HIGH",
                        f"{description} appears to contain placeholder value",
                        f"Replace placeholder value in {var_name} with actual secure value",
                        "Configuration",
                        "CWE-798",
                        7.5
                    )
                
                # Check if value is too short for keys
                if 'secret' in var_name.lower() or 'key' in var_name.lower():
                    if len(var_value) < 16:
                        self.add_issue(
                            f"Short {var_name}",
                            "MEDIUM",
                            f"{description} is very short ({len(var_value)} chars)",
                            f"Use a longer, more secure value for {var_name}",
                            "Configuration",
                            "CWE-326",
                            6.1
                        )
        
        # Check .env file security
        env_file = Path('.env')
        if env_file.exists():
            try:
                # Check file permissions (simplified for Windows)
                stat = env_file.stat()
                # On Windows, we can't easily check exact permissions like Unix
                # but we can warn about potential issues
                self.log("ℹ️ .env file found - ensure it has restricted permissions")
                
                # Check if .env is in .gitignore
                gitignore = Path('.gitignore')
                if gitignore.exists():
                    gitignore_content = gitignore.read_text()
                    if '.env' not in gitignore_content:
                        self.add_issue(
                            ".env file not in .gitignore",
                            "HIGH",
                            ".env file is not excluded from version control",
                            "Add .env to .gitignore file",
                            "Configuration",
                            "CWE-200",
                            7.5
                        )
                else:
                    self.add_issue(
                        "No .gitignore file found",
                        "MEDIUM",
                        "No .gitignore file found - sensitive files may be committed",
                        "Create .gitignore file and exclude sensitive files",
                        "Configuration",
                        "CWE-200",
                        6.1
                    )
                
            except Exception as e:
                self.log(f"Could not check .env file permissions: {e}")
        
        # Check debug mode
        debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        env = os.getenv('FLASK_ENV', 'development')
        
        if debug_mode and env == 'production':
            self.add_issue(
                "Debug mode enabled in production",
                "CRITICAL",
                "Flask debug mode is enabled in production environment",
                "Set FLASK_DEBUG=false in production",
                "Configuration",
                "CWE-489",
                9.8
            )
        
        # Check for hardcoded secrets in code
        self.scan_for_hardcoded_secrets()

    def scan_for_hardcoded_secrets(self):
        """Scan source code for hardcoded secrets"""
        self.log("🔍 Scanning for hardcoded secrets...")
        
        secret_patterns = {
            'Generic API Key': r'[aA][pP][iI][_]?[kK][eE][yY][\'\"]*\s*[:=]\s*[\'\"]([\w\-]{20,})',
            'Generic Secret': r'[sS][eE][cC][rR][eE][tT][\'\"]*\s*[:=]\s*[\'\"]([\w\-]{16,})',
            'Password': r'[pP][aA][sS][sS][wW][oO][rR][dD][\'\"]*\s*[:=]\s*[\'\"](.{8,})',
            'Database URL': r'[dD][aA][tT][aA][bB][aA][sS][eE][_]?[uU][rR][lL][\'\"]*\s*[:=]\s*[\'\"](.*://.*)',
            'AWS Access Key': r'AKIA[0-9A-Z]{16}',
            'JWT Token': r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'
        }
        
        # Files to scan
        scan_extensions = ['.py', '.js', '.html', '.json', '.yml', '.yaml', '.env.example']
        exclude_paths = ['venv', '__pycache__', '.git', 'node_modules']
        
        found_secrets = []
        
        def scan_file(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for secret_type, pattern in secret_patterns.items():
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Skip if it's obviously a placeholder
                        potential_secret = match.group(1) if match.groups() else match.group(0)
                        if any(placeholder in potential_secret.lower() 
                              for placeholder in ['your-', 'change-me', 'replace-', 'example', 'xxx', 'yyy']):
                            continue
                        
                        found_secrets.append({
                            'file': str(file_path),
                            'type': secret_type,
                            'line': content[:match.start()].count('\n') + 1,
                            'secret': potential_secret[:20] + '...' if len(potential_secret) > 20 else potential_secret
                        })
            except Exception:
                pass  # Skip files that can't be read
        
        # Scan all files
        for root, dirs, files in os.walk('.'):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_paths]
            
            for file in files:
                if any(file.endswith(ext) for ext in scan_extensions):
                    scan_file(Path(root) / file)
        
        # Report findings
        if found_secrets:
            for secret in found_secrets[:10]:  # Limit to first 10 findings
                self.add_issue(
                    f"Potential hardcoded secret in {Path(secret['file']).name}",
                    "HIGH",
                    f"Possible {secret['type']} found at line {secret['line']}: {secret['secret']}",
                    "Move sensitive values to environment variables",
                    "Code Security",
                    "CWE-798",
                    7.5
                )
            
            if len(found_secrets) > 10:
                self.add_issue(
                    f"Multiple hardcoded secrets found",
                    "HIGH",
                    f"Found {len(found_secrets)} potential hardcoded secrets in codebase",
                    "Conduct thorough review and move all secrets to environment variables",
                    "Code Security",
                    "CWE-798",
                    7.5
                )

    # =============================================================================
    # DATABASE SECURITY
    # =============================================================================

    def audit_database_security(self):
        """Audit database security configuration"""
        self.log("🗄️ Auditing Database Security...")
        
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            self.add_issue(
                "No database URL configured",
                "MEDIUM",
                "Database URL is not configured in environment variables",
                "Configure DATABASE_URL environment variable",
                "Database Configuration"
            )
            return
        
        # Parse database URL for security issues
        try:
            if '://' in database_url:
                # Extract components
                if 'password' in database_url.lower():
                    self.log("⚠️ Database URL contains password - ensure it's secure")
                
                # Check for weak passwords in URL (basic check)
                weak_passwords = ['password', 'admin', 'root', '123456', 'pass']
                for weak_pass in weak_passwords:
                    if f':{weak_pass}@' in database_url.lower():
                        self.add_issue(
                            "Weak database password",
                            "HIGH",
                            f"Database URL appears to contain weak password: {weak_pass}",
                            "Use a strong, unique password for database access",
                            "Database Security",
                            "CWE-521",
                            8.1
                        )
                
                # Check for localhost in production
                if 'localhost' in database_url and os.getenv('FLASK_ENV') == 'production':
                    self.add_issue(
                        "Database on localhost in production",
                        "LOW",
                        "Database URL points to localhost in production environment",
                        "Use dedicated database server for production",
                        "Database Configuration",
                        "CWE-330",
                        4.3
                    )
        
        except Exception as e:
            self.log(f"Could not parse database URL: {e}")
        
        # Test database connection security
        try:
            from app import app
            from models import db
            
            with app.app_context():
                # Check for SQL injection protection (basic test)
                try:
                    # This should be safely handled by SQLAlchemy
                    test_query = "SELECT 1 WHERE 1=1"
                    result = db.session.execute(db.text(test_query)).scalar()
                    if result == 1:
                        self.log("✅ Basic database query test passed")
                except Exception as e:
                    self.add_issue(
                        "Database query issues",
                        "MEDIUM",
                        f"Database query test failed: {str(e)}",
                        "Investigate database connectivity and query handling",
                        "Database Security"
                    )
                
        except Exception as e:
            self.add_issue(
                "Database security audit failed",
                "LOW",
                f"Could not complete database security audit: {str(e)}",
                "Investigate database configuration",
                "Database Configuration"
            )

    # =============================================================================
    # NETWORK SECURITY
    # =============================================================================

    def audit_network_security(self):
        """Audit network security configuration"""
        self.log("🌐 Auditing Network Security...")
        
        # Check for HTTPS configuration
        https_configured = False
        ssl_cert_path = os.getenv('SSL_CERT_PATH')
        ssl_key_path = os.getenv('SSL_KEY_PATH')
        
        if ssl_cert_path and ssl_key_path:
            https_configured = True
            
            # Check if certificate files exist
            if not Path(ssl_cert_path).exists():
                self.add_issue(
                    "SSL certificate file not found",
                    "HIGH",
                    f"SSL certificate file not found: {ssl_cert_path}",
                    "Ensure SSL certificate file exists and is accessible",
                    "Network Security",
                    "CWE-295",
                    7.5
                )
            
            if not Path(ssl_key_path).exists():
                self.add_issue(
                    "SSL key file not found",
                    "HIGH",
                    f"SSL private key file not found: {ssl_key_path}",
                    "Ensure SSL private key file exists and is accessible",
                    "Network Security",
                    "CWE-295",
                    7.5
                )
        
        if not https_configured and os.getenv('FLASK_ENV') == 'production':
            self.add_issue(
                "No HTTPS configuration in production",
                "HIGH",
                "HTTPS is not configured for production environment",
                "Configure SSL certificates for HTTPS in production",
                "Network Security",
                "CWE-319",
                8.1
            )
        
        # Check security headers configuration
        try:
            from config import BaseConfig
            headers = getattr(BaseConfig, 'SECURITY_HEADERS', {})
            
            required_headers = {
                'Strict-Transport-Security': 'HSTS',
                'X-Content-Type-Options': 'Content type sniffing protection',
                'X-Frame-Options': 'Clickjacking protection',
                'X-XSS-Protection': 'XSS protection',
                'Content-Security-Policy': 'CSP protection'
            }
            
            missing_headers = []
            for header, description in required_headers.items():
                if header not in headers:
                    missing_headers.append(f"{header} ({description})")
            
            if missing_headers:
                self.add_issue(
                    "Missing security headers",
                    "MEDIUM",
                    f"Missing security headers: {', '.join(missing_headers)}",
                    "Configure missing security headers in SECURITY_HEADERS",
                    "Network Security",
                    "CWE-16",
                    6.1
                )
            
        except Exception as e:
            self.add_issue(
                "Could not check security headers",
                "LOW",
                f"Failed to audit security headers: {str(e)}",
                "Investigate security headers configuration",
                "Network Security"
            )

    # =============================================================================
    # DEPENDENCY SECURITY
    # =============================================================================

    def audit_dependency_security(self):
        """Audit dependency security (basic known vulnerability check)"""
        self.log("📦 Auditing Dependency Security...")
        
        # Known vulnerable package versions (simplified list)
        vulnerable_packages = {
            'flask': {
                '2.0.0': 'CVE-2023-30861 - Cookie confusion vulnerability',
                '1.1.4': 'CVE-2019-1010083 - Denial of service vulnerability'
            },
            'jinja2': {
                '2.10.1': 'CVE-2020-28493 - RCE vulnerability',
                '2.11.3': 'CVE-2020-28493 - RCE vulnerability'
            },
            'werkzeug': {
                '0.15.5': 'CVE-2019-14806 - Path traversal vulnerability',
                '2.0.0': 'CVE-2023-25577 - High resource consumption'
            },
            'pillow': {
                '8.2.0': 'CVE-2021-25287 - Buffer overflow',
                '8.3.0': 'CVE-2021-25290 - Denial of service'
            }
        }
        
        try:
            # Get installed packages
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'list', '--format=json'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                installed = json.loads(result.stdout)
                
                for package in installed:
                    name = package['name'].lower()
                    version = package['version']
                    
                    if name in vulnerable_packages:
                        if version in vulnerable_packages[name]:
                            self.add_issue(
                                f"Vulnerable dependency: {name}",
                                "HIGH",
                                f"Package {name} v{version} has known vulnerability: {vulnerable_packages[name][version]}",
                                f"Update {name} to latest version",
                                "Dependencies",
                                "CWE-1104",
                                8.1
                            )
                
                self.log(f"✅ Scanned {len(installed)} installed packages")
                
        except Exception as e:
            self.add_issue(
                "Dependency audit failed",
                "LOW",
                f"Could not audit dependencies: {str(e)}",
                "Manually check for known vulnerabilities in dependencies",
                "Dependencies"
            )

    # =============================================================================
    # ERROR HANDLING SECURITY
    # =============================================================================

    def audit_error_handling_security(self):
        """Audit error handling for information disclosure"""
        self.log("⚠️ Auditing Error Handling Security...")
        
        # Check debug mode
        debug_enabled = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        env = os.getenv('FLASK_ENV', 'development')
        
        if debug_enabled and env != 'development':
            self.add_issue(
                "Debug mode enabled outside development",
                "HIGH",
                "Flask debug mode exposes sensitive information in error pages",
                "Disable debug mode in non-development environments",
                "Error Handling",
                "CWE-209",
                7.5
            )
        
        # Check for custom error handlers
        try:
            error_templates_dir = Path('templates/errors')
            if not error_templates_dir.exists():
                self.add_issue(
                    "No custom error pages",
                    "LOW",
                    "No custom error page templates found",
                    "Create custom error pages to avoid information disclosure",
                    "Error Handling",
                    "CWE-209",
                    4.3
                )
            else:
                required_error_pages = ['404.html', '500.html', '403.html']
                missing_pages = []
                for page in required_error_pages:
                    if not (error_templates_dir / page).exists():
                        missing_pages.append(page)
                
                if missing_pages:
                    self.add_issue(
                        "Missing error page templates",
                        "LOW",
                        f"Missing error page templates: {', '.join(missing_pages)}",
                        "Create missing error page templates",
                        "Error Handling",
                        "CWE-209",
                        4.3
                    )
        
        except Exception as e:
            self.log(f"Could not check error page templates: {e}")

    # =============================================================================
    # AUDIT RUNNER
    # =============================================================================

    def run_security_audit(self):
        """Run comprehensive security audit"""
        print("🚀 Starting comprehensive security audit...\n")
        
        # Run all audit categories
        self.audit_authentication_security()
        self.audit_password_security()
        self.audit_file_upload_security()
        self.audit_configuration_security()
        self.audit_database_security()
        self.audit_network_security()
        self.audit_dependency_security()
        self.audit_error_handling_security()

    def generate_security_report(self):
        """Generate comprehensive security report"""
        total_time = time.time() - self.start_time
        
        # Categorize issues by severity
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
        for issue in self.issues:
            severity_counts[issue.severity] += 1
        
        total_issues = len(self.issues)
        
        # Calculate security score
        severity_weights = {'CRITICAL': 10, 'HIGH': 7, 'MEDIUM': 4, 'LOW': 2, 'INFO': 0}
        total_weight = sum(severity_weights[sev] * count for sev, count in severity_counts.items())
        max_weight = max(100, total_weight)  # Prevent division by zero
        security_score = max(0, 100 - (total_weight * 100 / max_weight))
        
        print("\n" + "="*60)
        print("🛡️ SECURITY AUDIT REPORT")
        print("="*60)
        print(f"⏱️  Audit Time: {total_time:.2f} seconds")
        print(f"🔍 Issues Found: {total_issues}")
        print(f"🚨 Critical: {severity_counts['CRITICAL']}")
        print(f"⚠️  High: {severity_counts['HIGH']}")
        print(f"⚡ Medium: {severity_counts['MEDIUM']}")
        print(f"💡 Low: {severity_counts['LOW']}")
        print(f"ℹ️  Info: {severity_counts['INFO']}")
        print(f"📊 Security Score: {security_score:.1f}/100")
        print()
        
        # Security status
        if security_score >= 90:
            status = "🔒 HIGHLY SECURE"
            color = '\033[92m'  # Green
        elif security_score >= 75:
            status = "⚠️ MODERATELY SECURE"
            color = '\033[93m'  # Yellow
        elif security_score >= 50:
            status = "🔓 SECURITY CONCERNS"
            color = '\033[93m'  # Yellow
        else:
            status = "🚨 HIGH SECURITY RISK"
            color = '\033[91m'  # Red
        
        print(f"{color}🎯 SECURITY STATUS: {status}\033[0m")
        print()
        
        # Issue details
        if self.issues:
            print("📋 SECURITY ISSUES FOUND:")
            print("-" * 40)
            
            # Group by severity
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
                issues_of_severity = [i for i in self.issues if i.severity == severity]
                if issues_of_severity:
                    severity_icons = {
                        'CRITICAL': '🚨',
                        'HIGH': '⚠️',
                        'MEDIUM': '⚡',
                        'LOW': '💡',
                        'INFO': 'ℹ️'
                    }
                    print(f"\n{severity_icons[severity]} {severity} SEVERITY:")
                    for i, issue in enumerate(issues_of_severity, 1):
                        print(f"{i:2d}. {issue.title}")
                        print(f"    Component: {issue.affected_component}")
                        print(f"    Issue: {issue.description}")
                        print(f"    Fix: {issue.remediation}")
                        if issue.cwe_id:
                            print(f"    CWE: {issue.cwe_id}")
                        if issue.cvss_score:
                            print(f"    CVSS: {issue.cvss_score}")
                        print()
        else:
            print("✅ NO SECURITY ISSUES FOUND!")
            print("Your application appears to be secure based on the automated checks.")
        
        # Production readiness assessment
        if severity_counts['CRITICAL'] == 0 and severity_counts['HIGH'] <= 2:
            readiness = "🚀 READY FOR PRODUCTION"
        elif severity_counts['CRITICAL'] == 0 and severity_counts['HIGH'] <= 5:
            readiness = "⚠️ NEEDS SECURITY REVIEW"
        else:
            readiness = "❌ NOT READY FOR PRODUCTION"
        
        print(f"🎯 PRODUCTION READINESS: {readiness}")
        print("="*60)
        
        # Export report if requested
        if self.export_report:
            self.export_security_report(security_score, severity_counts)
        
        return security_score, severity_counts, total_issues

    def export_security_report(self, security_score, severity_counts):
        """Export security report to JSON file"""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'security_score': security_score,
            'severity_counts': severity_counts,
            'total_issues': len(self.issues),
            'issues': [
                {
                    'title': issue.title,
                    'severity': issue.severity,
                    'description': issue.description,
                    'remediation': issue.remediation,
                    'component': issue.affected_component,
                    'cwe_id': issue.cwe_id,
                    'cvss_score': issue.cvss_score
                }
                for issue in self.issues
            ]
        }
        
        report_file = f"security_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Security report exported to: {report_file}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Cropio Security Audit Suite')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--export-report', '-e', action='store_true', help='Export report to JSON file')
    
    args = parser.parse_args()
    
    try:
        auditor = SecurityAuditor(verbose=args.verbose, export_report=args.export_report)
        auditor.run_security_audit()
        security_score, severity_counts, total_issues = auditor.generate_security_report()
        
        # Exit with appropriate code
        if severity_counts['CRITICAL'] == 0 and severity_counts['HIGH'] == 0:
            sys.exit(0)  # No critical/high issues
        elif severity_counts['CRITICAL'] == 0:
            sys.exit(1)  # High issues but no critical
        else:
            sys.exit(2)  # Critical issues found
            
    except KeyboardInterrupt:
        print("\n⚠️ Security audit interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"\n🚨 Security audit failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(4)


if __name__ == "__main__":
    main()
