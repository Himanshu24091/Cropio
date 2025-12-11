"""
Authentication Routes - Enhanced Security Implementation
User registration, login, logout functionality with comprehensive security protection
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, g
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
import uuid

# ENHANCED SECURITY IMPORTS - New Security Framework
from security.core.decorators import (
    rate_limit, require_csrf, require_authentication, validate_file_upload
)
from security.core.validators import validate_user_input, validate_content, validate_ip_address
from security.core.sanitizers import sanitize_user_input, remove_script_tags
from security.core.exceptions import (
    SecurityViolationError, RateLimitExceededError, CSRFValidationError
)

from models import db, User, SystemSettings, UserSession
from forms import LoginForm, RegistrationForm
from utils.email_service import send_verification_email, verify_email_token, send_password_reset_email
from utils.permissions import get_user_permissions
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import secrets

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
@rate_limit(requests_per_minute=5, per_user=False)  # NEW: Rate limit registration attempts
def register():
    """User registration with enhanced security validation"""
    if request.method == 'POST':
        # NEW: CSRF validation for form submissions
        try:
            from flask_wtf.csrf import validate_csrf
            validate_csrf(request.form.get('csrf_token'))
        except Exception as csrf_error:
            current_app.logger.warning(
                f'CSRF validation failed for registration: IP={request.remote_addr}, error={csrf_error}'
            )
            flash('Security validation failed. Please try again.', 'error')
            from flask_wtf.csrf import generate_csrf
            return render_template('auth/register.html', csrf_token=generate_csrf())
        
        # NEW: Enhanced input validation and sanitization
        raw_username = request.form.get('username', '').strip()
        raw_email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # NEW: Validate and sanitize inputs
        username_valid, username_errors = validate_user_input(raw_username, 'username')
        email_valid, email_errors = validate_user_input(raw_email, 'email')
        
        if not username_valid:
            for error in username_errors:
                flash(f'Username validation: {error}', 'error')
            from flask_wtf.csrf import generate_csrf
            return render_template('auth/register.html', username=raw_username, email=raw_email, csrf_token=generate_csrf())
        
        if not email_valid:
            for error in email_errors:
                flash(f'Email validation: {error}', 'error')
            return render_template('auth/register.html', username=raw_username, email=raw_email)
        
        # NEW: Sanitize validated inputs
        username = sanitize_user_input(raw_username)
        email = sanitize_user_input(raw_email)
        
        # NEW: Log registration attempt for security monitoring
        current_app.logger.info(
            f'Registration attempt: username={username}, email={email}, '
            f'IP={request.remote_addr}, User-Agent={request.headers.get("User-Agent", "Unknown")}'
        )
        
        # Validation
        errors = []
        
        # Check if registration is enabled
        registration_enabled = SystemSettings.get_setting('registration_enabled', 'true').lower() == 'true'
        if not registration_enabled:
            errors.append('Registration is currently disabled.')
        
        # Basic validation
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            from flask_wtf.csrf import generate_csrf
            return render_template('auth/register.html', username=username, email=email, csrf_token=generate_csrf())
        
        try:
            # Create new user
            new_user = User(
                username=username,
                email=email,
                subscription_tier='free',
                email_verified=False,  # In production, implement email verification
                is_active=True
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            # Attempt to send verification email (non-blocking)
            try:
                send_verification_email(new_user)
                flash('Registration successful! Please check your email to verify your account.', 'success')
            except Exception as mail_err:
                print(f"Email send error (verification): {mail_err}")
                flash('Registration successful! Email verification could not be sent now.', 'warning')
            
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {e}")
    
    # Generate CSRF token for the template
    from flask_wtf.csrf import generate_csrf
    return render_template('auth/register.html', csrf_token=generate_csrf())


@auth_bp.route('/login', methods=['GET', 'POST'])
@rate_limit(requests_per_minute=10, per_user=False)  # NEW: Rate limit login attempts
def login():
    """User login with enhanced security monitoring"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # NEW: CSRF validation is already handled by WTF forms validation
        # NEW: Enhanced input validation and sanitization
        raw_username_or_email = form.username_or_email.data.strip()
        password = form.password.data
        remember_me = form.remember_me.data
        
        # NEW: Validate login input
        login_valid, login_errors = validate_user_input(raw_username_or_email, 'general')
        if not login_valid:
            for error in login_errors:
                flash(f'Login validation: {error}', 'error')
            return render_template('auth/login.html', form=form)
        
        # NEW: Sanitize input
        username_or_email = sanitize_user_input(raw_username_or_email)
        
        # NEW: Log login attempt for security monitoring
        current_app.logger.info(
            f'Login attempt: user={username_or_email}, '
            f'IP={request.remote_addr}, User-Agent={request.headers.get("User-Agent", "Unknown")}'
        )
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email.lower())
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                # NEW: Log deactivated account access attempt
                current_app.logger.warning(
                    f'Deactivated account login attempt: user={user.username}, '
                    f'IP={request.remote_addr}'
                )
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('auth/login.html', form=form)
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # NEW: Log successful login
            current_app.logger.info(
                f'Successful login: user={user.username}, '
                f'IP={request.remote_addr}, last_login={user.last_login}'
            )
            
            # Login user
            login_user(user, remember=remember_me)
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                # NEW: Validate redirect URL for security
                next_valid, next_errors = validate_user_input(next_page, 'url')
                if next_valid:
                    return redirect(next_page)
                else:
                    current_app.logger.warning(
                        f'Invalid redirect URL blocked: {next_page}, user={user.username}'
                    )
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('main.index'))
        else:
            # NEW: Log failed login attempt with more detail
            current_app.logger.warning(
                f'Failed login attempt: user={username_or_email}, '
                f'IP={request.remote_addr}, reason=invalid_credentials'
            )
            flash('Invalid username/email or password.', 'error')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/verify-email')
def verify_email():
    """Email verification endpoint"""
    token = request.args.get('token')
    if not token:
        flash('Invalid verification link.', 'error')
        return redirect(url_for('main.index'))
    try:
        email = verify_email_token(token, expiration=3600)
        if not email:
            flash('Verification link is invalid or expired.', 'error')
            return redirect(url_for('auth.login'))
        user = User.query.filter_by(email=email.lower()).first()
        if not user:
            flash('Account not found.', 'error')
            return redirect(url_for('auth.register'))
        user.email_verified = True
        db.session.commit()
        flash('Email verified successfully! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        db.session.rollback()
        flash('Failed to verify email. Please try again.', 'error')
        print(f"verify_email error: {e}")
        return redirect(url_for('auth.login'))

@auth_bp.route('/request-password-reset', methods=['GET', 'POST'])
@rate_limit(requests_per_minute=3, per_user=False)  # NEW: Rate limit password reset requests
def request_password_reset():
    """Request password reset link via email with enhanced security"""
    if request.method == 'POST':
        raw_email = request.form.get('email', '').strip().lower()
        
        # NEW: Validate and sanitize email input
        email_valid, email_errors = validate_user_input(raw_email, 'email')
        if not email_valid:
            for error in email_errors:
                flash(f'Email validation: {error}', 'error')
            return render_template('auth/request_password_reset.html')
        
        email = sanitize_user_input(raw_email)
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/request_password_reset.html')
        user = User.query.filter_by(email=email).first()
        if not user:
            # Do not reveal whether email exists
            flash('If an account exists for this email, a reset link has been sent.', 'info')
            return redirect(url_for('auth.login'))
        # Generate password reset token
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(user.email, salt='password-reset')
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        try:
            send_password_reset_email(user, reset_url)
            flash('If an account exists for this email, a reset link has been sent.', 'info')
            return redirect(url_for('auth.login'))
        except Exception as e:
            print(f"send_password_reset_email error: {e}")
            flash('Failed to send reset email. Please try again later.', 'error')
    return render_template('auth/request_password_reset.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password using token"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    email = None
    try:
        email = serializer.loads(token, salt='password-reset', max_age=3600)
    except (SignatureExpired, BadSignature):
        flash('This reset link is invalid or has expired.', 'error')
        return redirect(url_for('auth.request_password_reset'))

    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        flash('Account not found.', 'error')
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/reset_password.html', token=token)
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)
        try:
            user.set_password(password)
            db.session.commit()
            flash('Password has been reset. You can now login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to reset password. Please try again.', 'error')
            print(f"reset_password error: {e}")
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    logout_user()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@rate_limit(requests_per_minute=10, per_user=True)  # NEW: Rate limit profile edits
def edit_profile():
    """Edit user profile"""
    # Debug: Log current user info
    print(f"\n🔍 PROFILE EDIT DEBUG:")
    print(f"Current user ID: {current_user.id}")
    print(f"Current user username: '{current_user.username}'")
    print(f"Current user email: '{current_user.email}'")
    print(f"Request method: {request.method}")
    
    if request.method == 'POST':
        # NEW: Enhanced input validation and sanitization
        raw_username = request.form.get('username', '').strip()
        raw_email = request.form.get('email', '').strip().lower()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # NEW: Validate inputs before processing
        username_valid, username_errors = validate_user_input(raw_username, 'username')
        email_valid, email_errors = validate_user_input(raw_email, 'email')
        
        if not username_valid:
            for error in username_errors:
                flash(f'Username validation: {error}', 'error')
            return render_template('auth/edit_profile.html')
        
        if not email_valid:
            for error in email_errors:
                flash(f'Email validation: {error}', 'error')
            return render_template('auth/edit_profile.html')
        
        # NEW: Sanitize validated inputs
        username = sanitize_user_input(raw_username)
        email = sanitize_user_input(raw_email)
        
        # Debug: Log form data
        print(f"📝 FORM DATA:")
        print(f"  Form username: '{username}'")
        print(f"  Form email: '{email}'")
        print(f"  Has current password: {bool(current_password)}")
        print(f"  Has new password: {bool(new_password)}")
        print(f"  Form data keys: {list(request.form.keys())}")
        
        errors = []
        
        # Debug validation steps
        print(f"🔎 VALIDATION DEBUG:")
        print(f"  Username check: '{username}' vs current '{current_user.username}' -> changed: {username != current_user.username}")
        print(f"  Email check: '{email}' vs current '{current_user.email}' -> changed: {email != current_user.email}")
        print(f"  Password change requested: {bool(new_password)}")
        
        # Username validation
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
            print(f"  ❌ Username too short: '{username}'")
        elif len(username) > 20:
            errors.append('Username must be less than 20 characters long.')
            print(f"  ❌ Username too long: '{username}'")
        elif username != current_user.username:
            # Check if username is already taken
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                errors.append('Username already taken. Please choose a different one.')
                print(f"  ❌ Username taken: '{username}'")
            else:
                print(f"  ✅ Username available: '{username}'")
        else:
            print(f"  ℹ️ Username unchanged: '{username}'")
        
        # Email validation
        if not email or '@' not in email:
            errors.append('Please enter a valid email address.')
            print(f"  ❌ Invalid email: '{email}'")
        elif email != current_user.email:
            # Check if email is already taken
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                errors.append('Email already registered to another account.')
                print(f"  ❌ Email taken: '{email}'")
            else:
                print(f"  ✅ Email available: '{email}'")
        else:
            print(f"  ℹ️ Email unchanged: '{email}'")
        
        # Current password validation (required for any changes)
        changes_made = username != current_user.username or email != current_user.email or new_password
        print(f"  Changes detected: {changes_made}")
        
        if changes_made:
            if not current_password:
                errors.append('Please enter your current password to confirm changes.')
                print(f"  ❌ No current password provided")
            elif not current_user.check_password(current_password):
                errors.append('Current password is incorrect.')
                print(f"  ❌ Current password incorrect")
            else:
                print(f"  ✅ Current password verified")
        else:
            print(f"  ℹ️ No changes made, password not required")
        
        # Password change validation
        if new_password:
            if len(new_password) < 6:
                errors.append('New password must be at least 6 characters long.')
                print(f"  ❌ New password too short")
            elif new_password != confirm_password:
                errors.append('New passwords do not match.')
                print(f"  ❌ New passwords don't match")
            else:
                print(f"  ✅ New password valid")
        
        print(f"  Total validation errors: {len(errors)}")
        if errors:
            print(f"  Errors: {errors}")
            for error in errors:
                flash(error, 'error')
            return render_template('auth/edit_profile.html')
        
        print(f"\n🔄 STARTING UPDATE PROCESS...")
        try:
            # Fetch the user explicitly from database to ensure we have the latest version
            user_to_update = User.query.get(current_user.id)
            if not user_to_update:
                flash('User not found. Please try logging in again.', 'error')
                return redirect(url_for('auth.login'))
            
            print(f"Before update:")
            print(f"  Database user: {user_to_update.username} ({user_to_update.email})")
            print(f"  Current user: {current_user.username} ({current_user.email})")
            
            # Update user info
            user_to_update.username = username
            user_to_update.email = email
            if new_password:
                user_to_update.set_password(new_password)
                print(f"  🔑 Password updated")
            
            print(f"After assignment:")
            print(f"  user_to_update.username = '{user_to_update.username}'")
            print(f"  user_to_update.email = '{user_to_update.email}'")
            
            # Mark the session as dirty and commit
            db.session.add(user_to_update)
            db.session.commit()
            print(f"  ✅ Database commit successful!")
            
            # Verify the update worked
            db.session.refresh(user_to_update)
            verification_user = User.query.get(current_user.id)
            print(f"Post-commit verification:")
            print(f"  Refreshed user: {user_to_update.username} ({user_to_update.email})")
            print(f"  Database user: {verification_user.username} ({verification_user.email})")
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to update profile. Please try again.', 'error')
            print(f"❌ Profile update error: {e}")
            import traceback
            traceback.print_exc()
    
    return render_template('auth/edit_profile.html')


@auth_bp.route('/settings')
@login_required
def settings():
    """User settings page (different from profile edit)"""
    return render_template('auth/settings.html')


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
@rate_limit(requests_per_minute=5, per_user=True)  # NEW: Rate limit password changes
def change_password():
    """Change password page"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        errors = []
        
        # Validation
        if not current_password:
            errors.append('Please enter your current password.')
        elif not current_user.check_password(current_password):
            errors.append('Current password is incorrect.')
        
        if not new_password or len(new_password) < 6:
            errors.append('New password must be at least 6 characters long.')
        
        if new_password != confirm_password:
            errors.append('New passwords do not match.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/change_password.html')
        
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to change password. Please try again.', 'error')
            print(f"Password change error: {e}")
    
    return render_template('auth/change_password.html')


@auth_bp.route('/delete-account', methods=['GET', 'POST'])
@login_required
@rate_limit(requests_per_minute=2, per_user=True)  # NEW: Strict rate limit for account deletion
def delete_account():
    """Delete user account"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_delete = request.form.get('confirm_delete') == 'on'
        
        if not password:
            flash('Please enter your password to delete account.', 'error')
            return render_template('auth/delete_account.html')
        
        if not current_user.check_password(password):
            flash('Incorrect password.', 'error')
            return render_template('auth/delete_account.html')
        
        if not confirm_delete:
            flash('Please confirm account deletion.', 'error')
            return render_template('auth/delete_account.html')
        
        try:
            username = current_user.username
            user_id = current_user.id
            
            # NEW: Log account deletion for security monitoring
            current_app.logger.warning(
                f'Account deletion: user={username}, id={user_id}, '
                f'IP={request.remote_addr}, timestamp={datetime.utcnow()}'
            )
            
            # Delete user (cascades to related records)
            db.session.delete(current_user)
            db.session.commit()
            
            # Logout user
            logout_user()
            
            # NEW: Log successful deletion
            current_app.logger.info(f'Account successfully deleted: username={username}, id={user_id}')
            
            flash(f'Account "{username}" has been permanently deleted.', 'info')
            return redirect(url_for('main.index'))
            
        except Exception as e:
            db.session.rollback()
            flash('Failed to delete account. Please try again.', 'error')
            print(f"Account deletion error: {e}")
    
    return render_template('auth/delete_account.html')


@auth_bp.route('/sessions')
@login_required
def user_sessions():
    """User's active sessions management"""
    try:
        # Get user's active sessions
        active_sessions = UserSession.get_active_sessions(current_user.id)
        
        # Clean up expired sessions
        UserSession.cleanup_expired()
        
        return render_template('auth/sessions.html', 
                             active_sessions=active_sessions)
        
    except Exception as e:
        current_app.logger.error(f"User sessions page error: {e}")
        flash('Error loading sessions', 'error')
        return redirect(url_for('auth.profile'))


@auth_bp.route('/sessions/<int:session_id>/revoke', methods=['POST'])
@login_required
@rate_limit(requests_per_minute=10, per_user=True)  # NEW: Rate limit session operations
def revoke_session(session_id):
    """Revoke a specific session"""
    try:
        session_obj = UserSession.query.filter_by(
            id=session_id,
            user_id=current_user.id
        ).first_or_404()
        
        session_obj.invalidate()
        
        return jsonify({'success': True, 'message': 'Session revoked successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Session revocation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/sessions/revoke-all', methods=['POST'])
@login_required
@rate_limit(requests_per_minute=5, per_user=True)  # NEW: Rate limit bulk operations
def revoke_all_sessions():
    """Revoke all other sessions for current user"""
    try:
        # Get all active sessions for current user
        active_sessions = UserSession.get_active_sessions(current_user.id)
        
        # Get current session token to avoid invalidating current session
        current_session_token = session.get('session_id')
        
        revoked_count = 0
        for session_obj in active_sessions:
            if session_obj.session_token != current_session_token:
                session_obj.invalidate()
                revoked_count += 1
        
        return jsonify({
            'success': True, 
            'message': f'Revoked {revoked_count} other sessions'
        })
        
    except Exception as e:
        current_app.logger.error(f"Bulk session revocation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Utility functions for templates
@auth_bp.app_template_filter('subscription_status')
def subscription_status(user):
    """Template filter to get user subscription status"""
    if user.is_premium():
        days_left = (user.subscription_end - datetime.now().date()).days
        return f'Premium ({days_left} days left)'
    return 'Free'


@auth_bp.app_template_global('current_user_usage')
def current_user_usage():
    """Template global to get current user's daily usage"""
    if current_user.is_authenticated:
        usage = current_user.get_daily_usage()
        if usage:
            return {
                'conversions': usage.conversions_count,
                'limit': 5 if not current_user.is_premium() else 'Unlimited'
            }
    return {'conversions': 0, 'limit': 'Login Required'}


# NEW: Security error handlers for authentication blueprint
@auth_bp.errorhandler(RateLimitExceededError)
def handle_auth_rate_limit(e):
    """Handle rate limit exceeded for auth routes"""
    current_app.logger.warning(
        f'Rate limit exceeded on auth route: IP={request.remote_addr}, '
        f'path={request.path}, user={getattr(current_user, "username", "anonymous")}'
    )
    flash('Too many attempts. Please wait before trying again.', 'error')
    return redirect(url_for('main.index')), 429


@auth_bp.errorhandler(CSRFValidationError)
def handle_auth_csrf_error(e):
    """Handle CSRF validation errors for auth routes"""
    current_app.logger.warning(
        f'CSRF validation failed on auth route: IP={request.remote_addr}, '
        f'path={request.path}, user={getattr(current_user, "username", "anonymous")}'
    )
    flash('Security validation failed. Please try again.', 'error')
    return redirect(url_for('main.index')), 400


@auth_bp.errorhandler(SecurityViolationError)
def handle_auth_security_violation(e):
    """Handle general security violations for auth routes"""
    current_app.logger.error(
        f'Security violation on auth route: IP={request.remote_addr}, '
        f'path={request.path}, user={getattr(current_user, "username", "anonymous")}, '
        f'violation={str(e)}'
    )
    flash('Security violation detected. Action blocked.', 'error')
    return redirect(url_for('main.index')), 403


# NEW: After request hook for security logging
@auth_bp.after_request
def log_auth_security_events(response):
    """Log security-relevant events for authentication routes"""
    # Log suspicious response codes
    if response.status_code >= 400:
        current_app.logger.warning(
            f'Auth security event: {request.method} {request.path} - '
            f'Status: {response.status_code}, IP: {request.remote_addr}, '
            f'User: {getattr(current_user, "username", "anonymous")}'
        )
    
    # Log successful sensitive operations
    sensitive_paths = ['/login', '/register', '/delete-account', '/change-password']
    if request.path in sensitive_paths and response.status_code < 400:
        current_app.logger.info(
            f'Auth operation completed: {request.method} {request.path} - '
            f'Status: {response.status_code}, IP: {request.remote_addr}'
        )
    
    return response
