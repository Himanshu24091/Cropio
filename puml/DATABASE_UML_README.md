# Cropio Database Schema - UML Documentation

This directory contains comprehensive UML documentation for the Cropio platform database schema, designed for a security-first file processing platform with real-time analytics.

## 📁 Files Overview

### 1. `database_schema_uml.puml`
- **Type**: PlantUML Class Diagram
- **Purpose**: Complete database schema showing all tables, relationships, and constraints
- **Features**: 
  - Color-coded entities by type (User, File, Security, Analytics, etc.)
  - Detailed field specifications with data types
  - Foreign key relationships
  - Business rule notes
  - Check constraints documentation

### 2. `database_erd_uml.puml`
- **Type**: Entity-Relationship Diagram (ERD)
- **Purpose**: Traditional ERD view with focus on relationships and indexes
- **Features**:
  - Primary keys (PK) and Foreign keys (FK) clearly marked
  - Unique constraints (UK) highlighted
  - Index information included
  - Business rules and constraints detailed
  - Simplified relationship notation

### 3. `database_schema.sql`
- **Type**: PostgreSQL DDL Script
- **Purpose**: Complete database creation script
- **Features**:
  - Production-ready SQL with all tables, indexes, and constraints
  - Default data and configuration
  - Database views for common queries
  - Triggers for automatic timestamp updates
  - Performance optimization indexes

## 🚀 How to Use These Files

### Viewing UML Diagrams

#### Option 1: Online PlantUML Editor
1. Go to [PlantUML Online](http://www.plantuml.com/plantuml/uml)
2. Copy content from `.puml` files
3. Paste and view the generated diagram

#### Option 2: VS Code Extension
1. Install "PlantUML" extension in VS Code
2. Open the `.puml` files
3. Press `Alt+D` to preview diagrams

#### Option 3: Local PlantUML Installation
```bash
# Install PlantUML (requires Java)
java -jar plantuml.jar database_schema_uml.puml

# Generate PNG images
java -jar plantuml.jar -tpng *.puml

# Generate SVG images
java -jar plantuml.jar -tsvg *.puml
```

### Creating Database from SQL

#### PostgreSQL Setup
```bash
# Create database
createdb cropio_platform

# Run schema script
psql -d cropio_platform -f database_schema.sql

# Verify creation
psql -d cropio_platform -c "\dt"  # List tables
psql -d cropio_platform -c "\dv"  # List views
```

## 📊 Database Schema Overview

### Core Entity Groups

#### 🔐 **User Management**
- `users` - User accounts with authentication
- `user_sessions` - Active user sessions

#### 📁 **File Processing**
- `file_operations` - File processing operations tracking
- `file_metadata` - File security analysis and metadata

#### 🛡️ **Security Monitoring**
- `sec_request_log` - Real-time request logging
- `sec_blocklist` - IP and CIDR blocking management
- `sec_incidents` - Security incident tracking

#### ⚙️ **System Configuration**
- `app_settings` - Application configuration
- `feature_flags` - Feature rollout management

#### 📈 **Analytics & Reporting**
- `usage_analytics` - User behavior tracking
- `daily_stats` - Pre-aggregated statistics
- `audit_log` - Comprehensive audit trail

## 🔗 Key Relationships

```
users (1) ←→ (N) user_sessions
users (1) ←→ (N) file_operations
users (1) ←→ (N) sec_request_log
users (1) ←→ (N) sec_incidents (as affected_user)
users (1) ←→ (N) sec_incidents (as assigned_admin)

file_operations (1) ←→ (1) file_metadata
file_operations (N) ←→ (1) users
```

## 📋 Database Features

### Security Features
- **Request Logging**: Every HTTP request logged with geographic data
- **IP Blocking**: Support for individual IPs and CIDR ranges
- **Risk Scoring**: Automatic risk assessment (0-100 scale)
- **Incident Management**: Complete security incident workflow
- **Audit Trail**: Comprehensive logging of all system actions

### File Processing Features
- **Operation Tracking**: Complete lifecycle tracking
- **Status Management**: pending → processing → completed/failed/quarantined
- **Metadata Extraction**: EXIF, PDF properties, document metadata
- **Hash-based Deduplication**: SHA-256 file identification
- **Auto-cleanup**: Configurable file retention policies

### Performance Optimizations
- **Strategic Indexing**: Indexes on all frequently queried columns
- **Partial Indexes**: Conditional indexes for boolean flags
- **JSONB Fields**: Efficient storage for metadata and configuration
- **Database Views**: Pre-optimized queries for common operations

## 🏗️ Implementation Roadmap

### Phase 1: Core Tables (Current)
```sql
-- Essential tables for basic functionality
CREATE TABLE users (...);
CREATE TABLE file_operations (...);
CREATE TABLE file_metadata (...);
```

### Phase 2: Security Infrastructure
```sql
-- Security monitoring and logging
CREATE TABLE sec_request_log (...);
CREATE TABLE sec_blocklist (...);
CREATE TABLE sec_incidents (...);
```

### Phase 3: Analytics & Configuration
```sql
-- System configuration and analytics
CREATE TABLE app_settings (...);
CREATE TABLE usage_analytics (...);
CREATE TABLE audit_log (...);
```

## 🔧 Customization Options

### Adjusting for Your Environment

#### Development Environment
- Reduce index complexity
- Enable debug logging
- Simplified security rules

#### Production Environment
- Full index implementation
- Enhanced security monitoring
- Automated backup schedules

#### High-Scale Environment
- Table partitioning by date
- Read replicas for analytics
- Connection pooling configuration

## 🚨 Security Considerations

### Data Protection
- Password hashing (bcrypt recommended)
- Sensitive data in JSONB fields should be encrypted
- Regular security audits of database permissions

### Access Control
- Separate database users for different application components
- Read-only users for analytics and reporting
- Admin users with limited access scope

### Monitoring
- Regular analysis of security logs
- Automated alerting for suspicious activities
- Performance monitoring for query optimization

## 📚 Additional Resources

### PlantUML Documentation
- [PlantUML Class Diagrams](https://plantuml.com/class-diagram)
- [PlantUML Entity Relationship](https://plantuml.com/ie-diagram)

### PostgreSQL Resources
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)

### Database Design
- [Database Design Best Practices](https://www.vertabelo.com/blog/database-design-best-practices/)
- [Security in Database Design](https://owasp.org/www-project-top-ten/)

---

## 🤝 Contributing

To modify or extend the database schema:

1. Update the relevant `.puml` files
2. Regenerate diagrams to verify changes
3. Update the SQL script accordingly
4. Test migrations on development database
5. Update documentation

---

**Built for Cropio Platform - Security-First File Processing with Real-Time Analytics**

*Created by: Himanshu*  
*License: MIT*  
*Version: 2.0.0*
