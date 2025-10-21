# **CROPIO PLATFORM — DATABASE SCHEMA**
### **Security-First File Processing with Real-Time Analytics**

---

## **📌 USER MANAGEMENT TABLES**

### **users**
- **PK**: `id`  
- **UK**: `username`, `email`  
- **Fields**: password_hash, first_name, last_name, role, is_active, email_verified, created_at, updated_at, last_login, login_attempts, locked_until  

### **user_sessions**
- **PK**: `id`  
- **FK**: `user_id` → users.id  
- **Fields**: session_token, ip_address, user_agent, created_at, expires_at, is_active  

---

## **📌 FILE PROCESSING TABLES**

### **file_operations**
- **PK**: `id`  
- **FK**: `user_id` → users.id  
- **Fields**: session_id, operation_type, operation_subtype, status, input_file_path, output_file_path, original_filename, processed_filename, file_size_bytes, processed_file_size, processing_time_ms, error_message, metadata (JSONB), created_at, completed_at, expires_at  

### **file_metadata**
- **PK**: `id`  
- **FK**: `file_operation_id` → file_operations.id  
- **UK**: `file_hash`  
- **Fields**: mime_type, actual_mime_type, file_extension, file_size_bytes, is_suspicious, malware_scan_result, malware_scanner, scan_timestamp, exif_data (JSONB), pdf_metadata (JSONB), document_properties, created_at  

---

## **📌 SECURITY & MONITORING TABLES**

### **sec_request_log**
- **PK**: `id`  
- **FK**: `user_id` → users.id  
- **Fields**: session_id, ip_address, user_agent, request_method, request_path, request_size_bytes, response_status, response_time_ms, country_code, region, city, is_suspicious, risk_score, threat_indicators, created_at  

### **sec_blocklist**
- **PK**: `id`  
- **Fields**: ip_address, ip_range (CIDR), block_type, blocked_by_user_id, reason, severity, is_active, expires_at, created_at, updated_at  

### **sec_incidents**
- **PK**: `id`  
- **Fields**: incident_type, severity, title, description, affected_user_id, affected_ip, source_data (JSONB), status, assigned_to_user_id, resolution_notes, created_at, resolved_at  

---

## **📌 SYSTEM CONFIGURATION TABLES**

### **app_settings**
- **PK**: `id`  
- **UK**: `setting_key`  
- **Fields**: setting_value, setting_type, description, is_public, created_at, updated_at, updated_by_user_id  

### **feature_flags**
- **PK**: `id`  
- **UK**: `flag_name`  
- **Fields**: is_enabled, rollout_percentage, target_users (JSONB), description, created_at, updated_at  

---

## **📌 ANALYTICS & REPORTING TABLES**

### **usage_analytics**
- **PK**: `id`  
- **FK**: `user_id` → users.id  
- **Fields**: event_type, session_id, ip_address, user_agent, page_path, referrer, event_data (JSONB), created_at  

### **daily_stats**
- **PK**: `id`  
- **UK**: `date`  
- **Fields**: total_users, new_users, total_files_processed, total_data_bytes, successful_ops, failed_operations, security_incidents, blocked_requests, unique_ips, created_at  

### **audit_log**
- **PK**: `id`  
- **FK**: `user_id` → users.id  
- **Fields**: action, resource_type, resource_id, old_values (JSONB), new_values (JSONB), ip_address, user_agent, success, error_message, created_at  

---

## **🔗 RELATIONSHIP OVERVIEW**
- `users` (1) → (N) `user_sessions`
- `users` (1) → (N) `file_operations`
- `file_operations` (1) → (1) `file_metadata`
- `users` (1) → (N) `sec_request_log`
- `users` (1) → (N) `sec_blocklist` (as blocker)
- `users` (1) → (N) `sec_incidents` (as affected_user / assigned_admin)
- `users` (1) → (N) `app_settings` (as updater)
- `users` (1) → (N) `usage_analytics`
- `users` (1) → (N) `audit_log`

---

## **⚙️ CHECK CONSTRAINTS**
- `users.role` ∈ ('admin', 'user', 'moderator')
- `file_operations.status` ∈ ('pending', 'processing', 'completed', 'failed', 'quarantined')
- `file_metadata.malware_scan_result` ∈ ('clean', 'infected', 'suspicious', 'pending')
- `sec_request_log.risk_score` between 0 and 100
- `sec_blocklist.block_type` ∈ ('manual', 'auto', 'geo', 'reputation')
- `sec_blocklist.severity` ∈ ('low', 'medium', 'high', 'critical')
- `sec_incidents.severity` ∈ ('low', 'medium', 'high', 'critical')
- `sec_incidents.status` ∈ ('open', 'investigating', 'resolved', 'false_positive')
- `app_settings.setting_type` ∈ ('string', 'integer', 'boolean', 'json')
- `feature_flags.rollout_percentage` between 0 and 100  

---

## **📜 BUSINESS RULES**
- Either `user_id` OR `session_id` must be present in file_operations
- Either `ip_address` OR `ip_range` must be present in sec_blocklist
- `file_metadata.file_hash` must be uppercase SHA-256
- Auto-cleanup of expired file_operations based on expires_at
- Session management with automatic expiration
- Geographic data collection for security analysis
- Real-time risk scoring and threat detection

---

## **🚀 PERFORMANCE INDEXES**
- **USERS**: `idx_users_email`, `idx_users_username`, `idx_users_role_active`
- **FILE_OPERATIONS**: `idx_file_operations_user_id`, `idx_file_operations_status`, `idx_file_operations_type`, `idx_file_operations_expires_at`
- **SEC_REQUEST_LOG**: `idx_sec_request_log_ip_address`, `idx_sec_request_log_created_at`, `idx_sec_request_log_suspicious`, `idx_sec_request_log_risk_score`
- **SEC_BLOCKLIST**: `idx_sec_blocklist_ip_address`, `idx_sec_blocklist_active`
- **FILE_METADATA**: `idx_file_metadata_hash`, `idx_file_metadata_suspicious`

---

## **📝 IMPLEMENTATION NOTES**
- PK = Primary Key, FK = Foreign Key, UK = Unique Key  
- JSONB fields provide flexible storage for metadata/configuration  
- All timestamps use `TIMESTAMP WITH TIME ZONE`  
- Comprehensive logging and monitoring  
- Quarantine and validation in file processing pipeline  
- Real-time analytics with pre-aggregated stats  
- Feature flag system for gradual rollouts / A-B testing  
- Complete audit trail for compliance and debugging  

---

**Created by:** Himanshu  
**Version:** 2.0.0  
**License:** MIT
