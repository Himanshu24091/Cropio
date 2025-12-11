# Security Framework Migration Guide

## Overview

This guide provides step-by-step instructions for migrating from the existing `utils/security.py` implementation to the new comprehensive security framework. The migration is designed to be incremental and backward-compatible where possible.

## Migration Strategy

### Phase 1: Preparation and Setup
### Phase 2: Core Security Migration
### Phase 3: Feature-Specific Migrations
### Phase 4: Testing and Validation
### Phase 5: Cleanup and Optimization

---

## Phase 1: Preparation and Setup

### 1.1 Install Dependencies

First, install the new required packages:

```bash
pip install python-magic yara-python clamav-python redis bleach cryptography argon2-cffi
```

### 1.2 Update Requirements

Add to your `requirements.txt`:

```txt
# Security Framework Dependencies
python-magic>=0.4.27
yara-python>=4.3.1
clamav-python>=0.103.8
redis>=4.5.4
bleach>=6.0.0
cryptography>=41.0.0
argon2-cffi>=23.1.0
```

### 1.3 Configuration Setup

Create initial security configuration:

```python
# config/security_settings.py
from security.config import SecurityConfig, SecurityLevel

# Development configuration
SECURITY_CONFIG = SecurityConfig(
    environment='development',
    security_level=SecurityLevel.MEDIUM,
    enable_malware_scanning=False,  # Start disabled for dev
    rate_limit_enabled=True
)

# Production configuration (for later)
PRODUCTION_SECURITY_CONFIG = SecurityConfig(
    environment='production',
    security_level=SecurityLevel.HIGH,
    enable_malware_scanning=True,
    strict_file_validation=True,
    enable_audit_logging=True
)
```

### 1.4 Initialize Security Framework

Update your Flask app initialization:

```python
# app.py or main.py
from security import initialize_security
from config.security_settings import SECURITY_CONFIG

app = Flask(__name__)

# Initialize security framework
initialize_security(app, SECURITY_CONFIG)
```

---

## Phase 2: Core Security Migration

### 2.1 CSRF Protection Migration

**Before (utils/security.py):**
```python
from utils.security import generate_csrf_token, validate_csrf_token

@app.route('/form')
def show_form():
    token = generate_csrf_token()
    return render_template('form.html', csrf_token=token)

@app.route('/submit', methods=['POST'])
def submit_form():
    if not validate_csrf_token(request.form.get('csrf_token')):
        abort(403)
    # Process form
```

**After (new security framework):**
```python
from security.core.decorators import require_csrf
from security.web_security.csrf import generate_csrf_token

@app.route('/form')
def show_form():
    token = generate_csrf_token(user_id=session.get('user_id'))
    return render_template('form.html', csrf_token=token)

@app.route('/submit', methods=['POST'])
@require_csrf()  # Automatic validation
def submit_form():
    # Process form - CSRF automatically validated
    pass
```

### 2.2 Rate Limiting Migration

**Before:**
```python
from utils.security import check_rate_limit

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if not check_rate_limit(request.remote_addr):
        return {"error": "Rate limit exceeded"}, 429
    # Process upload
```

**After:**
```python
from security.core.decorators import rate_limit

@app.route('/api/upload', methods=['POST'])
@rate_limit(requests_per_minute=10, per_user=True)
def upload_file():
    # Process upload - rate limiting automatic
    pass
```

### 2.3 File Validation Migration

**Before:**
```python
from utils.security import validate_file_upload

@app.route('/upload', methods=['POST'])
def upload_document():
    file = request.files['document']
    if not validate_file_upload(file, ['pdf', 'docx'], max_size=50*1024*1024):
        return {"error": "Invalid file"}, 400
    # Process file
```

**After:**
```python
from security.core.decorators import validate_file_upload

@app.route('/upload', methods=['POST'])
@validate_file_upload(allowed_types=['pdf', 'docx'], max_size_mb=50, scan_malware=True)
def upload_document():
    # File validation automatic, including malware scanning
    file = request.files['document']
    # Process file
```

### 2.4 Security Headers Migration

**Before:**
```python
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response
```

**After:**
```python
from security.web_security.headers import SecurityHeaders

security_headers = SecurityHeaders()

@app.after_request
def apply_security_headers(response):
    return security_headers.apply_security_headers(response, SECURITY_CONFIG)
```

---

## Phase 3: Feature-Specific Migrations

### 3.1 PDF Processing Security

**Before:**
```python
def process_pdf(file_path):
    # Basic validation
    if not file_path.endswith('.pdf'):
        raise ValueError("Not a PDF file")
    
    # Process PDF
    with open(file_path, 'rb') as f:
        content = f.read()
    # ... processing logic
```

**After:**
```python
from security.file_security import analyze_pdf_content, scan_for_malware
from security.core.validators import validate_content

def process_pdf(file_path):
    # Comprehensive validation
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # Malware scanning
    scan_result = scan_for_malware(content, 'pdf')
    if not scan_result.is_safe:
        raise MalwareDetectedError(f"Threats found: {scan_result.threats}")
    
    # Content validation
    is_safe, issues = validate_content(content, 'pdf')
    if not is_safe:
        raise ContentValidationError(f"Content issues: {issues}")
    
    # Deep PDF analysis
    analysis = analyze_pdf_content(content)
    if analysis.has_security_risks:
        raise SecurityViolationError(f"PDF security risks: {analysis.risks}")
    
    # Process PDF (now safe)
    # ... processing logic
```

### 3.2 Document Conversion Security

**Before:**
```python
def convert_document(input_file, output_format):
    # Basic checks
    if os.path.getsize(input_file) > 100 * 1024 * 1024:
        raise ValueError("File too large")
    
    # Convert
    # ... conversion logic
```

**After:**
```python
from security.core.decorators import validate_file_upload
from security.file_security import FileValidator
from security.core.sanitizers import sanitize_filename

def convert_document(input_file, output_format, user_type='basic'):
    # Get security config
    config = current_app.security_config
    
    # Validate file size based on user type and file type
    file_ext = input_file.split('.')[-1].lower()
    max_size = config.get_max_file_size(file_ext, user_type)
    
    validator = FileValidator()
    if not validator.validate_file_size(input_file, max_size):
        raise FileSizeExceededError(f"File exceeds {max_size/1024/1024}MB limit")
    
    # Validate file type
    if not config.is_file_type_allowed(file_ext):
        raise InvalidFileTypeError(f"File type {file_ext} not allowed")
    
    # Content validation
    with open(input_file, 'rb') as f:
        content = f.read()
    
    is_safe, issues = validate_content(content, file_ext)
    if not is_safe:
        raise ContentValidationError(f"Content validation failed: {issues}")
    
    # Sanitize output filename
    safe_output_name = sanitize_filename(f"converted_{uuid4()}.{output_format}")
    
    # Convert (now safe)
    # ... conversion logic
```

### 3.3 User Input Validation Migration

**Before:**
```python
def process_user_input(user_data):
    # Basic validation
    if len(user_data) > 1000:
        raise ValueError("Input too long")
    
    # Process
    # ... processing logic
```

**After:**
```python
from security.core.validators import validate_user_input
from security.core.sanitizers import sanitize_content

def process_user_input(user_data, input_type='general'):
    # Comprehensive validation
    is_valid, errors = validate_user_input(user_data, input_type)
    if not is_valid:
        raise ContentValidationError(f"Input validation failed: {errors}")
    
    # Sanitize content
    safe_data = sanitize_content(user_data, 'text')
    
    # Process sanitized data
    # ... processing logic with safe_data
```

---

## Phase 4: Testing and Validation

### 4.1 Create Migration Tests

Create comprehensive tests to validate the migration:

```python
# tests/test_security_migration.py
import pytest
from security.tests import create_mock_file, create_malware_sample
from security.file_security import scan_for_malware

class TestSecurityMigration:
    
    def test_csrf_protection_migration(self, client):
        """Test CSRF protection works after migration"""
        # Test that CSRF-protected endpoints require valid tokens
        response = client.post('/submit', data={'data': 'test'})
        assert response.status_code == 403  # CSRF validation should fail
        
    def test_rate_limiting_migration(self, client):
        """Test rate limiting works after migration"""
        # Make multiple requests to trigger rate limit
        for _ in range(15):  # Assuming 10 req/min limit
            response = client.post('/api/upload')
        
        assert response.status_code == 429  # Rate limit should be hit
        
    def test_file_validation_migration(self):
        """Test file validation improvements"""
        # Test safe file
        safe_pdf = create_mock_file('pdf', size_kb=100)
        result = scan_for_malware(safe_pdf, 'pdf')
        assert result.is_safe
        
        # Test malware detection
        malware_pdf = create_malware_sample('eicar')
        result = scan_for_malware(malware_pdf, 'pdf')
        assert not result.is_safe
```

### 4.2 Performance Testing

Test that the new security framework doesn't significantly impact performance:

```python
# tests/test_performance.py
import time
from security.file_security import scan_for_malware
from security.tests import create_mock_file

def test_scanning_performance():
    """Test malware scanning performance"""
    large_file = create_mock_file('pdf', size_kb=5000)  # 5MB file
    
    start_time = time.time()
    result = scan_for_malware(large_file, 'pdf')
    scan_time = time.time() - start_time
    
    # Scanning should complete within reasonable time
    assert scan_time < 10.0  # 10 seconds max for 5MB file
    assert result is not None
```

### 4.3 Integration Testing

Test integration with existing application features:

```python
# tests/test_integration.py
def test_pdf_conversion_integration(client):
    """Test PDF conversion with new security"""
    # Upload a valid PDF
    with open('tests/fixtures/sample.pdf', 'rb') as f:
        response = client.post('/convert', data={
            'file': (f, 'sample.pdf'),
            'format': 'docx'
        })
    
    assert response.status_code == 200
    
def test_malware_blocking_integration(client):
    """Test that malware is properly blocked"""
    malware_content = create_malware_sample('eicar')
    
    response = client.post('/upload', data={
        'file': (io.BytesIO(malware_content), 'malware.pdf')
    })
    
    assert response.status_code == 400
    assert 'malware' in response.get_json()['error'].lower()
```

---

## Phase 5: Cleanup and Optimization

### 5.1 Remove Old Security Code

After confirming the migration works correctly:

1. **Backup the old code:**
   ```bash
   cp utils/security.py utils/security.py.backup
   ```

2. **Update imports throughout the codebase:**
   ```bash
   # Find all files that import from utils.security
   grep -r "from utils.security" . --include="*.py"
   
   # Update each file to use new imports
   ```

3. **Remove or deprecate old functions:**
   ```python
   # utils/security.py - Add deprecation warnings first
   import warnings
   
   def validate_csrf_token(*args, **kwargs):
       warnings.warn(
           "utils.security.validate_csrf_token is deprecated. "
           "Use security.web_security.csrf.validate_csrf_token",
           DeprecationWarning,
           stacklevel=2
       )
       from security.web_security.csrf import validate_csrf_token
       return validate_csrf_token(*args, **kwargs)
   ```

### 5.2 Update Configuration

**Production Configuration:**
```python
# config/production.py
from security.config import SecurityConfig, SecurityLevel

SECURITY_CONFIG = SecurityConfig(
    environment='production',
    security_level=SecurityLevel.HIGH,
    enable_malware_scanning=True,
    strict_file_validation=True,
    enable_audit_logging=True,
    rate_limit_multiplier=0.5,  # Stricter rate limits
    max_file_size_multiplier=1.0  # Standard file sizes
)
```

**Development Configuration:**
```python
# config/development.py
SECURITY_CONFIG = SecurityConfig(
    environment='development',
    security_level=SecurityLevel.MEDIUM,
    enable_malware_scanning=False,  # Faster development
    rate_limit_multiplier=2.0,  # More lenient for testing
    max_file_size_multiplier=1.5
)
```

### 5.3 Monitoring and Alerting

Set up monitoring for the new security features:

```python
# monitoring/security_monitoring.py
from security.utils.monitoring import SecurityMonitor
from security.utils.logging import SecurityLogger

# Initialize monitoring
monitor = SecurityMonitor()
logger = SecurityLogger()

# Set up alerts
@app.after_request
def log_security_metrics(response):
    if hasattr(g, 'security_events'):
        for event in g.security_events:
            monitor.record_metric('security_event', 1, tags={
                'event_type': event['type'],
                'severity': event['severity']
            })
    return response
```

---

## Common Migration Issues and Solutions

### Issue 1: Import Errors

**Problem:** `ImportError: cannot import name 'X' from 'utils.security'`

**Solution:**
```python
# Old import
from utils.security import validate_csrf_token

# New import
from security.web_security.csrf import validate_csrf_token
```

### Issue 2: Configuration Conflicts

**Problem:** Hardcoded security values conflict with new configuration

**Solution:**
```python
# Old hardcoded approach
MAX_FILE_SIZE = 50 * 1024 * 1024

# New configurable approach
from flask import current_app
max_size = current_app.security_config.get_max_file_size('pdf', user_type)
```

### Issue 3: Performance Degradation

**Problem:** New security checks slow down the application

**Solution:**
```python
# For development, disable expensive operations
if current_app.config['ENVIRONMENT'] == 'development':
    security_config.enable_malware_scanning = False
    security_config.strict_file_validation = False
```

### Issue 4: Test Failures

**Problem:** Existing tests fail due to new security validations

**Solution:**
```python
# Update tests to include required security tokens/headers
def test_upload_endpoint(client):
    # Get CSRF token first
    response = client.get('/get-csrf-token')
    token = response.get_json()['token']
    
    # Include token in request
    response = client.post('/upload', data={
        'csrf_token': token,
        'file': (io.BytesIO(b'test'), 'test.pdf')
    })
    assert response.status_code == 200
```

---

## Migration Checklist

### Pre-Migration
- [ ] Install required dependencies
- [ ] Set up security configuration
- [ ] Create backup of existing security code
- [ ] Write migration tests

### Core Migration
- [ ] Migrate CSRF protection
- [ ] Migrate rate limiting
- [ ] Migrate file validation
- [ ] Migrate security headers
- [ ] Update app initialization

### Feature Migration
- [ ] Migrate PDF processing
- [ ] Migrate document conversion
- [ ] Migrate user input validation
- [ ] Update error handling
- [ ] Add security logging

### Testing & Validation
- [ ] Run migration tests
- [ ] Perform integration testing
- [ ] Conduct performance testing
- [ ] Validate security improvements
- [ ] Test all endpoints

### Cleanup
- [ ] Remove deprecated code
- [ ] Update documentation
- [ ] Set up monitoring
- [ ] Configure production settings
- [ ] Deploy and monitor

---

## Post-Migration Recommendations

1. **Monitor Security Events:** Set up alerts for security violations
2. **Regular Updates:** Keep malware signatures and security rules updated
3. **Performance Tuning:** Monitor and optimize security check performance
4. **Security Audits:** Regularly audit the security configuration
5. **Team Training:** Train development team on new security features
6. **Documentation:** Keep security documentation up to date

## Getting Help

If you encounter issues during migration:

1. Check the [API Documentation](api_documentation.md) for correct usage
2. Review the [examples](examples/) directory for implementation patterns
3. Run the health check: `python -c "from security import health_check; print(health_check())"`
4. Enable debug logging to troubleshoot issues
5. Consult the troubleshooting guide for common problems

The migration should be performed incrementally, testing each phase thoroughly before proceeding to the next.