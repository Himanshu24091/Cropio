"""
Universal Security Framework - Input Sanitizers
Advanced sanitization for preventing XSS, injection attacks, and data corruption
"""
import re
import html
import os
import unicodedata
from urllib.parse import quote, unquote

def sanitize_filename(filename, max_length=255):
    """
    Sanitize filename for safe storage and processing
    """
    if not filename:
        return "unnamed_file"
    
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKC', filename)
    
    # Remove path separators and dangerous characters
    dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\x00']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Remove path traversal attempts
    filename = filename.replace('..', '_')
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Handle Windows reserved names
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
    if name_without_ext.upper() in reserved_names:
        filename = f"safe_{filename}"
    
    # Truncate if too long
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext) - 1
        filename = f"{name[:max_name_length]}_{ext}"
    
    # Ensure filename is not empty
    if not filename or filename == '.':
        filename = "sanitized_file"
    
    return filename

def sanitize_search_query(query, max_length=100):
    """
    Sanitize search query to prevent injection attacks
    """
    if not query:
        return ""
    
    # Convert to string and normalize
    query = str(query)
    query = unicodedata.normalize('NFKC', query)
    
    # Remove dangerous SQL characters
    query = re.sub(r'[;\'\"\\]', '', query)
    
    # Remove script tags and javascript
    query = re.sub(r'<script[^>]*>.*?</script>', '', query, flags=re.IGNORECASE | re.DOTALL)
    query = re.sub(r'javascript:', '', query, flags=re.IGNORECASE)
    query = re.sub(r'vbscript:', '', query, flags=re.IGNORECASE)
    
    # Remove HTML tags
    query = re.sub(r'<[^>]+>', '', query)
    
    # HTML decode
    query = html.unescape(query)
    
    # Limit length
    if len(query) > max_length:
        query = query[:max_length]
    
    # Strip whitespace
    query = query.strip()
    
    return query

def sanitize_admin_params(param_value, max_length=500):
    """
    Sanitize admin input parameters with strict validation
    """
    if param_value is None:
        return None
    
    # Convert to string
    param_value = str(param_value)
    
    # Normalize unicode
    param_value = unicodedata.normalize('NFKC', param_value)
    
    # Remove control characters except newlines and tabs
    param_value = ''.join(char for char in param_value 
                         if unicodedata.category(char)[0] != 'C' or char in '\n\t')
    
    # Remove dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'data:',
        r'<iframe[^>]*>.*?</iframe>',
        r'<embed[^>]*>',
        r'<object[^>]*>.*?</object>'
    ]
    
    for pattern in dangerous_patterns:
        param_value = re.sub(pattern, '', param_value, flags=re.IGNORECASE | re.DOTALL)
    
    # HTML encode remaining content
    param_value = html.escape(param_value)
    
    # Limit length
    if len(param_value) > max_length:
        param_value = param_value[:max_length]
    
    # Strip whitespace
    param_value = param_value.strip()
    
    return param_value

def sanitize_html_content(content, allowed_tags=None):
    """
    Sanitize HTML content, allowing only safe tags
    """
    if not content:
        return ""
    
    content = str(content)
    
    # Default allowed tags
    if allowed_tags is None:
        allowed_tags = ['b', 'i', 'em', 'strong', 'u', 'br', 'p', 'div', 'span']
    
    # Remove all script and style tags
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove dangerous attributes
    dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'onfocus', 'onblur', 'onchange', 'onsubmit']
    for attr in dangerous_attrs:
        content = re.sub(f'{attr}\\s*=\\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
    
    # Remove javascript and vbscript URLs
    content = re.sub(r'javascript:[^"\'\\s]*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'vbscript:[^"\'\\s]*', '', content, flags=re.IGNORECASE)
    
    # If allowed_tags is empty, strip all HTML
    if not allowed_tags:
        content = re.sub(r'<[^>]+>', '', content)
    else:
        # Remove tags not in allowed list
        allowed_pattern = '|'.join(allowed_tags)
        content = re.sub(f'<(?!/?(?:{allowed_pattern})\\b)[^>]*>', '', content, flags=re.IGNORECASE)
    
    return content.strip()

def sanitize_file_content(content, content_type='text'):
    """
    Sanitize file content based on type
    """
    if not content:
        return content
    
    if isinstance(content, bytes):
        try:
            content = content.decode('utf-8', errors='ignore')
        except:
            return content  # Return binary content as-is if can't decode
    
    if content_type == 'text':
        # Remove null bytes and control characters
        content = content.replace('\x00', '')
        content = ''.join(char for char in content 
                         if unicodedata.category(char)[0] != 'C' or char in '\n\r\t')
        
        # Remove potential script injections
        content = sanitize_html_content(content, allowed_tags=[])
        
    elif content_type == 'html':
        # Allow basic HTML but sanitize dangerous content
        content = sanitize_html_content(content)
        
    elif content_type == 'csv':
        # Remove potential CSV injection
        lines = content.split('\n')
        sanitized_lines = []
        
        for line in lines:
            # Remove leading dangerous characters
            line = line.lstrip('=+-@')
            sanitized_lines.append(line)
        
        content = '\n'.join(sanitized_lines)
    
    return content

def sanitize_output_format(format_str):
    """
    Sanitize output format parameter
    """
    if not format_str:
        return "pdf"
    
    # Convert to lowercase and strip
    format_str = str(format_str).lower().strip()
    
    # Allow only alphanumeric characters and common format names
    format_str = re.sub(r'[^a-z0-9]', '', format_str)
    
    # List of safe output formats
    safe_formats = [
        'pdf', 'docx', 'doc', 'txt', 'rtf', 'html', 'odt',
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp',
        'csv', 'xlsx', 'xls', 'ods', 'json', 'xml'
    ]
    
    if format_str not in safe_formats:
        return "pdf"  # Default safe format
    
    return format_str

def sanitize_user_input(user_input, input_type='general'):
    """
    General-purpose user input sanitization
    """
    if not user_input:
        return ""
    
    user_input = str(user_input)
    
    # Normalize unicode
    user_input = unicodedata.normalize('NFKC', user_input)
    
    if input_type == 'email':
        # Basic email sanitization
        user_input = user_input.lower().strip()
        user_input = re.sub(r'[^a-z0-9@._-]', '', user_input)
        
    elif input_type == 'username':
        # Username sanitization
        user_input = user_input.lower().strip()
        user_input = re.sub(r'[^a-z0-9_-]', '', user_input)
        
    elif input_type == 'general':
        # General text sanitization
        user_input = html.escape(user_input)
        user_input = sanitize_html_content(user_input, allowed_tags=[])
        
    # Remove excessive whitespace
    user_input = re.sub(r'\s+', ' ', user_input)
    user_input = user_input.strip()
    
    return user_input

def sanitize_url_path(path):
    """
    Sanitize URL path to prevent directory traversal
    """
    if not path:
        return ""
    
    path = str(path)
    
    # Remove null bytes
    path = path.replace('\x00', '')
    
    # Normalize path separators
    path = path.replace('\\', '/')
    
    # Remove path traversal attempts
    path = re.sub(r'\.\.+', '', path)
    
    # Remove leading/trailing slashes
    path = path.strip('/')
    
    # URL decode
    path = unquote(path)
    
    # Remove dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '|', ';']
    for char in dangerous_chars:
        path = path.replace(char, '')
    
    # URL encode the result
    path = quote(path, safe='/')
    
    return path

def generate_safe_filename(original_filename, prefix="file", suffix=""):
    """
    Generate a safe filename with optional prefix and suffix
    """
    if not original_filename:
        original_filename = "unknown"
    
    # Sanitize the original filename
    safe_name = sanitize_filename(original_filename)
    
    # Split name and extension
    name, ext = os.path.splitext(safe_name)
    
    # Add prefix and suffix
    if prefix:
        name = f"{prefix}_{name}"
    if suffix:
        name = f"{name}_{suffix}"
    
    # Combine back with extension
    return f"{name}{ext}" if ext else name