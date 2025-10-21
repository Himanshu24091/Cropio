# 🚀 Production Deployment Checklist for Cropio

## ✅ Pre-Deployment Checklist

### 📋 **Environment Configuration**
- [ ] **Copy `.env.production` to `.env`** on production server
- [ ] **Set `FLASK_ENV=production`** in environment variables
- [ ] **Set `FLASK_DEBUG=false`** in production
- [ ] **Generate new production secret key**: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] **Update `DATABASE_URL`** with production database credentials
- [ ] **Configure `SSL_CERT_PATH`** and `SSL_KEY_PATH`** for HTTPS
- [ ] **Configure production email settings** (MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD)

### 🗄️ **Database Setup**
- [ ] **Create production database**: `createdb cropio_prod`
- [ ] **Update database password** (not 'root')
- [ ] **Run database migrations**: `flask db upgrade`
- [ ] **Configure database connection pooling**
- [ ] **Set up database backups**
- [ ] **Configure database monitoring**

### 🔒 **Security Configuration**
- [ ] **Enable `SESSION_COOKIE_SECURE=true`**
- [ ] **Enable `SESSION_COOKIE_HTTPONLY=true`**
- [ ] **Set `SESSION_COOKIE_SAMESITE=Lax`**
- [ ] **Configure CSRF protection**
- [ ] **Set up SSL certificates** (Let's Encrypt recommended)
- [ ] **Configure firewall rules**
- [ ] **Set up fail2ban** for intrusion prevention

### 📁 **File System Setup**
- [ ] **Create production directories**: `uploads/`, `outputs/`, `compressed/`, `temp/`, `logs/`
- [ ] **Set proper file permissions**: `chmod 755` for directories, `chmod 644` for files
- [ ] **Configure `.htaccess` files** in upload directories (already done)
- [ ] **Set up log rotation**: `logrotate` configuration
- [ ] **Configure file cleanup scripts**

---

## 🖥️ **Server Setup**

### 🐧 **System Requirements**
- [ ] **Python 3.8+** installed
- [ ] **PostgreSQL 12+** installed and running
- [ ] **Redis server** (optional, for caching)
- [ ] **Nginx** or **Apache** web server
- [ ] **Supervisor** or **systemd** for process management

### 📦 **Application Deployment**
- [ ] **Clone repository** to production server
- [ ] **Create virtual environment**: `python -m venv venv`
- [ ] **Install dependencies**: `pip install -r requirements.txt`
- [ ] **Install missing system dependencies**:
  ```bash
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install python3-dev libpq-dev
  
  # CentOS/RHEL
  sudo yum install python3-devel postgresql-devel
  ```

### 🔧 **Web Server Configuration**

#### **Nginx Configuration** (recommended)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # File upload size limit
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/cropio/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Block direct access to upload directories
    location ~ ^/(uploads|outputs|compressed|temp)/ {
        deny all;
        return 404;
    }
}
```

#### **Gunicorn Configuration**
Create `gunicorn_config.py`:
```python
bind = "127.0.0.1:5000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 2
preload_app = True
```

#### **Supervisor Configuration**
Create `/etc/supervisor/conf.d/cropio.conf`:
```ini
[program:cropio]
command=/path/to/cropio/venv/bin/gunicorn -c gunicorn_config.py app:app
directory=/path/to/cropio
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/cropio.log
environment=PATH="/path/to/cropio/venv/bin"
```

---

## 🏥 **Monitoring & Health Checks**

### 📊 **Application Monitoring**
- [ ] **Configure health check endpoints**: `/api/health`, `/api/status`
- [ ] **Set up uptime monitoring** (Pingdom, UptimeRobot)
- [ ] **Configure error tracking** (Sentry)
- [ ] **Set up log aggregation** (ELK Stack, Splunk)
- [ ] **Configure performance monitoring** (New Relic, DataDog)

### 📝 **Logging Configuration**
- [ ] **Configure log rotation**: `/etc/logrotate.d/cropio`
```bash
/path/to/cropio/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 www-data www-data
    postrotate
        supervisorctl reload cropio
    endscript
}
```

### 🚨 **Alerting Setup**
- [ ] **Configure disk space alerts** (< 80% full)
- [ ] **Configure memory usage alerts** (> 80% used)
- [ ] **Configure application error alerts**
- [ ] **Configure database connection alerts**
- [ ] **Configure SSL certificate expiry alerts**

---

## 🧪 **Testing & Validation**

### ✅ **Pre-Go-Live Tests**
- [ ] **Run production readiness test**: `python production_readiness_test.py`
- [ ] **Test all conversion features**
- [ ] **Verify health check endpoints**: `curl https://your-domain.com/api/health`
- [ ] **Test user registration and login**
- [ ] **Verify email functionality**
- [ ] **Test file uploads and downloads**
- [ ] **Perform load testing** (optional)

### 🚦 **Load Testing** (optional but recommended)
```bash
# Using Apache Bench
ab -n 1000 -c 10 https://your-domain.com/

# Using wrk
wrk -t12 -c400 -d30s https://your-domain.com/
```

---

## 📈 **Performance Optimization**

### ⚡ **Application Performance**
- [ ] **Enable Redis caching** (if applicable)
- [ ] **Configure CDN** for static files (CloudFlare, AWS CloudFront)
- [ ] **Enable gzip compression** in web server
- [ ] **Optimize database queries**
- [ ] **Configure database connection pooling**

### 🗜️ **Static File Optimization**
- [ ] **Minify CSS and JavaScript files**
- [ ] **Optimize image files**
- [ ] **Configure browser caching headers**
- [ ] **Enable HTTP/2** in web server

---

## 🔄 **Backup & Disaster Recovery**

### 💾 **Backup Strategy**
- [ ] **Database backups**: Daily automated backups
- [ ] **File system backups**: User uploaded files
- [ ] **Application backups**: Code and configuration
- [ ] **Test backup restoration** regularly

### 🆘 **Disaster Recovery**
- [ ] **Document recovery procedures**
- [ ] **Test disaster recovery plan**
- [ ] **Set up monitoring for backup failures**
- [ ] **Configure off-site backup storage**

---

## 🚀 **Go-Live Deployment**

### 📋 **Final Deployment Steps**
1. [ ] **Stop application**: `supervisorctl stop cropio`
2. [ ] **Update code**: `git pull origin main`
3. [ ] **Install/update dependencies**: `pip install -r requirements.txt`
4. [ ] **Run database migrations**: `flask db upgrade`
5. [ ] **Update configuration**: Copy `.env.production` to `.env`
6. [ ] **Start application**: `supervisorctl start cropio`
7. [ ] **Verify health check**: `curl https://your-domain.com/api/health`
8. [ ] **Test critical functionality**

### 🔍 **Post-Deployment Verification**
- [ ] **Monitor application logs** for errors
- [ ] **Check system resource usage**
- [ ] **Verify all features working**
- [ ] **Run smoke tests**
- [ ] **Notify stakeholders** of successful deployment

---

## 📚 **Documentation**

### 📖 **Operations Documentation**
- [ ] **Server access credentials** (secure storage)
- [ ] **Deployment procedures**
- [ ] **Troubleshooting guide**
- [ ] **Rollback procedures**
- [ ] **Contact information** for support

### 🔧 **Maintenance Procedures**
- [ ] **Regular security updates**
- [ ] **Application updates**
- [ ] **Database maintenance**
- [ ] **Log cleanup**
- [ ] **SSL certificate renewal**

---

## 🛡️ **Security Hardening**

### 🔒 **System Security**
- [ ] **Disable root SSH access**
- [ ] **Configure SSH key authentication**
- [ ] **Set up fail2ban**
- [ ] **Configure firewall** (ufw, iptables)
- [ ] **Regular security updates**
- [ ] **Configure intrusion detection** (OSSEC, Samhain)

### 🔐 **Application Security**
- [ ] **Regular security scans**
- [ ] **Dependency vulnerability scans**
- [ ] **HTTPS enforcement**
- [ ] **Secure session configuration**
- [ ] **Input validation audits**

---

## ✅ **Production Readiness Checklist Summary**

### 🚦 **Status Indicators**
- 🟢 **Ready for Production**: All critical items completed
- 🟡 **Needs Minor Fixes**: 1-2 non-critical items pending
- 🔴 **Not Ready**: Critical items still pending

### 📊 **Current Status: 🟡 NEEDS MINOR FIXES**
**Completed**: 77.8% production readiness score
**Pending**: Environment configuration (production mode, SSL)

---

**⚠️ IMPORTANT NOTES:**
1. **Never deploy with `FLASK_DEBUG=True` in production**
2. **Always test deployments in staging environment first**
3. **Keep backups before major deployments**
4. **Monitor application closely after deployment**
5. **Have rollback plan ready**

**🎯 Next Steps:**
1. Set up production environment variables
2. Configure SSL certificates
3. Run final production readiness test
4. Deploy to staging for final testing
5. Deploy to production

---

*This checklist ensures your Cropio application is production-ready with enterprise-grade security, performance, and reliability.*
