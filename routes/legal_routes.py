"""
Legal Routes - Terms of Service and Privacy Policy
Provides routes for legal documents
"""
from flask import Blueprint, render_template

# Create legal blueprint
legal_bp = Blueprint('legal', __name__, url_prefix='/legal')

@legal_bp.route('/terms-of-service')
def terms_of_service():
    """Terms of Service page"""
    return render_template('legal/terms_of_service.html')

@legal_bp.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy page"""
    return render_template('legal/privacy_policy.html')
