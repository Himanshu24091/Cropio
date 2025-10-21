# 🚀 Cropio - Render Configuration Details (हिंदी + English)

## 📌 Exact Versions Being Used

### Python Version
```
Python 3.11.5
```
**Source**: `runtime.txt`

### Key Framework Versions (from requirements.txt)
```
Flask==3.0.0
Werkzeug==3.0.1
SQLAlchemy==2.0.23
gunicorn==21.2.0
cryptography==42.0.8  ✅ FIXED
```

---

## 🔐 Environment Variables - Complete List

### ✅ REQUIRED (जरूरी - बिना इनके app नहीं चलेगी)

#### 1. **FLASK_SECRET_KEY** (सबसे जरूरी!)
```bash
FLASK_SECRET_KEY=<generate-this-first>
```
**Generate kaise karein:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
**Output Example**: `a1b2c3d4e5f6...` (64 characters)

---

#### 2. **DATABASE_URL** (Database connection)
```bash
DATABASE_URL=postgresql://username:password@host:port/dbname
```
**Render से कहां से मिलेगा:**
- Render Dashboard → PostgreSQL Database → **Internal Database URL** copy करो
- Example: `postgresql://cropio:xyz@dpg-abc123:5432/cropio_db`

**⚠️ Important**: 
- Use **Internal URL** (not External)
- Format: `postgresql://` se start hona chahiye

---

#### 3. **REDIS_URL** (Session & Rate limiting के लिए)
```bash
REDIS_URL=redis://default:password@host:port
```
**Kahan से लें:**
- **Upstash** (FREE): https://upstash.com
- **Redis Cloud** (30MB FREE): https://redis.com/try-free

Example: `redis://default:abc123@us1-example.upstash.io:6379`

---

#### 4. **FLASK_ENV** (Environment type)
```bash
FLASK_ENV=production
```
**Fixed value hai - change mat karna!**

---

### 🔧 RECOMMENDED (जरूर set करना चाहिए)

#### 5. **SESSION_TYPE** (Session storage)
```bash
SESSION_TYPE=redis
```

#### 6. **PERMANENT_SESSION_LIFETIME** (Session timeout)
```bash
PERMANENT_SESSION_LIFETIME=86400
```
(86400 = 24 hours in seconds)

#### 7. **WTF_CSRF_ENABLED** (Security)
```bash
WTF_CSRF_ENABLED=true
```

#### 8. **MAX_CONTENT_LENGTH** (Max upload size)
```bash
MAX_CONTENT_LENGTH=52428800
```
(50MB in bytes, free tier limit)

#### 9. **UPLOAD_FOLDER** (Upload directory)
```bash
UPLOAD_FOLDER=uploads
```

#### 10. **SECURITY_PASSWORD_SALT** (Password hashing)
```bash
SECURITY_PASSWORD_SALT=<generate-random-string>
```
**Generate kaise karein:**
```bash
python -c "import secrets; print(secrets.token_hex(16))"
```

---

### 📧 OPTIONAL - Email Configuration (बाद में भी set कर सकते हो)

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
```

**Gmail app password कैसे बनाएं:**
1. Google Account → Security
2. 2-Step Verification enable करो
3. App Passwords → Generate
4. वो password यहां use करो

---

### 📊 OPTIONAL - Monitoring (Production के लिए recommended)

```bash
# Sentry error tracking (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/123456

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

---

### 💳 OPTIONAL - Payment Gateways (जब payment add करोगे)

```bash
# Razorpay (India)
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxx

# Stripe (International)
STRIPE_PUBLIC_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
```

---

## 📋 Environment Variables - Copy-Paste Template

### Render Dashboard में exactly ये variables add karo:

```bash
# === REQUIRED ===
FLASK_SECRET_KEY=<generate-with-python-command>
DATABASE_URL=<copy-from-render-postgres>
REDIS_URL=<copy-from-upstash>
FLASK_ENV=production

# === SESSION & SECURITY ===
SESSION_TYPE=redis
PERMANENT_SESSION_LIFETIME=86400
WTF_CSRF_ENABLED=true
SECURITY_PASSWORD_SALT=<generate-with-python-command>

# === FILE UPLOAD ===
MAX_CONTENT_LENGTH=52428800
UPLOAD_FOLDER=uploads

# === SITE CONFIG ===
SITE_NAME=Cropio
SUPPORT_EMAIL=support@cropio.com
```

---

## 🎯 Step-by-Step Setup Order

### Step 1: Generate Secret Keys (पहले ये local machine पर run करो)
```bash
# Terminal में run करो:
python -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"
python -c "import secrets; print('SECURITY_PASSWORD_SALT=' + secrets.token_hex(16))"
```
**Output copy करके safe रखो!**

---

### Step 2: Create PostgreSQL on Render
1. Render Dashboard → **New** → **PostgreSQL**
2. Name: `cropio-db`
3. Database: `cropio`
4. Region: Choose closest (Singapore for India)
5. Plan: **Free**
6. Create Database
7. **Copy Internal Database URL** → Save it!

---

### Step 3: Create Redis (Upstash - Free Forever)
1. Go to: https://upstash.com/signup
2. Create account
3. Create Database:
   - Name: `cropio-redis`
   - Region: Choose closest
   - Type: **Regional** (free)
4. **Copy Redis URL** → Save it!

---

### Step 4: Add Environment Variables in Render

Render Dashboard → Web Service → **Environment** tab:

```
Variable Name              | Value
---------------------------|----------------------------------
FLASK_SECRET_KEY           | <from step 1>
DATABASE_URL               | <from step 2>
REDIS_URL                  | <from step 3>
FLASK_ENV                  | production
SESSION_TYPE               | redis
PERMANENT_SESSION_LIFETIME | 86400
WTF_CSRF_ENABLED          | true
SECURITY_PASSWORD_SALT     | <from step 1>
MAX_CONTENT_LENGTH         | 52428800
UPLOAD_FOLDER              | uploads
SITE_NAME                  | Cropio
SUPPORT_EMAIL              | support@cropio.com
```

---

## 🔍 Quick Verification Commands

### Check kar lo sab kuch set hai ya nahi:

```bash
# Local check (before deploy)
python check_render_ready.py
```

**Expected output:**
```
[SUCCESS] All checks passed! Ready to deploy to Render.
```

---

## ❓ Troubleshooting - Common Issues

### Issue 1: "SECRET_KEY is not set"
**Fix:** 
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Output ko `FLASK_SECRET_KEY` में paste करो

---

### Issue 2: "Database connection failed"
**Check:**
- ✅ Use **Internal Database URL** (not External)
- ✅ Format: `postgresql://user:pass@host:5432/dbname`
- ✅ Database instance running hai

---

### Issue 3: "Redis connection refused"
**Check:**
- ✅ Redis URL format: `redis://default:pass@host:port`
- ✅ Upstash database active hai
- ✅ No typos in URL

---

### Issue 4: Build fails
**Common reasons:**
- Missing environment variables
- Wrong Python version (should be 3.11.5)
- Dependency conflicts

**Solution:**
```bash
# Locally test first:
python check_render_ready.py
```

---

## 📱 After Deployment - Initialize Database

Render Dashboard → Shell tab:

```bash
# Step 1: Run migrations
flask db upgrade

# Step 2: Initialize database
python -c "from models import init_database; init_database()"

# Step 3: Create admin user
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
admin.set_password('YourStrongPassword123!')
db.session.add(admin)
db.session.commit()
print('Admin created successfully!')
"
```

---

## ✅ Final Checklist

- [ ] Python 3.11.5 set in runtime.txt
- [ ] SECRET_KEY generated and set
- [ ] PostgreSQL database created on Render
- [ ] Redis created on Upstash
- [ ] DATABASE_URL copied to environment
- [ ] REDIS_URL copied to environment
- [ ] All required env variables set
- [ ] Build command: `./render-build.sh`
- [ ] Start command: `gunicorn --config gunicorn_config.py app:app`
- [ ] Deploy successful
- [ ] Database initialized
- [ ] Admin user created
- [ ] Can login successfully

---

## 🚀 Commands Summary

### Build Command (Render में):
```bash
./render-build.sh
```

### Start Command (Render में):
```bash
gunicorn --config gunicorn_config.py app:app
```

### Generate Secrets (Local में):
```bash
python -c "import secrets; print(secrets.token_hex(32))"
python -c "import secrets; print(secrets.token_hex(16))"
```

### Pre-deployment Check (Local में):
```bash
python check_render_ready.py
```

---

**Sab kuch ready hai! Ab deploy karo!** 🎉

Agar koi problem aaye toh `RENDER_DEPLOYMENT.md` dekho ya message karo!

