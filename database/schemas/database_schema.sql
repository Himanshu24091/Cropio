-- =====================================================
-- Cropio Platform - Database Schema Creation Script
-- Security-First File Processing Platform
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";

-- =====================================================
-- 1. USERS MANAGEMENT TABLES
-- =====================================================

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

-- =====================================================
-- 2. FILE OPERATIONS & PROCESSING TABLES
-- =====================================================

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
    malware_scan_result VARCHAR(20) CHECK (malware_scan_result IN ('clean', 'infected', 'suspicious', 'pending')),
    malware_scanner VARCHAR(50),
    scan_timestamp TIMESTAMP WITH TIME ZONE,
    exif_data JSONB, -- For images
    pdf_metadata JSONB, -- For PDFs
    document_properties JSONB, -- For documents
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 3. SECURITY & MONITORING TABLES
-- =====================================================

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

-- =====================================================
-- 4. SYSTEM CONFIGURATION & SETTINGS TABLES
-- =====================================================

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

-- =====================================================
-- 5. ANALYTICS & REPORTING TABLES
-- =====================================================

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

-- =====================================================
-- 6. AUDIT TRAIL & COMPLIANCE TABLE
-- =====================================================

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

-- =====================================================
-- 7. CREATE INDEXES FOR PERFORMANCE
-- =====================================================

-- Users table indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_role_active ON users(role, is_active);
CREATE INDEX idx_users_last_login ON users(last_login);

-- User sessions indexes
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_active ON user_sessions(is_active) WHERE is_active = TRUE;

-- File operations indexes
CREATE INDEX idx_file_operations_user_id ON file_operations(user_id);
CREATE INDEX idx_file_operations_session_id ON file_operations(session_id);
CREATE INDEX idx_file_operations_type ON file_operations(operation_type, operation_subtype);
CREATE INDEX idx_file_operations_status ON file_operations(status);
CREATE INDEX idx_file_operations_created_at ON file_operations(created_at);
CREATE INDEX idx_file_operations_expires_at ON file_operations(expires_at) WHERE expires_at IS NOT NULL;

-- File metadata indexes
CREATE INDEX idx_file_metadata_hash ON file_metadata(file_hash);
CREATE INDEX idx_file_metadata_operation_id ON file_metadata(file_operation_id);
CREATE INDEX idx_file_metadata_mime_type ON file_metadata(mime_type);
CREATE INDEX idx_file_metadata_suspicious ON file_metadata(is_suspicious) WHERE is_suspicious = TRUE;
CREATE INDEX idx_file_metadata_scan_result ON file_metadata(malware_scan_result);

-- Security request log indexes
CREATE INDEX idx_sec_request_log_ip_address ON sec_request_log(ip_address);
CREATE INDEX idx_sec_request_log_user_id ON sec_request_log(user_id);
CREATE INDEX idx_sec_request_log_created_at ON sec_request_log(created_at);
CREATE INDEX idx_sec_request_log_suspicious ON sec_request_log(is_suspicious) WHERE is_suspicious = TRUE;
CREATE INDEX idx_sec_request_log_risk_score ON sec_request_log(risk_score);
CREATE INDEX idx_sec_request_log_status_code ON sec_request_log(response_status_code);
CREATE INDEX idx_sec_request_log_path ON sec_request_log(request_path);

-- Security blocklist indexes
CREATE INDEX idx_sec_blocklist_ip_address ON sec_blocklist(ip_address);
CREATE INDEX idx_sec_blocklist_ip_range ON sec_blocklist(ip_range);
CREATE INDEX idx_sec_blocklist_active ON sec_blocklist(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_sec_blocklist_expires_at ON sec_blocklist(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_sec_blocklist_block_type ON sec_blocklist(block_type);
CREATE INDEX idx_sec_blocklist_severity ON sec_blocklist(severity);

-- Security incidents indexes
CREATE INDEX idx_sec_incidents_type ON sec_incidents(incident_type);
CREATE INDEX idx_sec_incidents_severity ON sec_incidents(severity);
CREATE INDEX idx_sec_incidents_status ON sec_incidents(status);
CREATE INDEX idx_sec_incidents_affected_user ON sec_incidents(affected_user_id);
CREATE INDEX idx_sec_incidents_assigned_to ON sec_incidents(assigned_to_user_id);
CREATE INDEX idx_sec_incidents_created_at ON sec_incidents(created_at);
CREATE INDEX idx_sec_incidents_affected_ip ON sec_incidents(affected_ip);

-- Application settings indexes
CREATE INDEX idx_app_settings_key ON app_settings(setting_key);
CREATE INDEX idx_app_settings_type ON app_settings(setting_type);
CREATE INDEX idx_app_settings_public ON app_settings(is_public);

-- Feature flags indexes
CREATE INDEX idx_feature_flags_name ON feature_flags(flag_name);
CREATE INDEX idx_feature_flags_enabled ON feature_flags(is_enabled);

-- Usage analytics indexes
CREATE INDEX idx_usage_analytics_event_type ON usage_analytics(event_type);
CREATE INDEX idx_usage_analytics_user_id ON usage_analytics(user_id);
CREATE INDEX idx_usage_analytics_created_at ON usage_analytics(created_at);
CREATE INDEX idx_usage_analytics_ip_address ON usage_analytics(ip_address);
CREATE INDEX idx_usage_analytics_page_path ON usage_analytics(page_path);

-- Daily stats indexes
CREATE INDEX idx_daily_stats_date ON daily_stats(date);
CREATE INDEX idx_daily_stats_created_at ON daily_stats(created_at);

-- Audit log indexes
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource_type ON audit_log(resource_type);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_success ON audit_log(success);
CREATE INDEX idx_audit_log_ip_address ON audit_log(ip_address);

-- =====================================================
-- 8. CREATE TRIGGERS FOR AUTO-UPDATING TIMESTAMPS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

-- Apply triggers to tables with updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sec_blocklist_updated_at BEFORE UPDATE ON sec_blocklist
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_app_settings_updated_at BEFORE UPDATE ON app_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feature_flags_updated_at BEFORE UPDATE ON feature_flags
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 9. INSERT DEFAULT SETTINGS AND CONFIGURATION
-- =====================================================

-- Insert default application settings
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('max_file_size_mb', '50', 'integer', 'Maximum file size allowed for uploads in MB', TRUE),
('max_files_per_hour', '100', 'integer', 'Maximum files a user can process per hour', TRUE),
('session_timeout_minutes', '60', 'integer', 'Session timeout in minutes', FALSE),
('max_login_attempts', '5', 'integer', 'Maximum login attempts before account lock', FALSE),
('lockout_duration_minutes', '30', 'integer', 'Account lockout duration in minutes', FALSE),
('auto_cleanup_hours', '1', 'integer', 'Hours after which processed files are deleted', TRUE),
('security_risk_threshold', '75', 'integer', 'Risk score threshold for auto-blocking', FALSE),
('enable_geoip', 'true', 'boolean', 'Enable geographic IP tracking', FALSE),
('enable_malware_scan', 'true', 'boolean', 'Enable malware scanning for uploaded files', TRUE),
('allowed_file_extensions', '["pdf","jpg","jpeg","png","webp","docx","xlsx","txt"]', 'json', 'List of allowed file extensions', TRUE);

-- Insert default feature flags
INSERT INTO feature_flags (flag_name, is_enabled, rollout_percentage, description) VALUES
('real_time_dashboard', FALSE, 0, 'Enable real-time WebSocket dashboard updates'),
('advanced_security', FALSE, 0, 'Enable advanced security monitoring and detection'),
('file_quarantine', TRUE, 100, 'Enable file quarantine system'),
('auto_blocking', FALSE, 0, 'Enable automatic IP blocking based on risk score'),
('admin_notifications', TRUE, 100, 'Enable admin email notifications for security events'),
('file_encryption', FALSE, 0, 'Enable file encryption for stored files'),
('audit_logging', TRUE, 100, 'Enable comprehensive audit logging'),
('performance_monitoring', FALSE, 50, 'Enable performance monitoring and metrics collection');

-- Create default admin user (password: admin123 - CHANGE IN PRODUCTION!)
-- Note: This uses a bcrypt hash for 'admin123' - you should change this immediately
INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active, email_verified) VALUES
('admin', 'admin@cropio.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqyc0z8avHiop5eHaQr1g5O', 'System', 'Administrator', 'admin', TRUE, TRUE);

-- =====================================================
-- 10. CREATE VIEWS FOR COMMON QUERIES
-- =====================================================

-- View for active user sessions with user details
CREATE VIEW active_user_sessions AS
SELECT 
    us.id,
    us.session_token,
    us.ip_address,
    us.created_at,
    us.expires_at,
    u.username,
    u.email,
    u.role
FROM user_sessions us
JOIN users u ON us.user_id = u.id
WHERE us.is_active = TRUE 
    AND us.expires_at > CURRENT_TIMESTAMP;

-- View for file processing statistics
CREATE VIEW file_processing_stats AS
SELECT 
    operation_type,
    operation_subtype,
    status,
    COUNT(*) as total_operations,
    AVG(processing_time_ms) as avg_processing_time_ms,
    SUM(file_size_bytes) as total_file_size_bytes,
    SUM(processed_file_size_bytes) as total_processed_size_bytes
FROM file_operations
GROUP BY operation_type, operation_subtype, status;

-- View for security threat summary
CREATE VIEW security_threat_summary AS
SELECT 
    DATE(created_at) as threat_date,
    COUNT(*) as total_requests,
    COUNT(CASE WHEN is_suspicious = TRUE THEN 1 END) as suspicious_requests,
    COUNT(DISTINCT ip_address) as unique_ips,
    AVG(risk_score) as avg_risk_score,
    MAX(risk_score) as max_risk_score
FROM sec_request_log
GROUP BY DATE(created_at)
ORDER BY threat_date DESC;

-- View for blocked IPs with admin details
CREATE VIEW blocked_ips_with_admin AS
SELECT 
    sb.id,
    sb.ip_address,
    sb.ip_range,
    sb.block_type,
    sb.reason,
    sb.severity,
    sb.is_active,
    sb.expires_at,
    sb.created_at,
    u.username as blocked_by_username
FROM sec_blocklist sb
LEFT JOIN users u ON sb.blocked_by_user_id = u.id
WHERE sb.is_active = TRUE;

-- =====================================================
-- 11. ADDITIONAL CONSTRAINTS AND BUSINESS RULES
-- =====================================================

-- Ensure either user_id or session_id is present in file_operations
ALTER TABLE file_operations ADD CONSTRAINT check_user_or_session 
CHECK ((user_id IS NOT NULL) OR (session_id IS NOT NULL));

-- Ensure either ip_address or ip_range is present in sec_blocklist
ALTER TABLE sec_blocklist ADD CONSTRAINT check_ip_or_range 
CHECK ((ip_address IS NOT NULL) OR (ip_range IS NOT NULL));

-- Ensure file hash is always uppercase SHA-256
ALTER TABLE file_metadata ADD CONSTRAINT check_file_hash_format 
CHECK (file_hash ~ '^[A-F0-9]{64}$');

-- Ensure risk score is within valid range
ALTER TABLE sec_request_log ADD CONSTRAINT check_risk_score_range 
CHECK (risk_score >= 0 AND risk_score <= 100);

-- =====================================================
-- SCHEMA CREATION COMPLETE
-- =====================================================

-- Grant permissions to application user (create this user separately)
-- GRANT CONNECT ON DATABASE cropio TO cropio_app;
-- GRANT USAGE ON SCHEMA public TO cropio_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cropio_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cropio_app;

-- Display completion message
DO $$
BEGIN
    RAISE NOTICE 'Cropio database schema creation completed successfully!';
    RAISE NOTICE 'Tables created: %, Views created: %', 
        (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'),
        (SELECT count(*) FROM information_schema.views WHERE table_schema = 'public');
    RAISE NOTICE 'Remember to:';
    RAISE NOTICE '1. Change the default admin password';
    RAISE NOTICE '2. Create application database user with proper permissions';
    RAISE NOTICE '3. Configure your application connection settings';
    RAISE NOTICE '4. Review and adjust default settings in app_settings table';
END $$;
