"""
Analytics Tracker Utility
Track feature usage for logged-in users
"""
from models import db, UsageAnalytics
from flask_login import current_user
from datetime import datetime, timedelta
import json


def track_feature(feature_name, feature_category=None, extra_metadata=None, processing_time=None, success=True):
    """
    Track a feature usage for the current logged-in user
    
    Args:
        feature_name (str): Name of the feature being used
        feature_category (str): Category of the feature (e.g., 'conversion', 'pdf_tool')
        extra_metadata (dict): Additional metadata as dictionary
        processing_time (float): Time taken to process in seconds
        success (bool): Whether the operation was successful
    
    Returns:
        UsageAnalytics: The created usage record
    """
    if not current_user.is_authenticated:
        return None
    
    # Convert metadata dict to JSON string if provided
    metadata_str = json.dumps(extra_metadata) if extra_metadata else None
    
    return UsageAnalytics.track_usage(
        user_id=current_user.id,
        feature_name=feature_name,
        feature_category=feature_category,
        extra_metadata=metadata_str,
        processing_time=processing_time,
        success=success
    )


def get_user_analytics(user_id, period='day', days=None):
    """
    Get analytics data for a user
    
    Args:
        user_id (int): User ID
        period (str): Time period ('day', 'week', 'month', 'year')
        days (int): Number of days to look back (optional)
    
    Returns:
        dict: Analytics data organized by period and feature
    """
    usage_data = UsageAnalytics.get_usage_by_period(user_id, period)
    
    # Organize data for charts
    result = {}
    for row in usage_data:
        period_key = str(row.period)
        if period_key not in result:
            result[period_key] = {}
        result[period_key][row.feature_name] = row.count
    
    return result


def get_user_stats_summary(user_id, days=30):
    """
    Get summary statistics for a user
    
    Args:
        user_id (int): User ID
        days (int): Number of days to look back
    
    Returns:
        dict: Summary statistics including total usage, top features, etc.
    """
    from sqlalchemy import func
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Total usage count
    total_usage = db.session.query(func.count(UsageAnalytics.id)).filter(
        UsageAnalytics.user_id == user_id,
        UsageAnalytics.timestamp >= cutoff_date
    ).scalar()
    
    # Usage by category
    category_stats = db.session.query(
        UsageAnalytics.feature_category,
        func.count(UsageAnalytics.id).label('count')
    ).filter(
        UsageAnalytics.user_id == user_id,
        UsageAnalytics.timestamp >= cutoff_date,
        UsageAnalytics.feature_category.isnot(None)
    ).group_by(UsageAnalytics.feature_category).all()
    
    # Top features
    top_features = db.session.query(
        UsageAnalytics.feature_name,
        func.count(UsageAnalytics.id).label('count')
    ).filter(
        UsageAnalytics.user_id == user_id,
        UsageAnalytics.timestamp >= cutoff_date
    ).group_by(UsageAnalytics.feature_name).order_by(
        func.count(UsageAnalytics.id).desc()
    ).limit(10).all()
    
    # Success rate
    success_count = db.session.query(func.count(UsageAnalytics.id)).filter(
        UsageAnalytics.user_id == user_id,
        UsageAnalytics.timestamp >= cutoff_date,
        UsageAnalytics.success == True
    ).scalar()
    
    success_rate = (success_count / total_usage * 100) if total_usage > 0 else 0
    
    return {
        'total_usage': total_usage or 0,
        'categories': {cat.feature_category: cat.count for cat in category_stats},
        'top_features': [{'name': f.feature_name, 'count': f.count} for f in top_features],
        'success_rate': round(success_rate, 2),
        'period_days': days
    }


def get_daily_usage_trend(user_id, days=7):
    """
    Get daily usage trend for the last N days
    
    Args:
        user_id (int): User ID
        days (int): Number of days to look back
    
    Returns:
        list: Daily usage counts
    """
    from sqlalchemy import func
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    daily_usage = db.session.query(
        func.date(UsageAnalytics.timestamp).label('date'),
        func.count(UsageAnalytics.id).label('count')
    ).filter(
        UsageAnalytics.user_id == user_id,
        UsageAnalytics.timestamp >= cutoff_date
    ).group_by('date').order_by('date').all()
    
    return [{'date': str(row.date), 'count': row.count} for row in daily_usage]
