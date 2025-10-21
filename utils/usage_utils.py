# utils/usage_utils.py
"""
Usage tracking utilities for Cropio converter
"""

from flask_login import current_user
from models import db, UsageTracking, ConversionHistory
from datetime import datetime, date


def check_usage_limit(user_id=None, conversion_type='general', limit=5):
    """
    Check if user has reached their daily usage limit
    
    Args:
        user_id: User ID (if None, uses current_user.id)
        conversion_type: Type of conversion
        limit: Daily limit (default 5 for free users)
    
    Returns:
        bool: True if user can perform conversion, False if limit reached
    """
    try:
        if user_id is None:
            if current_user.is_authenticated:
                user_id = current_user.id
                # Premium users have unlimited conversions
                if current_user.is_premium():
                    return True
            else:
                return False
        
        # Get or create today's usage record
        today_usage = UsageTracking.get_or_create_today(user_id)
        
        return today_usage.conversions_count < limit
        
    except Exception as e:
        print(f"Error checking usage limit: {e}")
        return False


def increment_usage(user_id=None, conversion_type='general', credit_cost=1.0, file_size=0):
    """
    Increment usage counter for a user
    
    Args:
        user_id: User ID (if None, uses current_user.id)
        conversion_type: Type of conversion
        credit_cost: Credits to deduct
        file_size: Size of processed file in bytes
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if user_id is None:
            if current_user.is_authenticated:
                user_id = current_user.id
            else:
                return False
        
        # Get or create today's usage record
        today_usage = UsageTracking.get_or_create_today(user_id)
        
        # Increment usage
        today_usage.increment_usage(conversion_type, credit_cost, file_size)
        
        # Commit changes
        db.session.commit()
        
        return True
        
    except Exception as e:
        print(f"Error incrementing usage: {e}")
        db.session.rollback()
        return False


def get_user_usage(user_id=None, date_obj=None):
    """
    Get usage statistics for a user on a specific date
    
    Args:
        user_id: User ID (if None, uses current_user.id)
        date_obj: Date to check (if None, uses today)
    
    Returns:
        UsageTracking object or None
    """
    try:
        if user_id is None:
            if current_user.is_authenticated:
                user_id = current_user.id
            else:
                return None
        
        if date_obj is None:
            date_obj = date.today()
        
        return UsageTracking.query.filter_by(
            user_id=user_id,
            usage_date=date_obj
        ).first()
        
    except Exception as e:
        print(f"Error getting user usage: {e}")
        return None


def can_user_convert(user_id=None, conversion_type='general'):
    """
    Check if user can perform a conversion (combining multiple checks)
    
    Args:
        user_id: User ID (if None, uses current_user.id)
        conversion_type: Type of conversion
    
    Returns:
        tuple: (can_convert: bool, reason: str)
    """
    try:
        if user_id is None:
            if current_user.is_authenticated:
                user_id = current_user.id
            else:
                return False, "User not authenticated"
        
        # Check if user exists and is active
        from models import User
        user = User.query.get(user_id)
        if not user:
            return False, "User not found"
        
        # Premium users can always convert
        if user.is_premium():
            return True, "Premium user - unlimited conversions"
        
        # Check daily limits for free users
        if not check_usage_limit(user_id, conversion_type):
            return False, "Daily conversion limit reached. Please upgrade to premium for unlimited conversions."
        
        return True, "Conversion allowed"
        
    except Exception as e:
        print(f"Error checking user conversion ability: {e}")
        return False, "Error checking conversion limits"


def log_conversion_history(user_id, original_filename, original_format, target_format, 
                          file_size=0, conversion_type='general', tool_used='unknown',
                          status='completed', error_message=None):
    """
    Log conversion to history
    
    Args:
        user_id: User ID
        original_filename: Name of original file
        original_format: Original file format
        target_format: Target file format
        file_size: Size of file in bytes
        conversion_type: Type of conversion
        tool_used: Name of tool used
        status: 'completed', 'failed', etc.
        error_message: Error message if failed
    
    Returns:
        bool: True if logged successfully
    """
    try:
        conversion = ConversionHistory(
            user_id=user_id,
            original_filename=original_filename,
            original_format=original_format,
            target_format=target_format,
            file_size=file_size,
            conversion_type=conversion_type,
            tool_used=tool_used,
            status=status,
            error_message=error_message,
            completed_at=datetime.utcnow()
        )
        
        db.session.add(conversion)
        db.session.commit()
        
        return True
        
    except Exception as e:
        print(f"Error logging conversion history: {e}")
        db.session.rollback()
        return False


def get_conversion_history(user_id=None, limit=50):
    """
    Get conversion history for a user
    
    Args:
        user_id: User ID (if None, uses current_user.id)
        limit: Maximum number of records to return
    
    Returns:
        List of ConversionHistory objects
    """
    try:
        if user_id is None:
            if current_user.is_authenticated:
                user_id = current_user.id
            else:
                return []
        
        return ConversionHistory.query.filter_by(
            user_id=user_id
        ).order_by(
            ConversionHistory.completed_at.desc()
        ).limit(limit).all()
        
    except Exception as e:
        print(f"Error getting conversion history: {e}")
        return []


def reset_daily_usage(user_id=None):
    """
    Reset daily usage for a user (admin function)
    
    Args:
        user_id: User ID to reset
    
    Returns:
        bool: True if successful
    """
    try:
        if user_id is None:
            return False
        
        today_usage = UsageTracking.get_or_create_today(user_id)
        today_usage.conversions_count = 0
        today_usage.credits_used = 0
        today_usage.total_file_size = 0
        
        db.session.commit()
        return True
        
    except Exception as e:
        print(f"Error resetting daily usage: {e}")
        db.session.rollback()
        return False
