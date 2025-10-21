"""
Security Sanitizers Module

This module provides functions to sanitize and clean user input, filenames,
and content to prevent security vulnerabilities.
"""

import re
import html
import urllib.parse
from typing import Dict, Any, Optional
import os


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for storage
    """
    if not filename:
        return "unnamed_file"
    
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace dangerous characters
    dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(dangerous_chars, '_', filename)
    
    # Handle Windows reserved names
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_part = filename.rsplit('.', 1)[0] if '.' in filename else filename
    if name_part.upper() in reserved_names:
        filename = f"safe_{filename}"
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure not empty after sanitization
    if not filename:
        filename = "unnamed_file"
    
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename


def sanitize_content(content: str, content_type: str = 'html') -> str:
    """
    Sanitizes content based on type.
    
    Args:
        content: Content to sanitize
        content_type: Type of content ('html', 'text', 'json', etc.)
        
    Returns:
        Sanitized content
    """
    if not content:
        return ""
    
    if content_type == 'html':
        return _sanitize_html(content)
    elif content_type == 'text':
        return _sanitize_text(content)
    elif content_type == 'json':
        return _sanitize_json_string(content)
    elif content_type == 'url':
        return _sanitize_url(content)
    else:
        # Default to text sanitization
        return _sanitize_text(content)


def sanitize_user_input(user_input: str, input_type: str = 'general') -> str:
    """
    Sanitizes user input for safe processing.
    
    Args:
        user_input: User input to sanitize
        input_type: Type of input ('general', 'search', 'comment', etc.)
        
    Returns:
        Sanitized input
    """
    if not user_input:
        return ""
    
    # Remove null bytes
    user_input = user_input.replace('\x00', '')
    
    # Normalize unicode
    user_input = user_input.encode('utf-8', errors='ignore').decode('utf-8')
    
    # Remove control characters except common ones
    control_chars = ''.join(chr(i) for i in range(32) if i not in [9, 10, 13])  # Keep tab, LF, CR
    for char in control_chars:
        user_input = user_input.replace(char, '')
    
    # Type-specific sanitization
    if input_type == 'search':
        user_input = _sanitize_search_input(user_input)
    elif input_type == 'comment':
        user_input = _sanitize_html(user_input)
    elif input_type == 'email':
        user_input = _sanitize_email(user_input)
    
    # General cleanup
    user_input = user_input.strip()
    
    # Limit length
    max_lengths = {
        'general': 1000,
        'search': 200,
        'comment': 2000,
        'email': 254
    }
    max_len = max_lengths.get(input_type, 1000)
    if len(user_input) > max_len:
        user_input = user_input[:max_len]
    
    return user_input


def remove_script_tags(content: str) -> str:
    """
    Removes all script tags and their content.
    
    Args:
        content: Content to clean
        
    Returns:
        Content with script tags removed
    """
    # Remove script tags with content
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove lone script tags
    content = re.sub(r'</?script[^>]*>', '', content, flags=re.IGNORECASE)
    
    return content


def remove_dangerous_attributes(content: str) -> str:
    """
    Removes dangerous HTML attributes that could execute JavaScript.
    
    Args:
        content: HTML content to clean
        
    Returns:
        Content with dangerous attributes removed
    """
    dangerous_attrs = [
        r'on\w+\s*=\s*["\'][^"\']*["\']',  # Event handlers like onclick, onload
        r'javascript:\s*[^"\'>\s]*',        # JavaScript URLs
        r'vbscript:\s*[^"\'>\s]*',         # VBScript URLs
        r'data:\s*[^"\'>\s]*',             # Data URLs (can be dangerous)
    ]
    
    for pattern in dangerous_attrs:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    return content


def sanitize_json_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitizes JSON object keys to prevent injection attacks.
    
    Args:
        data: Dictionary to sanitize
        
    Returns:
        Dictionary with sanitized keys
    """
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    for key, value in data.items():
        # Sanitize key
        clean_key = re.sub(r'[^\w\-_.]', '', str(key))
        if len(clean_key) > 50:
            clean_key = clean_key[:50]
        
        # Recursively sanitize nested dictionaries
        if isinstance(value, dict):
            value = sanitize_json_keys(value)
        elif isinstance(value, list):
            value = [sanitize_json_keys(item) if isinstance(item, dict) else item for item in value]
        
        sanitized[clean_key] = value
    
    return sanitized


def strip_metadata(content: bytes, file_type: str) -> bytes:
    """
    Removes metadata from files to prevent information leakage.
    
    Args:
        content: File content
        file_type: Type of file
        
    Returns:
        Content with metadata removed
    """
    # Note: This is a simplified implementation
    # In practice, you'd use specialized libraries for each file type
    
    if file_type in ['jpg', 'jpeg']:
        return _strip_jpeg_metadata(content)
    elif file_type == 'pdf':
        return _strip_pdf_metadata(content)
    else:
        return content


# Helper functions for specific sanitization types

def _sanitize_html(html_content: str) -> str:
    """Sanitize HTML content"""
    # Remove script tags
    html_content = remove_script_tags(html_content)
    
    # Remove dangerous attributes
    html_content = remove_dangerous_attributes(html_content)
    
    # Escape remaining HTML
    html_content = html.escape(html_content)
    
    return html_content


def _sanitize_text(text_content: str) -> str:
    """Sanitize plain text content"""
    # Remove HTML tags completely
    text_content = re.sub(r'<[^>]+>', '', text_content)
    
    # Remove URLs that could be dangerous
    text_content = re.sub(r'javascript:[^\s]*', '', text_content, flags=re.IGNORECASE)
    text_content = re.sub(r'vbscript:[^\s]*', '', text_content, flags=re.IGNORECASE)
    
    # Remove excessive whitespace
    text_content = re.sub(r'\s+', ' ', text_content)
    
    return text_content.strip()


def _sanitize_json_string(json_str: str) -> str:
    """Sanitize JSON string content"""
    # Remove potential script injections
    json_str = json_str.replace('<script', '&lt;script')
    json_str = json_str.replace('</script>', '&lt;/script&gt;')
    json_str = json_str.replace('javascript:', 'blocked:')
    json_str = json_str.replace('vbscript:', 'blocked:')
    
    return json_str


def _sanitize_url(url: str) -> str:
    """Sanitize URL"""
    # Parse and rebuild URL to remove dangerous components
    try:
        parsed = urllib.parse.urlparse(url)
        
        # Block dangerous schemes
        if parsed.scheme.lower() in ['javascript', 'vbscript', 'data']:
            return ''
        
        # Ensure scheme is safe
        if parsed.scheme and parsed.scheme.lower() not in ['http', 'https', 'ftp']:
            return ''
        
        # Rebuild URL
        return urllib.parse.urlunparse(parsed)
    except:
        return ''


def _sanitize_search_input(search_input: str) -> str:
    """Sanitize search query input"""
    # Remove SQL injection patterns
    sql_patterns = [
        r'\bUNION\b', r'\bSELECT\b', r'\bINSERT\b', r'\bDELETE\b', 
        r'\bDROP\b', r'\bUPDATE\b', r'--', r'/\*', r'\*/',
        r"'", r'"', r';'
    ]
    
    for pattern in sql_patterns:
        search_input = re.sub(pattern, '', search_input, flags=re.IGNORECASE)
    
    # Remove excessive special characters
    search_input = re.sub(r'[^\w\s\-_@.]', '', search_input)
    
    return search_input


def _sanitize_email(email: str) -> str:
    """Sanitize email address"""
    # Remove dangerous characters
    email = re.sub(r'[^\w@.\-+]', '', email)
    
    # Basic format enforcement
    if '@' not in email:
        return ''
    
    return email.lower()


def _strip_jpeg_metadata(content: bytes) -> bytes:
    """Remove EXIF data from JPEG images"""
    # Simplified implementation - in practice use pillow or similar
    # This just removes obvious metadata markers
    
    # Find JPEG markers
    if not content.startswith(b'\xff\xd8'):
        return content  # Not a valid JPEG
    
    # Remove APP0-APP15 segments (which contain metadata)
    cleaned = b'\xff\xd8'  # Start with JPEG magic number
    i = 2
    
    while i < len(content) - 1:
        if content[i] == 0xff:
            marker = content[i + 1]
            
            # APP0-APP15 markers (0xe0-0xef) contain metadata
            if 0xe0 <= marker <= 0xef:
                # Skip this segment
                if i + 3 < len(content):
                    segment_length = (content[i + 2] << 8) | content[i + 3]
                    i += 2 + segment_length
                    continue
            
            # Keep other segments
            cleaned += content[i:i+2]
            i += 2
        else:
            cleaned += bytes([content[i]])
            i += 1
    
    return cleaned


def _strip_pdf_metadata(content: bytes) -> bytes:
    """Remove metadata from PDF files"""
    # Simplified implementation - remove obvious metadata
    
    # Remove /Info dictionary entries
    content = re.sub(rb'/Title\s*\([^)]*\)', b'', content)
    content = re.sub(rb'/Author\s*\([^)]*\)', b'', content)
    content = re.sub(rb'/Subject\s*\([^)]*\)', b'', content)
    content = re.sub(rb'/Creator\s*\([^)]*\)', b'', content)
    content = re.sub(rb'/Producer\s*\([^)]*\)', b'', content)
    content = re.sub(rb'/CreationDate\s*\([^)]*\)', b'', content)
    content = re.sub(rb'/ModDate\s*\([^)]*\)', b'', content)
    
    return content


def normalize_line_endings(content: str) -> str:
    """
    Normalize line endings to prevent CRLF injection attacks.
    
    Args:
        content: Content to normalize
        
    Returns:
        Content with normalized line endings
    """
    # Convert all line endings to LF
    content = content.replace('\r\n', '\n')
    content = content.replace('\r', '\n')
    
    return content


def truncate_safely(content: str, max_length: int, suffix: str = '...') -> str:
    """
    Safely truncate content without breaking in the middle of words or special sequences.
    
    Args:
        content: Content to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated content
    """
    if len(content) <= max_length:
        return content
    
    # Try to break at word boundary
    truncated = content[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If space is reasonably close to end
        truncated = truncated[:last_space]
    
    return truncated + suffix


def sanitize_search_query(query: str) -> str:
    """Sanitize search query for safe database operations"""
    return sanitize_user_input(query, 'search')


def sanitize_admin_params(params: dict) -> dict:
    """Sanitize admin parameters"""
    return sanitize_json_keys(params)
