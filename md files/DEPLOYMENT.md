# Cropio SaaS Platform - Professional Deployment Guide

This guide provides comprehensive instructions for deploying Cropio in production environments.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- PostgreSQL 13+
- Redis 6+
- Python 3.11+
- Node.js 18+ (for frontend builds)

### Environment Setup

1. **Copy environment configuration:**
```bash
cp .env.example .env
```

2. **Configure your environment variables in `.env`:**
```env
# Required - Generate with: python -c "import secrets; print(secrets.token_hex(32))"
FLASK_SECRET_KEY=your-super-secret-key-min-32-chars-long-and-random

# Database
DATABASE_URL=postgresql://cropio:secure_password@localhost:5432/cropio_prod

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Site Configuration
SITE_NAME=Cropio
SUPPORT_EMAIL=support@yourdomain.com

# Redis
REDIS_URL=redis://localhost:6379/0

# Optional - Error Tracking
SENTRY_DSN=your-sentry-dsn
```

## 🐳 Docker Deployment (Recommended)

### Production Deployment with Docker Compose

1. **Build and start services:**
```bash
docker-compose up -d
```

2. **Initialize database:**
```bash
docker-compose exec web flask db upgrade
docker-compose exec web python -c "from models import init_database; init_database()"
```

3. **Create admin user:**
```bash
docker-compose exec web python -c "
from models import db, User
from datetime import date, timedelta
admin = User(
    username='admin',
    email='admin@yourdomain.com',
    subscription_tier='premium',
    subscription_start=date.today(),
    subscription_end=date.today() + timedelta(days=365),
    email_verified=True,
    is_active=True,
    is_admin=True
)
admin.set_password('your-secure-admin-password')
db.session.add(admin)
db.session.commit()
print('Admin user created successfully')
"
```

### Single Container Deployment

```bash
# Build image
docker build -t cropio:latest .

# Run with external database
docker run -d \
  --name cropio \
  -p 5000:5000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/dbname \
  -e FLASK_SECRET_KEY=your-secret-key \
  -e REDIS_URL=redis://redis-host:6379/0 \
  -v /path/to/uploads:/app/uploads \
  -v /path/to/logs:/app/logs \
  cropio:latest
```

## 🖥️ Traditional Server Deployment

### 1. System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y postgresql-client libpq-dev
sudo apt install -y redis-server
sudo apt install -y libmagic1 libmagic-dev
sudo apt install -y poppler-utils  # For PDF processing
sudo apt install -y nginx  # For reverse proxy
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3.11 python3.11-devel
sudo yum install -y postgresql-devel
sudo yum install -y redis
sudo yum install -y file-devel
sudo yum install -y poppler-utils
sudo yum install -y nginx
```

### 2. Application Setup

```bash
# Clone repository
git clone <your-repo-url> cropio
cd cropio

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Initialize database
flask db upgrade
python -c "from models import init_database; init_database()"
```

### 3. Process Management with Systemd

Create `/etc/systemd/system/cropio.service`:
```ini
[Unit]
Description=Cropio SaaS Platform
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=cropio
Group=cropio
WorkingDirectory=/opt/cropio
Environment=FLASK_ENV=production
ExecStart=/opt/cropio/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --max-requests 1000 --preload app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable cropio
sudo systemctl start cropio
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/cropio`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # File upload size limit
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for file processing
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }
    
    # Static files
    location /static {
        alias /opt/cropio/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/cropio /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔧 Database Setup

### PostgreSQL Configuration

```sql
-- Create database and user
CREATE USER cropio WITH PASSWORD 'secure_password';
CREATE DATABASE cropio OWNER cropio;
GRANT ALL PRIVILEGES ON DATABASE cropio TO cropio;

-- Connect to cropio database
\c cropio

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO cropio;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cropio;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cropio;
```

### Database Performance Tuning

Add to PostgreSQL config:
```ini
# postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

## 📊 Monitoring & Logging

### Log Management

```bash
# Create log rotation config
sudo tee /etc/logrotate.d/cropio << EOF
/opt/cropio/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 cropio cropio
    postrotate
        systemctl reload cropio
    endscript
}
EOF
```

### Health Checks

```bash
# Add to crontab for monitoring
*/5 * * * * curl -f http://localhost:5000/admin/monitoring/health || echo "Cropio health check failed" | mail -s "Cropio Alert" admin@yourdomain.com
```

## 🔒 Security Hardening

### SSL/TLS Configuration

```bash
# Generate strong SSL certificate with Let's Encrypt
sudo certbot --nginx -d yourdomain.com
```

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Restrict PostgreSQL and Redis to localhost only
sudo ufw deny 5432
sudo ufw deny 6379
```

### File Permissions

```bash
# Set secure permissions
sudo chown -R cropio:cropio /opt/cropio
sudo chmod -R 750 /opt/cropio
sudo chmod -R 755 /opt/cropio/static
sudo chmod 600 /opt/cropio/.env
```

## 🚀 Performance Optimization

### Gunicorn Configuration

Create `gunicorn.conf.py`:
```python
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
keepalive = 5
timeout = 30
graceful_timeout = 30
```

### Redis Configuration

```bash
# redis.conf optimization
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## 📋 Maintenance Tasks

### Regular Maintenance

```bash
# Weekly tasks (add to cron)
0 2 * * 0 /opt/cropio/maintenance.sh

# maintenance.sh
#!/bin/bash
cd /opt/cropio
source venv/bin/activate

# Cleanup old files
python -c "
from utils.helpers import cleanup_files
from flask import Flask
app = Flask(__name__)
with app.app_context():
    cleanup_files()
"

# Backup database
pg_dump cropio > /backup/cropio_$(date +%Y%m%d).sql

# Log rotation
systemctl reload rsyslog
```

### Database Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backup/cropio"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
pg_dump -h localhost -U cropio cropio | gzip > $BACKUP_DIR/cropio_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -type f -mtime +30 -delete
```

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Error:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql
# Check connection
psql -h localhost -U cropio -d cropio
```

2. **Redis Connection Error:**
```bash
# Check Redis status
sudo systemctl status redis
# Test connection
redis-cli ping
```

3. **File Permission Issues:**
```bash
# Fix permissions
sudo chown -R cropio:cropio /opt/cropio
sudo chmod -R 755 /opt/cropio/uploads
```

4. **SSL Certificate Issues:**
```bash
# Renew Let's Encrypt certificates
sudo certbot renew --dry-run
```

### Log Locations

- Application logs: `/opt/cropio/logs/`
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`
- PostgreSQL logs: `/var/log/postgresql/`

## 📞 Support

For deployment assistance:
- GitHub Issues: [Repository URL]
- Documentation: [Docs URL]
- Email: support@yourdomain.com

## 📝 License

[Your License Information]
