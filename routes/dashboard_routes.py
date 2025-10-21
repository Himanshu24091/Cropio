"""
User Dashboard Routes - Phase 2 Complete Implementation
Comprehensive dashboard with analytics, history, and subscription management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import and_, desc, func
import json

from models import db, ConversionHistory, UsageTracking, SystemSettings

# Create dashboard blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page with comprehensive analytics"""
    try:
        # Get today's usage
        today_usage = current_user.get_daily_usage()
        if not today_usage:
            today_usage = UsageTracking.get_or_create_today(current_user.id)
        
        # Get last 30 days usage for chart
        thirty_days_ago = date.today() - timedelta(days=30)
        usage_history = UsageTracking.query.filter(
            and_(
                UsageTracking.user_id == current_user.id,
                UsageTracking.date >= thirty_days_ago
            )
        ).order_by(UsageTracking.date.desc()).limit(30).all()
        
        # Get recent conversions (last 10)
        recent_conversions = ConversionHistory.query.filter_by(
            user_id=current_user.id
        ).order_by(desc(ConversionHistory.created_at)).limit(10).all()
        
        # Calculate statistics (favor UsageTracking for accuracy even when output is streamed)
        total_conversions = db.session.query(
            func.coalesce(func.sum(UsageTracking.conversions_count), 0)
        ).filter(UsageTracking.user_id == current_user.id).scalar() or 0
        
        # Total storage used (sum of all processed storage from UsageTracking)
        total_storage_used = db.session.query(
            func.coalesce(func.sum(UsageTracking.storage_used), 0)
        ).filter(UsageTracking.user_id == current_user.id).scalar() or 0
        
        # Most used tool - prefer ConversionHistory if present; otherwise derive from UsageTracking counters
        most_used_tool = db.session.query(
            ConversionHistory.tool_used,
            func.count(ConversionHistory.tool_used).label('usage_count')
        ).filter_by(user_id=current_user.id).group_by(
            ConversionHistory.tool_used
        ).order_by(desc('usage_count')).first()
        
        if not most_used_tool:
            # Fallback from usage counters
            counters = db.session.query(
                func.coalesce(func.sum(UsageTracking.image_conversions), 0),
                func.coalesce(func.sum(UsageTracking.pdf_conversions), 0),
                func.coalesce(func.sum(UsageTracking.document_conversions), 0)
            ).filter(UsageTracking.user_id == current_user.id).first()
            names = ['image_converter', 'pdf_converter', 'document_converter']
            most_idx = max(range(3), key=lambda i: counters[i] if counters else 0)
            most_used_tool = (names[most_idx], counters[most_idx] if counters else 0)
        
        # Get system limits
        daily_limit = int(SystemSettings.get_setting('free_daily_limit', '5'))
        max_file_size = int(SystemSettings.get_setting(
            'max_file_size_premium' if current_user.is_premium() else 'max_file_size_free',
            '5368709120' if current_user.is_premium() else '52428800'
        ))
        
        # Prepare chart data for last 7 days
        chart_data = []
        labels = []
        for i in range(6, -1, -1):  # Last 7 days
            day = date.today() - timedelta(days=i)
            usage = next((u for u in usage_history if u.date == day), None)
            chart_data.append(usage.conversions_count if usage else 0)
            labels.append(day.strftime('%a'))
        
        # Tool usage breakdown - use ConversionHistory if available else derive from UsageTracking counters
        tool_usage_q = db.session.query(
            ConversionHistory.conversion_type,
            func.count(ConversionHistory.conversion_type).label('count')
        ).filter_by(user_id=current_user.id).group_by(
            ConversionHistory.conversion_type
        ).all()
        if tool_usage_q:
            tool_usage = dict(tool_usage_q)
        else:
            # Build from UsageTracking counters
            aggregates = db.session.query(
                func.coalesce(func.sum(UsageTracking.image_conversions), 0).label('image'),
                func.coalesce(func.sum(UsageTracking.pdf_conversions), 0).label('pdf'),
                func.coalesce(func.sum(UsageTracking.document_conversions), 0).label('document')
            ).filter(UsageTracking.user_id == current_user.id).first()
            tool_usage = {
                'image_converter': int(aggregates.image or 0),
                'pdf_converter': int(aggregates.pdf or 0),
                'document_converter': int(aggregates.document or 0)
            }
        
        dashboard_data = {
            'today_usage': today_usage,
            'recent_conversions': recent_conversions,
            'total_conversions': total_conversions,
            'total_storage_used': total_storage_used,
            'most_used_tool': most_used_tool[0] if most_used_tool else 'N/A',
            'daily_limit': daily_limit if not current_user.is_premium() else 'Unlimited',
            'max_file_size_mb': round(max_file_size / (1024 * 1024)),
            'chart_data': chart_data,
            'chart_labels': labels,
            'tool_usage': dict(tool_usage),
            'usage_percentage': (today_usage.conversions_count / daily_limit * 100) if not current_user.is_premium() and daily_limit > 0 else 0
        }
        
        return render_template('user_dashboard/dashboard.html', data=dashboard_data)
        
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard. Please try again.', 'error')
        return redirect(url_for('main.index'))


@dashboard_bp.route('/history')
@login_required
def conversion_history():
    """Detailed conversion history with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filter options
    tool_filter = request.args.get('tool')
    date_filter = request.args.get('date')
    status_filter = request.args.get('status')
    
    query = ConversionHistory.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if tool_filter:
        query = query.filter(ConversionHistory.tool_used == tool_filter)
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(func.date(ConversionHistory.created_at) == filter_date)
        except ValueError:
            flash('Invalid date format', 'warning')
    
    if status_filter:
        query = query.filter(ConversionHistory.status == status_filter)
    
    # Paginate results
    conversions = query.order_by(desc(ConversionHistory.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get unique tools for filter dropdown
    available_tools = db.session.query(ConversionHistory.tool_used).filter_by(
        user_id=current_user.id
    ).distinct().all()
    
    return render_template('user_dashboard/history.html', 
                         conversions=conversions,
                         available_tools=[t[0] for t in available_tools],
                         current_filters={
                             'tool': tool_filter,
                             'date': date_filter,
                             'status': status_filter
                         })


@dashboard_bp.route('/usage')
@login_required
def usage_analytics():
    """Detailed usage analytics and trends"""
    # Get usage data for last 90 days
    ninety_days_ago = date.today() - timedelta(days=90)
    usage_data = UsageTracking.query.filter(
        and_(
            UsageTracking.user_id == current_user.id,
            UsageTracking.date >= ninety_days_ago
        )
    ).order_by(UsageTracking.date).all()
    
    # Monthly breakdown
    monthly_stats = {}
    for usage in usage_data:
        month_key = usage.date.strftime('%Y-%m')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                'conversions': 0,
                'storage': 0,
                'processing_time': 0,
                'image_conversions': 0,
                'pdf_conversions': 0,
                'document_conversions': 0
            }
        
        monthly_stats[month_key]['conversions'] += usage.conversions_count
        monthly_stats[month_key]['storage'] += usage.storage_used
        monthly_stats[month_key]['processing_time'] += usage.processing_time
        monthly_stats[month_key]['image_conversions'] += usage.image_conversions
        monthly_stats[month_key]['pdf_conversions'] += usage.pdf_conversions
        monthly_stats[month_key]['document_conversions'] += usage.document_conversions
    
    # Weekly usage pattern (last 4 weeks)
    weekly_pattern = {i: 0 for i in range(7)}  # 0 = Monday, 6 = Sunday
    four_weeks_ago = date.today() - timedelta(weeks=4)
    
    for usage in usage_data:
        if usage.date >= four_weeks_ago:
            day_of_week = usage.date.weekday()
            weekly_pattern[day_of_week] += usage.conversions_count
    
    return render_template('user_dashboard/usage.html',
                         usage_data=usage_data,
                         monthly_stats=monthly_stats,
                         weekly_pattern=weekly_pattern)


@dashboard_bp.route('/subscription')
@login_required
def subscription():
    """Subscription management and billing"""
    # Get subscription details
    subscription_info = {
        'tier': current_user.subscription_tier,
        'start_date': current_user.subscription_start,
        'end_date': current_user.subscription_end,
        'is_premium': current_user.is_premium(),
        'days_remaining': None
    }
    
    if current_user.subscription_end:
        days_remaining = (current_user.subscription_end - date.today()).days
        subscription_info['days_remaining'] = days_remaining
    
    # Get pricing information
    premium_price = SystemSettings.get_setting('premium_price_monthly', '999')
    
    # Usage limits comparison
    limits_comparison = {
        'free': {
            'daily_conversions': SystemSettings.get_setting('free_daily_limit', '5'),
            'max_file_size': f"{int(SystemSettings.get_setting('max_file_size_free', '52428800')) // (1024*1024)}MB",
            'ai_features': 'No',
            'priority_support': 'No'
        },
        'premium': {
            'daily_conversions': 'Unlimited',
            'max_file_size': f"{int(SystemSettings.get_setting('max_file_size_premium', '5368709120')) // (1024*1024*1024)}GB",
            'ai_features': 'Yes',
            'priority_support': 'Yes'
        }
    }
    
    return render_template('user_dashboard/subscription.html',
                         subscription=subscription_info,
                         premium_price=premium_price,
                         limits=limits_comparison)


@dashboard_bp.route('/settings')
@login_required
def settings():
    """User account settings"""
    return render_template('user_dashboard/settings.html')


@dashboard_bp.route('/api/chart-data')
@login_required
def api_chart_data():
    """API endpoint for dashboard chart data"""
    days = request.args.get('days', 7, type=int)
    chart_type = request.args.get('type', 'conversions')
    
    start_date = date.today() - timedelta(days=days-1)
    
    usage_data = UsageTracking.query.filter(
        and_(
            UsageTracking.user_id == current_user.id,
            UsageTracking.date >= start_date
        )
    ).order_by(UsageTracking.date).all()
    
    # Prepare data for chart
    chart_data = []
    labels = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        usage = next((u for u in usage_data if u.date == current_date), None)
        
        if chart_type == 'conversions':
            chart_data.append(usage.conversions_count if usage else 0)
        elif chart_type == 'storage':
            chart_data.append(usage.storage_used if usage else 0)
        elif chart_type == 'processing_time':
            chart_data.append(usage.processing_time if usage else 0)
        
        labels.append(current_date.strftime('%m/%d'))
    
    return jsonify({
        'labels': labels,
        'data': chart_data,
        'type': chart_type
    })


@dashboard_bp.route('/api/usage-summary')
@login_required
def api_usage_summary():
    """API endpoint for current usage summary"""
    today_usage = current_user.get_daily_usage()
    if not today_usage:
        today_usage = UsageTracking.get_or_create_today(current_user.id)
    
    daily_limit = int(SystemSettings.get_setting('free_daily_limit', '5'))
    
    return jsonify({
        'conversions_used': today_usage.conversions_count,
        'daily_limit': daily_limit if not current_user.is_premium() else 'unlimited',
        'storage_used': today_usage.storage_used,
        'processing_time': today_usage.processing_time,
        'subscription_tier': current_user.subscription_tier,
        'is_premium': current_user.is_premium()
    })

@dashboard_bp.route('/api/debug-totals')
@login_required
def api_debug_totals():
    """Return raw aggregates used by the dashboard for debugging"""
    from sqlalchemy import func

    total_from_usage = db.session.query(
        func.coalesce(func.sum(UsageTracking.conversions_count), 0)
    ).filter(UsageTracking.user_id == current_user.id).scalar() or 0

    storage_from_usage = db.session.query(
        func.coalesce(func.sum(UsageTracking.storage_used), 0)
    ).filter(UsageTracking.user_id == current_user.id).scalar() or 0

    total_from_history = ConversionHistory.query.filter_by(user_id=current_user.id).count()

    return jsonify({
        'user_id': current_user.id,
        'today_usage': {
            'date': current_user.get_daily_usage().date.isoformat() if current_user.get_daily_usage() else None,
            'conversions_count': current_user.get_daily_usage().conversions_count if current_user.get_daily_usage() else 0,
            'storage_used': current_user.get_daily_usage().storage_used if current_user.get_daily_usage() else 0,
        },
        'total_conversions_from_usage': int(total_from_usage),
        'total_conversions_from_history': int(total_from_history),
        'total_storage_from_usage_bytes': int(storage_from_usage)
    })


# Context processor for dashboard navigation
@dashboard_bp.app_context_processor
def inject_dashboard_vars():
    """Inject dashboard variables into all templates"""
    if current_user.is_authenticated:
        today_usage = current_user.get_daily_usage()
        if not today_usage:
            today_usage = UsageTracking.get_or_create_today(current_user.id)
        
        return {
            'dashboard_usage': today_usage,
            'user_subscription': current_user.subscription_tier
        }
    return {}
