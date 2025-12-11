"""
Force Password Update Route
Handles mandatory password updates for users with weak passwords
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user
from models import db
from utils.password_validator import validate_password_strength
from flask_wtf.csrf import generate_csrf

# This route should be added to auth_routes.py

@auth_bp.route('/force-password-update', methods=['GET', 'POST'])
@login_required
def force_password_update():
    """Force users with weak passwords to update before accessing the site"""
    
    # Check if user actually needs to update password
    if current_user.password_strength_checked:
        # Password is already strong, redirect to dashboard
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        errors = []
        
        # Verify current password
        if not current_user.check_password(current_password):
            errors.append('Current password is incorrect.')
        
        # Validate new password strength
        password_check = validate_password_strength(new_password)
        if not password_check['is_strong']:
            errors.append('New password does not meet security requirements.')
            for req in password_check['missing_requirements']:
                errors.append(f'  • {req}')
        
        # Check if passwords match
        if new_password != confirm_password:
            errors.append('New passwords do not match.')
        
        # Check if new password is different from current
        if current_password == new_password:
            errors.append('New password must be different from your current password.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/force_password_update.html', csrf_token=generate_csrf())
        
        # Update password
        try:
            current_user.set_password(new_password)
            current_user.mark_password_as_strong()
            current_user.last_password_change = datetime.utcnow()
            db.session.commit()
            
            # Clear session flag
            session.pop('force_password_update', None)
            session.pop('weak_password_reason', None)
            
            current_app.logger.info(f'Password updated successfully for user: {current_user.username}')
            flash('Password updated successfully! Your account is now secure.', 'success')
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Password update failed for user {current_user.username}: {e}')
            flash('Failed to update password. Please try again.', 'error')
            return render_template('auth/force_password_update.html', csrf_token=generate_csrf())
    
    # GET request - show the form
    return render_template('auth/force_password_update.html', csrf_token=generate_csrf())
