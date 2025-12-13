"""
Analytics Routes Blueprint
Dashboard and API endpoints for usage analytics
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import db, UsageAnalytics
from utils.analytics_tracker import (
    get_user_analytics,
    get_user_stats_summary,
    get_daily_usage_trend
)
from datetime import datetime, timedelta

# Create analytics blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/')
@login_required
def dashboard():
    """Main analytics dashboard page"""
    from flask_wtf.csrf import generate_csrf
    return render_template('analytics/usage_analytics.html', csrf_token=generate_csrf())


@analytics_bp.route('/api/stats')
@login_required
def get_stats():
    """
    API endpoint to get usage statistics
    Query params:
        - period: day, week, month, year (default: day)
        - days: number of days to look back (optional)
    """
    period = request.args.get('period', 'day')
    days_param = request.args.get('days', None)
    
    # Determine days based on period if not specified
    if days_param:
        days = int(days_param)
    else:
        days_map = {
            'day': 7,
            'week': 28,
            'month': 90,
            'year': 365
        }
        days = days_map.get(period, 30)
    
    # Get summary statistics
    stats = get_user_stats_summary(current_user.id, days=days)
    
    return jsonify({
        'success': True,
        'data': stats
    })


@analytics_bp.route('/api/data')
@login_required
def get_data():
    """
    API endpoint to get detailed usage data for charts
    Query params:
        - period: day, week, month, year (default: day)
    """
    period = request.args.get('period', 'day')
    
    # Get usage data organized by period
    usage_data = get_user_analytics(current_user.id, period=period)
    
    # Get daily trend
    if period == 'day':
        trend_days = 7
    elif period == 'week':
        trend_days = 28
    elif period == 'month':
        trend_days = 90
    else:  # year
        trend_days = 365
    
    daily_trend = get_daily_usage_trend(current_user.id, days=trend_days)
    
    return jsonify({
        'success': True,
        'data': {
            'usage_by_period': usage_data,
            'daily_trend': daily_trend,
            'period': period
        }
    })


@analytics_bp.route('/api/features')
@login_required
def get_features():
    """Get list of all features used by the user"""
    from sqlalchemy import func, distinct
    
    features = db.session.query(
        distinct(UsageAnalytics.feature_name),
        UsageAnalytics.feature_category,
        func.count(UsageAnalytics.id).label('total_uses'),
        func.max(UsageAnalytics.timestamp).label('last_used')
    ).filter(
        UsageAnalytics.user_id == current_user.id
    ).group_by(
        UsageAnalytics.feature_name,
        UsageAnalytics.feature_category
    ).order_by(
        func.count(UsageAnalytics.id).desc()
    ).all()
    
    features_list = [{
        'name': f[0],
        'category': f[1],
        'total_uses': f[2],
        'last_used': f[3].isoformat() if f[3] else None
    } for f in features]
    
    return jsonify({
        'success': True,
        'data': features_list
    })


@analytics_bp.route('/api/recent')
@login_required
def get_recent():
    """Get recent usage history"""
    limit = request.args.get('limit', 20, type=int)
    
    recent_usage = UsageAnalytics.query.filter_by(
        user_id=current_user.id
    ).order_by(
        UsageAnalytics.timestamp.desc()
    ).limit(limit).all()
    
    usage_list = [{
        'feature_name': u.feature_name,
        'feature_category': u.feature_category,
        'timestamp': u.timestamp.isoformat(),
        'success': u.success,
        'processing_time': u.processing_time
    } for u in recent_usage]
    
    return jsonify({
        'success': True,
        'data': usage_list
    })
