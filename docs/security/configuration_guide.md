# Security Configuration Guide

## Overview

The security framework is highly configurable to adapt to different environments, security requirements, and use cases. This guide covers all configuration options, best practices, and examples for different scenarios.

## Table of Contents

1. [Basic Configuration](#basic-configuration)
2. [Environment-Specific Configuration](#environment-specific-configuration)
3. [Security Levels](#security-levels)
4. [Feature Configuration](#feature-configuration)
5. [Performance Tuning](#performance-tuning)
6. [Advanced Configuration](#advanced-configuration)
7. [Configuration Examples](#configuration-examples)
8. [Troubleshooting](#troubleshooting)

---

## Basic Configuration

### SecurityConfig Class

The main configuration is handled through the `SecurityConfig` class:

```python
from security.config import SecurityConfig, SecurityLevel

config = SecurityConfig(
    environment='production',           # Environment type
    security_level=SecurityLevel.HIGH,  # Security level
    enable_malware_scanning=True,       # Enable malware detection
    rate_limit_enabled=True,           # Enable rate limiting
    strict_file_validation=True,       # Strict file validation
    enable_audit_logging=True          # Enable security audit logs
)
```

### Environment Variables

You can also configure using environment variables:

```bash
# Basic settings
SECURITY_ENVIRONMENT=production
SECURITY_LEVEL=high
SECURITY_ENABLE_MALWARE_SCANNING=true
SECURITY_ENABLE_AUDIT_LOGGING=true

# File settings
SECURITY_MAX_FILE_SIZE_MULTIPLIER=1.0
SECURITY_ALLOWED_FILE_TYPES=pdf,docx,xlsx,pptx,txt,jpg,png

# Rate limiting
SECURITY_RATE_LIMIT_MULTIPLIER=0.5
SECURITY_RATE_LIMIT_ENABLED=true

# Redis settings (for rate limiting)
SECURITY_REDIS_URL=redis://localhost:6379/0
SECURITY_REDIS_PASSWORD=your_redis_password
```

### Loading from Configuration File

```python
# config.yaml
security:
  environment: production
  security_level: high
  malware_scanning:
    enabled: true
    signature_db_path: /opt/security/signatures
    cloud_scanning: false
  file_validation:
    strict_mode: true
    max_size_multiplier: 1.0
    allowed_types: [pdf, docx, xlsx, txt, jpg, png]
  rate_limiting:
    enabled: true
    multiplier: 0.5
    redis_url: redis://localhost:6379/0
  logging:
    audit_enabled: true
    log_level: INFO
```

```python
# Load from YAML
import yaml
from security.config import SecurityConfig

with open('config.yaml', 'r') as f:
    config_data = yaml.safe_load(f)

security_config = SecurityConfig.from_dict(config_data['security'])
```

---

## Environment-Specific Configuration

### Development Environment

Optimized for development speed with moderate security:

```python
dev_config = SecurityConfig(
    environment='development',
    security_level=SecurityLevel.MEDIUM,
    
    # Performance optimizations for dev
    enable_malware_scanning=False,       # Faster file processing
    strict_file_validation=False,        # More lenient validation
    rate_limit_multiplier=5.0,          # Very high rate limits
    max_file_size_multiplier=2.0,       # Larger file sizes allowed
    
    # Development features
    enable_debug_logging=True,          # Detailed logging
    enable_security_metrics=False,     # Disable metrics collection
    cache_validation_results=False,    # Always re-validate for testing
)
```

### Testing Environment

Balanced configuration for automated testing:

```python
test_config = SecurityConfig(
    environment='testing',
    security_level=SecurityLevel.MEDIUM,
    
    # Testing optimizations
    enable_malware_scanning=True,        # Test security features
    malware_scanner_timeout=5,          # Quick scans for tests
    strict_file_validation=True,        # Test validation logic
    rate_limit_multiplier=10.0,         # High limits for test speed
    
    # Test-specific settings
    enable_audit_logging=False,         # Reduce log noise
    use_mock_external_services=True,    # Mock external APIs
    fail_fast_on_security_errors=True,  # Quick failure for tests
)
```

### Staging Environment

Production-like configuration with some relaxed constraints:

```python
staging_config = SecurityConfig(
    environment='staging',
    security_level=SecurityLevel.HIGH,
    
    # Production-like security
    enable_malware_scanning=True,
    strict_file_validation=True,
    rate_limit_multiplier=1.0,
    max_file_size_multiplier=1.2,       # Slightly more lenient
    
    # Staging-specific
    enable_audit_logging=True,
    enable_security_metrics=True,
    malware_scanner_engines=['clamav'], # Subset of engines
)
```

### Production Environment

Maximum security configuration:

```python
prod_config = SecurityConfig(
    environment='production',
    security_level=SecurityLevel.HIGH,
    
    # Maximum security
    enable_malware_scanning=True,
    strict_file_validation=True,
    rate_limit_multiplier=0.5,          # Strict rate limits
    max_file_size_multiplier=1.0,       # Standard file sizes
    
    # Production features
    enable_audit_logging=True,
    enable_security_metrics=True,
    enable_threat_intelligence=True,    # External threat feeds
    malware_scanner_engines=['clamav', 'yara', 'custom'],
    
    # Performance settings
    cache_validation_results=True,
    enable_async_scanning=True,
    max_concurrent_scans=5,
)
```

---

## Security Levels

### SecurityLevel.LOW
- Basic input validation
- Standard rate limiting
- No malware scanning
- Minimal logging
- Suitable for: Internal development, low-risk applications

```python
low_security = SecurityConfig(
    security_level=SecurityLevel.LOW,
    rate_limit_multiplier=10.0,
    enable_malware_scanning=False,
    strict_file_validation=False,
    log_security_events=False,
)
```

### SecurityLevel.MEDIUM
- Enhanced input validation
- Moderate rate limiting
- Basic malware scanning
- Standard logging
- Suitable for: Internal applications, testing environments

```python
medium_security = SecurityConfig(
    security_level=SecurityLevel.MEDIUM,
    rate_limit_multiplier=2.0,
    enable_malware_scanning=True,
    malware_scanner_engines=['clamav'],
    strict_file_validation=True,
)
```

### SecurityLevel.HIGH
- Comprehensive input validation
- Strict rate limiting
- Advanced malware scanning
- Detailed logging and monitoring
- Suitable for: Production applications, high-risk environments

```python
high_security = SecurityConfig(
    security_level=SecurityLevel.HIGH,
    rate_limit_multiplier=0.5,
    enable_malware_scanning=True,
    malware_scanner_engines=['clamav', 'yara', 'custom'],
    strict_file_validation=True,
    enable_content_analysis=True,
    enable_threat_intelligence=True,
)
```

---

## Feature Configuration

### File Upload Security

```python
file_config = SecurityConfig(
    # File size limits (in bytes)
    default_max_file_size=50 * 1024 * 1024,  # 50MB default
    max_file_size_limits={
        'pdf': 100 * 1024 * 1024,     # 100MB for PDFs
        'docx': 50 * 1024 * 1024,     # 50MB for Word docs
        'xlsx': 25 * 1024 * 1024,     # 25MB for Excel
        'txt': 1 * 1024 * 1024,       # 1MB for text files
        'jpg': 10 * 1024 * 1024,      # 10MB for images
        'png': 10 * 1024 * 1024,      # 10MB for images
    },
    
    # File type restrictions
    allowed_file_extensions=[
        'pdf', 'docx', 'xlsx', 'pptx', 'txt',
        'jpg', 'jpeg', 'png', 'gif', 'bmp'
    ],
    
    # MIME type validation
    validate_mime_types=True,
    allowed_mime_types={
        'pdf': ['application/pdf'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'txt': ['text/plain'],
        'jpg': ['image/jpeg'],
        'png': ['image/png'],
    },
    
    # User-type specific limits
    file_size_multipliers={
        'basic': 1.0,      # Standard limits
        'premium': 2.0,    # Double the limits
        'enterprise': 5.0,  # 5x the limits
        'admin': 10.0,     # 10x the limits
    },
)
```

### Malware Scanning Configuration

```python
malware_config = SecurityConfig(
    enable_malware_scanning=True,
    
    # Scanner engines
    malware_scanner_engines=['clamav', 'yara'],
    
    # ClamAV configuration
    clamav_config={
        'database_path': '/var/lib/clamav',
        'update_frequency': 3600,  # Update every hour
        'max_scan_size': 100 * 1024 * 1024,  # 100MB max scan
        'max_files': 10000,        # Max files in archive
        'max_recursion': 16,       # Max archive depth
    },
    
    # YARA configuration
    yara_config={
        'rules_path': '/opt/security/yara_rules',
        'custom_rules_enabled': True,
        'rule_update_frequency': 7200,  # Update every 2 hours
    },
    
    # Scanning behavior
    scan_timeout=30,               # 30 second timeout
    async_scanning=True,          # Scan in background
    quarantine_threats=True,      # Quarantine detected threats
    scan_archives=True,           # Scan inside archives
    max_concurrent_scans=5,       # Limit concurrent scans
)
```

### Rate Limiting Configuration

```python
rate_limit_config = SecurityConfig(
    rate_limit_enabled=True,
    
    # Global rate limits (requests per minute)
    default_rate_limits={
        'api': 100,           # API endpoints
        'upload': 10,         # File uploads
        'conversion': 5,      # Document conversion
        'download': 50,       # File downloads
        'login': 5,           # Authentication attempts
    },
    
    # User-type specific multipliers
    rate_limit_multipliers={
        'anonymous': 0.5,     # Half the limits
        'basic': 1.0,         # Standard limits
        'premium': 2.0,       # Double the limits
        'enterprise': 5.0,    # 5x the limits
        'admin': 10.0,        # 10x the limits
    },
    
    # Redis configuration for rate limiting
    redis_config={
        'url': 'redis://localhost:6379/1',
        'password': None,
        'socket_timeout': 5,
        'connection_pool_max_connections': 20,
    },
    
    # Rate limit behavior
    rate_limit_window=60,         # 60 second window
    rate_limit_headers=True,      # Include rate limit headers
    rate_limit_strategy='sliding_window',  # or 'fixed_window'
)
```

### CSRF Protection Configuration

```python
csrf_config = SecurityConfig(
    csrf_enabled=True,
    
    # Token configuration
    csrf_token_length=32,         # 32 character tokens
    csrf_token_expiry=3600,       # 1 hour expiry
    csrf_secret_key='your-secret-key',  # Or load from env
    
    # Protection behavior
    csrf_protect_all_forms=True,  # Protect all POST requests
    csrf_exempt_endpoints=[       # Exempt specific endpoints
        '/api/webhook',
        '/health-check',
    ],
    
    # Error handling
    csrf_error_handler='custom',  # Custom error handler
    csrf_error_message='CSRF token validation failed',
)
```

---

## Performance Tuning

### Caching Configuration

```python
cache_config = SecurityConfig(
    # Validation result caching
    cache_validation_results=True,
    validation_cache_ttl=300,      # 5 minutes
    validation_cache_size=1000,    # Cache 1000 results
    
    # Malware signature caching
    cache_malware_signatures=True,
    signature_cache_ttl=3600,      # 1 hour
    
    # File hash caching
    cache_file_hashes=True,
    file_hash_cache_ttl=1800,     # 30 minutes
    
    # Redis caching
    cache_backend='redis',         # or 'memory', 'filesystem'
    cache_redis_url='redis://localhost:6379/2',
)
```

### Asynchronous Processing

```python
async_config = SecurityConfig(
    # Async malware scanning
    enable_async_scanning=True,
    async_scan_queue='celery',     # or 'rq', 'dramatiq'
    async_scan_timeout=300,        # 5 minutes
    
    # Async validation
    enable_async_validation=False, # Keep synchronous for now
    
    # Background processing
    enable_background_tasks=True,
    background_worker_count=4,
    
    # Queue configuration
    task_queue_config={
        'broker_url': 'redis://localhost:6379/3',
        'result_backend': 'redis://localhost:6379/3',
        'task_serializer': 'json',
        'result_serializer': 'json',
    },
)
```

### Resource Limits

```python
resource_config = SecurityConfig(
    # Memory limits
    max_memory_per_scan=512 * 1024 * 1024,  # 512MB per scan
    max_total_scan_memory=2 * 1024 * 1024 * 1024,  # 2GB total
    
    # Processing limits
    max_concurrent_operations=10,   # Max concurrent security ops
    max_scan_time=60,              # Max scan time in seconds
    max_validation_time=30,        # Max validation time
    
    # File limits
    max_file_handles=1000,         # Max open file handles
    max_temp_files=100,           # Max temporary files
    temp_file_cleanup_interval=300, # Clean temp files every 5 min
)
```

---

## Advanced Configuration

### Custom Security Policies

```python
custom_config = SecurityConfig(
    # Custom validation rules
    custom_validation_rules={
        'pdf': [
            'no_javascript',      # No JavaScript in PDFs
            'no_external_links',  # No external links
            'max_pages:100',      # Max 100 pages
        ],
        'docx': [
            'no_macros',         # No VBA macros
            'no_external_data',  # No external data connections
        ],
    },
    
    # Custom threat patterns
    custom_threat_patterns=[
        r'<script.*?>.*?</script>',  # Script tags
        r'javascript:',              # JavaScript URLs
        r'vbscript:',               # VBScript URLs
    ],
    
    # Custom content filters
    custom_content_filters={
        'remove_metadata': True,     # Remove file metadata
        'sanitize_filenames': True,  # Clean filenames
        'compress_images': False,    # Don't compress images
    },
)
```

### Integration with External Services

```python
external_config = SecurityConfig(
    # Threat intelligence feeds
    enable_threat_intelligence=True,
    threat_intel_providers=[
        {
            'name': 'virustotal',
            'api_key': 'your-vt-api-key',
            'enabled': True,
            'timeout': 10,
        },
        {
            'name': 'hybrid_analysis',
            'api_key': 'your-ha-api-key',
            'enabled': False,
            'timeout': 15,
        }
    ],
    
    # External malware scanners
    external_scanners=[
        {
            'name': 'metadefender',
            'api_key': 'your-md-api-key',
            'endpoint': 'https://api.metadefender.com/v4',
            'enabled': True,
        }
    ],
    
    # SIEM integration
    siem_integration={
        'enabled': True,
        'endpoint': 'https://your-siem.company.com/api/events',
        'api_key': 'your-siem-api-key',
        'event_types': ['malware_detected', 'rate_limit_exceeded'],
    },
)
```

### Monitoring and Alerting

```python
monitoring_config = SecurityConfig(
    # Metrics collection
    enable_security_metrics=True,
    metrics_backend='prometheus',   # or 'statsd', 'datadog'
    metrics_endpoint='http://prometheus:9090',
    
    # Alerting
    enable_alerts=True,
    alert_channels=[
        {
            'type': 'email',
            'recipients': ['security@company.com'],
            'severity_threshold': 'HIGH',
        },
        {
            'type': 'slack',
            'webhook_url': 'https://hooks.slack.com/...',
            'channel': '#security-alerts',
            'severity_threshold': 'MEDIUM',
        },
        {
            'type': 'pagerduty',
            'service_key': 'your-pd-service-key',
            'severity_threshold': 'CRITICAL',
        }
    ],
    
    # Health checks
    enable_health_checks=True,
    health_check_interval=60,      # Check every minute
    health_check_endpoints=[
        '/health/security',
        '/health/malware-scanner',
        '/health/rate-limiter',
    ],
)
```

---

## Configuration Examples

### Small Application (Single Server)

```python
small_app_config = SecurityConfig(
    environment='production',
    security_level=SecurityLevel.MEDIUM,
    
    # Simplified security
    enable_malware_scanning=True,
    malware_scanner_engines=['clamav'],
    rate_limit_enabled=True,
    default_rate_limits={'api': 60, 'upload': 10},
    
    # Local storage
    cache_backend='memory',
    redis_config=None,  # No Redis required
    
    # Basic logging
    enable_audit_logging=True,
    log_level='INFO',
)
```

### Medium Application (Load Balanced)

```python
medium_app_config = SecurityConfig(
    environment='production',
    security_level=SecurityLevel.HIGH,
    
    # Enhanced security
    enable_malware_scanning=True,
    malware_scanner_engines=['clamav', 'yara'],
    rate_limit_enabled=True,
    enable_threat_intelligence=False,  # Not needed yet
    
    # Redis for scaling
    cache_backend='redis',
    redis_config={
        'url': 'redis://redis-cluster:6379/0',
        'password': 'redis-password',
    },
    
    # Monitoring
    enable_security_metrics=True,
    metrics_backend='prometheus',
)
```

### Large Application (Microservices)

```python
large_app_config = SecurityConfig(
    environment='production',
    security_level=SecurityLevel.HIGH,
    
    # Maximum security
    enable_malware_scanning=True,
    malware_scanner_engines=['clamav', 'yara', 'custom'],
    enable_threat_intelligence=True,
    enable_async_scanning=True,
    
    # Distributed caching
    cache_backend='redis',
    redis_config={
        'url': 'redis://redis-cluster:6379/0',
        'sentinel_service': 'mymaster',
        'sentinel_hosts': [
            ('redis-sentinel-1', 26379),
            ('redis-sentinel-2', 26379),
            ('redis-sentinel-3', 26379),
        ],
    },
    
    # Advanced monitoring
    enable_security_metrics=True,
    enable_alerts=True,
    siem_integration={'enabled': True},
    
    # Performance optimization
    max_concurrent_scans=10,
    enable_async_validation=True,
    cache_validation_results=True,
)
```

---

## Configuration Validation

### Validating Configuration

```python
from security.config import SecurityConfig, validate_config

# Load configuration
config = SecurityConfig(environment='production')

# Validate configuration
is_valid, errors = validate_config(config)
if not is_valid:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
    exit(1)

print("Configuration is valid")
```

### Configuration Testing

```python
# Test configuration in different environments
configs = {
    'dev': SecurityConfig(environment='development'),
    'test': SecurityConfig(environment='testing'),
    'prod': SecurityConfig(environment='production'),
}

for env_name, config in configs.items():
    print(f"\nTesting {env_name} configuration:")
    
    # Test file size limits
    pdf_limit = config.get_max_file_size('pdf', 'basic')
    print(f"PDF size limit: {pdf_limit / 1024 / 1024:.1f}MB")
    
    # Test rate limits
    api_limit = config.get_rate_limit('api', 'basic')
    print(f"API rate limit: {api_limit} requests/minute")
    
    # Test features
    print(f"Malware scanning: {config.enable_malware_scanning}")
    print(f"Strict validation: {config.strict_file_validation}")
```

---

## Troubleshooting

### Common Configuration Issues

#### Redis Connection Issues
```python
# Problem: Redis connection fails
redis_config = {
    'url': 'redis://localhost:6379/0',
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True,
    'health_check_interval': 30,
}

# Test Redis connection
from security.utils.redis_helper import test_redis_connection
if not test_redis_connection(redis_config):
    print("Redis connection failed - falling back to memory cache")
    config.cache_backend = 'memory'
```

#### Malware Scanner Issues
```python
# Problem: ClamAV not working
try:
    from security.file_security.malware_scanner import test_clamav
    test_clamav()
except Exception as e:
    print(f"ClamAV test failed: {e}")
    # Disable malware scanning or use alternative
    config.enable_malware_scanning = False
    # Or use only YARA
    config.malware_scanner_engines = ['yara']
```

#### Performance Issues
```python
# Problem: Security checks are too slow
performance_config = SecurityConfig(
    # Reduce scan intensity
    malware_scanner_timeout=15,  # Reduce timeout
    enable_async_scanning=True,  # Use background scanning
    cache_validation_results=True,  # Cache results
    
    # Optimize file handling
    max_concurrent_scans=3,      # Reduce concurrent scans
    scan_archives=False,         # Skip archive scanning
    
    # Skip expensive checks in development
    enable_content_analysis=False if environment == 'development' else True,
)
```

### Configuration Debugging

Enable debug logging to troubleshoot configuration issues:

```python
import logging

# Enable debug logging
logging.getLogger('security').setLevel(logging.DEBUG)

# Load configuration with debugging
config = SecurityConfig(
    environment='development',
    enable_debug_logging=True,
    debug_config_validation=True,
)

# This will print detailed configuration information
print(config.debug_info())
```

### Health Checks

Monitor configuration health:

```python
from security import health_check

# Run comprehensive health check
health_status = health_check()

print("Security framework health:")
for component, status in health_status.items():
    print(f"  {component}: {'✓' if status['healthy'] else '✗'} {status.get('message', '')}")
```

---

## Best Practices

1. **Environment-specific configs**: Use different configurations for each environment
2. **Validate on startup**: Always validate configuration when the application starts
3. **Monitor performance**: Track the impact of security features on performance
4. **Regular updates**: Keep malware signatures and threat intelligence updated
5. **Graceful degradation**: Handle configuration errors gracefully
6. **Security by default**: Use secure defaults and require explicit opt-out
7. **Document changes**: Document any configuration changes and their impact
8. **Test configurations**: Test security configurations in staging before production