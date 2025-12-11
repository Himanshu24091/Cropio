"""
Basic Flask Application Example using Security Framework

This example demonstrates how to integrate the universal security framework
into a simple Flask application with file upload and conversion functionality.
"""

from flask import Flask, request, render_template, jsonify, session, g
import os
from werkzeug.utils import secure_filename

# Security framework imports
from security import initialize_security, SecurityConfig, SecurityLevel
from security.core.decorators import (
    require_csrf, rate_limit, validate_file_upload, require_authentication
)
from security.core.validators import validate_user_input
from security.core.sanitizers import sanitize_filename
from security.web_security.csrf import generate_csrf_token
from security.utils.logging import SecurityLogger
from security.core.exceptions import SecurityViolationError

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change in production

# Initialize security framework
security_config = SecurityConfig(
    environment='development',
    security_level=SecurityLevel.MEDIUM,
    enable_malware_scanning=True,
    rate_limit_enabled=True,
    enable_audit_logging=True
)

initialize_security(app, security_config)

# Initialize security logger
security_logger = SecurityLogger()

# Mock user session management (use proper auth in production)
def get_current_user():
    """Get current user from session"""
    return session.get('user_id')

def get_user_type():
    """Get current user type"""
    return session.get('user_type', 'basic')

@app.before_request
def before_request():
    """Set up request context"""
    g.user_id = get_current_user()
    g.user_type = get_user_type()

@app.route('/')
def index():
    """Main page with upload form"""
    # Generate CSRF token for forms
    csrf_token = generate_csrf_token(user_id=g.user_id)
    
    return render_template('index.html', csrf_token=csrf_token)

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(requests_per_minute=5)  # Protect against brute force
def login():
    """Simple login endpoint"""
    if request.method == 'GET':
        csrf_token = generate_csrf_token()
        return render_template('login.html', csrf_token=csrf_token)
    
    try:
        # Validate input
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # Validate user input
        username_valid, username_errors = validate_user_input(username, 'username')
        if not username_valid:
            return jsonify({'error': 'Invalid username', 'details': username_errors}), 400
        
        password_valid, password_errors = validate_user_input(password, 'password')
        if not password_valid:
            return jsonify({'error': 'Invalid password', 'details': password_errors}), 400
        
        # Mock authentication (implement proper auth in production)
        if username == 'admin' and password == 'password':
            session['user_id'] = 'admin'
            session['user_type'] = 'admin'
            
            # Log successful authentication
            security_logger.log_authentication_attempt(
                user_id='admin',
                success=True,
                ip_address=request.remote_addr
            )
            
            return jsonify({'success': 'Login successful'})
        else:
            # Log failed authentication
            security_logger.log_authentication_attempt(
                user_id=username,
                success=False,
                ip_address=request.remote_addr,
                failure_reason='invalid_credentials'
            )
            
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except SecurityViolationError as e:
        security_logger.log_security_event(
            event_type='login_security_violation',
            user_id=username,
            details=e.get_audit_data()
        )
        return jsonify({'error': 'Security violation detected'}), 400

@app.route('/upload', methods=['POST'])
@require_csrf()  # CSRF protection
@rate_limit(requests_per_minute=10, per_user=True)  # Rate limiting
@validate_file_upload(
    allowed_types=['pdf', 'docx', 'txt', 'jpg', 'png'],
    max_size_mb=25,
    scan_malware=True
)
def upload_file():
    """File upload endpoint with comprehensive security"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(app.instance_path, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file with sanitized name
        file_path = os.path.join(upload_dir, safe_filename)
        file.save(file_path)
        
        # Log successful upload
        security_logger.log_file_operation(
            operation='upload',
            file_info={
                'original_name': file.filename,
                'safe_name': safe_filename,
                'size': os.path.getsize(file_path),
                'type': file.content_type
            },
            user_id=g.user_id,
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'success': 'File uploaded successfully',
            'filename': safe_filename,
            'size': os.path.getsize(file_path)
        })
        
    except SecurityViolationError as e:
        security_logger.log_security_event(
            event_type='file_upload_blocked',
            user_id=g.user_id,
            details=e.get_audit_data()
        )
        return jsonify({'error': str(e)}), 400

@app.route('/convert', methods=['POST'])
@require_csrf()
@require_authentication()  # Require login
@rate_limit(requests_per_minute=5, per_user=True)  # Stricter rate limit
@validate_file_upload(
    allowed_types=['pdf', 'docx'],
    max_size_mb=50,
    scan_malware=True
)
def convert_document():
    """Document conversion endpoint with authentication"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        target_format = request.form.get('format', 'pdf')
        
        # Validate target format
        allowed_formats = ['pdf', 'docx', 'txt']
        if target_format not in allowed_formats:
            return jsonify({
                'error': 'Invalid target format',
                'allowed_formats': allowed_formats
            }), 400
        
        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)
        
        # Mock conversion logic (implement actual conversion)
        converted_filename = f"converted_{safe_filename}.{target_format}"
        
        # Log conversion
        security_logger.log_file_operation(
            operation='convert',
            file_info={
                'original_name': file.filename,
                'safe_name': safe_filename,
                'target_format': target_format,
                'size': len(file.read())
            },
            user_id=g.user_id,
            ip_address=request.remote_addr
        )
        
        file.seek(0)  # Reset file pointer after read
        
        return jsonify({
            'success': 'File converted successfully',
            'original_file': safe_filename,
            'converted_file': converted_filename,
            'format': target_format
        })
        
    except SecurityViolationError as e:
        security_logger.log_security_event(
            event_type='file_conversion_blocked',
            user_id=g.user_id,
            details=e.get_audit_data()
        )
        return jsonify({'error': str(e)}), 400

@app.route('/api/files', methods=['GET'])
@require_authentication()
@rate_limit(requests_per_minute=30, per_user=True)
def list_files():
    """API endpoint to list uploaded files"""
    try:
        upload_dir = os.path.join(app.instance_path, 'uploads')
        
        if not os.path.exists(upload_dir):
            return jsonify({'files': []})
        
        files = []
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                files.append({
                    'name': filename,
                    'size': os.path.getsize(file_path),
                    'modified': os.path.getmtime(file_path)
                })
        
        return jsonify({'files': files})
        
    except Exception as e:
        return jsonify({'error': 'Failed to list files'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint (no security restrictions)"""
    from security import health_check
    
    health_status = health_check()
    
    # Return overall status
    overall_healthy = all(
        component['healthy'] for component in health_status.values()
    )
    
    status_code = 200 if overall_healthy else 503
    
    return jsonify({
        'status': 'healthy' if overall_healthy else 'unhealthy',
        'components': health_status
    }), status_code

@app.route('/security/csrf-token', methods=['GET'])
def get_csrf_token():
    """Get CSRF token for AJAX requests"""
    token = generate_csrf_token(user_id=g.user_id)
    return jsonify({'csrf_token': token})

@app.errorhandler(SecurityViolationError)
def handle_security_violation(e):
    """Global handler for security violations"""
    security_logger.log_security_event(
        event_type='security_violation',
        user_id=g.user_id,
        details=e.get_audit_data(),
        ip_address=request.remote_addr
    )
    
    return jsonify({
        'error': 'Security violation detected',
        'message': str(e),
        'severity': e.severity
    }), 400

@app.errorhandler(429)
def handle_rate_limit_exceeded(e):
    """Handler for rate limit exceeded"""
    security_logger.log_security_event(
        event_type='rate_limit_exceeded',
        user_id=g.user_id,
        ip_address=request.remote_addr,
        endpoint=request.endpoint
    )
    
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please slow down.'
    }), 429

if __name__ == '__main__':
    # Create instance directory
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Run the application
    app.run(debug=True, host='127.0.0.1', port=5000)