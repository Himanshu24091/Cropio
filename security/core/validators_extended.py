"""
Universal Security Framework - Input Validators
Comprehensive validation for all input types and security contexts
"""
import re
import os
import mimetypes
from flask import request
from security.core.exceptions import ValidationException, InvalidFileTypeException, InvalidUserIdException

# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {
    'images': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'heic'},
    'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'},
    'spreadsheets': {'xls', 'xlsx', 'csv', 'ods'},
    'presentations': {'ppt', 'pptx', 'odp'},
    'archives': {'zip', 'rar', '7z', 'tar', 'gz'}
}

SAFE_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff',
    'image/webp', 'application/pdf', 'text/plain', 'text/csv',
    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}

# Security patterns
DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'vbscript:',
    r'onload\s*=',
    r'onerror\s*=',
    r'onclick\s*=',
    r'eval\s*\(',
    r'exec\s*\(',
    r'document\.write',
    r'window\.location',
    r'<iframe[^>]*>',
    r'<embed[^>]*>',
    r'<object[^>]*>'
]

def validate_filename(filename):
    """Validate and sanitize uploaded filename"""
    if not filename:
        raise ValidationException("Filename is required")
    
    # Remove path traversal attempts
    filename = os.path.basename(filename)
    
    # Check for dangerous characters
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*', '\x00']
    for char in dangerous_chars:
        if char in filename:
            raise ValidationException(f"Invalid character '{char}' in filename")
    
    # Check filename length
    if len(filename) > 255:
        raise ValidationException("Filename too long")
    
    # Check for empty filename
    if not filename.strip():
        raise ValidationException("Filename cannot be empty")
    
    return filename.strip()

def validate_file_extension(filename, allowed_categories=None):
    """Validate file extension against allowed types"""
    if not filename:
        raise InvalidFileTypeException("No filename provided")
    
    # Get file extension
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if not ext:
        raise InvalidFileTypeException("File must have an extension")
    
    # Check against allowed categories
    if allowed_categories:
        allowed_exts = set()
        for category in allowed_categories:
            if category in ALLOWED_EXTENSIONS:
                allowed_exts.update(ALLOWED_EXTENSIONS[category])
        
        if ext not in allowed_exts:
            raise InvalidFileTypeException(f"File type '.{ext}' not allowed")
    
    return ext

def validate_file_size(file_obj, max_size_mb=50):
    """Validate file size"""
    if not file_obj:
        raise ValidationException("No file provided")
    
    # Check file size
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(0)  # Reset position
    
    max_size_bytes = max_size_mb * 1024 * 1024
    if size > max_size_bytes:
        raise ValidationException(f"File size ({size/1024/1024:.2f}MB) exceeds maximum ({max_size_mb}MB)")
    
    if size == 0:
        raise ValidationException("File is empty")
    
    return size

def validate_mime_type(file_obj, filename=None):
    """Validate MIME type against file extension"""
    if not file_obj:
        raise ValidationException("No file provided")
    
    # Get MIME type from file content
    file_obj.seek(0)
    file_content = file_obj.read(1024)  # Read first 1KB
    file_obj.seek(0)
    
    # Use python-magic if available, otherwise use mimetypes
    try:
        import magic
        mime_type = magic.from_buffer(file_content, mime=True)
    except ImportError:
        if filename:
            mime_type, _ = mimetypes.guess_type(filename)
        else:
            mime_type = 'application/octet-stream'
    
    # Validate against safe MIME types
    if mime_type not in SAFE_MIME_TYPES:
        raise InvalidFileTypeException(f"MIME type '{mime_type}' not allowed")
    
    return mime_type

def validate_user_id(user_id):
    """Validate user ID parameter"""
    if not user_id:
        raise InvalidUserIdException("User ID is required")
    
    try:
        user_id = int(user_id)
        if user_id <= 0:
            raise InvalidUserIdException("User ID must be positive")
    except (ValueError, TypeError):
        raise InvalidUserIdException("Invalid user ID format")
    
    return user_id

def validate_pagination(page, max_page=1000):
    """Validate pagination parameters"""
    if not page:
        return 1
    
    try:
        page = int(page)
        if page < 1:
            raise ValidationException("Page number must be positive")
        if page > max_page:
            raise ValidationException(f"Page number exceeds maximum ({max_page})")
    except (ValueError, TypeError):
        raise ValidationException("Invalid page number format")
    
    return page

def validate_admin_input(value, allowed_values=None, data_type='str', min_val=None, max_val=None):
    """Validate admin input with comprehensive checks"""
    if value is None:
        raise ValidationException("Input value is required")
    
    # Type conversion and validation
    if data_type == 'int':
        try:
            value = int(value)
            if min_val is not None and value < min_val:
                raise ValidationException(f"Value must be at least {min_val}")
            if max_val is not None and value > max_val:
                raise ValidationException(f"Value must be at most {max_val}")
        except (ValueError, TypeError):
            raise ValidationException("Invalid integer format")
    
    elif data_type == 'str':
        value = str(value).strip()
        if not value:
            raise ValidationException("String value cannot be empty")
        if min_val is not None and len(value) < min_val:
            raise ValidationException(f"String must be at least {min_val} characters")
        if max_val is not None and len(value) > max_val:
            raise ValidationException(f"String must be at most {max_val} characters")
    
    # Check against allowed values
    if allowed_values and value not in allowed_values:
        raise ValidationException(f"Value must be one of: {', '.join(map(str, allowed_values))}")
    
    return value

def validate_json_request(request_obj):
    """Validate JSON request structure"""
    if not request_obj:
        raise ValidationException("No request provided")
    
    if not request_obj.is_json:
        raise ValidationException("Request must be JSON")
    
    if not request_obj.json:
        raise ValidationException("JSON body is required")
    
    return True

def validate_content_safety(content):
    """Validate content for dangerous patterns"""
    if not content:
        return True
    
    content_str = str(content)
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, content_str, re.IGNORECASE):
            raise ValidationException(f"Content contains dangerous pattern: {pattern}")
    
    return True

def validate_file_content(file_obj, filename):
    """Comprehensive file content validation"""
    if not file_obj or not filename:
        raise ValidationException("File and filename required")
    
    # Read file content for analysis
    file_obj.seek(0)
    content = file_obj.read(8192)  # Read first 8KB
    file_obj.seek(0)
    
    # Check for executable signatures
    dangerous_signatures = [
        b'MZ',  # Windows executable
        b'\x7fELF',  # Linux executable
        b'\xca\xfe\xba\xbe',  # Java class file
        b'PK\x03\x04',  # ZIP archive (could contain executables)
    ]
    
    for sig in dangerous_signatures:
        if content.startswith(sig):
            ext = filename.lower().split('.')[-1] if '.' in filename else ''
            if ext not in ['zip', 'jar', 'docx', 'xlsx', 'pptx']:  # These are legitimate ZIP-based formats
                raise ValidationException("File appears to contain executable code")
    
    # Check for embedded scripts in text files
    if isinstance(content, bytes):
        try:
            content_str = content.decode('utf-8', errors='ignore')
            validate_content_safety(content_str)
        except UnicodeDecodeError:
            pass  # Binary files are OK
    
    return True

def validate_upload_params(request_obj):
    """Validate file upload parameters"""
    if 'file' not in request_obj.files:
        raise ValidationException("No file uploaded")
    
    file_obj = request_obj.files['file']
    if not file_obj or file_obj.filename == '':
        raise ValidationException("No file selected")
    
    return file_obj