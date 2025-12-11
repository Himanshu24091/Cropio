# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## About This Project

**Cropio** is a comprehensive SaaS file conversion platform built with Flask. It provides 20+ specialized file converters with a modern web interface, user authentication, role-based permissions, and premium features. The platform supports everything from basic image conversion to advanced features like RAW photo processing, LaTeX compilation, and AI-powered tools.

## Key Architecture Overview

### Application Structure
- **Modular Blueprint Architecture**: Each converter is implemented as a separate Flask blueprint
- **Database-Driven**: PostgreSQL with SQLAlchemy ORM, comprehensive user management
- **Security-First**: CSRF protection, rate limiting, role-based access control
- **Professional Grade**: Logging, error handling, monitoring, and deployment ready

### Major Components
- **Core App** (`app.py`): Main Flask application with professional initialization
- **Blueprints** (`routes/`): Organized by feature type (image/, document/, web_code/, etc.)
- **Database Models** (`models.py`): User management, usage tracking, role-based permissions
- **Configuration** (`config.py`): Environment-aware config with security validation
- **Utilities** (`utils/`, `core/`): Shared functionality and professional systems

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment (REQUIRED)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### Database Management
```bash
# Initialize database with default data
python db_manager.py init

# View database structure
python db_manager.py structure

# Create new migration
python db_manager.py migrate create migration_name

# List all migrations
python db_manager.py migrate list

# Direct database initialization (alternative)
python database/scripts/init_db.py
```

### Running the Application
```bash
# Development mode (with debug, auto-reload)
python app.py

# Production mode with Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app

# Docker deployment
docker-compose up --build
```

### Testing
```bash
# Run system health tests
python test_system_health.py

# Run specific component tests
python test_image_converter.py
python test_file_compressor.py
python test_auth_routes.py

# Integration tests
python tests/integration_phase1.py
```

### System Dependencies (Required for Full Functionality)
```bash
# Windows (using Chocolatey)
choco install ffmpeg tesseract wkhtmltopdf pandoc miktex

# macOS (using Homebrew)  
brew install ffmpeg tesseract-ocr wkhtmltopdf pandoc mactex

# Ubuntu/Debian
sudo apt-get install ffmpeg tesseract-ocr wkhtmltopdf pandoc texlive-latex-recommended
```

## Architecture Deep Dive

### Blueprint Organization
The application is organized into feature-specific blueprints:

**Core Blueprints:**
- `main_routes.py` - Homepage and navigation
- `auth_routes.py` - User authentication (login/register/verify)
- `dashboard_routes.py` - User dashboard and profile management
- `admin.py` - Admin panel with user management

**Converter Categories:**
- **Images**: `image/` (RAW processing, HEIC conversion, GIF handling)
- **Documents**: `document/` (LaTeX, Markdown/HTML conversion)  
- **Web Code**: `web_code/` (HTML snapshots, YAML/JSON)
- **PDF Tools**: Multiple PDF manipulation blueprints
- **Legacy Routes**: Flat structure for older converters

### Database Architecture
**User Management System:**
- `User` - Comprehensive user profiles with subscription tiers
- `UserRole` - Role-based permissions (user/premium/staff/admin)  
- `UserSession` - Database-backed session management
- `ConversionHistory` - Complete audit trail of all conversions
- `UsageTracking` - Daily usage quotas and analytics
- `SystemSettings` - Configuration management

**Key Features:**
- Bcrypt password hashing with legacy migration support
- Role-based file size limits and daily quotas  
- Session security with IP tracking and expiration
- Comprehensive usage analytics for business intelligence

### Security Implementation
**Multi-Layer Security:**
- CSRF protection with Flask-WTF
- Rate limiting per IP and authenticated user
- Role-based access control with fine-grained permissions
- Secure file upload validation and quarantine
- Professional logging and error monitoring

### Configuration Management
**Environment-Aware Config:**
- `DevelopmentConfig` - Local development with debug features
- `ProductionConfig` - Hardened security, performance optimization  
- `TestingConfig` - In-memory database, disabled security for testing
- Automatic validation of critical security settings

## File Processing Architecture

### Converter Categories
**Phase 1 (Core):** Basic image, PDF, document, Excel converters
**Phase 1.5 (Advanced):** RAW images, HEIC support, GIF processing, LaTeX, Markdown/HTML, YAML/JSON, HTML snapshots
**Phase 2 (Premium):** AI-powered tools (watermark removal, background changing, enhancement)

### Processing Pipeline
1. **Upload Validation**: File type, size, and content validation
2. **Quarantine**: Temporary secure storage during processing
3. **Processing**: Format-specific conversion with error handling
4. **Output Management**: Secure delivery and cleanup
5. **Usage Tracking**: Analytics and quota management

### Specialized Processors
- **RAW Images** (`utils/image/raw_processor.py`): Smart format detection, metadata preservation
- **Video/GIF** (`utils/video/`): FFmpeg integration for format conversion
- **LaTeX** (`utils/latex_utils.py`): XeLaTeX compilation with dependency management
- **Web Content** (`utils/web_code/`): HTML snapshots with screenshot capability

## Development Guidelines

### Adding New Converters
1. Create blueprint in appropriate category folder (`routes/image/`, `routes/document/`, etc.)
2. Implement processing logic in `utils/` with error handling
3. Add frontend templates and JavaScript in organized structure
4. Register blueprint in `app.py` with proper error handling
5. Update navigation and user interface as needed

### Database Changes
1. Create migration using `python db_manager.py migrate create migration_name`
2. Edit generated migration file in `database/migrations/`
3. Update models in `models.py` if needed
4. Test migration in development environment

### Security Considerations
- All file uploads must use `allowed_file()` validation
- User input requires proper sanitization and validation
- New admin features need role-based permission checks
- Rate limiting should be applied to resource-intensive operations

## Key Configuration Files

### Environment Configuration
- `.env` - Environment variables (copy from `.env.example`)
- `config.py` - Application configuration with security validation
- `requirements.txt` - Production dependencies with pinned versions
- `docker-compose.yml` - Multi-service deployment configuration

### Critical Environment Variables
```bash
# Database
DATABASE_URL=postgresql://postgres:root@localhost:5432/cropio_dev
FLASK_SECRET_KEY=your-secure-secret-key

# Email (for user verification)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379/1
```

## Common Development Tasks

### User Management
```python
# Create admin user programmatically
from models import User, db
admin = User(username='admin', email='admin@example.com')
admin.set_password('secure_password')
admin.assign_role('admin')
db.session.add(admin)
db.session.commit()
```

### Adding Rate Limits
```python
from middleware import rate_limit
@route.route('/api/convert')
@rate_limit('10 per minute')
def convert_endpoint():
    # Processing logic
```

### Usage Tracking
```python
from middleware import track_conversion_result
@track_conversion_result
def process_file():
    # Conversion logic
    # Usage automatically tracked via decorator
```

## Production Deployment

### Docker Deployment (Recommended)
```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f web

# Scale web workers
docker-compose up --scale web=3
```

### Manual Deployment
```bash
# Install production dependencies
pip install -r requirements.txt

# Set production environment
export FLASK_ENV=production
export DATABASE_URL=postgresql://user:pass@host:5432/db

# Run with Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 \
         --worker-class sync --max-requests 1000 \
         --max-requests-jitter 100 --preload \
         --access-logfile - --error-logfile - \
         app:app
```

## Business Logic

### Subscription Tiers
- **Guest** - No registration, limited features, 50MB files
- **Free** - Registration required, 5 conversions/day, 100MB files
- **Premium** - Unlimited conversions, 5GB files, AI features
- **Staff/Admin** - System management capabilities

### Usage Quotas
- Tracked daily per user with automatic reset
- Role-based limits with premium override capability  
- Comprehensive analytics for business intelligence
- API endpoints for quota checking and management

## Important Notes

- **Virtual Environment Required**: Application will attempt to auto-exec with correct venv
- **Database Password**: Default development password is "root"  
- **System Dependencies**: Many converters require external tools (FFmpeg, Tesseract, etc.)
- **LaTeX Processing**: Requires XeLaTeX for PDF generation from notebooks
- **File Cleanup**: Background scheduler removes temporary files every 30 minutes
- **Session Security**: Database-backed sessions with IP tracking and expiration

This platform represents a complete SaaS solution with professional-grade architecture, security, and deployment capabilities. The modular design allows for easy extension and maintenance while providing comprehensive file processing capabilities.
