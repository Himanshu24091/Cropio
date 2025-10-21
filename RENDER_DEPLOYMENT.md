# 🚀 Cropio - Render Deployment Guide

## ✅ Quick Deployment Steps

### 1. **Create Render Account**
- Sign up at [render.com](https://render.com)
- Connect your GitHub/GitLab repository

### 2. **Create PostgreSQL Database (Free)**
1. Go to Render Dashboard → New → PostgreSQL
2. Name: `cropio-db`
3. Database: `cropio`
4. User: `cropio`
5. Region: Choose closest to you
6. Plan: **Free** (expires after 90 days)
7. Click "Create Database"
8. **Copy the Internal Database URL** (starts with `postgresql://`)

### 3. **Create Redis Instance**

**Option A: Upstash Redis (Free Forever)**
1. Go to [upstash.com](https://upstash.com)
2. Create account and new Redis database
3. Copy the Redis URL (format: `redis://default:password@host:port`)

**Option B: Redis Cloud (Free 30MB)**
1. Go to [redis.com/try-free](https://redis.com/try-free/)
2. Create free database
3. Copy connection URL

### 4. **Create Web Service**
1. Go to Render Dashboard → New → Web Service
2. Connect your repository
3. Configure:
   - **Name**: `cropio`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Environment**: `Python 3`
   - **Build Command**: `./render-build.sh`
   - **Start Command**: `gunicorn --config gunicorn_config.py app:app`
   - **Plan**: **Free**

### 5. **Environment Variables**

Add these in Render Dashboard → Environment:

#### Required Variables
```bash
# Flask Configuration
FLASK_SECRET_KEY=<generate-with-python-secrets-token-hex-32>
FLASK_ENV=production

# Database (from step 2)
DATABASE_URL=<your-postgres-internal-url>

# Redis (from step 3)
REDIS_URL=<your-redis-url>

# Session Configuration
SESSION_TYPE=redis
PERMANENT_SESSION_LIFETIME=86400

# Security
SECURITY_PASSWORD_SALT=<generate-random-salt>
WTF_CSRF_ENABLED=true

# File Upload
MAX_CONTENT_LENGTH=52428800
UPLOAD_FOLDER=uploads
```

#### Optional Variables (Email, Monitoring)
```bash
# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Monitoring (Optional)
SENTRY_DSN=<your-sentry-dsn>
```

### 6. **Generate Secret Keys**

Run locally to generate secure keys:
```python
python -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('SECURITY_PASSWORD_SALT=' + secrets.token_hex(16))"
```

### 7. **Deploy**
- Click "Create Web Service"
- Wait for build (5-10 minutes on free tier)
- Monitor logs for any errors

### 8. **Initialize Database**

After deployment, run these commands via Render Shell:

1. Go to your web service → Shell
2. Run:
```bash
# Initialize database schema
flask db upgrade

# Create tables
python -c "from models import init_database; init_database()"

# Create admin user (optional)
python -c "
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
admin.set_password('ChangeThisPassword123!')
db.session.add(admin)
db.session.commit()
print('✅ Admin user created')
"
```

---

## ⚠️ Free Tier Limitations

### Resource Constraints
- **RAM**: 512 MB (1 Gunicorn worker only)
- **Build time**: 15 minutes max
- **Sleep after inactivity**: 15 minutes
- **Cold start**: 30-60 seconds
- **Bandwidth**: 100 GB/month
- **Persistent storage**: No (use external storage for uploads)

### Disabled Features on Free Tier
Due to system dependency limitations:
- ❌ LaTeX to PDF conversion (no TeX Live)
- ❌ Pandoc document conversion
- ❌ OCR text extraction (no Tesseract)
- ❌ Advanced video processing (no FFmpeg)

### Working Features
- ✅ Image conversion (PNG, JPG, WebP, etc.)
- ✅ Basic PDF operations (merge, split, compress)
- ✅ Excel/CSV conversions
- ✅ Document conversions (DOCX, TXT)
- ✅ User authentication
- ✅ File compression
- ✅ Image cropping/editing

---

## 🔧 Troubleshooting

### Build Fails with Memory Error
**Solution**: The dependencies are too heavy. Consider:
1. Removing unused converters from `requirements.txt`
2. Using `--no-cache-dir` flag (already in build script)
3. Upgrading to Render Starter ($7/month) with 512MB → 2GB RAM

### Database Connection Error
**Check**:
1. Environment variable `DATABASE_URL` is set correctly
2. Using **Internal Database URL** (not External)
3. Database instance is running

### Redis Connection Error
**Check**:
1. `REDIS_URL` format: `redis://user:password@host:port`
2. Redis instance is accessible
3. Firewall allows connections

### App Sleeps After Inactivity
**Free tier limitation**: Service sleeps after 15 min of inactivity
**Solutions**:
- Upgrade to paid plan ($7/month)
- Use external uptime monitor (UptimeRobot, etc.)
- Accept cold starts for free tier

### File Upload Persists After Restart
**Not on free tier**: Free tier has ephemeral storage
**Solutions**:
- Use external storage (AWS S3, Cloudinary)
- Implement cleanup on startup
- Upgrade to paid plan with persistent disk

---

## 📊 Monitoring Your Deployment

### Health Check Endpoint
```
https://your-app.onrender.com/admin/monitoring/health
```

### View Logs
```bash
# In Render Dashboard
Logs → Real-time logs
```

### Metrics
Check Render Dashboard for:
- Response times
- Memory usage
- Request counts
- Error rates

---

## 🚀 Upgrading to Paid Plan

For production use, consider Render Starter:

### Starter Plan Benefits ($7/month)
- ✅ 512 MB → **2 GB RAM** (run 4 workers)
- ✅ No sleep/cold starts
- ✅ Persistent disk (up to 1 GB free)
- ✅ Custom domains
- ✅ Faster builds

### Add-ons
- **Redis**: $5/month (25MB)
- **PostgreSQL**: $7/month (persistent, no expiration)
- **Disk Storage**: Free up to 1GB, then $0.25/GB/month

---

## 🔐 Security Checklist

- [ ] Changed default admin password
- [ ] Set strong `FLASK_SECRET_KEY`
- [ ] Enabled HTTPS (automatic on Render)
- [ ] Set up CSRF protection
- [ ] Configured rate limiting
- [ ] Set up error monitoring (Sentry)
- [ ] Regular database backups
- [ ] Environment variables secured

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Render Free Tier Limits](https://render.com/docs/free)
- [Flask Deployment Best Practices](https://flask.palletsprojects.com/en/latest/deploying/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/settings.html)

---

## 💡 Tips for Free Tier Success

1. **Minimize Dependencies**: Only install what you need
2. **Use CDN**: Host static assets on Cloudinary/Imgur
3. **Optimize Images**: Compress before uploading
4. **Cache Aggressively**: Use Redis for caching
5. **Monitor Memory**: Watch for memory leaks
6. **Accept Cold Starts**: Normal for free tier
7. **Regular Cleanup**: Delete old files to save space

---

## 🆘 Getting Help

- **Render Support**: [render.com/support](https://render.com/support)
- **Community Forum**: [community.render.com](https://community.render.com)
- **GitHub Issues**: [Your repo]/issues

---

## ✅ Deployment Checklist

- [ ] PostgreSQL database created
- [ ] Redis instance configured
- [ ] Environment variables set
- [ ] Build script updated
- [ ] Gunicorn config created
- [ ] Repository connected
- [ ] Service deployed
- [ ] Database initialized
- [ ] Admin user created
- [ ] Health check passes
- [ ] Login tested
- [ ] File upload tested

---

**Good luck with your deployment! 🚀**

