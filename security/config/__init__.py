"""
Security Configuration Module

This module contains all security-related configuration settings,
constants, and environment-specific configurations.

Usage:
    from security.config import SecurityConfig, FILE_SECURITY_CONFIG
    
    # Get file upload limits
    max_size = SecurityConfig.get_max_file_size(user_type='free')
    
    # Get allowed file types for images
    allowed = FILE_SECURITY_CONFIG['image']['extensions']
"""

from .security_config import SecurityConfig
from .constants import (
    DEFAULT_RATE_LIMITS,
    SECURITY_HEADERS,
    ALLOWED_MIME_TYPES,
    DANGEROUS_PATTERNS,
    CSRF_CONFIG,
    SESSION_CONFIG
)

__all__ = [
    'SecurityConfig',
    'DEFAULT_RATE_LIMITS',
    'SECURITY_HEADERS',
    'ALLOWED_MIME_TYPES',
    'DANGEROUS_PATTERNS',
    'CSRF_CONFIG',
    'SESSION_CONFIG'
]
