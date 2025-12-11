# Security Framework Troubleshooting Guide

## Overview

This guide covers common issues you might encounter when using the security framework, along with their solutions and prevention strategies.

## Table of Contents

1. [Installation and Setup Issues](#installation-and-setup-issues)
2. [Configuration Problems](#configuration-problems)
3. [Performance Issues](#performance-issues)
4. [Security Feature Problems](#security-feature-problems)
5. [Logging and Monitoring Issues](#logging-and-monitoring-issues)
6. [Integration Problems](#integration-problems)
7. [Error Messages Reference](#error-messages-reference)
8. [Debugging Tools](#debugging-tools)

---

## Installation and Setup Issues

### Issue: Import Errors

**Symptom:**
```python
ImportError: cannot import name 'SecurityConfig' from 'security.config'
ModuleNotFoundError: No module named 'security'
```

**Causes:**
- Security framework not properly installed
- Python path issues
- Missing dependencies

**Solutions:**

1. **Verify Installation:**
   ```bash
   pip list | grep security
   python -c "import security; print(security.__version__)"
   ```

2. **Reinstall Framework:**
   ```bash
   pip uninstall security-framework
   pip install --upgrade security-framework
   ```

3. **Check Python Path:**
   ```python
   import sys
   print(sys.path)
   # Ensure your security module path is included
   ```

4. **Install Missing Dependencies:**
   ```bash
   pip install -r requirements.txt
   # Or install specific missing packages
   pip install redis python-magic yara-python
   ```

### Issue: Dependency Conflicts

**Symptom:**
```
ERROR: pip's dependency resolver does not currently consider all the packages that are installed
```

**Solutions:**

1. **Use Virtual Environment:**
   ```bash
   python -m venv security_env
   source security_env/bin/activate  # Linux/Mac
   security_env\Scripts\activate     # Windows
   pip install security-framework
   ```

2. **Resolve Version Conflicts:**
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install --force-reinstall security-framework
   ```

3. **Manual Dependency Resolution:**
   ```bash
   pip install cryptography==41.0.0
   pip install redis==4.5.4
   pip install security-framework --no-deps
   ```

### Issue: System Dependencies Missing

**Symptom:**
```
OSError: cannot load library 'libmagic': error 0x7e
FileNotFoundError: ClamAV not found
```

**Solutions:**

**For Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install libmagic1 libmagic-dev
sudo apt-get install clamav clamav-daemon
sudo freshclam  # Update virus definitions
```

**For CentOS/RHEL:**
```bash
sudo yum install file-devel
sudo yum install clamav clamav-update
sudo freshclam
```

**For macOS:**
```bash
brew install libmagic
brew install clamav
sudo freshclam
```

**For Windows:**
```powershell
# Install using Windows package manager
winget install File.File
# For ClamAV, download from official website
```

---

## Configuration Problems

### Issue: Configuration Validation Errors

**Symptom:**
```
ConfigurationError: Invalid security level specified
ConfigurationError: Redis URL format is invalid
```

**Solution:**

1. **Validate Configuration:**
   ```python
   from security.config import SecurityConfig, validate_config
   
   config = SecurityConfig(environment='production')
   is_valid, errors = validate_config(config)
   
   if not is_valid:
       for error in errors:
           print(f"Config Error: {error}")
   ```

2. **Common Configuration Fixes:**
   ```python
   # Fix security level
   config = SecurityConfig(
       security_level='HIGH'  # Wrong - use enum
   )
   # Correct:
   from security.config import SecurityLevel
   config = SecurityConfig(
       security_level=SecurityLevel.HIGH
   )
   
   # Fix Redis URL
   config = SecurityConfig(
       redis_url='localhost:6379'  # Wrong - missing protocol
   )
   # Correct:
   config = SecurityConfig(
       redis_url='redis://localhost:6379/0'
   )
   ```

### Issue: Environment Variable Not Loading

**Symptom:**
```
Configuration using default values instead of environment variables
```

**Solution:**

1. **Check Environment Variable Names:**
   ```bash
   # Correct naming convention
   export SECURITY_ENVIRONMENT=production
   export SECURITY_LEVEL=high
   export SECURITY_REDIS_URL=redis://localhost:6379/0
   
   # Verify they're set
   env | grep SECURITY_
   ```

2. **Load Environment Variables in Code:**
   ```python
   import os
   from security.config import SecurityConfig
   
   config = SecurityConfig(
       environment=os.getenv('SECURITY_ENVIRONMENT', 'development'),
       redis_url=os.getenv('SECURITY_REDIS_URL'),
   )
   ```

### Issue: Invalid File Type Configuration

**Symptom:**
```
ConfigurationError: Invalid file extension in allowed_file_extensions
```

**Solution:**

```python
# Wrong - includes dots
config = SecurityConfig(
    allowed_file_extensions=['.pdf', '.docx']
)

# Correct - no dots
config = SecurityConfig(
    allowed_file_extensions=['pdf', 'docx']
)
```

---

## Performance Issues

### Issue: Slow Malware Scanning

**Symptom:**
- File uploads taking very long
- High CPU usage during scans
- Timeout errors

**Solutions:**

1. **Enable Async Scanning:**
   ```python
   config = SecurityConfig(
       enable_async_scanning=True,
       max_concurrent_scans=3,  # Reduce if CPU limited
       scan_timeout=30,         # Set reasonable timeout
   )
   ```

2. **Optimize Scanner Configuration:**
   ```python
   config = SecurityConfig(
       malware_scanner_engines=['clamav'],  # Use single engine
       scan_archives=False,                 # Skip archive scanning
       max_scan_size=50 * 1024 * 1024,     # Limit scan size to 50MB
   )
   ```

3. **Use Caching:**
   ```python
   config = SecurityConfig(
       cache_validation_results=True,
       validation_cache_ttl=3600,  # Cache for 1 hour
   )
   ```

### Issue: Redis Connection Slow

**Symptom:**
- Rate limiting delays
- Cache operation timeouts

**Solutions:**

1. **Optimize Redis Configuration:**
   ```python
   config = SecurityConfig(
       redis_config={
           'url': 'redis://localhost:6379/0',
           'socket_timeout': 5,
           'socket_connect_timeout': 5,
           'retry_on_timeout': True,
           'connection_pool_max_connections': 20,
       }
   )
   ```

2. **Use Redis Sentinel for HA:**
   ```python
   config = SecurityConfig(
       redis_config={
           'sentinel_hosts': [
               ('redis-sentinel-1', 26379),
               ('redis-sentinel-2', 26379),
           ],
           'service_name': 'mymaster',
       }
   )
   ```

### Issue: Memory Usage Too High

**Symptom:**
- High memory consumption
- Out of memory errors
- System slowdown

**Solutions:**

1. **Set Resource Limits:**
   ```python
   config = SecurityConfig(
       max_memory_per_scan=256 * 1024 * 1024,  # 256MB per scan
       max_concurrent_scans=2,                  # Reduce concurrent scans
       max_file_size_limits={
           'pdf': 50 * 1024 * 1024,  # Reduce max file sizes
       }
   )
   ```

2. **Enable Garbage Collection:**
   ```python
   import gc
   
   # In your application
   @app.after_request
   def cleanup_memory(response):
       gc.collect()
       return response
   ```

---

## Security Feature Problems

### Issue: CSRF Validation Failing

**Symptom:**
```
CSRFValidationError: CSRF token validation failed
```

**Debugging Steps:**

1. **Check Token Generation:**
   ```python
   from security.web_security.csrf import generate_csrf_token
   
   token = generate_csrf_token(user_id='test_user')
   print(f"Generated token: {token}")
   ```

2. **Verify Token in Request:**
   ```python
   # In your view
   print(f"Token from form: {request.form.get('csrf_token')}")
   print(f"Token from headers: {request.headers.get('X-CSRF-Token')}")
   ```

3. **Check Token Expiry:**
   ```python
   config = SecurityConfig(
       csrf_token_expiry=3600,  # 1 hour - increase if needed
   )
   ```

### Issue: Rate Limiting Too Strict

**Symptom:**
- Users getting rate limited too quickly
- Legitimate requests being blocked

**Solutions:**

1. **Adjust Rate Limits:**
   ```python
   config = SecurityConfig(
       rate_limit_multiplier=2.0,  # Double the default limits
       default_rate_limits={
           'api': 120,     # Increase from default 60
           'upload': 20,   # Increase from default 10
       }
   )
   ```

2. **Implement User-Type Based Limits:**
   ```python
   config = SecurityConfig(
       rate_limit_multipliers={
           'basic': 1.0,
           'premium': 3.0,
           'enterprise': 10.0,
       }
   )
   ```

### Issue: File Upload Validation Too Strict

**Symptom:**
- Valid files being rejected
- False positive malware detection

**Solutions:**

1. **Review File Type Configuration:**
   ```python
   config = SecurityConfig(
       allowed_file_extensions=['pdf', 'docx', 'txt', 'jpg', 'png'],
       validate_mime_types=True,  # Ensure MIME validation is working
   )
   ```

2. **Check Malware Scanner Sensitivity:**
   ```python
   config = SecurityConfig(
       malware_scanner_engines=['clamav'],  # Use single engine
       custom_threat_patterns=[],            # Remove overly broad patterns
   )
   ```

3. **Enable Debug Logging:**
   ```python
   import logging
   logging.getLogger('security.file_security').setLevel(logging.DEBUG)
   ```

### Issue: Authentication Decorator Not Working

**Symptom:**
```
AttributeError: 'NoneType' object has no attribute 'get'
```

**Solutions:**

1. **Verify User Context Setup:**
   ```python
   from flask import g, session
   
   @app.before_request
   def load_user():
       g.user_id = session.get('user_id')
       g.user_type = session.get('user_type', 'basic')
   ```

2. **Check Decorator Usage:**
   ```python
   from security.core.decorators import require_authentication
   
   # Correct usage
   @app.route('/protected')
   @require_authentication(role='user')
   def protected_view():
       return "Protected content"
   ```

---

## Logging and Monitoring Issues

### Issue: No Security Logs Generated

**Symptom:**
- Expected security events not appearing in logs
- Silent failures

**Solutions:**

1. **Enable Audit Logging:**
   ```python
   config = SecurityConfig(
       enable_audit_logging=True,
       log_level='INFO',
   )
   ```

2. **Configure Logger:**
   ```python
   import logging
   
   # Set up security logger
   security_logger = logging.getLogger('security')
   security_logger.setLevel(logging.INFO)
   
   handler = logging.StreamHandler()
   formatter = logging.Formatter(
       '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   handler.setFormatter(formatter)
   security_logger.addHandler(handler)
   ```

3. **Test Logging:**
   ```python
   from security.utils.logging import SecurityLogger
   
   logger = SecurityLogger()
   logger.log_security_event('test_event', test_data='hello')
   ```

### Issue: Log Files Too Large

**Symptom:**
- Disk space filling up
- Performance degradation

**Solutions:**

1. **Configure Log Rotation:**
   ```python
   import logging.handlers
   
   handler = logging.handlers.RotatingFileHandler(
       'security.log',
       maxBytes=100*1024*1024,  # 100MB
       backupCount=5
   )
   ```

2. **Reduce Log Verbosity:**
   ```python
   config = SecurityConfig(
       log_level='WARNING',  # Only log warnings and errors
       log_security_events=False,  # Disable detailed event logging
   )
   ```

### Issue: Metrics Not Being Collected

**Symptom:**
- No metrics in monitoring dashboard
- Health checks failing

**Solutions:**

1. **Enable Metrics Collection:**
   ```python
   config = SecurityConfig(
       enable_security_metrics=True,
       metrics_backend='prometheus',
   )
   ```

2. **Verify Metrics Endpoint:**
   ```bash
   curl http://localhost:5000/metrics
   # Should return Prometheus metrics
   ```

3. **Check Monitoring Configuration:**
   ```python
   from security.utils.monitoring import SecurityMonitor
   
   monitor = SecurityMonitor()
   health = monitor.check_system_health()
   print(health)
   ```

---

## Integration Problems

### Issue: Flask Integration Problems

**Symptom:**
- Security middleware not working
- Decorators not applying

**Solutions:**

1. **Verify Initialization Order:**
   ```python
   from flask import Flask
   from security import initialize_security, SecurityConfig
   
   app = Flask(__name__)
   
   # Initialize security BEFORE defining routes
   config = SecurityConfig()
   initialize_security(app, config)
   
   # Define routes AFTER initialization
   @app.route('/upload', methods=['POST'])
   @validate_file_upload()
   def upload():
       pass
   ```

2. **Check App Context:**
   ```python
   # Ensure you're in app context when needed
   with app.app_context():
       from security import health_check
       status = health_check()
   ```

### Issue: Database Integration Problems

**Symptom:**
- Session management not working
- User data not loading

**Solutions:**

1. **Configure Session Backend:**
   ```python
   config = SecurityConfig(
       session_backend='database',  # or 'redis'
       database_url=os.getenv('DATABASE_URL'),
   )
   ```

2. **Initialize Database Tables:**
   ```python
   from security.auth_security import init_db
   
   with app.app_context():
       init_db()
   ```

### Issue: Load Balancer Issues

**Symptom:**
- Rate limiting not working across instances
- Session inconsistencies

**Solutions:**

1. **Use Shared Storage:**
   ```python
   config = SecurityConfig(
       cache_backend='redis',
       redis_url='redis://shared-redis:6379/0',
       session_backend='redis',
   )
   ```

2. **Configure Sticky Sessions:**
   ```nginx
   # In nginx.conf
   upstream app_servers {
       ip_hash;  # Enable sticky sessions
       server app1:5000;
       server app2:5000;
   }
   ```

---

## Error Messages Reference

### Common Error Messages and Solutions

#### `SecurityViolationError: Malware detected in uploaded file`
**Cause:** File contains malware or matches threat patterns
**Solution:** 
- Check if it's a false positive
- Update malware signatures
- Review threat patterns

#### `RateLimitExceededError: Too many requests`
**Cause:** User exceeded rate limit
**Solution:**
- Increase rate limits
- Implement exponential backoff
- Check for bot traffic

#### `InvalidFileTypeError: File type not allowed`
**Cause:** File extension not in allowed list
**Solution:**
- Add file type to configuration
- Check MIME type validation

#### `CSRFValidationError: Invalid or missing CSRF token`
**Cause:** CSRF token missing or invalid
**Solution:**
- Ensure token is included in requests
- Check token expiry settings

#### `ConfigurationError: Invalid configuration parameter`
**Cause:** Configuration value is invalid
**Solution:**
- Validate configuration on startup
- Check parameter types and ranges

---

## Debugging Tools

### Health Check Script

```python
#!/usr/bin/env python3
"""
Security Framework Health Check Script
Run this to diagnose common issues
"""

import sys
import os
from security import health_check, SecurityConfig
from security.config import validate_config

def run_health_check():
    print("Security Framework Health Check")
    print("=" * 50)
    
    # Test basic imports
    try:
        from security import __version__
        print(f"✓ Security framework version: {__version__}")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Test configuration
    try:
        config = SecurityConfig()
        is_valid, errors = validate_config(config)
        if is_valid:
            print("✓ Configuration is valid")
        else:
            print("✗ Configuration errors:")
            for error in errors:
                print(f"    - {error}")
    except Exception as e:
        print(f"✗ Configuration error: {e}")
    
    # Test health check
    try:
        health_status = health_check()
        print("\nComponent Health:")
        for component, status in health_status.items():
            indicator = "✓" if status['healthy'] else "✗"
            print(f"  {indicator} {component}: {status.get('message', 'OK')}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
    
    return True

if __name__ == '__main__':
    run_health_check()
```

### Configuration Validator

```python
def validate_security_config(config_file=None):
    """Validate security configuration and report issues"""
    
    if config_file:
        # Load from file
        import yaml
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        config = SecurityConfig.from_dict(config_data)
    else:
        # Use default config
        config = SecurityConfig()
    
    # Run validation
    from security.config import validate_config
    is_valid, errors = validate_config(config)
    
    print("Configuration Validation Report")
    print("=" * 40)
    
    if is_valid:
        print("✓ Configuration is valid")
    else:
        print("✗ Configuration has errors:")
        for error in errors:
            print(f"  - {error}")
    
    # Print configuration summary
    print(f"\nConfiguration Summary:")
    print(f"  Environment: {config.environment}")
    print(f"  Security Level: {config.security_level}")
    print(f"  Malware Scanning: {config.enable_malware_scanning}")
    print(f"  Rate Limiting: {config.rate_limit_enabled}")
    print(f"  Audit Logging: {config.enable_audit_logging}")
    
    return is_valid, errors
```

### Performance Profiler

```python
import time
import cProfile
from security.file_security import scan_for_malware
from security.tests import create_mock_file

def profile_security_operations():
    """Profile security operations to identify bottlenecks"""
    
    print("Security Performance Profiling")
    print("=" * 40)
    
    # Create test file
    test_file = create_mock_file('pdf', size_kb=1000)  # 1MB file
    
    # Profile malware scanning
    print("Profiling malware scanning...")
    
    def scan_test():
        return scan_for_malware(test_file, 'pdf')
    
    # Time the operation
    start_time = time.time()
    result = scan_test()
    scan_time = time.time() - start_time
    
    print(f"Scan time: {scan_time:.2f} seconds")
    print(f"Scan result: {'Safe' if result.is_safe else 'Threat detected'}")
    
    # Profile with cProfile
    print("\nDetailed profiling:")
    cProfile.run('scan_test()', sort='cumulative')

if __name__ == '__main__':
    profile_security_operations()
```

## Getting Additional Help

### Debug Mode Setup

1. **Enable Debug Logging:**
   ```python
   import logging
   logging.getLogger('security').setLevel(logging.DEBUG)
   
   config = SecurityConfig(
       enable_debug_logging=True,
       log_level='DEBUG'
   )
   ```

2. **Use Debug Configuration:**
   ```python
   config = SecurityConfig(
       environment='development',
       enable_debug_mode=True,
       debug_security_operations=True
   )
   ```

### Reporting Issues

When reporting issues, include:

1. **Environment Information:**
   - Python version
   - Operating system
   - Security framework version
   - Dependencies versions

2. **Configuration:**
   - Sanitized configuration (remove secrets)
   - Environment variables

3. **Error Details:**
   - Full error traceback
   - Steps to reproduce
   - Expected vs actual behavior

4. **Logs:**
   - Relevant log entries
   - Debug output if available

### Support Resources

- **Documentation:** Check the [API Documentation](api_documentation.md)
- **Examples:** Review [Examples Directory](examples/)
- **Configuration:** See [Configuration Guide](configuration_guide.md)
- **Migration:** Check [Migration Guide](migration_guide.md)

This troubleshooting guide should help you resolve most common issues with the security framework. If you encounter problems not covered here, enable debug logging and consult the detailed error messages for additional clues.