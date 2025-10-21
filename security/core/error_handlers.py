"""
Universal Security Framework - Error Handlers
Centralized error handling for security exceptions
"""
from flask import jsonify, render_template, request
from security.logging import security_logger

def handle_admin_security_error(error):
    """Handle admin security violations"""
    security_logger.error(f"Admin security error: {error}")
    return jsonify({
        'success': False,
        'error': 'Security violation',
        'message': 'Access denied for security reasons'
    }), 403

def handle_validation_error(error):
    """Handle validation errors"""
    return jsonify({
        'success': False,
        'error': 'Validation failed',
        'message': str(error)
    }), 400

def handle_file_upload_error(error):
    """Handle file upload errors"""
    return jsonify({
        'success': False,
        'error': 'File upload failed',
        'message': str(error)
    }), 400

def handle_rate_limit_error(error):
    """Handle rate limit errors"""
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.'
    }), 429