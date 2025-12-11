# Security Framework Migration Guide

This guide provides step-by-step instructions for migrating your application from the old security system (`utils/security.py`) to the new comprehensive security framework.

## Migration Overview

The new security framework provides:
- **Enhanced file validation** with malware scanning
- **Advanced rate limiting** with user-type support  
- **Input validation and sanitization**
- **Role-based access controls**
- **Comprehensive audit logging**
- **Scalable architecture** for production use

## Phase 1: Critical Routes (High Priority)

### Step 1: Update Main Application File (`app.py`)

**REMOVE old security initialization:**
```python
# OLD - Remove these lines
from utils.security import SecurityConfig
app.config.from_object(SecurityConfig)
csrf.init_app(app)
```

**ADD new security initialization:**
```python
# NEW - Add these lines
from security import init_security

# Initialize the new security framework
init_security(app)
```

### Step 2: Route File Migration Template

For each route file, follow this pattern:

#### 1. Update Imports
**REMOVE:**
```python
from utils.security import csrf
```

**ADD:**
```python
from security.core.decorators import (
    require_csrf, rate_limit, validate_file_upload, require_authentication
)
from security.core.validators import validate_content, validate_user_input
from security.core.sanitizers import sanitize_filename
```

#### 2. Apply Security Decorators

**File Upload Routes:**
```python
@your_bp.route('/upload', methods=['POST'])
@rate_limit(requests_per_minute=15, per_user=True)
@validate_file_upload(
    allowed_types=['jpg', 'png', 'pdf'],
    max_size_mb=50,
    scan_malware=True
)
def upload_route():
    # Your existing logic here
    pass
```

**Form Processing Routes:**
```python
@your_bp.route('/process', methods=['POST'])
@rate_limit(requests_per_minute=30, per_user=True)
@require_csrf()
def process_route():
    # Validate user inputs
    input_valid, errors = validate_user_input(request.form.get('data'), 'general')
    if not input_valid:
        flash(f'Invalid input: {", ".join(errors)}', 'error')
        return redirect(request.url)
    
    # Your existing logic here
    pass
```

**Authentication Required Routes:**
```python
@your_bp.route('/admin', methods=['GET'])
@require_authentication(required_role='admin')
@rate_limit(requests_per_minute=60, per_user=True)
def admin_route():
    # Your existing logic here
    pass
```

#### 3. Enhanced File Handling

**REPLACE old filename handling:**
```python
# OLD
filename = secure_filename(file.filename)
```

**WITH new sanitization:**
```python
# NEW
from security.core.sanitizers import sanitize_filename
safe_filename = sanitize_filename(file.filename)
```

**ADD content validation:**
```python
# After reading file content
file_content = file.read()
is_safe, issues = validate_content(file_content, file_extension)
if not is_safe:
    return jsonify({
        'error': f'File validation failed: {", ".join(issues)}'
    }), 400
```

### Step 3: Priority Route Files to Migrate First

1. **Authentication Routes** (`routes/auth.py`)
2. **File Upload Routes** (`routes/image_converter.py`, `routes/pdf_converter.py`)
3. **Document Processing** (`routes/document_converter.py`)
4. **API Routes** (`routes/api.py`)
5. **Admin Routes** (`routes/admin.py`)

## Phase 2: Processing Routes (Medium Priority)

### Routes to Migrate:
- `routes/cropper_routes.py` (example provided)
- `routes/compressor_routes.py`
- `routes/pdf_editor_routes.py`
- `routes/merger_routes.py`

### Enhanced Processing Logic

Add resource limits and security checks:

```python
def process_large_file(file_path):
    # Check file size before processing
    file_size = os.path.getsize(file_path)
    if file_size > 100 * 1024 * 1024:  # 100MB limit
        raise ValueError("File too large for processing")
    
    # Your processing logic here
    pass
```

## Phase 3: Utility Routes (Low Priority)

### Routes to Migrate:
- `routes/main.py`
- `routes/health.py`
- Other utility routes

## Configuration Updates

### Step 1: Update Configuration Files

**Create new security config** (`config/security_config.py`):
```python
import os

class SecurityConfig:
    """Enhanced security configuration"""
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = "100/hour"
    
    # File validation
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # Malware scanning
    ENABLE_MALWARE_SCAN = True
    CLAMD_HOST = 'localhost'
    CLAMD_PORT = 3310
    
    # CSRF Protection
    SECRET_KEY = os.environ.get('SECRET_KEY')
    WTF_CSRF_TIME_LIMIT = 3600
    
    # Audit logging
    AUDIT_LOG_LEVEL = 'INFO'
    SECURITY_LOG_FILE = 'logs/security.log'
```

### Step 2: Environment Variables

Add to your `.env` file:
```env
# Security Configuration
SECRET_KEY=your-secret-key-here
REDIS_URL=redis://localhost:6379/0
ENABLE_MALWARE_SCAN=true
CLAMD_HOST=localhost
CLAMD_PORT=3310
```

## Testing Migration

### Step 1: Create Test Script

```python
# test_security_migration.py
import requests
import json

def test_rate_limiting():
    """Test rate limiting functionality"""
    url = 'http://localhost:5000/your-endpoint'
    
    # Make multiple requests rapidly
    for i in range(20):
        response = requests.post(url, json={'test': i})
        print(f"Request {i}: {response.status_code}")
        if response.status_code == 429:
            print("Rate limiting working correctly!")
            break

def test_file_validation():
    """Test file validation functionality"""
    url = 'http://localhost:5000/upload-endpoint'
    
    # Test with valid file
    with open('test_image.jpg', 'rb') as f:
        response = requests.post(url, files={'file': f})
        print(f"Valid file: {response.status_code}")
    
    # Test with invalid file type
    with open('test_script.exe', 'rb') as f:
        response = requests.post(url, files={'file': f})
        print(f"Invalid file: {response.status_code}")

if __name__ == '__main__':
    test_rate_limiting()
    test_file_validation()
```

### Step 2: Run Migration Tests

```bash
# Run the security framework tests
python test_security_migration.py

# Test specific routes
curl -X POST http://localhost:5000/crop-image \
     -F "file=@test_image.jpg" \
     -F "crop_data={\"x\":0,\"y\":0,\"width\":100,\"height\":100}"
```

## Common Migration Issues

### Issue 1: Import Errors
**Problem:** `ModuleNotFoundError: No module named 'security'`
**Solution:** Ensure the security framework is properly installed and in your Python path.

### Issue 2: Configuration Conflicts
**Problem:** Old and new security systems conflicting
**Solution:** Remove all old security imports and initialization before adding new ones.

### Issue 3: Rate Limiting Not Working
**Problem:** Rate limits not being enforced
**Solution:** Check Redis connection and ensure proper decorator ordering.

### Issue 4: File Validation Failures
**Problem:** Valid files being rejected
**Solution:** Check file type validation rules and content scanning configuration.

## Migration Checklist

### Pre-Migration
- [ ] Backup current application code
- [ ] Set up Redis for rate limiting (if using Redis)
- [ ] Install ClamAV for malware scanning (if enabled)
- [ ] Update environment variables
- [ ] Test security framework in development

### Phase 1 - Critical Routes
- [ ] Update main application initialization
- [ ] Migrate authentication routes
- [ ] Migrate file upload routes
- [ ] Migrate API routes
- [ ] Migrate admin routes
- [ ] Test critical functionality

### Phase 2 - Processing Routes
- [ ] Migrate image processing routes
- [ ] Migrate PDF processing routes
- [ ] Migrate document processing routes
- [ ] Add resource limits and checks
- [ ] Test processing functionality

### Phase 3 - Utility Routes
- [ ] Migrate remaining routes
- [ ] Update error handling
- [ ] Add security logging
- [ ] Test complete application

### Post-Migration
- [ ] Remove old security system files
- [ ] Update documentation
- [ ] Monitor security logs
- [ ] Performance testing
- [ ] Security penetration testing

## Monitoring and Maintenance

### Log Analysis
Monitor these security log events:
- Failed authentication attempts
- Rate limit violations
- File validation failures
- Malware detection alerts
- Suspicious request patterns

### Performance Monitoring
Track these metrics:
- Request processing time impact
- Memory usage with file scanning
- Redis connection health
- Rate limiting effectiveness

### Regular Updates
- Keep security rules updated
- Update malware scanning signatures  
- Review and adjust rate limits
- Update allowed file types as needed

## Support

If you encounter issues during migration:
1. Check the security framework logs
2. Verify configuration settings
3. Test individual components
4. Review the migration example files
5. Consult the security framework documentation

Remember: Migrate incrementally and test thoroughly at each step!