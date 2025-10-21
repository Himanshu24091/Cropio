"""
Security Testing Infrastructure

This module provides utilities and fixtures for testing security functionality.

Features:
- Mock file generators for testing
- Test data and fixtures
- Security test utilities
- Malware simulation (safe samples)

Usage:
    from security.tests import create_test_image, create_malicious_pdf_sample
    
    # Create test file for upload testing
    test_file = create_test_image('jpg', size=(100, 100))
    
    # Create safe malware sample for scanner testing
    malware_sample = create_malicious_pdf_sample(safe=True)
"""

import os
import io
import tempfile
from typing import Dict, List, Optional, Union, BinaryIO
from pathlib import Path

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / 'fixtures'
MALWARE_SAMPLES_DIR = Path(__file__).parent / 'malware_samples'

# Ensure test directories exist
TEST_DATA_DIR.mkdir(exist_ok=True)
MALWARE_SAMPLES_DIR.mkdir(exist_ok=True)

# Test file generators
def create_test_image(file_format: str = 'jpg', size: tuple = (100, 100), 
                     color: tuple = (255, 255, 255)) -> io.BytesIO:
    """
    Create a test image file in memory
    
    Args:
        file_format: Image format (jpg, png, gif, etc.)
        size: Image dimensions (width, height)
        color: RGB color tuple
        
    Returns:
        BytesIO buffer containing the image
    """
    try:
        from PIL import Image
        
        # Create image
        img = Image.new('RGB', size, color)
        
        # Save to buffer
        buffer = io.BytesIO()
        img.save(buffer, format=file_format.upper())
        buffer.seek(0)
        
        return buffer
    except ImportError:
        # Fallback: create a minimal valid image header
        if file_format.lower() == 'jpg':
            # Minimal JPEG header
            buffer = io.BytesIO(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb')
        elif file_format.lower() == 'png':
            # Minimal PNG header
            buffer = io.BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde')
        else:
            # Generic binary data
            buffer = io.BytesIO(b'TEST_IMAGE_DATA' + b'\x00' * 100)
        
        buffer.seek(0)
        return buffer

def create_test_pdf(content: str = "Test PDF Content", 
                   include_javascript: bool = False) -> io.BytesIO:
    """
    Create a test PDF file
    
    Args:
        content: Text content for the PDF
        include_javascript: Whether to include JavaScript (for malware testing)
        
    Returns:
        BytesIO buffer containing the PDF
    """
    # Basic PDF structure
    pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length {len(content) + 50}
>>
stream
BT
/F1 12 Tf
72 720 Td
({content}) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
{300 + len(content)}
%%EOF"""

    if include_javascript:
        # Add JavaScript for malware testing (safe, non-functional)
        pdf_content = pdf_content.replace(
            "/Contents 4 0 R",
            "/Contents 4 0 R\n/OpenAction << /S /JavaScript /JS (app.alert('Test');) >>"
        )

    buffer = io.BytesIO(pdf_content.encode())
    buffer.seek(0)
    return buffer

def create_test_document(doc_type: str = 'txt', content: str = "Test document content") -> io.BytesIO:
    """
    Create a test document file
    
    Args:
        doc_type: Document type (txt, html, xml, etc.)
        content: Document content
        
    Returns:
        BytesIO buffer containing the document
    """
    if doc_type == 'html':
        content = f"<html><body><h1>{content}</h1></body></html>"
    elif doc_type == 'xml':
        content = f"<?xml version='1.0'?><root><content>{content}</content></root>"
    elif doc_type == 'json':
        content = f'{{"content": "{content}"}}'
    
    buffer = io.BytesIO(content.encode('utf-8'))
    buffer.seek(0)
    return buffer

def create_malware_sample(sample_type: str = 'eicar', safe: bool = True) -> io.BytesIO:
    """
    Create safe malware samples for testing
    
    Args:
        sample_type: Type of malware sample (eicar, script, pdf_js)
        safe: Whether to create safe, non-functional samples
        
    Returns:
        BytesIO buffer containing the sample
    """
    if sample_type == 'eicar' and safe:
        # Standard EICAR test string (safe, detected by all AV)
        content = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
    elif sample_type == 'script':
        # Suspicious script patterns (safe, non-functional)
        content = b'<script>alert("test");</script><?php system($_GET["cmd"]); ?>'
    elif sample_type == 'pdf_js':
        return create_test_pdf("Test PDF", include_javascript=True)
    elif sample_type == 'zip_bomb':
        # Minimal ZIP with suspicious compression ratio
        content = b'PK\x03\x04\x14\x00\x00\x00\x08\x00' + b'A' * 1000 + b'PK\x01\x02'
    else:
        content = b'MALWARE_SAMPLE_' + sample_type.encode() + b'_TEST'
    
    buffer = io.BytesIO(content)
    buffer.seek(0)
    return buffer

def create_large_file(size_mb: int = 10) -> io.BytesIO:
    """
    Create a large file for size limit testing
    
    Args:
        size_mb: Size in megabytes
        
    Returns:
        BytesIO buffer containing the large file
    """
    size_bytes = size_mb * 1024 * 1024
    chunk_size = 1024 * 1024  # 1MB chunks
    
    buffer = io.BytesIO()
    
    # Write in chunks to avoid memory issues
    remaining = size_bytes
    while remaining > 0:
        chunk_data = b'A' * min(chunk_size, remaining)
        buffer.write(chunk_data)
        remaining -= len(chunk_data)
    
    buffer.seek(0)
    return buffer

def create_test_archive(archive_type: str = 'zip', 
                       files: Dict[str, bytes] = None) -> io.BytesIO:
    """
    Create a test archive file
    
    Args:
        archive_type: Archive type (zip, tar, etc.)
        files: Dictionary of filename -> content
        
    Returns:
        BytesIO buffer containing the archive
    """
    import zipfile
    
    if files is None:
        files = {
            'test.txt': b'Test file content',
            'image.jpg': create_test_image('jpg').getvalue()
        }
    
    buffer = io.BytesIO()
    
    if archive_type == 'zip':
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files.items():
                zf.writestr(filename, content)
    else:
        # Fallback: create a simple "archive" format
        for filename, content in files.items():
            buffer.write(f"FILE:{filename}:".encode())
            buffer.write(content)
            buffer.write(b'\n---\n')
    
    buffer.seek(0)
    return buffer

# Test utilities
class SecurityTestUtils:
    """Utilities for security testing"""
    
    @staticmethod
    def create_mock_request(method: str = 'POST', content_type: str = 'multipart/form-data',
                           headers: Dict[str, str] = None, data: Dict = None):
        """Create a mock request for testing"""
        # This would need to be implemented with actual Flask test client
        # For now, return a basic structure
        return {
            'method': method,
            'content_type': content_type,
            'headers': headers or {},
            'data': data or {}
        }
    
    @staticmethod
    def assert_security_violation(response, violation_type: str):
        """Assert that a security violation was properly detected"""
        # Implementation depends on test framework
        assert response.status_code in [400, 403, 422, 429], f"Expected security violation, got {response.status_code}"
    
    @staticmethod
    def create_test_user(user_type: str = 'free'):
        """Create a test user for authentication testing"""
        from security.config import UserType
        
        return {
            'id': 1,
            'username': f'test_user_{user_type}',
            'email': f'test_{user_type}@example.com',
            'user_type': user_type,
            'is_active': True,
            'created_at': '2025-01-01T00:00:00Z'
        }

# Test fixtures for common scenarios
TEST_FILES = {
    'valid_image_jpg': lambda: create_test_image('jpg'),
    'valid_image_png': lambda: create_test_image('png'),
    'valid_pdf': lambda: create_test_pdf(),
    'valid_text': lambda: create_test_document('txt'),
    'malware_eicar': lambda: create_malware_sample('eicar'),
    'malware_script': lambda: create_malware_sample('script'),
    'malicious_pdf': lambda: create_malware_sample('pdf_js'),
    'large_file_50mb': lambda: create_large_file(50),
    'large_file_100mb': lambda: create_large_file(100),
    'test_archive': lambda: create_test_archive()
}

TEST_SCENARIOS = {
    'file_upload_valid': {
        'file': 'valid_image_jpg',
        'expected_result': 'success'
    },
    'file_upload_too_large': {
        'file': 'large_file_100mb',
        'expected_result': 'file_too_large'
    },
    'file_upload_malware': {
        'file': 'malware_eicar',
        'expected_result': 'malware_detected'
    },
    'rate_limit_exceeded': {
        'requests': 100,
        'time_window': 60,
        'expected_result': 'rate_limit_exceeded'
    }
}

# Export main testing functions
__all__ = [
    'create_test_image',
    'create_test_pdf',
    'create_test_document',
    'create_malware_sample',
    'create_large_file',
    'create_test_archive',
    'SecurityTestUtils',
    'TEST_FILES',
    'TEST_SCENARIOS',
    'TEST_DATA_DIR',
    'MALWARE_SAMPLES_DIR'
]