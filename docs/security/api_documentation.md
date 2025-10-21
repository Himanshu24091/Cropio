# Security Framework API Documentation

## Table of Contents

1. [Core Security API](#core-security-api)
2. [File Security API](#file-security-api)
3. [Web Security API](#web-security-api)
4. [Authentication Security API](#authentication-security-api)
5. [Configuration API](#configuration-api)
6. [Utilities API](#utilities-api)
7. [Testing API](#testing-api)

---

## Core Security API

### Decorators (`security.core.decorators`)

#### `@require_csrf(token_field='csrf_token')`
Validates CSRF token for protected endpoints.

**Parameters:**
- `token_field` (str): Field name containing CSRF token (default: 'csrf_token')

**Returns:**
- Decorated function that validates CSRF before execution

**Raises:**
- `CSRFValidationError`: When CSRF token is invalid or missing

**Example:**
```python
@app.route('/sensitive-action', methods=['POST'])
@require_csrf()
def sensitive_action():
    return "Action completed"
```

#### `@rate_limit(requests_per_minute=60, per_user=True)`
Applies rate limiting to endpoints.

**Parameters:**
- `requests_per_minute` (int): Maximum requests per minute (default: 60)
- `per_user` (bool): Apply limit per user vs globally (default: True)

**Returns:**
- Decorated function with rate limiting applied

**Raises:**
- `RateLimitExceededError`: When rate limit is exceeded

**Example:**
```python
@app.route('/api/upload', methods=['POST'])
@rate_limit(requests_per_minute=10, per_user=True)
def upload_endpoint():
    return "Upload processed"
```

#### `@validate_file_upload(allowed_types=None, max_size_mb=50, scan_malware=True)`
Validates file uploads comprehensively.

**Parameters:**
- `allowed_types` (List[str]): Allowed file extensions (default: None = all allowed)
- `max_size_mb` (int): Maximum file size in MB (default: 50)
- `scan_malware` (bool): Enable malware scanning (default: True)

**Returns:**
- Decorated function with file validation applied

**Raises:**
- `InvalidFileTypeError`: When file type is not allowed
- `FileSizeExceededError`: When file exceeds size limit
- `MalwareDetectedError`: When malware is detected

**Example:**
```python
@app.route('/upload-document', methods=['POST'])
@validate_file_upload(
    allowed_types=['pdf', 'docx', 'txt'],
    max_size_mb=25,
    scan_malware=True
)
def upload_document():
    return "Document uploaded successfully"
```

#### `@require_authentication(role=None)`
Requires user authentication and optional role validation.

**Parameters:**
- `role` (str): Required user role (optional)

**Returns:**
- Decorated function that checks authentication

**Raises:**
- `AuthenticationError`: When user is not authenticated
- `AuthorizationError`: When user lacks required role

**Example:**
```python
@app.route('/admin/users', methods=['GET'])
@require_authentication(role='admin')
def list_users():
    return "User list"
```

### Validators (`security.core.validators`)

#### `validate_content(content: bytes, file_type: str) -> Tuple[bool, List[str]]`
Validates file content for security threats.

**Parameters:**
- `content` (bytes): File content to validate
- `file_type` (str): File extension/type

**Returns:**
- Tuple of (is_safe: bool, issues: List[str])

**Example:**
```python
is_safe, issues = validate_content(file_data, 'pdf')
if not is_safe:
    print(f"Security issues: {issues}")
```

#### `validate_filename(filename: str) -> bool`
Validates filename for security compliance.

**Parameters:**
- `filename` (str): Filename to validate

**Returns:**
- bool: True if filename is safe

**Example:**
```python
if validate_filename(user_filename):
    safe_name = sanitize_filename(user_filename)
```

#### `validate_user_input(input_data: str, input_type: str = 'general') -> Tuple[bool, List[str]]`
Validates user input for various contexts.

**Parameters:**
- `input_data` (str): User input to validate
- `input_type` (str): Type of input ('email', 'password', 'general', etc.)

**Returns:**
- Tuple of (is_valid: bool, errors: List[str])

**Example:**
```python
is_valid, errors = validate_user_input(email, 'email')
if not is_valid:
    return {"errors": errors}, 400
```

### Sanitizers (`security.core.sanitizers`)

#### `sanitize_filename(filename: str) -> str`
Sanitizes filename for safe storage.

**Parameters:**
- `filename` (str): Original filename

**Returns:**
- str: Sanitized filename

**Example:**
```python
safe_name = sanitize_filename("../../../etc/passwd")
# Returns: "etc_passwd"
```

#### `sanitize_content(content: str, content_type: str = 'html') -> str`
Sanitizes content based on type.

**Parameters:**
- `content` (str): Content to sanitize
- `content_type` (str): Type of content ('html', 'text', 'json', etc.)

**Returns:**
- str: Sanitized content

**Example:**
```python
safe_html = sanitize_content("<script>alert('xss')</script>", 'html')
# Returns: "&lt;script&gt;alert('xss')&lt;/script&gt;"
```

### Exceptions (`security.core.exceptions`)

All security exceptions inherit from `SecurityViolationError` and include:

- `timestamp`: When the exception occurred
- `severity`: Security severity level
- `details`: Additional context information
- `get_audit_data()`: Method to get structured audit data

**Available Exceptions:**

- `SecurityViolationError`: Base security exception
- `MalwareDetectedError`: Malware found in content
- `RateLimitExceededError`: Rate limit exceeded
- `InvalidFileTypeError`: Unsupported file type
- `FileSizeExceededError`: File too large
- `CSRFValidationError`: CSRF token validation failed
- `AuthenticationError`: Authentication required
- `AuthorizationError`: Insufficient permissions
- `ContentValidationError`: Content failed validation
- `ConfigurationError`: Security configuration error

---

## File Security API

### Malware Scanner (`security.file_security.malware_scanner`)

#### `MalwareScanner` Class

##### `__init__(signature_db_path: str = None, enable_cloud_scanning: bool = False)`
Initialize malware scanner.

**Parameters:**
- `signature_db_path` (str): Path to signature database
- `enable_cloud_scanning` (bool): Enable cloud-based scanning

##### `scan_file(file_path: str) -> ScanResult`
Scan file for malware.

**Parameters:**
- `file_path` (str): Path to file to scan

**Returns:**
- `ScanResult`: Object containing scan results

**Example:**
```python
scanner = MalwareScanner()
result = scanner.scan_file('suspicious_file.pdf')
if not result.is_safe:
    print(f"Threats found: {result.threats}")
```

##### `scan_content(content: bytes, file_type: str) -> ScanResult`
Scan content directly.

**Parameters:**
- `content` (bytes): File content
- `file_type` (str): File extension

**Returns:**
- `ScanResult`: Object containing scan results

#### `ScanResult` Class

Properties:
- `is_safe` (bool): Whether content is safe
- `threats` (List[str]): List of detected threats
- `scan_time` (float): Time taken for scan
- `engine_results` (Dict): Results from different scan engines

### File Validator (`security.file_security.file_validator`)

#### `FileValidator` Class

##### `validate_file_type(file_path: str, allowed_types: List[str]) -> bool`
Validate file type against allowed types.

##### `validate_file_size(file_path: str, max_size_bytes: int) -> bool`
Validate file size constraints.

##### `validate_file_permissions(file_path: str) -> bool`
Validate file has secure permissions.

### Content Analyzer (`security.file_security.content_analyzer`)

#### `analyze_pdf_content(content: bytes) -> AnalysisResult`
Deep analysis of PDF content for security threats.

#### `analyze_office_document(content: bytes) -> AnalysisResult`
Analysis of Office documents (docx, xlsx, pptx).

#### `analyze_image_content(content: bytes) -> AnalysisResult`
Analysis of image files for embedded threats.

---

## Web Security API

### CSRF Protection (`security.web_security.csrf`)

#### `generate_csrf_token(user_id: str = None) -> str`
Generate CSRF token for user session.

**Parameters:**
- `user_id` (str): User identifier (optional)

**Returns:**
- str: CSRF token

#### `validate_csrf_token(token: str, user_id: str = None) -> bool`
Validate CSRF token.

**Parameters:**
- `token` (str): Token to validate
- `user_id` (str): User identifier (optional)

**Returns:**
- bool: True if token is valid

### Rate Limiting (`security.web_security.rate_limiting`)

#### `RateLimiter` Class

##### `__init__(redis_client=None, default_limits: Dict = None)`
Initialize rate limiter.

##### `is_allowed(key: str, limit: int, window_seconds: int = 60) -> bool`
Check if request is allowed under rate limit.

##### `get_remaining(key: str, limit: int, window_seconds: int = 60) -> int`
Get remaining requests in current window.

### Security Headers (`security.web_security.headers`)

#### `SecurityHeaders` Class

##### `apply_security_headers(response, config: SecurityConfig) -> Response`
Apply comprehensive security headers to response.

**Parameters:**
- `response`: Flask response object
- `config`: Security configuration

**Returns:**
- Response: Modified response with security headers

**Example:**
```python
@app.after_request
def apply_security_headers(response):
    headers = SecurityHeaders()
    return headers.apply_security_headers(response, security_config)
```

---

## Authentication Security API

### Password Security (`security.auth_security.password_security`)

#### `PasswordValidator` Class

##### `validate_password_strength(password: str) -> Tuple[bool, List[str]]`
Validate password against security policies.

##### `hash_password(password: str) -> str`
Securely hash password using latest algorithms.

##### `verify_password(password: str, hash: str) -> bool`
Verify password against stored hash.

### Session Security (`security.auth_security.session_security`)

#### `SessionManager` Class

##### `create_secure_session(user_id: str, user_data: Dict) -> str`
Create secure session for user.

##### `validate_session(session_id: str) -> Tuple[bool, Dict]`
Validate and get session data.

##### `invalidate_session(session_id: str) -> bool`
Securely invalidate session.

---

## Configuration API

### Security Configuration (`security.config.security_config`)

#### `SecurityConfig` Class

Main configuration class for the security framework.

##### `__init__(environment: str = 'development', **kwargs)`
Initialize security configuration.

**Parameters:**
- `environment` (str): Environment type ('development', 'testing', 'production')
- `**kwargs`: Additional configuration options

##### Key Methods:

- `get_max_file_size(file_type: str, user_type: str = 'basic') -> int`
- `get_rate_limit(endpoint: str, user_type: str = 'basic') -> int`
- `is_file_type_allowed(file_type: str) -> bool`
- `get_security_level() -> SecurityLevel`
- `update_config(updates: Dict) -> None`

**Example:**
```python
config = SecurityConfig(
    environment='production',
    enable_malware_scanning=True,
    max_file_size_multiplier=2.0,
    rate_limit_multiplier=0.5
)

max_pdf_size = config.get_max_file_size('pdf', 'premium')
```

### Constants (`security.config.constants`)

Centralized constants for the security framework:

- `DEFAULT_RATE_LIMITS`: Default rate limiting values
- `HTTP_SECURITY_HEADERS`: Security header configurations
- `ALLOWED_MIME_TYPES`: Permitted MIME types by category
- `DANGEROUS_CONTENT_PATTERNS`: Regex patterns for threat detection
- `FILE_SIZE_LIMITS`: Default file size limitations
- `PASSWORD_REQUIREMENTS`: Password policy constants

---

## Utilities API

### Cryptographic Utilities (`security.utils.crypto`)

#### `generate_secure_token(length: int = 32) -> str`
Generate cryptographically secure random token.

#### `encrypt_sensitive_data(data: str, key: str = None) -> str`
Encrypt sensitive data for storage.

#### `decrypt_sensitive_data(encrypted_data: str, key: str = None) -> str`
Decrypt previously encrypted data.

### Security Logging (`security.utils.logging`)

#### `SecurityLogger` Class

##### `log_security_event(event_type: str, **kwargs) -> None`
Log security events with structured data.

##### `log_authentication_attempt(user_id: str, success: bool, **kwargs) -> None`
Log authentication attempts.

##### `log_file_operation(operation: str, file_info: Dict, **kwargs) -> None`
Log file-related security operations.

### Security Monitoring (`security.utils.monitoring`)

#### `SecurityMonitor` Class

##### `record_metric(metric_name: str, value: float, tags: Dict = None) -> None`
Record security metrics.

##### `check_system_health() -> Dict`
Perform security system health check.

##### `get_security_stats(time_range: str = '1h') -> Dict`
Get security statistics for specified time range.

---

## Testing API

### Test Utilities (`security.tests`)

#### File Generation Functions

- `create_mock_file(file_type: str, size_kb: int = 100) -> bytes`
- `create_malware_sample(sample_type: str = 'eicar') -> bytes`
- `create_large_file(size_mb: int) -> bytes`
- `create_test_archive(files: List[Tuple[str, bytes]]) -> bytes`

#### User and Request Generators

- `create_test_user(user_type: str = 'basic') -> Dict`
- `create_mock_request(method: str = 'POST', **kwargs) -> MockRequest`

#### Test Fixtures

- `valid_files_fixture() -> List[Tuple[str, bytes]]`
- `malware_files_fixture() -> List[Tuple[str, bytes]]`
- `large_files_fixture() -> List[Tuple[str, bytes]]`
- `rate_limit_scenarios_fixture() -> List[Dict]`

**Example:**
```python
from security.tests import create_mock_file, create_malware_sample

# Test file validation
safe_pdf = create_mock_file('pdf', size_kb=500)
malware_pdf = create_malware_sample('eicar')

# Test with security framework
from security.file_security import scan_for_malware

safe_result = scan_for_malware(safe_pdf)
assert safe_result.is_safe

malware_result = scan_for_malware(malware_pdf)
assert not malware_result.is_safe
```

---

## Error Handling

All API functions follow consistent error handling patterns:

1. **Input Validation**: All inputs are validated before processing
2. **Structured Exceptions**: Custom security exceptions with detailed context
3. **Logging**: All errors are automatically logged with security context
4. **Graceful Degradation**: Non-critical failures don't break core functionality

### Common Error Response Format

```python
{
    "error": True,
    "error_type": "SecurityViolationError",
    "message": "Human-readable error message",
    "details": {
        "timestamp": "2024-01-15T10:30:00Z",
        "severity": "HIGH",
        "context": {...}
    },
    "suggestions": ["List of suggested fixes"]
}
```

---

## Performance Guidelines

### Caching Strategies

- **Malware Signatures**: Cached in memory with TTL
- **File Validation Rules**: Cached per request cycle
- **Rate Limit Counters**: Redis-based with automatic expiration
- **User Sessions**: Cached with configurable timeout

### Optimization Tips

1. Use async operations for heavy scanning
2. Implement file size pre-checks before content analysis
3. Cache validation results for identical file hashes
4. Use streaming for large file operations
5. Implement circuit breakers for external services

### Resource Limits

- Maximum concurrent scans: Configurable (default: 10)
- Memory usage per scan: Limited to 512MB
- Scan timeout: Configurable (default: 30 seconds)
- Cache size limits: Automatic cleanup based on memory pressure