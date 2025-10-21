"""
Email Service - Phase 2
Email verification, notifications, and communication system
"""
from flask import current_app, render_template, url_for
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with app"""
    mail.init_app(app)

def generate_verification_token(email):
    """Generate email verification token"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-verification')

def verify_email_token(token, expiration=3600):
    """Verify email verification token"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-verification', max_age=expiration)
        return email
    except (SignatureExpired, BadSignature):
        return None

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
            current_app.logger.info(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {e}")

def send_email(to, subject, template, **kwargs):
    """Send email with template"""
    try:
        msg = Message(
            subject=f"[Cropio] {subject}",
            recipients=[to] if isinstance(to, str) else to,
            sender=current_app.config.get('MAIL_USERNAME', 'noreply@cropio.com')
        )
        
        # Render HTML template
        msg.html = render_template(f'email/{template}.html', **kwargs)
        
        # Send email asynchronously
        thread = threading.Thread(
            target=send_async_email,
            args=(current_app._get_current_object(), msg)
        )
        thread.start()
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error preparing email: {e}")
        return False

def send_verification_email(user):
    """Send email verification to new user"""
    token = generate_verification_token(user.email)
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    
    return send_email(
        to=user.email,
        subject="Verify Your Email Address",
        template="verify_email",
        user=user,
        verification_url=verification_url,
        site_name=current_app.config.get('SITE_NAME', 'Cropio')
    )

def send_welcome_email(user):
    """Send welcome email after successful verification"""
    return send_email(
        to=user.email,
        subject="Welcome to Cropio!",
        template="welcome",
        user=user,
        dashboard_url=url_for('dashboard.index', _external=True),
        tools_url=url_for('main.index', _external=True)
    )

def send_password_reset_email(user, reset_url):
    """Send password reset email"""
    return send_email(
        to=user.email,
        subject="Reset Your Password",
        template="password_reset",
        user=user,
        reset_url=reset_url
    )

def send_account_deletion_email(user):
    """Send account deletion confirmation email"""
    return send_email(
        to=user.email,
        subject="Account Deletion Confirmation",
        template="account_deleted",
        user=user,
        support_email=current_app.config.get('MAIL_USERNAME', 'support@cropio.com')
    )

def send_subscription_notification(user, subscription_type, action):
    """Send subscription-related notifications"""
    subject_map = {
        'upgrade': "Welcome to Cropio Premium!",
        'renewal': "Your Premium Subscription Renewed",
        'expiry_warning': "Your Premium Subscription Expires Soon",
        'expired': "Your Premium Subscription Has Expired",
        'cancelled': "Premium Subscription Cancelled"
    }
    
    subject = subject_map.get(action, "Subscription Update")
    
    return send_email(
        to=user.email,
        subject=subject,
        template="subscription_notification",
        user=user,
        subscription_type=subscription_type,
        action=action,
        dashboard_url=url_for('dashboard.subscription', _external=True)
    )

def send_usage_limit_notification(user, limit_type):
    """Send usage limit notifications"""
    subject_map = {
        'approaching': "Daily Conversion Limit Approaching",
        'reached': "Daily Conversion Limit Reached",
        'exceeded': "Daily Conversion Limit Exceeded"
    }
    
    subject = subject_map.get(limit_type, "Usage Notification")
    
    return send_email(
        to=user.email,
        subject=subject,
        template="usage_notification",
        user=user,
        limit_type=limit_type,
        upgrade_url=url_for('dashboard.subscription', _external=True)
    )

def send_admin_notification(subject, message, admin_emails=None):
    """Send notification to administrators"""
    if not admin_emails:
        admin_emails = [current_app.config.get('MAIL_USERNAME', 'admin@cropio.com')]
    
    return send_email(
        to=admin_emails,
        subject=f"[ADMIN] {subject}",
        template="admin_notification",
        message=message,
        timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    )

def send_contact_form_email(name, email, subject, message):
    """Send contact form submission email"""
    admin_email = current_app.config.get('MAIL_USERNAME', 'admin@cropio.com')
    
    # Send to admin
    admin_sent = send_email(
        to=admin_email,
        subject=f"Contact Form: {subject}",
        template="contact_form_admin",
        name=name,
        email=email,
        user_subject=subject,
        message=message
    )
    
    # Send confirmation to user
    user_sent = send_email(
        to=email,
        subject="We Received Your Message",
        template="contact_form_user",
        name=name,
        user_subject=subject,
        message=message
    )
    
    return admin_sent and user_sent

def test_email_config():
    """Test email configuration"""
    try:
        # Test SMTP connection
        if current_app.config.get('MAIL_USERNAME') and current_app.config.get('MAIL_PASSWORD'):
            # Try to send a test email to admin
            admin_email = current_app.config.get('MAIL_USERNAME')
            
            test_sent = send_email(
                to=admin_email,
                subject="Email Configuration Test",
                template="test_email",
                test_time=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            )
            
            return test_sent
        else:
            current_app.logger.warning("Email credentials not configured")
            return False
            
    except Exception as e:
        current_app.logger.error(f"Email configuration test failed: {e}")
        return False

# Email template fallbacks for when templates don't exist
EMAIL_TEMPLATES = {
    'verify_email': """
    <h2>Welcome to Cropio!</h2>
    <p>Hello {{ user.username }},</p>
    <p>Please verify your email address by clicking the link below:</p>
    <p><a href="{{ verification_url }}" style="background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
    <p>This link will expire in 1 hour.</p>
    <p>Best regards,<br>The Cropio Team</p>
    """,
    
    'welcome': """
    <h2>Welcome to Cropio!</h2>
    <p>Hello {{ user.username }},</p>
    <p>Your email has been verified successfully! You can now enjoy all features of Cropio.</p>
    <p><a href="{{ dashboard_url }}" style="background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a></p>
    <p>Start converting your files with our powerful tools!</p>
    <p>Best regards,<br>The Cropio Team</p>
    """,
    
    'password_reset': """
    <h2>Password Reset Request</h2>
    <p>Hello {{ user.username }},</p>
    <p>You requested a password reset. Click the link below to reset your password:</p>
    <p><a href="{{ reset_url }}" style="background: #dc2626; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
    <p>This link will expire in 1 hour. If you didn't request this, please ignore this email.</p>
    <p>Best regards,<br>The Cropio Team</p>
    """
}

def render_email_template(template_name, **kwargs):
    """Render email template with fallback"""
    try:
        return render_template(f'email/{template_name}.html', **kwargs)
    except:
        # Use fallback template
        template = EMAIL_TEMPLATES.get(template_name, "")
        if template:
            from jinja2 import Template
            return Template(template).render(**kwargs)
        return f"<p>Email content for {template_name}</p>"

# Helper functions for email formatting
def format_file_size_email(size_bytes):
    """Format file size for email display"""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"

def generate_usage_report_email(user, usage_data):
    """Generate usage report for email"""
    total_conversions = sum(u.conversions_count for u in usage_data)
    total_storage = sum(u.storage_used for u in usage_data)
    
    return {
        'total_conversions': total_conversions,
        'total_storage': format_file_size_email(total_storage),
        'period': f"{len(usage_data)} days",
        'avg_daily': round(total_conversions / max(len(usage_data), 1), 1)
    }
