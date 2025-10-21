"""
Universal Security Framework - Security Exceptions
Custom exceptions for comprehensive security error handling
"""

class SecurityException(Exception):
    """Base security exception"""
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

class ValidationException(SecurityException):
    """Input validation failed"""
    pass

class InvalidFileTypeException(SecurityException):
    """Invalid or dangerous file type"""
    pass

class InvalidFileTypeError(SecurityException):
    """Invalid file type error"""
    pass

class FileSizeExceededException(SecurityException):
    """File size exceeds limits"""
    pass

class FileSizeExceededError(SecurityException):
    """File size exceeded error"""
    pass

class MalwareDetectedError(SecurityException):
    """Malware or suspicious content detected"""
    pass

class RateLimitExceededException(SecurityException):
    """Rate limit exceeded"""
    pass

class RateLimitExceededError(SecurityException):
    """Rate limit exceeded error"""
    pass

class AdminSecurityException(SecurityException):
    """Admin-specific security violation"""
    pass

class InvalidUserIdException(SecurityException):
    """Invalid user ID provided"""
    pass

class CSRFTokenError(SecurityException):
    """CSRF token validation failed"""
    pass

class CSRFValidationError(SecurityException):
    """CSRF validation error"""
    pass

class AuthenticationException(SecurityException):
    """Authentication failed"""
    pass

class AuthenticationError(SecurityException):
    """Authentication error"""
    pass

class AuthorizationException(SecurityException):
    """Authorization/permission denied"""
    pass

class AuthorizationError(SecurityException):
    """Authorization error"""
    pass

class ContentSecurityException(SecurityException):
    """Content contains dangerous patterns"""
    pass

class ContentValidationError(SecurityException):
    """Content validation error"""
    pass

class FileUploadException(SecurityException):
    """File upload security violation"""
    pass

class PathTraversalException(SecurityException):
    """Path traversal attempt detected"""
    pass

class InjectionAttemptException(SecurityException):
    """Code injection attempt detected"""
    pass

class SecurityViolationError(SecurityException):
    """Security violation error"""
    pass
