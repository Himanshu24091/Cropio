"""
Security Configuration

This module provides centralized configuration for all security features.
Supports environment-based configuration and dynamic user-based limits.

Features:
- File upload limits by user type
- Rate limiting configuration
- Security feature toggles
- Environment-specific settings

Usage:
    from security.config import SecurityConfig
    
    config = SecurityConfig()
    max_size = config.get_max_file_size('premium')
    rate_limit = config.get_rate_limit('api', 'free')
"""

import os
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum


class UserType(Enum):
    """User types for security configuration"""
    FREE = "free"
    PREMIUM = "premium"
    STAFF = "staff"
    ADMIN = "admin"


class SecurityLevel(Enum):
    """Security levels for different environments"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int
    requests_per_hour: int
    burst_limit: int
    lockout_duration: int = 300  # seconds


@dataclass
class FileUploadConfig:
    """File upload security configuration"""
    max_size_bytes: int
    allowed_extensions: List[str]
    scan_for_malware: bool = True
    sanitize_content: bool = True
    check_mime_type: bool = True


class SecurityConfig:
    """
    Centralized security configuration for the entire platform
    """
    
    def __init__(self, environment: str = None, security_level: SecurityLevel = None,
                 enable_malware_scanning: bool = None, rate_limit_enabled: bool = None,
                 **kwargs):
        """
        Initialize security configuration
        
        Args:
            environment: Environment type ('development', 'testing', 'production')
            security_level: Security level (LOW, MEDIUM, HIGH)
            enable_malware_scanning: Enable malware scanning
            rate_limit_enabled: Enable rate limiting
            **kwargs: Additional configuration options
        """
        # Set environment
        self.environment = environment or os.getenv('FLASK_ENV', 'development')
        
        # Set security level
        if security_level:
            self.security_level = security_level
        else:
            level_map = {
                'development': SecurityLevel.MEDIUM,
                'testing': SecurityLevel.MEDIUM,
                'staging': SecurityLevel.HIGH,
                'production': SecurityLevel.HIGH
            }
            self.security_level = level_map.get(self.environment, SecurityLevel.MEDIUM)
        
        # Get environment-specific features
        features = self.SECURITY_FEATURES.get(self.environment, self.SECURITY_FEATURES['development'])
        
        # Set individual features
        self.enable_malware_scanning = enable_malware_scanning if enable_malware_scanning is not None else features['malware_scanning']
        self.rate_limit_enabled = rate_limit_enabled if rate_limit_enabled is not None else features['rate_limiting']
        self.csrf_protection = kwargs.get('csrf_protection', features['csrf_protection'])
        self.content_sanitization = kwargs.get('content_sanitization', features['content_sanitization'])
        self.audit_logging = kwargs.get('audit_logging', features['audit_logging'])
        self.security_headers = kwargs.get('security_headers', features['security_headers'])
        self.https_only = kwargs.get('https_only', features['https_only'])
        
        # Additional configuration
        self.strict_file_validation = kwargs.get('strict_file_validation', True)
        self.debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    
    def get_max_file_size(self, user_type: str = 'free', file_category: str = 'default') -> int:
        """Instance method to get max file size"""
        return self.__class__.get_max_file_size(user_type, file_category)
    
    def get_rate_limit(self, endpoint_category: str, user_type: str = 'free') -> RateLimitConfig:
        """Instance method to get rate limit config"""
        return self.__class__.get_rate_limit(endpoint_category, user_type)
    
    def is_file_type_allowed(self, file_extension: str) -> bool:
        """Check if file type is allowed"""
        for category in self.FILE_CATEGORIES.values():
            if file_extension.lower() in category['extensions']:
                return True
        return False
    
    # Environment-based configuration
    ENVIRONMENT = os.getenv('FLASK_ENV', 'development')
    DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Base file size limits (in bytes)
    BASE_FILE_SIZES = {
        UserType.FREE.value: 50 * 1024 * 1024,        # 50MB
        UserType.PREMIUM.value: 500 * 1024 * 1024,    # 500MB
        UserType.STAFF.value: 1024 * 1024 * 1024,     # 1GB
        UserType.ADMIN.value: 2048 * 1024 * 1024,     # 2GB
    }
    
    # Rate limiting by user type and endpoint category
    RATE_LIMITS = {
        'api': {
            UserType.FREE.value: RateLimitConfig(20, 100, 5, 300),
            UserType.PREMIUM.value: RateLimitConfig(100, 1000, 20, 60),
            UserType.STAFF.value: RateLimitConfig(200, 2000, 50, 30),
            UserType.ADMIN.value: RateLimitConfig(500, 5000, 100, 0),
        },
        'upload': {
            UserType.FREE.value: RateLimitConfig(5, 20, 2, 600),
            UserType.PREMIUM.value: RateLimitConfig(20, 100, 5, 300),
            UserType.STAFF.value: RateLimitConfig(50, 500, 10, 60),
            UserType.ADMIN.value: RateLimitConfig(100, 1000, 20, 0),
        },
        'conversion': {
            UserType.FREE.value: RateLimitConfig(10, 50, 3, 300),
            UserType.PREMIUM.value: RateLimitConfig(50, 500, 10, 60),
            UserType.STAFF.value: RateLimitConfig(100, 1000, 20, 30),
            UserType.ADMIN.value: RateLimitConfig(200, 2000, 50, 0),
        }
    }
    
    # Security features by environment
    SECURITY_FEATURES = {
        'development': {
            'csrf_protection': True,
            'rate_limiting': True,
            'malware_scanning': True,
            'content_sanitization': True,
            'audit_logging': True,
            'security_headers': False,  # Can interfere with dev tools
            'https_only': False,
        },
        'testing': {
            'csrf_protection': False,   # Disabled for easier testing
            'rate_limiting': False,     # Disabled for testing
            'malware_scanning': True,
            'content_sanitization': True,
            'audit_logging': False,     # Reduce noise in tests
            'security_headers': False,
            'https_only': False,
        },
        'staging': {
            'csrf_protection': True,
            'rate_limiting': True,
            'malware_scanning': True,
            'content_sanitization': True,
            'audit_logging': True,
            'security_headers': True,
            'https_only': True,
        },
        'production': {
            'csrf_protection': True,
            'rate_limiting': True,
            'malware_scanning': True,
            'content_sanitization': True,
            'audit_logging': True,
            'security_headers': True,
            'https_only': True,
        }
    }
    
    # File type configurations
    FILE_CATEGORIES = {
        'image': {
            'extensions': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff', 'ico', 'heic'],
            'mime_types': ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp', 
                          'image/tiff', 'image/x-icon', 'image/heic'],
            'max_size_multiplier': 1.0,  # Use base size
            'special_handling': ['heic', 'raw', 'tiff']  # Need special processing
        },
        'document': {
            'extensions': ['pdf', 'docx', 'doc', 'odt', 'rtf', 'txt'],
            'mime_types': ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                          'application/msword', 'application/vnd.oasis.opendocument.text', 'text/rtf', 'text/plain'],
            'max_size_multiplier': 2.0,  # Documents can be larger
            'special_handling': ['pdf', 'docx']  # Need macro/script scanning
        },
        'spreadsheet': {
            'extensions': ['xlsx', 'xls', 'ods', 'csv'],
            'mime_types': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                          'application/vnd.ms-excel', 'application/vnd.oasis.opendocument.spreadsheet', 'text/csv'],
            'max_size_multiplier': 1.5,
            'special_handling': ['xlsx', 'xls']  # Need formula injection scanning
        },
        'archive': {
            'extensions': ['zip', 'rar', '7z', 'tar', 'gz'],
            'mime_types': ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
                          'application/x-tar', 'application/gzip'],
            'max_size_multiplier': 0.8,  # Compressed files should be smaller
            'special_handling': ['zip', 'rar']  # Need deep scanning
        },
        'code': {
            'extensions': ['html', 'css', 'js', 'json', 'xml', 'yaml', 'yml', 'md'],
            'mime_types': ['text/html', 'text/css', 'application/javascript', 'application/json',
                          'application/xml', 'application/x-yaml', 'text/markdown'],
            'max_size_multiplier': 0.5,  # Code files are usually small
            'special_handling': ['html', 'js', 'xml']  # Need script injection scanning
        }
    }
    
    @classmethod
    def get_max_file_size(cls, user_type: str, file_category: str = 'default') -> int:
        """
        Get maximum file size for user type and file category
        
        Args:
            user_type: User type (free, premium, staff, admin)
            file_category: File category (image, document, etc.)
            
        Returns:
            Maximum file size in bytes
        """
        base_size = cls.BASE_FILE_SIZES.get(user_type, cls.BASE_FILE_SIZES[UserType.FREE.value])
        
        if file_category in cls.FILE_CATEGORIES:
            multiplier = cls.FILE_CATEGORIES[file_category]['max_size_multiplier']
            return int(base_size * multiplier)
        
        return base_size
    
    @classmethod
    def get_rate_limit(cls, endpoint_category: str, user_type: str) -> RateLimitConfig:
        """
        Get rate limit configuration for endpoint and user type
        
        Args:
            endpoint_category: Category (api, upload, conversion)
            user_type: User type (free, premium, staff, admin)
            
        Returns:
            RateLimitConfig instance
        """
        category_limits = cls.RATE_LIMITS.get(endpoint_category, cls.RATE_LIMITS['api'])
        return category_limits.get(user_type, category_limits[UserType.FREE.value])
    
    @classmethod
    def is_feature_enabled(cls, feature_name: str) -> bool:
        """
        Check if security feature is enabled for current environment
        
        Args:
            feature_name: Name of security feature
            
        Returns:
            True if feature is enabled
        """
        env_features = cls.SECURITY_FEATURES.get(cls.ENVIRONMENT, cls.SECURITY_FEATURES['development'])
        return env_features.get(feature_name, False)
    
    @classmethod
    def get_allowed_extensions(cls, file_category: str) -> List[str]:
        """
        Get allowed file extensions for category
        
        Args:
            file_category: File category name
            
        Returns:
            List of allowed extensions
        """
        return cls.FILE_CATEGORIES.get(file_category, {}).get('extensions', [])
    
    @classmethod
    def get_allowed_mime_types(cls, file_category: str) -> List[str]:
        """
        Get allowed MIME types for category
        
        Args:
            file_category: File category name
            
        Returns:
            List of allowed MIME types
        """
        return cls.FILE_CATEGORIES.get(file_category, {}).get('mime_types', [])
    
    @classmethod
    def needs_special_handling(cls, file_category: str, extension: str) -> bool:
        """
        Check if file extension needs special security handling
        
        Args:
            file_category: File category name
            extension: File extension
            
        Returns:
            True if special handling required
        """
        special_files = cls.FILE_CATEGORIES.get(file_category, {}).get('special_handling', [])
        return extension.lower() in special_files
    
    @classmethod
    def get_security_level(cls) -> SecurityLevel:
        """
        Get current security level based on environment
        
        Returns:
            SecurityLevel enum value
        """
        level_map = {
            'development': SecurityLevel.MEDIUM,
            'testing': SecurityLevel.LOW,
            'staging': SecurityLevel.HIGH,
            'production': SecurityLevel.MAXIMUM
        }
        return level_map.get(cls.ENVIRONMENT, SecurityLevel.MEDIUM)
    
    @classmethod
    def get_upload_config(cls, user_type: str, file_category: str) -> FileUploadConfig:
        """
        Get complete file upload configuration
        
        Args:
            user_type: User type
            file_category: File category
            
        Returns:
            FileUploadConfig instance
        """
        return FileUploadConfig(
            max_size_bytes=cls.get_max_file_size(user_type, file_category),
            allowed_extensions=cls.get_allowed_extensions(file_category),
            scan_for_malware=cls.is_feature_enabled('malware_scanning'),
            sanitize_content=cls.is_feature_enabled('content_sanitization'),
            check_mime_type=True  # Always check MIME types
        )
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        Convert configuration to dictionary for API/debugging
        
        Returns:
            Configuration as dictionary
        """
        return {
            'environment': cls.ENVIRONMENT,
            'debug_mode': cls.DEBUG_MODE,
            'security_level': cls.get_security_level().value,
            'enabled_features': {
                name: cls.is_feature_enabled(name)
                for name in cls.SECURITY_FEATURES.get(cls.ENVIRONMENT, {}).keys()
            },
            'file_categories': list(cls.FILE_CATEGORIES.keys()),
            'user_types': [t.value for t in UserType],
            'rate_limit_categories': list(cls.RATE_LIMITS.keys())
        }


# Global configuration instance
security_config = SecurityConfig()