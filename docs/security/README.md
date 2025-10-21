# Security Framework Documentation

## Overview

The universal security framework provides comprehensive, enterprise-grade security features for the document converter application. This framework centralizes all security controls, making them reusable across different components while maintaining consistency and reducing duplication.

## Quick Start

### 1. Basic Setup

```python
from security import SecurityConfig, initialize_security
from flask import Flask

app = Flask(__name__)

# Initialize security with default configuration
security_config = SecurityConfig()
initialize_security(app, security_config)
```

### 2. Apply Security Decorators

```python
from security.core.decorators import require_csrf, rate_limit, validate_file_upload

@app.route('/upload', methods=['POST'])
@require_csrf()
@rate_limit(requests_per_minute=10)
@validate_file_upload(allowed_types=['pdf', 'docx'], max_size_mb=50)
def upload_file():
    # Your upload logic here
    return "File uploaded successfully"
```

### 3. Content Validation

```python
from security.core.validators import validate_content, sanitize_filename

# Validate uploaded content
is_safe, issues = validate_content(file_content, 'pdf')
if not is_safe:
    return f"Security issues detected: {issues}", 400

# Sanitize filenames
safe_filename = sanitize_filename(original_filename)
```

## Key Features

### 🛡️ Core Security
- **Input Validation**: Comprehensive validation for all user inputs
- **Content Sanitization**: Clean and sanitize file contents and user data
- **Custom Exceptions**: Detailed security exception handling with metadata
- **Security Decorators**: Easy-to-use decorators for common security patterns

### 📁 File Security
- **Malware Scanning**: Multi-engine malware detection and prevention
- **File Type Validation**: Strict file type checking with MIME validation
- **Content Analysis**: Deep inspection of file contents for security threats
- **Size Limits**: Configurable file size restrictions by type and user role

### 🌐 Web Security
- **CSRF Protection**: Advanced CSRF token generation and validation
- **Rate Limiting**: Sophisticated rate limiting with user-based quotas
- **Security Headers**: Comprehensive HTTP security header management
- **Session Security**: Enhanced session management and validation

### 🔐 Authentication Security
- **Password Security**: Advanced password policies and validation
- **Session Management**: Secure session handling with automatic cleanup
- **User Role Validation**: Role-based access control integration

## Architecture

```
security/
├── core/                  # Core security functionality
│   ├── decorators.py     # Security decorators
│   ├── validators.py     # Input validation
│   ├── sanitizers.py     # Content sanitization
│   └── exceptions.py     # Security exceptions
├── file_security/        # File-specific security
│   ├── malware_scanner.py
│   ├── file_validator.py
│   └── content_analyzer.py
├── web_security/         # Web security features
│   ├── csrf.py
│   ├── rate_limiting.py
│   └── headers.py
├── auth_security/        # Authentication security
│   ├── password_security.py
│   └── session_security.py
├── config/               # Configuration management
│   ├── security_config.py
│   └── constants.py
└── utils/                # Utility functions
    ├── crypto.py
    ├── logging.py
    └── monitoring.py
```

## Configuration

The security framework is highly configurable through the `SecurityConfig` class:

```python
from security.config import SecurityConfig, SecurityLevel

# Development configuration
dev_config = SecurityConfig(
    environment='development',
    security_level=SecurityLevel.MEDIUM,
    enable_malware_scanning=False,
    rate_limit_enabled=True
)

# Production configuration
prod_config = SecurityConfig(
    environment='production',
    security_level=SecurityLevel.HIGH,
    enable_malware_scanning=True,
    strict_file_validation=True,
    enable_audit_logging=True
)
```

## Security Levels

The framework supports three security levels:

- **LOW**: Basic security features for development
- **MEDIUM**: Standard security for testing environments
- **HIGH**: Maximum security for production environments

Each level automatically adjusts:
- Rate limiting thresholds
- File validation strictness
- Malware scanning sensitivity
- Logging verbosity
- Content filtering rules

## Migration Guide

For migrating from the existing `utils/security.py`:

1. **Update Imports**:
   ```python
   # Old
   from utils.security import validate_csrf_token
   
   # New
   from security.web_security.csrf import validate_csrf_token
   ```

2. **Configuration Migration**:
   ```python
   # Old hardcoded values
   MAX_FILE_SIZE = 50 * 1024 * 1024
   
   # New configurable approach
   from security.config import SecurityConfig
   config = SecurityConfig()
   max_size = config.get_max_file_size('pdf', user_type='premium')
   ```

3. **Decorator Updates**:
   ```python
   # Old basic approach
   @csrf_required
   def upload_file():
       pass
   
   # New comprehensive approach
   @require_csrf()
   @rate_limit(requests_per_minute=10)
   @validate_file_upload(allowed_types=['pdf'])
   def upload_file():
       pass
   ```

## Testing

The framework includes comprehensive testing utilities:

```python
from security.tests import create_mock_file, create_malware_sample

# Create test files
safe_pdf = create_mock_file('pdf', size_kb=100)
malware_sample = create_malware_sample('eicar')

# Run security tests
from security.file_security import scan_for_malware
result = scan_for_malware(safe_pdf)
assert result.is_safe
```

## Monitoring and Logging

Security events are automatically logged with structured data:

```python
from security.utils.logging import SecurityLogger

logger = SecurityLogger()
logger.log_security_event(
    event_type='file_upload_blocked',
    user_id='user123',
    details={'reason': 'malware_detected', 'file_type': 'pdf'}
)
```

## Performance Considerations

- **Caching**: Malware signatures and validation rules are cached
- **Async Processing**: Heavy operations can be processed asynchronously
- **Resource Limits**: Built-in protection against resource exhaustion
- **Optimized Scanning**: Smart file analysis to minimize performance impact

## Security Best Practices

1. **Always validate inputs** at multiple layers
2. **Use appropriate security levels** for each environment
3. **Regularly update** malware signatures and security rules
4. **Monitor security events** and set up alerts
5. **Test security measures** regularly with automated tests
6. **Keep dependencies updated** and audit them regularly

## Getting Help

- **API Documentation**: See `api_documentation.md`
- **Examples**: Check the `examples/` directory
- **Configuration Guide**: See `configuration_guide.md`
- **Migration Guide**: See `migration_guide.md`
- **Troubleshooting**: See `troubleshooting.md`

## Contributing

When contributing to the security framework:

1. **Follow security coding practices**
2. **Add comprehensive tests** for new features
3. **Update documentation** for any API changes
4. **Consider performance implications**
5. **Test across all security levels**

## License

This security framework is part of the document converter project and follows the same licensing terms.