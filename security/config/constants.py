"""
Security Constants

This module contains all security-related constants used throughout
the security framework. Centralizing constants makes maintenance easier
and ensures consistency.

Usage:
    from security.config.constants import DEFAULT_RATE_LIMITS, DANGEROUS_PATTERNS
"""

from typing import Dict, List, Set

# Default rate limiting configurations
DEFAULT_RATE_LIMITS = {
    'api_requests_per_minute': 60,
    'upload_requests_per_minute': 10,
    'conversion_requests_per_minute': 20,
    'failed_login_attempts': 5,
    'password_reset_attempts': 3
}

# Security headers for all responses
SECURITY_HEADERS = {
    'X-Frame-Options': 'SAMEORIGIN',
    'X-Content-Type-Options': 'nosniff',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com"
}

# Comprehensive MIME type mapping for security validation
ALLOWED_MIME_TYPES = {
    # Images
    'jpg': ['image/jpeg'],
    'jpeg': ['image/jpeg'],
    'png': ['image/png'],
    'gif': ['image/gif'],
    'webp': ['image/webp'],
    'bmp': ['image/bmp'],
    'tiff': ['image/tiff'],
    'ico': ['image/x-icon', 'image/vnd.microsoft.icon'],
    'heic': ['image/heic', 'image/heif'],
    'svg': ['image/svg+xml'],
    
    # Documents
    'pdf': ['application/pdf'],
    'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    'doc': ['application/msword'],
    'odt': ['application/vnd.oasis.opendocument.text'],
    'rtf': ['text/rtf', 'application/rtf'],
    'txt': ['text/plain'],
    
    # Spreadsheets
    'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    'xls': ['application/vnd.ms-excel'],
    'ods': ['application/vnd.oasis.opendocument.spreadsheet'],
    'csv': ['text/csv', 'text/plain'],
    
    # Archives
    'zip': ['application/zip'],
    'rar': ['application/x-rar-compressed'],
    '7z': ['application/x-7z-compressed'],
    'tar': ['application/x-tar'],
    'gz': ['application/gzip'],
    
    # Code files
    'html': ['text/html'],
    'htm': ['text/html'],
    'css': ['text/css'],
    'js': ['application/javascript', 'text/javascript'],
    'json': ['application/json'],
    'xml': ['application/xml', 'text/xml'],
    'yaml': ['application/x-yaml', 'text/yaml'],
    'yml': ['application/x-yaml', 'text/yaml'],
    'md': ['text/markdown', 'text/x-markdown']
}

# Dangerous content patterns to scan for in uploaded files
DANGEROUS_PATTERNS = {
    # Script injection patterns
    'script_tags': [
        b'<script',
        b'</script>',
        b'javascript:',
        b'vbscript:',
        b'onload=',
        b'onerror=',
        b'onclick=',
        b'onmouseover=',
        b'onfocus='
    ],
    
    # PHP code injection
    'php_code': [
        b'<?php',
        b'<?=',
        b'eval(',
        b'exec(',
        b'system(',
        b'shell_exec(',
        b'passthru(',
        b'file_get_contents(',
        b'include(',
        b'require('
    ],
    
    # Server-side includes
    'ssi_includes': [
        b'<!--#',
        b'#exec',
        b'#include',
        b'#echo',
        b'#config',
        b'#set'
    ],
    
    # Macro and embedded code
    'macro_code': [
        b'Sub ',
        b'Function ',
        b'Private Sub',
        b'Public Sub',
        b'Auto_Open',
        b'Auto_Close',
        b'Document_Open',
        b'Workbook_Open'
    ],
    
    # Suspicious executables
    'executable_headers': [
        b'MZ',  # PE executable
        b'\x7fELF',  # ELF executable
        b'\xfe\xed\xfa',  # Mach-O
        b'PK\x03\x04',  # ZIP (could contain executables)
        b'Rar!'  # RAR archive
    ],
    
    # SQL injection patterns
    'sql_injection': [
        b'UNION SELECT',
        b'DROP TABLE',
        b'DELETE FROM',
        b'INSERT INTO',
        b'UPDATE SET',
        b'; --',
        b"'; DROP",
        b'OR 1=1',
        b'AND 1=1'
    ],
    
    # Path traversal
    'path_traversal': [
        b'../',
        b'..\\',
        b'%2e%2e%2f',
        b'%2e%2e%5c',
        b'..%2f',
        b'..%5c'
    ],
    
    # Command injection
    'command_injection': [
        b'| nc ',
        b'| netcat ',
        b'&& curl ',
        b'&& wget ',
        b'; curl ',
        b'; wget ',
        b'`curl ',
        b'`wget ',
        b'$(curl ',
        b'$(wget '
    ]
}

# CSRF configuration
CSRF_CONFIG = {
    'token_length': 32,
    'token_lifetime': 3600,  # 1 hour
    'header_name': 'X-CSRFToken',
    'field_name': 'csrf_token',
    'cookie_name': 'csrf_token',
    'cookie_secure': True,
    'cookie_httponly': True,
    'cookie_samesite': 'Strict'
}

# Session security configuration
SESSION_CONFIG = {
    'lifetime': 3600,  # 1 hour
    'refresh_threshold': 300,  # 5 minutes
    'max_concurrent_sessions': 3,
    'cookie_secure': True,
    'cookie_httponly': True,
    'cookie_samesite': 'Strict',
    'regenerate_on_login': True,
    'invalidate_on_logout': True
}

# File size limits (in bytes)
FILE_SIZE_LIMITS = {
    'thumbnail': 1024 * 1024,      # 1MB
    'small_image': 5 * 1024 * 1024,    # 5MB
    'large_image': 50 * 1024 * 1024,   # 50MB
    'document': 100 * 1024 * 1024,     # 100MB
    'archive': 200 * 1024 * 1024,      # 200MB
    'video': 500 * 1024 * 1024,        # 500MB
    'maximum': 1024 * 1024 * 1024      # 1GB absolute maximum
}

# Password security requirements
PASSWORD_REQUIREMENTS = {
    'min_length': 8,
    'max_length': 128,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_digits': True,
    'require_special_chars': True,
    'special_chars': '!@#$%^&*(),.?":{}|<>',
    'max_consecutive_chars': 3,
    'max_repeating_chars': 3,
    'common_passwords_file': 'common_passwords.txt'
}

# Audit logging event types
AUDIT_EVENT_TYPES = {
    'authentication': [
        'login_success',
        'login_failed',
        'logout',
        'password_changed',
        'password_reset_requested',
        'password_reset_completed',
        'account_locked',
        'account_unlocked'
    ],
    'file_operations': [
        'file_uploaded',
        'file_downloaded',
        'file_converted',
        'file_deleted',
        'malware_detected',
        'file_quarantined'
    ],
    'security_events': [
        'csrf_violation',
        'rate_limit_exceeded',
        'suspicious_activity',
        'privilege_escalation_attempt',
        'unauthorized_access_attempt'
    ],
    'system_events': [
        'configuration_changed',
        'service_started',
        'service_stopped',
        'backup_completed',
        'maintenance_mode_enabled',
        'maintenance_mode_disabled'
    ]
}

# Malware signature patterns (simplified for basic detection)
MALWARE_SIGNATURES = {
    'eicar_test': b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',
    'zip_bomb_headers': [
        b'PK\x03\x04\x14\x00\x00\x00\x08\x00',  # Highly compressed ZIP
        b'PK\x03\x04\x14\x00\x00\x00\x00\x00'   # Stored ZIP with suspicious size ratio
    ],
    'pdf_javascript': [
        b'/JavaScript',
        b'/JS',
        b'/Action',
        b'/OpenAction',
        b'app.alert',
        b'this.print'
    ],
    'office_macro': [
        b'macros/',
        b'vbaProject',
        b'Microsoft Office Word',
        b'Microsoft Excel'
    ]
}

# File extension security classifications
FILE_EXTENSION_CLASSES = {
    'safe': {
        'image': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'],
        'text': ['txt', 'md', 'csv'],
        'basic_document': ['pdf']  # PDFs need content scanning but are generally safe
    },
    'requires_scanning': {
        'document': ['docx', 'doc', 'odt', 'rtf'],
        'spreadsheet': ['xlsx', 'xls', 'ods'],
        'presentation': ['pptx', 'ppt', 'odp'],
        'code': ['html', 'htm', 'xml', 'js', 'css'],
        'advanced_image': ['heic', 'tiff', 'svg']
    },
    'high_risk': {
        'archive': ['zip', 'rar', '7z', 'tar', 'gz'],
        'executable': ['exe', 'msi', 'dmg', 'deb', 'rpm'],
        'script': ['py', 'sh', 'bat', 'cmd', 'ps1'],
        'binary': ['bin', 'dat', 'dll', 'so']
    },
    'blocked': {
        'dangerous': ['exe', 'scr', 'pif', 'bat', 'cmd', 'com', 'vbs', 'js', 'jar']
    }
}

# HTTP status codes for security responses
SECURITY_STATUS_CODES = {
    'rate_limit_exceeded': 429,
    'csrf_violation': 403,
    'malware_detected': 422,
    'file_too_large': 413,
    'invalid_file_type': 415,
    'authentication_required': 401,
    'authorization_failed': 403,
    'security_violation': 400
}

# Error messages (user-friendly)
SECURITY_ERROR_MESSAGES = {
    'file_too_large': 'File size exceeds the maximum allowed limit.',
    'invalid_file_type': 'This file type is not allowed.',
    'malware_detected': 'Security scan detected potentially harmful content in the uploaded file.',
    'rate_limit_exceeded': 'Too many requests. Please wait before trying again.',
    'csrf_violation': 'Security token validation failed. Please refresh the page.',
    'session_expired': 'Your session has expired. Please log in again.',
    'authentication_required': 'Authentication required to access this resource.',
    'authorization_failed': 'You do not have permission to perform this action.',
    'suspicious_activity': 'Suspicious activity detected. Please contact support if this continues.'
}

# Time constants (in seconds)
TIME_CONSTANTS = {
    'minute': 60,
    'hour': 3600,
    'day': 86400,
    'week': 604800,
    'month': 2592000,  # 30 days
    'year': 31536000   # 365 days
}

# Memory and resource limits
RESOURCE_LIMITS = {
    'max_memory_per_request': 512 * 1024 * 1024,  # 512MB
    'max_processing_time': 300,  # 5 minutes
    'max_concurrent_operations': 10,
    'max_file_handles': 100,
    'max_temp_files': 50
}