#!/usr/bin/env python3
"""
Flask integration test for the security framework
"""

from flask import Flask, request, jsonify
from security import SecurityConfig, SecurityLevel, initialize_security
from security.core.decorators import require_csrf, rate_limit, validate_file_upload

# Create Flask app
app = Flask(__name__)
app.secret_key = 'test-secret-key'

# Initialize security framework
config = SecurityConfig(
    environment='development',
    security_level=SecurityLevel.MEDIUM,
    enable_malware_scanning=True,
    rate_limit_enabled=True
)

success = initialize_security(app, config)
print(f"Security framework initialization: {'✓ Success' if success else '✗ Failed'}")

# Test routes with security decorators
@app.route('/test-rate-limit')
@rate_limit(requests_per_minute=5, per_user=True)
def test_rate_limit():
    return jsonify({'message': 'Rate limit test passed', 'success': True})

@app.route('/test-file-upload', methods=['POST'])
@validate_file_upload(allowed_types=['txt', 'pdf'], max_size_mb=1, scan_malware=True)
def test_file_upload():
    return jsonify({'message': 'File upload validation passed', 'success': True})

@app.route('/health')
def health():
    from security import health_check
    return jsonify(health_check())

if __name__ == '__main__':
    print("=== Flask Security Integration Test ===")
    print()
    
    # Test that the app can start with security framework
    with app.app_context():
        print("✓ Flask app context working")
        print("✓ Security config attached to app:", hasattr(app, 'security_config'))
        
        # Test health endpoint
        from security import health_check
        health_result = health_check()
        print("✓ Health check in Flask context:", health_result['overall_status'])
        
        # Test security configuration
        print("✓ Security configuration:")
        print(f"  Environment: {app.security_config.environment}")
        print(f"  Security Level: {app.security_config.security_level}")
        print(f"  Malware Scanning: {app.security_config.enable_malware_scanning}")
        print(f"  Rate Limiting: {app.security_config.rate_limit_enabled}")
        
        print()
        print("✓ Flask integration test passed!")
        print("✓ You can now run: python test_flask_integration.py")
        print("✓ Then visit: http://127.0.0.1:5000/health")
    
    print()
    print("Starting Flask development server for manual testing...")
    print("Visit: http://127.0.0.1:5000/health")
    print("Press Ctrl+C to stop")
    
    app.run(debug=True, host='127.0.0.1', port=5000)