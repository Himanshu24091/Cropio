"""
Security Validators Module

This module provides comprehensive validation functions for user input,
file content, and security compliance checks.
"""

import re
import os
from typing import Tuple, List, Dict, Any, Optional
from urllib.parse import urlparse

from .exceptions import ContentValidationError


def validate_content(content: bytes, file_type: str) -> Tuple[bool, List[str]]:
    """
    Validates file content for security threats.
    
    Args:
        content: File content to validate
        file_type: File extension/type
        
    Returns:
        Tuple of (is_safe: bool, issues: List[str])
    """
    issues = []
    
    # File type specific validation takes precedence for structured formats
    if file_type == 'pdf':
        issues.extend(_validate_pdf_content(content))
    elif file_type in ['docx', 'xlsx', 'pptx', 'ppt']:
        # Office documents are structured ZIP files with XML content
        # Use specialized validation instead of generic pattern matching
        issues.extend(_validate_office_content(content))
    elif file_type in ['jpg', 'jpeg', 'png', 'gif']:
        issues.extend(_validate_image_content(content))
    else:
        # For other file types, apply general dangerous pattern checking
        dangerous_patterns = [
            (rb'<script.*?>', 'JavaScript code detected'),
            (rb'javascript:', 'JavaScript URL detected'),
            (rb'vbscript:', 'VBScript URL detected'),
            (rb'data:.*?base64', 'Base64 encoded data URL detected'),
            (rb'<?php', 'PHP code detected'),
            (rb'<%.*?%>', 'Server-side code detected'),
            (rb'eval\s*\(', 'eval() function detected'),
            (rb'exec\s*\(', 'exec() function detected'),
            (rb'system\s*\(', 'system() function detected'),
            (rb'shell_exec\s*\(', 'shell_exec() function detected'),
        ]
        
        content_lower = content.lower()
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                issues.append(message)
    
    return len(issues) == 0, issues


def validate_filename(filename: str) -> bool:
    """
    Validates filename for security compliance.
    
    Args:
        filename: Filename to validate
        
    Returns:
        True if filename is safe
    """
    if not filename or len(filename) == 0:
        return False
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'\.\./',  # Directory traversal
        r'\\',     # Windows path separators
        r'/',      # Unix path separators (in filename)
        r'[<>:"|?*]',  # Invalid Windows filename characters
        r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)',  # Windows reserved names
        r'^\.',    # Hidden files
        r'\.$',    # Ending with dot
        r'\s$',    # Ending with space
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return False
    
    # Check length
    if len(filename) > 255:
        return False
    
    return True


def validate_user_input(input_data: str, input_type: str = 'general') -> Tuple[bool, List[str]]:
    """
    Validates user input for various contexts.
    
    Args:
        input_data: User input to validate
        input_type: Type of input ('email', 'password', 'username', 'general', etc.)
        
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []
    
    if not input_data:
        errors.append("Input cannot be empty")
        return False, errors
    
    # General validation
    if len(input_data) > 10000:  # 10KB limit for general input
        errors.append("Input too long (max 10,000 characters)")
    
    # Check for common injection patterns
    injection_patterns = [
        (r'<script.*?>', 'XSS script tag detected'),
        (r'javascript:', 'JavaScript URL detected'),
        (r'on\w+\s*=', 'Event handler detected'),
        (r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bDELETE\b|\bDROP\b)', 'SQL keywords detected'),
        (r'(\|\||&&|\;|\|)', 'Command injection characters detected'),
    ]
    
    for pattern, message in injection_patterns:
        if re.search(pattern, input_data, re.IGNORECASE):
            errors.append(message)
    
    # Type-specific validation
    if input_type == 'email':
        errors.extend(_validate_email(input_data))
    elif input_type == 'password':
        errors.extend(_validate_password(input_data))
    elif input_type == 'username':
        errors.extend(_validate_username(input_data))
    elif input_type == 'url':
        errors.extend(_validate_url(input_data))
    
    return len(errors) == 0, errors


def validate_ip_address(ip: str) -> bool:
    """
    Validates IP address format and checks for private/dangerous ranges.
    
    Args:
        ip: IP address to validate
        
    Returns:
        True if IP is valid and safe
    """
    import ipaddress
    
    try:
        ip_obj = ipaddress.ip_address(ip)
        
        # Check for dangerous/private ranges
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved:
            return False
            
        return True
    except ValueError:
        return False


def validate_json_input(json_data: Dict[str, Any], schema: Optional[Dict] = None) -> Tuple[bool, List[str]]:
    """
    Validates JSON input for security and structure.
    
    Args:
        json_data: JSON data to validate
        schema: Optional schema to validate against
        
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []
    
    # Check depth (prevent deep nesting attacks)
    max_depth = 10
    if _get_json_depth(json_data) > max_depth:
        errors.append(f"JSON nesting too deep (max {max_depth} levels)")
    
    # Check size (prevent large payload attacks)
    json_str = str(json_data)
    if len(json_str) > 1024 * 1024:  # 1MB limit
        errors.append("JSON payload too large (max 1MB)")
    
    # Validate string values for injection patterns
    _validate_json_strings(json_data, errors)
    
    # Schema validation if provided
    if schema:
        schema_errors = _validate_json_schema(json_data, schema)
        errors.extend(schema_errors)
    
    return len(errors) == 0, errors


def validate_admin_input(input_data: str, allowed_values: List[str] = None) -> str:
    """
    Validates admin input and returns sanitized value.
    
    Args:
        input_data: Input to validate
        allowed_values: List of allowed values (optional)
        
    Returns:
        Sanitized input value
    """
    if not input_data:
        return ''
    
    # Basic sanitization
    input_data = str(input_data).strip()
    
    # Check against allowed values if provided
    if allowed_values and input_data not in allowed_values:
        return allowed_values[0] if allowed_values else ''
    
    return input_data


def validate_user_id(user_id: int) -> int:
    """
    Validates user ID.
    
    Args:
        user_id: User ID to validate
        
    Returns:
        Validated user ID
        
    Raises:
        InvalidUserIdException: If user ID is invalid
    """
    from .exceptions import InvalidUserIdException
    
    try:
        user_id = int(user_id)
        if user_id <= 0:
            raise InvalidUserIdException("User ID must be positive")
        return user_id
    except (ValueError, TypeError):
        raise InvalidUserIdException("Invalid user ID format")


def validate_pagination(page: int, per_page: int = 20) -> int:
    """
    Validates pagination parameters.
    
    Args:
        page: Page number
        per_page: Items per page
        
    Returns:
        Validated page number
    """
    try:
        page = int(page)
        if page < 1:
            return 1
        if page > 10000:  # Reasonable upper limit
            return 10000
        return page
    except (ValueError, TypeError):
        return 1


def validate_json_request(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates JSON request data.
    
    Args:
        data: JSON data to validate
        
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    return validate_json_input(data)


# Helper functions for specific validation types

def _validate_pdf_content(content: bytes) -> List[str]:
    """Validate PDF-specific content"""
    issues = []
    
    if not content.startswith(b'%PDF'):
        issues.append("Invalid PDF header")
    
    # Check for JavaScript in PDF
    if b'/JavaScript' in content or b'/JS' in content:
        issues.append("PDF contains JavaScript")
    
    # Check for forms or actions - TEMPORARILY DISABLED
    # if b'/Action' in content:
    #     issues.append("PDF contains actions")
    
    return issues


def _validate_office_content(content: bytes) -> List[str]:
    """Validate Office document content with appropriate checks for structured documents"""
    issues = []
    
    # Check for macros (VBA) - legitimate security concern
    macro_indicators = [
        b'vbaProject',
        b'macros/',
        b'xl/vbaProject',
        b'word/vbaProject',
        b'ppt/vbaProject',
    ]
    
    for indicator in macro_indicators:
        if indicator in content:
            issues.append("Office document contains macros")
            break
    
    # Check for embedded objects that could be dangerous
    dangerous_embeds = [
        b'application/x-msdownload',  # Executable files
        b'application/octet-stream',  # Binary files
        b'Content-Type: application/x-',  # Various executable types
    ]
    
    for embed in dangerous_embeds:
        if embed in content:
            issues.append("Office document contains potentially dangerous embedded content")
            break
    
    # Check for external data connections (could be used for data exfiltration)
    external_connection_indicators = [
        b'<Connection ',
        b'external="1"',
        b'refreshedVersion=',
    ]
    
    connection_count = 0
    for indicator in external_connection_indicators:
        if indicator in content:
            connection_count += 1
            
    if connection_count >= 2:  # Multiple indicators suggest external connections
        issues.append("Office document contains external data connections")
    
    return issues


def _validate_image_content(content: bytes) -> List[str]:
    """Validate image content"""
    issues = []
    
    # Check for embedded scripts in image metadata
    script_patterns = [
        b'<script',
        b'javascript:',
        b'<?php',
    ]
    
    for pattern in script_patterns:
        if pattern in content.lower():
            issues.append("Image contains embedded script")
            break
    
    return issues


def _validate_email(email: str) -> List[str]:
    """Validate email address"""
    errors = []
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        errors.append("Invalid email format")
    
    if len(email) > 254:  # RFC 5321 limit
        errors.append("Email address too long")
    
    return errors


def _validate_password(password: str) -> List[str]:
    """Validate password strength"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    
    if len(password) > 128:
        errors.append("Password too long (max 128 characters)")
    
    # Check for complexity
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain special character")
    
    return errors


def _validate_username(username: str) -> List[str]:
    """Validate username"""
    errors = []
    
    if len(username) < 3:
        errors.append("Username must be at least 3 characters")
    
    if len(username) > 30:
        errors.append("Username too long (max 30 characters)")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        errors.append("Username can only contain letters, numbers, underscores, and hyphens")
    
    return errors


def _validate_url(url: str) -> List[str]:
    """Validate URL"""
    errors = []
    
    try:
        parsed = urlparse(url)
        
        if not parsed.scheme in ['http', 'https']:
            errors.append("URL must use HTTP or HTTPS")
        
        if not parsed.netloc:
            errors.append("URL must have a valid domain")
        
        # Check for dangerous protocols
        dangerous_schemes = ['javascript', 'data', 'vbscript', 'file']
        if parsed.scheme.lower() in dangerous_schemes:
            errors.append(f"Dangerous URL scheme: {parsed.scheme}")
            
    except Exception:
        errors.append("Invalid URL format")
    
    return errors


def _get_json_depth(obj: Any, current_depth: int = 0) -> int:
    """Get maximum depth of JSON object"""
    if isinstance(obj, dict):
        if not obj:
            return current_depth
        return max(_get_json_depth(v, current_depth + 1) for v in obj.values())
    elif isinstance(obj, list):
        if not obj:
            return current_depth
        return max(_get_json_depth(item, current_depth + 1) for item in obj)
    else:
        return current_depth


def _validate_json_strings(obj: Any, errors: List[str]) -> None:
    """Recursively validate strings in JSON object"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str):
                is_valid, key_errors = validate_user_input(key, 'general')
                if not is_valid:
                    errors.extend([f"Invalid key '{key}': {err}" for err in key_errors])
            _validate_json_strings(value, errors)
    elif isinstance(obj, list):
        for item in obj:
            _validate_json_strings(item, errors)
    elif isinstance(obj, str):
        if len(obj) > 1000:  # Limit string length
            errors.append("JSON string value too long")
        is_valid, string_errors = validate_user_input(obj, 'general')
        if not is_valid:
            errors.extend([f"Invalid string value: {err}" for err in string_errors])


def _validate_json_schema(data: Dict[str, Any], schema: Dict) -> List[str]:
    """Basic JSON schema validation"""
    errors = []
    
    # Simple schema validation (expand as needed)
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Required field '{field}' missing")
    
    # Type validation
    properties = schema.get('properties', {})
    for field, field_schema in properties.items():
        if field in data:
            expected_type = field_schema.get('type')
            actual_value = data[field]
            
            if expected_type == 'string' and not isinstance(actual_value, str):
                errors.append(f"Field '{field}' must be string")
            elif expected_type == 'number' and not isinstance(actual_value, (int, float)):
                errors.append(f"Field '{field}' must be number")
            elif expected_type == 'boolean' and not isinstance(actual_value, bool):
                errors.append(f"Field '{field}' must be boolean")
    
    return errors