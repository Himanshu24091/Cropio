# 📊 Database Schema Design for Cropio Converter Platform

## Overview
This document provides a comprehensive database schema design for the Cropio file processing platform. The schema supports current functionality (file conversion, PDF manipulation, compression, etc.) and future security features (real-time monitoring, threat detection, audit trails).

## 🏗️ Database Architecture

### Technology Stack
- **Primary Database**: PostgreSQL (production-ready, ACID compliant)
- **Cache Layer**: Redis (session management, real-time events)
- **Migration Tool**: Alembic (version control for database changes)
- **ORM**: SQLAlchemy (Python ORM integration)

---

## 📋 Core Tables Schema

### 1. Users Management

```sql
-- Users table for authentication and authorization
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'moderator')),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE
);

-- User sessions for session management
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 2. File Operations & Processing

```sql
-- File operations tracking
CREATE TABLE file_operations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(100), -- For anonymous users
    operation_type VARCHAR(50) NOT NULL, -- 'convert', 'compress', 'crop', 'merge', etc.
    operation_subtype VARCHAR(50), -- 'image_to_pdf', 'pdf_to_docx', etc.
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'quarantined')),
    input_file_path TEXT,
    output_file_path TEXT,
    original_filename VARCHAR(255),
    processed_filename VARCHAR(255),
    file_size_bytes BIGINT,
    processed_file_size_bytes BIGINT,
    processing_time_ms INTEGER,
    error_message TEXT,
    metadata JSONB, -- Store additional processing parameters
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE -- For cleanup
);

-- File metadata and security analysis
CREATE TABLE file_metadata (
    id SERIAL PRIMARY KEY,
    file_operation_id INTEGER REFERENCES file_operations(id) ON DELETE CASCADE,
    file_hash VARCHAR(64) UNIQUE NOT NULL, -- SHA-256 hash
    mime_type VARCHAR(100),
    actual_mime_type VARCHAR(100), -- Detected vs declared
    file_extension VARCHAR(10),
    file_size_bytes BIGINT,
    is_suspicious BOOLEAN DEFAULT FALSE,
    malware_scan_result VARCHAR(20), -- 'clean', 'infected', 'suspicious', 'pending'
    malware_scanner VARCHAR(50),
    scan_timestamp TIMESTAMP WITH TIME ZONE,
    exif_data JSONB, -- For images
    pdf_metadata JSONB, -- For PDFs
    document_properties JSONB, -- For documents
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Security & Monitoring

```sql
-- Request logging for security monitoring
CREATE TABLE sec_request_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(100),
    ip_address INET NOT NULL,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path TEXT,
    request_size_bytes INTEGER,
    response_status_code INTEGER,
    response_time_ms INTEGER,
    country_code VARCHAR(2),
    region VARCHAR(100),
    city VARCHAR(100),
    is_suspicious BOOLEAN DEFAULT FALSE,
    risk_score INTEGER DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
    threat_indicators JSONB, -- Array of detected threats
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- IP blocklist management
CREATE TABLE sec_blocklist (
    id SERIAL PRIMARY KEY,
    ip_address INET NOT NULL,
    ip_range CIDR, -- For subnet blocking
    block_type VARCHAR(20) DEFAULT 'manual' CHECK (block_type IN ('manual', 'auto', 'geo', 'reputation')),
    blocked_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reason TEXT NOT NULL,
    severity VARCHAR(10) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Security incidents and alerts
CREATE TABLE sec_incidents (
    id SERIAL PRIMARY KEY,
    incident_type VARCHAR(50) NOT NULL, -- 'malware_detected', 'suspicious_activity', 'brute_force', etc.
    severity VARCHAR(10) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    affected_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    affected_ip INET,
    source_data JSONB, -- Additional context data
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'investigating', 'resolved', 'false_positive')),
    assigned_to_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);
```

### 4. System Configuration & Settings

```sql
-- Application settings
CREATE TABLE app_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string' CHECK (setting_type IN ('string', 'integer', 'boolean', 'json')),
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE, -- Whether setting can be viewed by non-admins
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL
);

-- Feature flags for gradual rollouts
CREATE TABLE feature_flags (
    id SERIAL PRIMARY KEY,
    flag_name VARCHAR(100) UNIQUE NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    rollout_percentage INTEGER DEFAULT 0 CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),
    target_users JSONB, -- Array of user IDs or criteria
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Analytics & Reporting

```sql
-- Usage analytics
CREATE TABLE usage_analytics (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL, -- 'page_view', 'file_upload', 'conversion_complete', etc.
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    page_path VARCHAR(255),
    referrer VARCHAR(255),
    event_data JSONB, -- Additional event-specific data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Daily statistics summary
CREATE TABLE daily_stats (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    total_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    total_files_processed INTEGER DEFAULT 0,
    total_data_processed_bytes BIGINT DEFAULT 0,
    successful_operations INTEGER DEFAULT 0,
    failed_operations INTEGER DEFAULT 0,
    security_incidents INTEGER DEFAULT 0,
    blocked_requests INTEGER DEFAULT 0,
    unique_ips INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 6. Audit Trail & Compliance

```sql
-- Comprehensive audit log
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL, -- 'user_login', 'file_upload', 'admin_action', etc.
    resource_type VARCHAR(50), -- 'user', 'file', 'system', etc.
    resource_id VARCHAR(100),
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔗 Relationships & Indexes

### Primary Relationships
```sql
-- Foreign key relationships
ALTER TABLE user_sessions ADD CONSTRAINT fk_user_sessions_user_id FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE file_operations ADD CONSTRAINT fk_file_operations_user_id FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE file_metadata ADD CONSTRAINT fk_file_metadata_file_operation_id FOREIGN KEY (file_operation_id) REFERENCES file_operations(id);
ALTER TABLE sec_request_log ADD CONSTRAINT fk_sec_request_log_user_id FOREIGN KEY (user_id) REFERENCES users(id);
```

### Performance Indexes
```sql
-- Users table indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_role_active ON users(role, is_active);

-- File operations indexes
CREATE INDEX idx_file_operations_user_id ON file_operations(user_id);
CREATE INDEX idx_file_operations_session_id ON file_operations(session_id);
CREATE INDEX idx_file_operations_type ON file_operations(operation_type, operation_subtype);
CREATE INDEX idx_file_operations_status ON file_operations(status);
CREATE INDEX idx_file_operations_created_at ON file_operations(created_at);
CREATE INDEX idx_file_operations_expires_at ON file_operations(expires_at) WHERE expires_at IS NOT NULL;

-- Security indexes
CREATE INDEX idx_sec_request_log_ip_address ON sec_request_log(ip_address);
CREATE INDEX idx_sec_request_log_created_at ON sec_request_log(created_at);
CREATE INDEX idx_sec_request_log_suspicious ON sec_request_log(is_suspicious) WHERE is_suspicious = TRUE;
CREATE INDEX idx_sec_blocklist_ip_address ON sec_blocklist(ip_address);
CREATE INDEX idx_sec_blocklist_active ON sec_blocklist(is_active) WHERE is_active = TRUE;

-- File metadata indexes
CREATE INDEX idx_file_metadata_hash ON file_metadata(file_hash);
CREATE INDEX idx_file_metadata_mime_type ON file_metadata(mime_type);
CREATE INDEX idx_file_metadata_suspicious ON file_metadata(is_suspicious) WHERE is_suspicious = TRUE;
CREATE INDEX idx_file_metadata_scan_result ON file_metadata(malware_scan_result);
```

---

## 🚀 Implementation Guide

### 1. Database Setup

```bash
# Install dependencies
pip install psycopg2-binary sqlalchemy alembic redis flask-sqlalchemy

# Create PostgreSQL database
createdb cropio_converter

# Initialize Alembic
alembic init migrations

# Create initial migration
alembic revision --autogenerate -m "Initial database schema"

# Apply migration
alembic upgrade head
```

### 2. SQLAlchemy Models Example

```python
# models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(20), default='user')
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True))
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))

class FileOperation(Base):
    __tablename__ = 'file_operations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    session_id = Column(String(100))
    operation_type = Column(String(50), nullable=False)
    operation_subtype = Column(String(50))
    status = Column(String(20), default='pending')
    input_file_path = Column(Text)
    output_file_path = Column(Text)
    original_filename = Column(String(255))
    processed_filename = Column(String(255))
    file_size_bytes = Column(BigInteger)
    processed_file_size_bytes = Column(BigInteger)
    processing_time_ms = Column(Integer)
    error_message = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
```

### 3. Configuration Integration

```python
# config.py additions
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/cropio_converter')
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Database Engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Security Settings
SECURITY_SETTINGS = {
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION_MINUTES': 30,
    'SESSION_TIMEOUT_MINUTES': 60,
    'MAX_FILE_SIZE_MB': 32,
    'ALLOWED_COUNTRIES': ['US', 'CA', 'GB', 'DE', 'FR'],  # Empty list = all countries allowed
    'RISK_SCORE_THRESHOLD': 70,
    'AUTO_BLOCK_THRESHOLD': 85
}
```

### 4. Migration Commands

```bash
# Create new migration
alembic revision --autogenerate -m "Add security tables"

# View current migration status
alembic current

# Upgrade to latest version
alembic upgrade head

# Downgrade to previous version
alembic downgrade -1

# View migration history
alembic history
```

---

## 📊 Data Management Strategies

### 1. Data Retention Policies

```sql
-- Clean up expired file operations (runs daily)
DELETE FROM file_operations 
WHERE expires_at < CURRENT_TIMESTAMP AND status = 'completed';

-- Archive old request logs (keep 90 days)
DELETE FROM sec_request_log 
WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';

-- Clean up inactive sessions
DELETE FROM user_sessions 
WHERE expires_at < CURRENT_TIMESTAMP OR is_active = FALSE;
```

### 2. Backup Strategy

```bash
# Daily database backup
pg_dump cropio_converter > backup_$(date +%Y%m%d).sql

# Compressed backup with timestamp
pg_dump cropio_converter | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 3. Performance Monitoring

```sql
-- Monitor table sizes
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public';

-- Index usage statistics
SELECT 
    indexname,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes;
```

---

## 🔒 Security Considerations

### 1. Data Encryption
- **At Rest**: Enable PostgreSQL TLS encryption
- **In Transit**: Use SSL connections
- **Sensitive Data**: Hash passwords with bcrypt
- **File Storage**: Encrypt uploaded files

### 2. Access Control
- **Role-Based Access**: Admin, Moderator, User roles
- **IP Restrictions**: Geo-blocking and IP allowlists
- **Rate Limiting**: Per-IP and per-user limits
- **Session Management**: Secure session tokens

### 3. Audit & Compliance
- **Complete Audit Trail**: All actions logged
- **Data Retention**: Configurable retention policies
- **Privacy Compliance**: GDPR-ready data handling
- **Incident Response**: Automated alerting system

---

## 🚀 Scaling Considerations

### 1. Database Scaling
- **Read Replicas**: For analytics and reporting
- **Partitioning**: Large tables by date/user
- **Connection Pooling**: PgBouncer for connection management
- **Caching**: Redis for frequent queries

### 2. Application Scaling
- **Microservices**: Separate services for different functions
- **Message Queues**: Background processing with Celery/RQ
- **Load Balancing**: Multiple app instances
- **CDN**: Static file delivery

### 3. Monitoring & Alerting
- **Real-time Dashboards**: Grafana + Prometheus
- **Log Aggregation**: ELK stack or similar
- **Health Checks**: Application and database monitoring
- **Alerting**: Critical event notifications

---

## 📝 Next Steps for Implementation

### Phase 1: Core Database Setup (Week 1-2)
1. Set up PostgreSQL and Redis
2. Create initial migration with core tables
3. Implement basic models and database connection
4. Add user authentication system

### Phase 2: Security Integration (Week 3-5)
1. Implement request logging middleware
2. Add IP blocking and rate limiting
3. Create security monitoring dashboard
4. Implement file quarantine system

### Phase 3: Advanced Features (Week 6-8)
1. Real-time WebSocket integration
2. Advanced analytics and reporting
3. Complete admin dashboard
4. Performance optimization and testing

This schema provides a solid foundation for your current file processing needs while being extensible for the planned security and monitoring features. The design emphasizes performance, security, and maintainability.
