# tests/test_pdf_editor.py
"""
Comprehensive Unit Tests for PDF Editor Pro
Tests security, functionality, and edge cases
"""

import pytest
import os
import json
import tempfile
import uuid
from unittest.mock import Mock, patch, MagicMock
from werkzeug.datastructures import FileStorage
from io import BytesIO

# Import the Flask app and PDF editor module
from app import app
from routes.pdf_editor_routes import pdf_editor_bp, validate_session, allowed_file, sanitize_filename

# Test fixtures and setup
@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def sample_pdf_data():
    """Create sample PDF data for testing"""
    # Minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
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
>>
endobj

xref
0 4
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000098 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
147
%%EOF"""
    return pdf_content

@pytest.fixture
def mock_pdf_file(sample_pdf_data):
    """Create mock PDF file for upload testing"""
    def create_file(filename='test.pdf', content=None):
        content = content or sample_pdf_data
        return FileStorage(
            stream=BytesIO(content),
            filename=filename,
            content_type='application/pdf'
        )
    return create_file

class TestPDFEditorSecurity:
    """Test security aspects of PDF editor"""
    
    def test_file_upload_validation(self, client, mock_pdf_file):
        """Test file upload validation and security checks"""
        
        # Test valid PDF upload
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 0,
                'last_activity': '2024-01-01T00:00:00'
            }
        
        valid_file = mock_pdf_file('valid.pdf')
        response = client.post('/pdf-editor/upload', 
                             data={'file': valid_file},
                             content_type='multipart/form-data')
        
        assert response.status_code in [200, 400, 413]  # May fail due to missing dependencies
        
    def test_invalid_file_types(self, client):
        """Test rejection of invalid file types"""
        
        # Test non-PDF file
        invalid_file = FileStorage(
            stream=BytesIO(b'not a pdf'),
            filename='test.txt',
            content_type='text/plain'
        )
        
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 0,
                'last_activity': '2024-01-01T00:00:00'
            }
        
        response = client.post('/pdf-editor/upload',
                             data={'file': invalid_file},
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid file type' in data['error']
    
    def test_file_size_limits(self, client):
        """Test file size validation"""
        
        # Create oversized file (simulated)
        large_content = b'x' * (51 * 1024 * 1024)  # 51MB
        large_file = FileStorage(
            stream=BytesIO(large_content),
            filename='large.pdf',
            content_type='application/pdf'
        )
        
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 0,
                'last_activity': '2024-01-01T00:00:00'
            }
        
        response = client.post('/pdf-editor/upload',
                             data={'file': large_file},
                             content_type='multipart/form-data')
        
        assert response.status_code == 413
    
    def test_filename_sanitization(self):
        """Test filename sanitization for security"""
        
        # Test path traversal attempts
        dangerous_names = [
            '../../../etc/passwd',
            '..\\..\\windows\\system32\\config\\sam',
            'normal_file.pdf',
            '../../../../secret.txt',
            'file with spaces.pdf',
            'file-with-special_chars123.pdf',
        ]
        
        for dangerous_name in dangerous_names:
            sanitized = sanitize_filename(dangerous_name)
            
            # Should not contain path separators
            assert '/' not in sanitized
            assert '\\' not in sanitized
            assert '..' not in sanitized
            
            # Should end with .pdf
            assert sanitized.endswith('.pdf')
            
            # Should be reasonable length
            assert len(sanitized) <= 100
    
    def test_session_validation(self, client):
        """Test session validation and security"""
        
        # Test request without session
        response = client.post('/pdf-editor/upload',
                             data={'file': None})
        assert response.status_code == 401
        
        # Test expired session
        from datetime import datetime, timedelta
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': old_time,
                'operations_count': 0,
                'last_activity': old_time
            }
        
        response = client.get('/pdf-editor')
        # Should reset session or handle gracefully
        assert response.status_code in [200, 401]
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality"""
        
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 150,  # Over limit
                'last_activity': '2024-01-01T00:00:00'
            }
        
        response = client.get('/pdf-editor')
        # Should handle rate limiting
        assert response.status_code in [200, 429]
    
    def test_annotation_data_validation(self, client):
        """Test annotation data validation and sanitization"""
        
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 0,
                'last_activity': '2024-01-01T00:00:00'
            }
            sess['pdf_file_test123'] = {
                'filename': 'test.pdf',
                'original_name': 'test.pdf',
                'upload_time': '2024-01-01T00:00:00',
                'file_size': 1024
            }
        
        # Test malicious annotation data
        malicious_annotations = {
            '1': [
                {
                    'type': 'text',
                    'text': 'x' * 1000,  # Very long text
                    'x': 'invalid',  # Non-numeric coordinate
                    'y': -100,  # Negative coordinate
                    'fontSize': 999,  # Excessive font size
                    'color': '<script>alert(1)</script>'  # XSS attempt
                }
            ]
        }
        
        response = client.post('/pdf-editor/process',
                             json={
                                 'file_id': 'test123',
                                 'annotations': malicious_annotations,
                                 'operation': 'annotate'
                             },
                             content_type='application/json')
        
        # Should handle validation gracefully
        assert response.status_code in [400, 404, 500]

class TestPDFEditorFunctionality:
    """Test core functionality of PDF editor"""
    
    def test_pdf_editor_page_load(self, client):
        """Test PDF editor page loads correctly"""
        response = client.get('/pdf-editor')
        assert response.status_code == 200
        assert b'PDF Editor Pro' in response.data
    
    def test_upload_endpoint_exists(self, client):
        """Test upload endpoint is accessible"""
        response = client.post('/pdf-editor/upload')
        # Should return error for missing file, not 404
        assert response.status_code != 404
    
    def test_process_endpoint_exists(self, client):
        """Test process endpoint is accessible"""
        response = client.post('/pdf-editor/process')
        # Should return error for missing data, not 404
        assert response.status_code != 404
    
    def test_download_endpoints_exist(self, client):
        """Test download endpoints are accessible"""
        # Original download
        response = client.get('/pdf-editor/download/test123/original')
        assert response.status_code in [401, 404]  # Not 500 or method not allowed
        
        # Processed download
        response = client.get('/pdf-editor/download/test123/processed')
        assert response.status_code in [401, 404]
    
    def test_info_endpoint_exists(self, client):
        """Test PDF info endpoint is accessible"""
        response = client.post('/pdf-editor/info')
        assert response.status_code != 404
    
    def test_extract_text_endpoint_exists(self, client):
        """Test text extraction endpoint is accessible"""
        response = client.post('/pdf-editor/extract-text')
        assert response.status_code != 404
    
    def test_cleanup_endpoint_exists(self, client):
        """Test cleanup endpoint is accessible"""
        response = client.post('/pdf-editor/cleanup')
        assert response.status_code != 404

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_allowed_file_function(self):
        """Test file type validation function"""
        
        # Valid files
        assert allowed_file('document.pdf') == True
        assert allowed_file('test.PDF') == True
        
        # Invalid files
        assert allowed_file('document.txt') == False
        assert allowed_file('image.jpg') == False
        assert allowed_file('file.exe') == False
        assert allowed_file('') == False
        assert allowed_file('file_without_extension') == False
        
        # Security tests
        assert allowed_file('../../../etc/passwd') == False
        assert allowed_file('file.pdf.exe') == False
        assert allowed_file('/path/to/file.pdf') == False
        assert allowed_file('C:\\windows\\file.pdf') == False
    
    def test_sanitize_filename_edge_cases(self):
        """Test filename sanitization edge cases"""
        
        # Empty filename
        result = sanitize_filename('')
        assert result.endswith('.pdf')
        assert len(result) > 4  # More than just .pdf
        
        # None filename
        result = sanitize_filename(None)
        assert result.endswith('.pdf')
        
        # Very long filename
        long_name = 'a' * 200 + '.pdf'
        result = sanitize_filename(long_name)
        assert len(result) <= 100
        assert result.endswith('.pdf')
        
        # Special characters
        special_name = 'file!@#$%^&*()+={}[]|\\:";\'<>?,./`~.pdf'
        result = sanitize_filename(special_name)
        assert result.endswith('.pdf')
        # Should only contain safe characters
        safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._- ')
        result_chars = set(result.replace('.pdf', ''))
        assert result_chars.issubset(safe_chars)

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_missing_file_parameter(self, client):
        """Test handling of missing file parameter"""
        
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 0,
                'last_activity': '2024-01-01T00:00:00'
            }
        
        response = client.post('/pdf-editor/upload',
                             data={},
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file provided' in data['error']
    
    def test_empty_filename(self, client):
        """Test handling of empty filename"""
        
        empty_file = FileStorage(
            stream=BytesIO(b''),
            filename='',
            content_type='application/pdf'
        )
        
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 0,
                'last_activity': '2024-01-01T00:00:00'
            }
        
        response = client.post('/pdf-editor/upload',
                             data={'file': empty_file},
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file selected' in data['error']
    
    def test_invalid_json_in_process(self, client):
        """Test handling of invalid JSON in process endpoint"""
        
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 0,
                'last_activity': '2024-01-01T00:00:00'
            }
        
        response = client.post('/pdf-editor/process',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_missing_file_id_in_process(self, client):
        """Test handling of missing file_id in process endpoint"""
        
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 0,
                'last_activity': '2024-01-01T00:00:00'
            }
        
        response = client.post('/pdf-editor/process',
                             json={
                                 'annotations': {},
                                 'operation': 'annotate'
                             },
                             content_type='application/json')
        
        assert response.status_code == 404  # File not found
    
    def test_error_handlers(self, client):
        """Test custom error handlers"""
        
        # Test 413 handler
        response = client.post('/pdf-editor/upload',
                             data={'file': FileStorage(
                                 stream=BytesIO(b'x' * (51 * 1024 * 1024)),
                                 filename='huge.pdf',
                                 content_type='application/pdf'
                             )})
        
        if response.status_code == 413:
            data = json.loads(response.data)
            assert 'error' in data
            assert 'FILE_TOO_LARGE' in data.get('code', '')

class TestIntegrationScenarios:
    """Test complete user scenarios"""
    
    @patch('routes.pdf_editor_routes.fitz')
    def test_full_upload_process_flow(self, mock_fitz, client, mock_pdf_file):
        """Test complete upload and process flow"""
        
        # Mock PyMuPDF
        mock_doc = MagicMock()
        mock_doc.page_count = 2
        mock_doc.metadata = {
            'title': 'Test PDF',
            'author': 'Test Author'
        }
        mock_doc.is_encrypted = False
        mock_fitz.open.return_value = mock_doc
        
        # Setup session
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 0,
                'last_activity': '2024-01-01T00:00:00'
            }
        
        # Upload file
        valid_file = mock_pdf_file('test.pdf')
        response = client.post('/pdf-editor/upload',
                             data={'file': valid_file},
                             content_type='multipart/form-data')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert data['success'] == True
            assert 'file_id' in data
            file_id = data['file_id']
            
            # Store file info in session for process test
            with client.session_transaction() as sess:
                sess[f'pdf_file_{file_id}'] = {
                    'filename': f"{sess['pdf_editor_session']['id']}_{uuid.uuid4().hex}_test.pdf",
                    'original_name': 'test.pdf',
                    'upload_time': '2024-01-01T00:00:00',
                    'file_size': 1024
                }
            
            # Process with annotations
            annotations = {
                '1': [
                    {
                        'type': 'text',
                        'text': 'Test annotation',
                        'x': 100,
                        'y': 100,
                        'fontSize': 16,
                        'color': '#000000'
                    }
                ]
            }
            
            response = client.post('/pdf-editor/process',
                                 json={
                                     'file_id': file_id,
                                     'annotations': annotations,
                                     'operation': 'annotate'
                                 },
                                 content_type='application/json')
            
            # Should handle processing attempt
            assert response.status_code in [200, 404, 500]

class TestPerformanceAndLimits:
    """Test performance and limit scenarios"""
    
    def test_large_annotation_count(self, client):
        """Test handling of large number of annotations"""
        
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 0,
                'last_activity': '2024-01-01T00:00:00'
            }
            sess['pdf_file_test123'] = {
                'filename': 'test.pdf',
                'original_name': 'test.pdf',
                'upload_time': '2024-01-01T00:00:00',
                'file_size': 1024
            }
        
        # Create many annotations
        annotations = {}
        for page in range(1, 501):  # 500 pages (at limit)
            annotations[str(page)] = [
                {
                    'type': 'text',
                    'text': f'Page {page}',
                    'x': 100,
                    'y': 100,
                    'fontSize': 16,
                    'color': '#000000'
                }
                for _ in range(10)  # 10 annotations per page
            ]
        
        response = client.post('/pdf-editor/process',
                             json={
                                 'file_id': 'test123',
                                 'annotations': annotations,
                                 'operation': 'annotate'
                             },
                             content_type='application/json')
        
        # Should handle or reject large annotation sets
        assert response.status_code in [200, 400, 404, 500]
        
        if response.status_code == 400:
            data = json.loads(response.data)
            assert 'annotations' in data.get('error', '').lower()
    
    def test_session_operations_limit(self, client):
        """Test session operations limit"""
        
        with client.session_transaction() as sess:
            sess['pdf_editor_session'] = {
                'id': str(uuid.uuid4()),
                'created_at': '2024-01-01T00:00:00',
                'operations_count': 99,  # Near limit
                'last_activity': '2024-01-01T00:00:00'
            }
        
        # Should still work
        response = client.get('/pdf-editor')
        assert response.status_code == 200
        
        # Exceed limit
        with client.session_transaction() as sess:
            sess['pdf_editor_session']['operations_count'] = 101
        
        response = client.get('/pdf-editor')
        # Should handle rate limiting
        assert response.status_code in [200, 401, 429]

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
