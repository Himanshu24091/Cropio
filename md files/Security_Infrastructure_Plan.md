# Security Infrastructure Plan
## Complete Folder & File Structure for Universal Security Framework

**Created:** 2025-09-17  
**Purpose:** Define complete infrastructure needed before implementing universal security

---

## 📁 Required Folder Structure

```
converter/
├── security/                           # 🆕 MAIN SECURITY MODULE
│   ├── __init__.py                     # Module initialization
│   ├── core/                           # Core security components
│   │   ├── __init__.py
│   │   ├── decorators.py              # All security decorators
│   │   ├── validators.py              # Input/file validation functions
│   │   ├── sanitizers.py              # Content sanitization functions
│   │   └── exceptions.py              # Custom security exceptions
│   ├── file_security/                 # File-specific security
│   │   ├── __init__.py
│   │   ├── pdf_security.py           # PDF-specific security
│   │   ├── image_security.py         # Image-specific security
│   │   ├── document_security.py      # Document-specific security
│   │   ├── archive_security.py       # Archive/compression security
│   │   └── malware_scanner.py        # Malware detection
│   ├── web_security/                  # Web-specific security
│   │   ├── __init__.py
│   │   ├── csrf_protection.py        # CSRF handling
│   │   ├── rate_limiting.py          # Rate limiting implementation
│   │   ├── session_security.py       # Session management security
│   │   └── headers_security.py       # Security headers
│   ├── auth_security/                 # Authentication security
│   │   ├── __init__.py
│   │   ├── password_security.py      # Password validation/hashing
│   │   ├── login_security.py         # Login protection
│   │   └── permission_security.py    # Role/permission checks
│   ├── config/                        # Security configuration
│   │   ├── __init__.py
│   │   ├── security_config.py        # Main security config
│   │   ├── file_config.py            # File security config
│   │   └── constants.py              # Security constants
│   ├── utils/                         # Security utilities
│   │   ├── __init__.py
│   │   ├── crypto_utils.py           # Encryption/token generation
│   │   ├── audit_logger.py           # Security audit logging
│   │   └── monitoring.py             # Security monitoring
│   └── tests/                         # Security-specific tests
│       ├── __init__.py
│       ├── test_decorators.py
│       ├── test_validators.py
│       ├── test_sanitizers.py
│       ├── test_file_security.py
│       ├── test_web_security.py
│       ├── malware_samples/           # Test malware files
│       └── fixtures/                  # Test fixtures
├── utils/
│   └── security.py                    # 🔄 KEEP EXISTING (will be refactored)
├── tests/
│   └── security/                      # 🆕 SECURITY TESTS
│       ├── __init__.py
│       ├── integration/               # Integration tests
│       ├── unit/                      # Unit tests
│       └── performance/               # Performance tests
└── docs/
    └── security/                      # 🆕 SECURITY DOCUMENTATION
        ├── usage_guide.md
        ├── api_reference.md
        ├── migration_guide.md
        └── examples/
```

---

## 📄 Required Files Details

### 1. Core Security Module (`security/`)

#### A) `security/__init__.py`
- Main entry point for security module
- Export all important functions and classes
- Version management

#### B) `security/core/decorators.py`
- `@validate_file_upload()` - Universal file upload validator
- `@rate_limit()` - Rate limiting decorator
- `@csrf_required()` - CSRF protection decorator
- `@require_auth()` - Authentication requirement decorator
- `@require_role()` - Role-based access control decorator
- `@audit_log()` - Audit logging decorator

#### C) `security/core/validators.py`
- File validation functions
- Input validation functions
- Schema validation functions
- Content validation functions

#### D) `security/core/sanitizers.py`
- PDF content sanitization
- Image content sanitization  
- Text content sanitization
- HTML content sanitization

#### E) `security/core/exceptions.py`
- `SecurityViolationError`
- `MalwareDetectedError`
- `RateLimitExceededError`
- `InvalidFileTypeError`

### 2. File Security Module (`security/file_security/`)

#### A) `security/file_security/pdf_security.py`
- PDF bomb detection
- JavaScript removal from PDFs
- PDF structure validation
- PDF content sanitization

#### B) `security/file_security/image_security.py`
- Image malware detection
- EXIF data sanitization
- Image content rebuilding
- Steganography detection

#### C) `security/file_security/document_security.py`
- Macro detection and removal
- Document structure validation
- Content sanitization

#### D) `security/file_security/malware_scanner.py`
- File signature analysis
- Content pattern matching
- Suspicious behavior detection

### 3. Web Security Module (`security/web_security/`)

#### A) `security/web_security/rate_limiting.py`
- Redis-based rate limiting
- IP-based limiting
- User-based limiting
- Endpoint-specific limiting

#### B) `security/web_security/csrf_protection.py`
- Enhanced CSRF token management
- Custom CSRF validation
- CSRF bypass detection

### 4. Configuration Module (`security/config/`)

#### A) `security/config/security_config.py`
```python
class SecurityConfig:
    # File Upload Limits
    MAX_FILE_SIZE = {
        'free': 50 * 1024 * 1024,      # 50MB
        'premium': 500 * 1024 * 1024   # 500MB
    }
    
    # Allowed File Types
    ALLOWED_EXTENSIONS = {
        'image': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
        'document': ['pdf', 'docx', 'txt'],
        'archive': ['zip', 'rar']
    }
    
    # Rate Limiting
    RATE_LIMITS = {
        'api': 100,         # per minute
        'upload': 10,       # per minute  
        'conversion': 20    # per minute
    }
    
    # Malware Detection
    ENABLE_MALWARE_SCAN = True
    ENABLE_CONTENT_SANITIZATION = True
```

### 5. Testing Infrastructure

#### A) `security/tests/test_decorators.py`
- Test all security decorators
- Test edge cases and bypasses
- Performance testing

#### B) `security/tests/malware_samples/`
- Safe malware samples for testing
- Test files with embedded scripts
- Corrupted file samples

### 6. Documentation

#### A) `docs/security/usage_guide.md`
- How to use security decorators
- Best practices
- Common patterns

#### B) `docs/security/migration_guide.md`
- How to migrate existing routes
- Step-by-step migration process

---

## 🔧 Implementation Priority

### Phase 1: Core Infrastructure (Days 1-2)
1. Create folder structure
2. Setup `security/__init__.py`
3. Create `security/core/decorators.py`
4. Create `security/core/validators.py`
5. Create `security/config/security_config.py`

### Phase 2: File Security (Days 3-4)
1. Create `security/file_security/pdf_security.py`
2. Create `security/file_security/image_security.py`
3. Create `security/file_security/malware_scanner.py`

### Phase 3: Web Security (Day 5)
1. Create `security/web_security/rate_limiting.py`
2. Create `security/web_security/csrf_protection.py`

### Phase 4: Testing & Documentation (Days 6-7)
1. Create comprehensive tests
2. Create documentation
3. Create migration examples

---

## 🎯 Dependencies Required

### New Python Packages
```python
# Add to requirements.txt
python-magic-bin==0.4.14      # Windows file type detection
bleach==6.1.0                  # HTML sanitization
defusedxml==0.7.1             # Safe XML parsing
validators==0.22.0            # Input validation
yara-python==4.3.1           # Advanced malware detection (optional)
```

### System Dependencies
```bash
# For Windows development
pip install python-magic-bin

# For Linux production  
sudo apt-get install libmagic1 libmagic-dev
```

---

## 🔄 Migration Strategy

### Current `utils/security.py`
- Keep existing file initially for backward compatibility
- Gradually migrate functions to new structure
- Add deprecation warnings
- Eventually remove old file

### Route Files Migration
1. Import new security module: `from security import validate_file_upload, rate_limit`
2. Replace old decorators with new ones
3. Test each route individually
4. Deploy incrementally

---

## ✅ Success Criteria

### Infrastructure Setup Complete When:
- [ ] All folders and files created
- [ ] Core decorators working
- [ ] File validation working  
- [ ] Basic tests passing
- [ ] Documentation ready
- [ ] Example migrations working

### Ready for Implementation When:
- [ ] All PRD requirements can be implemented using this structure
- [ ] Performance benchmarks meet targets
- [ ] Security tests pass
- [ ] No breaking changes to existing functionality

---

This infrastructure will provide a solid foundation for implementing the universal security framework as defined in our PRD.