"""
Database Models for Cropio SaaS Platform
Phase 1: Database Foundation Setup
"""
from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import uuid

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Enhanced User model with comprehensive profile and security features"""
    __tablename__ = 'users'
    
    # Primary identification
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True, nullable=False, 
                         default=lambda: str(uuid.uuid4()), index=True)
    
    # Authentication credentials
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Personal information
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    display_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    
    # Profile information
    bio = db.Column(db.Text, nullable=True)
    profile_picture_url = db.Column(db.String(255), nullable=True)
    timezone = db.Column(db.String(50), default='UTC')
    language = db.Column(db.String(10), default='en')
    
    # Address information
    address_line1 = db.Column(db.String(100), nullable=True)
    address_line2 = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state_province = db.Column(db.String(50), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    
    # Subscription information
    subscription_tier = db.Column(db.String(20), default='free', nullable=False, index=True)
    subscription_start = db.Column(db.Date, default=date.today)
    subscription_end = db.Column(db.Date, nullable=True)
    subscription_renewal_date = db.Column(db.Date, nullable=True)
    
    # Account status and security
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    phone_verified = db.Column(db.Boolean, default=False, nullable=False)
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)
    two_factor_secret = db.Column(db.String(32), nullable=True)
    
    # Role-based access control
    role_id = db.Column(db.Integer, db.ForeignKey('user_roles.id'), nullable=True)
    
    # Account management (keeping for backward compatibility)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_staff = db.Column(db.Boolean, default=False, nullable=False)
    account_locked = db.Column(db.Boolean, default=False, nullable=False)
    lock_reason = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    last_seen = db.Column(db.DateTime, nullable=True)
    
    # Security tracking
    login_attempts = db.Column(db.Integer, default=0)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # TEMPORARILY COMMENTED: Password strength tracking (columns don't exist in DB yet)
    # TODO: Uncomment after running database migration (migrations/add_password_alert_fields.py)
    # password_alert_dismissed_at = db.Column(db.DateTime, nullable=True)
    # password_strength_checked = db.Column(db.Boolean, default=False, nullable=False)
    # last_password_change = db.Column(db.DateTime, nullable=True)
    
    # Preferences
    email_notifications = db.Column(db.Boolean, default=True)
    marketing_emails = db.Column(db.Boolean, default=False)
    sms_notifications = db.Column(db.Boolean, default=False)
    session_timeout_enabled = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    conversions = db.relationship('ConversionHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    usage_records = db.relationship('UsageTracking', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password using bcrypt for maximum security"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        """Check if password matches using bcrypt"""
        try:
            # Handle both bcrypt hashes and legacy werkzeug hashes
            if self.password_hash.startswith('$2b$'):
                # bcrypt hash
                return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
            else:
                # Legacy werkzeug hash - check and then upgrade
                if check_password_hash(self.password_hash, password):
                    # Upgrade to bcrypt hash
                    self.set_password(password)
                    # Note: In production, you'd want to save this to database here
                    return True
                return False
        except Exception:
            return False
    
    def is_premium(self):
        """Check if user has active premium subscription"""
        if self.subscription_tier == 'premium' and self.subscription_end:
            return self.subscription_end >= date.today()
        return False
    
    def get_daily_usage(self, conversion_date=None):
        """Get usage count for specific date"""
        if not conversion_date:
            conversion_date = date.today()
        
        return UsageTracking.query.filter_by(
            user_id=self.id,
            date=conversion_date
        ).first()
    
    def can_convert(self):
        """Check if user can perform conversion based on limits"""
        if self.is_premium():
            return True
        
        # Check role-based limits
        if self.user_role:
            if self.user_role.daily_conversion_limit == -1:  # Unlimited
                return True
            today_usage = self.get_daily_usage()
            if today_usage and today_usage.conversions_count >= self.user_role.daily_conversion_limit:
                return False
        else:
            # Fallback to subscription-based limits
            today_usage = self.get_daily_usage()
            if today_usage and today_usage.conversions_count >= 5:
                return False
        
        return True
    
    # Role-based permission methods
    def has_permission(self, permission):
        """Check if user has specific permission"""
        if not self.user_role:
            return False
        return getattr(self.user_role, permission, False)
    
    def can_access_admin(self):
        """Check if user can access admin interface"""
        return self.is_admin or (self.user_role and self.user_role.can_access_admin)
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.is_admin or (self.user_role and self.user_role.can_manage_users)
    
    def can_manage_content(self):
        """Check if user can manage content"""
        return self.is_admin or self.is_staff or (self.user_role and self.user_role.can_manage_content)
    
    def can_view_analytics(self):
        """Check if user can view analytics"""
        return self.is_admin or self.is_staff or (self.user_role and self.user_role.can_view_analytics)
    
    def can_manage_system(self):
        """Check if user can manage system settings"""
        return self.is_admin or (self.user_role and self.user_role.can_manage_system)
    
    def can_delete_users(self):
        """Check if user can delete other users"""
        return self.is_admin or (self.user_role and self.user_role.can_delete_users)
    
    def get_max_file_size(self):
        """Get maximum file size for this user"""
        if self.user_role:
            return self.user_role.max_file_size
        elif self.is_premium():
            return 5368709120  # 5GB
        else:
            return 52428800   # 50MB
    
    def get_role_name(self):
        """Get user's role name"""
        if self.user_role:
            return self.user_role.name
        elif self.is_admin:
            return 'admin'
        elif self.is_staff:
            return 'staff'
        else:
            return 'user'
    
    def assign_role(self, role_name):
        """Assign role to user"""
        role = UserRole.query.filter_by(name=role_name).first()
        if role:
            self.role_id = role.id
            # Update legacy fields for backward compatibility
            if role_name == 'admin':
                self.is_admin = True
                self.is_staff = True
            elif role_name == 'staff':
                self.is_staff = True
                self.is_admin = False
            else:
                self.is_admin = False
                self.is_staff = False
            return True
        return False
    
    def has_weak_password(self):
        """
        Check if user's password is weak based on current requirements.
        Note: This can only be checked during login when we have the plain password.
        This flag is set during login validation.
        """
        return not self.password_strength_checked
    
    def should_show_password_alert(self):
        """Check if weak password alert should be shown to user"""
        if self.password_strength_checked:
            return False  # Password is strong, no alert needed
        
        # Check if alert was recently dismissed
        if self.password_alert_dismissed_at:
            from datetime import timedelta
            # Show alert again after 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            if self.password_alert_dismissed_at > seven_days_ago:
                return False  # Alert was dismissed recently
        
        return True  # Show alert
    
    def dismiss_password_alert(self, days=7):
        """Temporarily dismiss the weak password alert"""
        self.password_alert_dismissed_at = datetime.utcnow()
        db.session.commit()
    
    def mark_password_as_strong(self):
        """Mark user's password as meeting strength requirements"""
        self.password_strength_checked = True
        self.password_alert_dismissed_at = None  # Clear any dismissal
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'


class ConversionHistory(db.Model):
    """Track all conversion operations for analytics and history"""
    __tablename__ = 'conversion_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # File details
    original_filename = db.Column(db.String(255), nullable=False)
    original_format = db.Column(db.String(20), nullable=False)
    target_format = db.Column(db.String(20), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes
    
    # Conversion details
    conversion_type = db.Column(db.String(50), nullable=False)  # image, pdf, document, etc.
    tool_used = db.Column(db.String(50), nullable=False)
    processing_time = db.Column(db.Float)  # in seconds
    
    # Status
    status = db.Column(db.String(20), default='completed')  # completed, failed, processing
    error_message = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Conversion {self.original_filename} -> {self.target_format}>'


class UsageTracking(db.Model):
    """Daily usage tracking for quota management"""
    __tablename__ = 'usage_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, default=date.today, nullable=False)
    
    # Daily usage counts
    conversions_count = db.Column(db.Integer, default=0)
    storage_used = db.Column(db.BigInteger, default=0)  # in bytes
    processing_time = db.Column(db.Float, default=0.0)  # total seconds
    
    # Feature usage (for analytics)
    image_conversions = db.Column(db.Integer, default=0)
    pdf_conversions = db.Column(db.Integer, default=0)
    document_conversions = db.Column(db.Integer, default=0)
    ai_features_used = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint for user per day
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_user_date_uc'),)
    
    def increment_usage(self, conversion_type='general', processing_time=0.0, file_size=0):
        """Increment usage counters"""
        self.conversions_count += 1
        self.processing_time += processing_time
        self.storage_used += file_size
        
        # Update specific counters
        if conversion_type.startswith('image'):
            self.image_conversions += 1
        elif conversion_type.startswith('pdf'):
            self.pdf_conversions += 1
        elif conversion_type.startswith('document'):
            self.document_conversions += 1
        elif conversion_type.startswith('ai'):
            self.ai_features_used += 1
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def get_or_create_today(user_id):
        """Get or create today's usage record for user"""
        today_usage = UsageTracking.query.filter_by(
            user_id=user_id, 
            date=date.today()
        ).first()
        
        if not today_usage:
            today_usage = UsageTracking(user_id=user_id, date=date.today())
            db.session.add(today_usage)
            db.session.commit()
        
        return today_usage
    
    def __repr__(self):
        return f'<Usage {self.user.username} - {self.date}: {self.conversions_count} conversions>'


class UserSession(db.Model):
    """Database-backed user sessions for enhanced security"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Session security information
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 compatible
    user_agent = db.Column(db.Text, nullable=True)
    csrf_token = db.Column(db.String(255), nullable=False)
    
    # Session status and timestamps
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    
    # Security tracking
    login_method = db.Column(db.String(50), default='password')  # password, 2fa, etc.
    device_fingerprint = db.Column(db.String(255), nullable=True)
    location_country = db.Column(db.String(2), nullable=True)  # ISO country code
    location_city = db.Column(db.String(100), nullable=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('sessions', lazy=True, cascade='all, delete-orphan'))
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if session is valid and active"""
        return self.is_active and not self.is_expired()
    
    def extend_expiry(self, hours=24):
        """Extend session expiry time"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_activity = datetime.utcnow()
    
    def invalidate(self):
        """Invalidate this session"""
        self.is_active = False
        db.session.commit()
    
    @staticmethod
    def cleanup_expired():
        """Clean up expired sessions"""
        expired_sessions = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow()
        ).all()
        
        for session in expired_sessions:
            db.session.delete(session)
        
        db.session.commit()
        return len(expired_sessions)
    
    @staticmethod
    def get_active_sessions(user_id):
        """Get all active sessions for a user"""
        return UserSession.query.filter_by(
            user_id=user_id,
            is_active=True
        ).filter(
            UserSession.expires_at > datetime.utcnow()
        ).order_by(UserSession.last_activity.desc()).all()
    
    def __repr__(self):
        return f'<UserSession {self.user.username} from {self.ip_address}>'


class UsageAnalytics(db.Model):
    """Track feature usage for logged-in users"""
    __tablename__ = 'usage_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Feature information
    feature_name = db.Column(db.String(100), nullable=False, index=True)
    feature_category = db.Column(db.String(50), nullable=True, index=True)  # e.g., 'conversion', 'pdf_tool', 'image'
    
    # Usage details
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Additional metadata (JSON format)
    extra_metadata = db.Column(db.Text, nullable=True)  # Store JSON data like file size, format, etc.
    
    # Performance tracking
    processing_time = db.Column(db.Float, nullable=True)  # Time taken in seconds
    success = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('usage_analytics', lazy=True, cascade='all, delete-orphan'))
    
    @staticmethod
    def track_usage(user_id, feature_name, feature_category=None, extra_metadata=None, processing_time=None, success=True):
        """Track a feature usage"""
        usage = UsageAnalytics(
            user_id=user_id,
            feature_name=feature_name,
            feature_category=feature_category,
            extra_metadata=extra_metadata,
            processing_time=processing_time,
            success=success
        )
        db.session.add(usage)
        db.session.commit()
        return usage
    
    @staticmethod
    def get_user_stats(user_id, days=30):
        """Get usage statistics for a user"""
        from sqlalchemy import func
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stats = db.session.query(
            UsageAnalytics.feature_name,
            func.count(UsageAnalytics.id).label('count')
        ).filter(
            UsageAnalytics.user_id == user_id,
            UsageAnalytics.timestamp >= cutoff_date
        ).group_by(UsageAnalytics.feature_name).all()
        
        return {stat.feature_name: stat.count for stat in stats}
    
    @staticmethod
    def get_usage_by_period(user_id, period='day'):
        """Get usage data grouped by time period"""
        from sqlalchemy import func, cast, String
        
        if period == 'day':
            days = 7
            # PostgreSQL: DATE(timestamp)
            date_format = func.date(UsageAnalytics.timestamp)
        elif period == 'week':
            days = 28
            # PostgreSQL: to_char(timestamp, 'IYYY-IW') for ISO week
            date_format = func.to_char(UsageAnalytics.timestamp, 'IYYY-IW')
        elif period == 'month':
            days = 365
            # PostgreSQL: to_char(timestamp, 'YYYY-MM')
            date_format = func.to_char(UsageAnalytics.timestamp, 'YYYY-MM')
        elif period == 'year':
            days = 365 * 3
            # PostgreSQL: EXTRACT(YEAR FROM timestamp)
            date_format = cast(func.extract('year', UsageAnalytics.timestamp), String)
        else:
            days = 7
            date_format = func.date(UsageAnalytics.timestamp)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        usage_data = db.session.query(
            date_format.label('period'),
            UsageAnalytics.feature_name,
            func.count(UsageAnalytics.id).label('count')
        ).filter(
            UsageAnalytics.user_id == user_id,
            UsageAnalytics.timestamp >= cutoff_date
        ).group_by('period', UsageAnalytics.feature_name).all()
        
        return usage_data
    
    def __repr__(self):
        return f'<UsageAnalytics {self.user.username} - {self.feature_name}>'



class UserRole(db.Model):
    """User roles and permissions system"""
    __tablename__ = 'user_roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Permission flags
    can_access_admin = db.Column(db.Boolean, default=False)
    can_manage_users = db.Column(db.Boolean, default=False)
    can_manage_content = db.Column(db.Boolean, default=False)
    can_view_analytics = db.Column(db.Boolean, default=False)
    can_manage_system = db.Column(db.Boolean, default=False)
    can_delete_users = db.Column(db.Boolean, default=False)
    
    # File processing permissions
    max_file_size = db.Column(db.BigInteger, default=52428800)  # 50MB default
    daily_conversion_limit = db.Column(db.Integer, default=5)
    can_use_ai_features = db.Column(db.Boolean, default=False)
    can_batch_process = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='user_role', lazy=True)
    
    @staticmethod
    def create_default_roles():
        """Create default system roles"""
        default_roles = [
            {
                'name': 'user',
                'display_name': 'Regular User',
                'description': 'Standard user with basic conversion features',
                'max_file_size': 52428800,  # 50MB
                'daily_conversion_limit': 5,
                'can_use_ai_features': False,
                'can_batch_process': False
            },
            {
                'name': 'premium',
                'display_name': 'Premium User',
                'description': 'Premium user with enhanced features',
                'max_file_size': 5368709120,  # 5GB
                'daily_conversion_limit': -1,  # Unlimited
                'can_use_ai_features': True,
                'can_batch_process': True
            },
            {
                'name': 'staff',
                'display_name': 'Staff Member',
                'description': 'Staff member with content management access',
                'can_access_admin': True,
                'can_manage_content': True,
                'can_view_analytics': True,
                'max_file_size': 5368709120,  # 5GB
                'daily_conversion_limit': -1,  # Unlimited
                'can_use_ai_features': True,
                'can_batch_process': True
            },
            {
                'name': 'admin',
                'display_name': 'Administrator',
                'description': 'Full system administrator',
                'can_access_admin': True,
                'can_manage_users': True,
                'can_manage_content': True,
                'can_view_analytics': True,
                'can_manage_system': True,
                'can_delete_users': True,
                'max_file_size': 10737418240,  # 10GB
                'daily_conversion_limit': -1,  # Unlimited
                'can_use_ai_features': True,
                'can_batch_process': True
            }
        ]
        
        for role_data in default_roles:
            existing_role = UserRole.query.filter_by(name=role_data['name']).first()
            if not existing_role:
                role = UserRole(**role_data)
                db.session.add(role)
        
        db.session.commit()
    
    def __repr__(self):
        return f'<UserRole {self.name}: {self.display_name}>'


class SystemSettings(db.Model):
    """System-wide configuration settings"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_setting(key, default=None):
        """Get system setting value"""
        setting = SystemSettings.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @staticmethod
    def set_setting(key, value, description=None):
        """Set system setting value"""
        setting = SystemSettings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = SystemSettings(key=key, value=value, description=description)
            db.session.add(setting)
        
        db.session.commit()
        return setting
    
    def __repr__(self):
        return f'<Setting {self.key}: {self.value}>'


def init_system_settings():
    """Initialize default system settings"""
    default_settings = [
        ('free_daily_limit', '5', 'Daily conversion limit for free users'),
        ('max_file_size_free', '52428800', 'Max file size for free users (50MB)'),
        ('max_file_size_premium', '5368709120', 'Max file size for premium users (5GB)'),
        ('maintenance_mode', 'false', 'System maintenance mode'),
        ('registration_enabled', 'true', 'Allow new user registrations'),
        ('premium_price_monthly', '999', 'Premium subscription price per month (INR)'),
        ('site_name', 'Cropio', 'Site name for branding'),
        ('admin_email', 'admin@cropio.com', 'Admin contact email'),
        ('max_concurrent_users', '500', 'Maximum concurrent users'),
        ('session_timeout', '3600', 'Session timeout in seconds (1 hour)'),
    ]
    
    for key, value, description in default_settings:
        if not SystemSettings.query.filter_by(key=key).first():
            SystemSettings.set_setting(key, value, description)


# Helper functions for database operations
def create_admin_user():
    """Create default admin user if not exists"""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        from datetime import date, timedelta
        
        admin = User(
            username='admin',
            email='admin@cropio.com',
            subscription_tier='premium',
            subscription_start=date.today(),
            subscription_end=date.today() + timedelta(days=365),  # 1 year premium
            email_verified=True,
            is_active=True,
            is_admin=True,
            is_staff=True
        )
        admin.set_password('admin123')  # Change this in production!
        db.session.add(admin)
        db.session.commit()
        
        # Assign admin role
        admin_role = UserRole.query.filter_by(name='admin').first()
        if admin_role:
            admin.role_id = admin_role.id
            db.session.commit()
            print("[DATABASE] Admin user created with admin role: admin / admin123")
        else:
            print("[DATABASE] Admin user created: admin / admin123 (role assignment pending)")
        
        return admin
    else:
        # Update existing admin user with role if needed
        if not admin.role_id:
            admin_role = UserRole.query.filter_by(name='admin').first()
            if admin_role:
                admin.role_id = admin_role.id
                admin.is_admin = True
                admin.is_staff = True
                db.session.commit()
                print("[DATABASE] Admin user updated with admin role")
    return admin


def init_database():
    """Initialize database with default data"""
    print("[DATABASE] Initializing database...")
    
    # Create all tables
    db.create_all()
    print("[DATABASE] Database tables created")
    
    # Initialize system settings
    init_system_settings()
    print("[DATABASE] System settings initialized")
    
    # Create default roles
    UserRole.create_default_roles()
    print("[DATABASE] User roles initialized")
    
    # Create admin user with proper role
    create_admin_user()
    print("[DATABASE] Admin user setup complete")
    
    # Clean up expired sessions
    UserSession.cleanup_expired()
    print("[DATABASE] Session cleanup complete")
    
    print("[DATABASE] Database initialization complete!")
