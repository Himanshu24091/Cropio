"""
Advanced Security Configuration Examples

This file demonstrates various security configurations for different use cases
and environments, showing the flexibility of the security framework.
"""

from security.config import SecurityConfig, SecurityLevel
from security import initialize_security
from flask import Flask
import os

# =============================================================================
# Example 1: High-Security Financial Application
# =============================================================================

def create_financial_app():
    """Configuration for a financial application with maximum security"""
    
    app = Flask(__name__)
    
    financial_config = SecurityConfig(
        environment='production',
        security_level=SecurityLevel.HIGH,
        
        # Strict file handling
        enable_malware_scanning=True,
        malware_scanner_engines=['clamav', 'yara', 'custom'],
        strict_file_validation=True,
        quarantine_threats=True,
        
        # Very strict rate limiting
        rate_limit_enabled=True,
        rate_limit_multiplier=0.1,  # Very restrictive
        default_rate_limits={
            'api': 20,              # 20 requests/minute for API
            'upload': 2,            # Only 2 uploads/minute
            'conversion': 1,        # 1 conversion/minute
            'login': 3,             # 3 login attempts/minute
        },
        
        # Advanced file restrictions
        allowed_file_extensions=['pdf', 'txt'],  # Very limited
        max_file_size_limits={
            'pdf': 10 * 1024 * 1024,    # 10MB max for PDFs
            'txt': 1 * 1024 * 1024,     # 1MB max for text
        },
        
        # Enhanced security features
        enable_threat_intelligence=True,
        enable_content_analysis=True,
        remove_file_metadata=True,
        encrypt_files_at_rest=True,
        
        # Comprehensive logging
        enable_audit_logging=True,
        log_level='DEBUG',
        enable_security_metrics=True,
        
        # External integrations
        siem_integration={
            'enabled': True,
            'endpoint': 'https://siem.financial-corp.com/api/events',
            'api_key': os.getenv('SIEM_API_KEY'),
            'event_types': ['all'],  # Log everything
        },
        
        # Monitoring and alerting
        enable_alerts=True,
        alert_channels=[
            {
                'type': 'email',
                'recipients': ['security@financial-corp.com'],
                'severity_threshold': 'MEDIUM',
            },
            {
                'type': 'pagerduty',
                'service_key': os.getenv('PAGERDUTY_KEY'),
                'severity_threshold': 'HIGH',
            }
        ],
    )
    
    initialize_security(app, financial_config)
    return app

# =============================================================================
# Example 2: Healthcare Application (HIPAA Compliant)
# =============================================================================

def create_healthcare_app():
    """Configuration for HIPAA-compliant healthcare application"""
    
    app = Flask(__name__)
    
    healthcare_config = SecurityConfig(
        environment='production',
        security_level=SecurityLevel.HIGH,
        
        # HIPAA-specific requirements
        enable_audit_logging=True,
        audit_log_retention_days=2555,  # 7 years as required by HIPAA
        encrypt_audit_logs=True,
        
        # File security for medical records
        enable_malware_scanning=True,
        scan_medical_documents=True,
        allowed_file_extensions=['pdf', 'docx', 'jpg', 'png', 'dicom'],
        
        # Medical file size limits
        max_file_size_limits={
            'pdf': 50 * 1024 * 1024,     # 50MB for medical PDFs
            'docx': 25 * 1024 * 1024,    # 25MB for documents
            'jpg': 25 * 1024 * 1024,     # 25MB for medical images
            'png': 25 * 1024 * 1024,     # 25MB for medical images
            'dicom': 100 * 1024 * 1024,  # 100MB for DICOM files
        },
        
        # Enhanced privacy protection
        anonymize_patient_data=True,
        redact_sensitive_content=True,
        enable_data_loss_prevention=True,
        
        # Access controls
        require_mfa_for_sensitive_operations=True,
        session_timeout_minutes=15,  # Short session timeout
        
        # Compliance monitoring
        enable_hipaa_compliance_checks=True,
        generate_compliance_reports=True,
        
        # Data encryption
        encrypt_files_at_rest=True,
        encryption_algorithm='AES-256-GCM',
        key_rotation_days=90,
    )
    
    initialize_security(app, healthcare_config)
    return app

# =============================================================================
# Example 3: Educational Platform (Balanced Security)
# =============================================================================

def create_education_app():
    """Configuration for educational platform with balanced security"""
    
    app = Flask(__name__)
    
    education_config = SecurityConfig(
        environment='production',
        security_level=SecurityLevel.MEDIUM,
        
        # Student-friendly file handling
        enable_malware_scanning=True,
        malware_scanner_engines=['clamav'],  # Single engine for speed
        allowed_file_extensions=[
            'pdf', 'docx', 'pptx', 'xlsx', 'txt',
            'jpg', 'jpeg', 'png', 'gif',
            'mp4', 'avi', 'mov'  # Video files for assignments
        ],
        
        # Generous but reasonable limits
        max_file_size_limits={
            'pdf': 100 * 1024 * 1024,    # 100MB for presentations
            'docx': 50 * 1024 * 1024,    # 50MB for documents
            'pptx': 100 * 1024 * 1024,   # 100MB for presentations
            'xlsx': 25 * 1024 * 1024,    # 25MB for spreadsheets
            'jpg': 20 * 1024 * 1024,     # 20MB for images
            'mp4': 500 * 1024 * 1024,    # 500MB for videos
        },
        
        # Student-tier rate limits
        rate_limit_multipliers={
            'student': 1.0,      # Standard limits
            'teacher': 3.0,      # Higher limits for teachers
            'admin': 10.0,       # Very high limits for admins
        },
        
        # Educational features
        enable_plagiarism_detection=True,
        content_filtering_level='moderate',
        allow_collaborative_uploads=True,
        
        # Moderate logging
        enable_audit_logging=True,
        log_level='INFO',
        log_student_activity=True,  # For academic integrity
        
        # Performance optimizations for many users
        cache_validation_results=True,
        enable_async_scanning=True,
        max_concurrent_scans=10,
    )
    
    initialize_security(app, education_config)
    return app

# =============================================================================
# Example 4: Development Environment
# =============================================================================

def create_development_app():
    """Configuration optimized for development speed"""
    
    app = Flask(__name__)
    
    dev_config = SecurityConfig(
        environment='development',
        security_level=SecurityLevel.LOW,
        
        # Minimal security for fast development
        enable_malware_scanning=False,  # Skip for speed
        strict_file_validation=False,
        
        # Very permissive limits
        rate_limit_multiplier=100.0,  # Essentially disabled
        max_file_size_multiplier=10.0,  # Very large files allowed
        
        # All file types allowed for testing
        allowed_file_extensions='*',  # Allow everything
        
        # Development features
        enable_debug_logging=True,
        log_level='DEBUG',
        enable_request_tracing=True,
        mock_external_services=True,
        
        # Fast caching
        cache_backend='memory',
        cache_validation_results=False,  # Always re-validate
        
        # Development-specific settings
        csrf_exempt_in_debug=True,
        disable_https_redirect=True,
        allow_weak_passwords=True,  # For testing only
        
        # Minimal monitoring
        enable_security_metrics=False,
        enable_alerts=False,
    )
    
    initialize_security(app, dev_config)
    return app

# =============================================================================
# Example 5: API-Only Service (Microservice)
# =============================================================================

def create_api_service():
    """Configuration for API-only microservice"""
    
    app = Flask(__name__)
    
    api_config = SecurityConfig(
        environment='production',
        security_level=SecurityLevel.HIGH,
        
        # API-specific security
        enable_api_key_validation=True,
        require_jwt_tokens=True,
        enable_oauth2=True,
        
        # No file uploads in this service
        disable_file_uploads=True,
        
        # API rate limiting
        rate_limit_strategy='sliding_window',
        default_rate_limits={
            'api': 1000,         # High API throughput
            'auth': 20,          # Limited auth attempts
        },
        
        # API-specific validation
        validate_json_schema=True,
        sanitize_json_input=True,
        max_request_size_mb=1,  # Small requests only
        
        # Monitoring for APIs
        enable_api_metrics=True,
        track_api_usage=True,
        enable_distributed_tracing=True,
        
        # Microservice features
        enable_circuit_breaker=True,
        health_check_endpoints=['/health', '/ready', '/live'],
        
        # Security headers for APIs
        api_security_headers={
            'X-API-Version': 'v1.0',
            'X-Rate-Limit-Policy': 'sliding-window',
            'X-Content-Type-Options': 'nosniff',
        },
    )
    
    initialize_security(app, api_config)
    return app

# =============================================================================
# Example 6: Multi-Tenant SaaS Application
# =============================================================================

def create_saas_app():
    """Configuration for multi-tenant SaaS application"""
    
    app = Flask(__name__)
    
    saas_config = SecurityConfig(
        environment='production',
        security_level=SecurityLevel.HIGH,
        
        # Tenant isolation
        enable_tenant_isolation=True,
        tenant_rate_limiting=True,
        per_tenant_file_limits=True,
        
        # Tenant-specific configurations
        tenant_configs={
            'enterprise': {
                'rate_limit_multiplier': 5.0,
                'max_file_size_multiplier': 3.0,
                'enable_advanced_scanning': True,
            },
            'premium': {
                'rate_limit_multiplier': 2.0,
                'max_file_size_multiplier': 2.0,
                'enable_malware_scanning': True,
            },
            'basic': {
                'rate_limit_multiplier': 1.0,
                'max_file_size_multiplier': 1.0,
                'enable_malware_scanning': False,
            }
        },
        
        # SaaS-specific features
        enable_usage_tracking=True,
        billing_integration=True,
        quota_enforcement=True,
        
        # Multi-tenant security
        tenant_data_isolation=True,
        enable_tenant_specific_keys=True,
        cross_tenant_access_prevention=True,
        
        # Scalability features
        distributed_caching=True,
        redis_cluster_config={
            'sentinel_hosts': [
                ('redis-sentinel-1', 26379),
                ('redis-sentinel-2', 26379),
                ('redis-sentinel-3', 26379),
            ],
            'service_name': 'mymaster',
        },
        
        # Advanced monitoring
        per_tenant_metrics=True,
        tenant_specific_alerting=True,
        usage_analytics=True,
    )
    
    initialize_security(app, saas_config)
    return app

# =============================================================================
# Example 7: Content Management System
# =============================================================================

def create_cms_app():
    """Configuration for content management system"""
    
    app = Flask(__name__)
    
    cms_config = SecurityConfig(
        environment='production',
        security_level=SecurityLevel.MEDIUM,
        
        # Media-heavy configuration
        allowed_file_extensions=[
            # Documents
            'pdf', 'docx', 'pptx', 'xlsx', 'txt', 'rtf',
            # Images
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg',
            # Audio
            'mp3', 'wav', 'flac', 'aac',
            # Video
            'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm',
            # Archives
            'zip', 'rar', '7z', 'tar', 'gz'
        ],
        
        # Large file support for media
        max_file_size_limits={
            # Documents
            'pdf': 100 * 1024 * 1024,
            'docx': 50 * 1024 * 1024,
            # Images
            'jpg': 50 * 1024 * 1024,
            'png': 50 * 1024 * 1024,
            'svg': 5 * 1024 * 1024,   # Smaller limit for SVG
            # Audio
            'mp3': 100 * 1024 * 1024,
            'wav': 200 * 1024 * 1024,
            # Video
            'mp4': 1000 * 1024 * 1024,  # 1GB for videos
            'avi': 1000 * 1024 * 1024,
            # Archives
            'zip': 500 * 1024 * 1024,
        },
        
        # Content-specific security
        enable_image_malware_scanning=True,
        scan_archives=True,
        max_archive_depth=5,
        extract_and_scan_archives=True,
        
        # Content processing
        auto_generate_thumbnails=True,
        image_optimization=True,
        video_transcoding=False,  # Handled separately
        
        # User role-based limits
        file_size_multipliers={
            'contributor': 0.5,   # Limited uploads
            'author': 1.0,        # Standard limits
            'editor': 2.0,        # Higher limits
            'admin': 5.0,         # Very high limits
        },
        
        # CMS-specific features
        content_versioning=True,
        draft_content_scanning=False,  # Skip scanning drafts
        published_content_verification=True,
        
        # Performance for media-heavy loads
        enable_async_processing=True,
        background_media_processing=True,
        cdn_integration=True,
    )
    
    initialize_security(app, cms_config)
    return app

# =============================================================================
# Configuration Helper Functions
# =============================================================================

def get_config_for_environment(environment_name):
    """Get appropriate configuration based on environment name"""
    
    configs = {
        'financial': create_financial_app,
        'healthcare': create_healthcare_app,
        'education': create_education_app,
        'development': create_development_app,
        'api': create_api_service,
        'saas': create_saas_app,
        'cms': create_cms_app,
    }
    
    if environment_name in configs:
        return configs[environment_name]()
    else:
        raise ValueError(f"Unknown environment: {environment_name}")

def validate_all_configurations():
    """Validate all example configurations"""
    from security.config import validate_config
    
    configs = {
        'Financial': create_financial_app,
        'Healthcare': create_healthcare_app,
        'Education': create_education_app,
        'Development': create_development_app,
        'API Service': create_api_service,
        'SaaS': create_saas_app,
        'CMS': create_cms_app,
    }
    
    results = {}
    
    for name, create_func in configs.items():
        try:
            app = create_func()
            config = app.security_config
            is_valid, errors = validate_config(config)
            results[name] = {
                'valid': is_valid,
                'errors': errors if not is_valid else []
            }
        except Exception as e:
            results[name] = {
                'valid': False,
                'errors': [str(e)]
            }
    
    return results

if __name__ == '__main__':
    # Validate all configurations
    results = validate_all_configurations()
    
    print("Configuration Validation Results:")
    print("=" * 50)
    
    for name, result in results.items():
        status = "✓ VALID" if result['valid'] else "✗ INVALID"
        print(f"{name:15} {status}")
        
        if not result['valid']:
            for error in result['errors']:
                print(f"    Error: {error}")
        print()
    
    # Example usage
    print("\nExample: Creating a financial application")
    financial_app = create_financial_app()
    print(f"Created financial app with config: {financial_app.security_config}")
    
    print("\nExample: Getting config for education environment")
    education_app = get_config_for_environment('education')
    print(f"Created education app with config: {education_app.security_config}")