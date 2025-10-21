# 🔐 Render Environment Variables - Step by Step Guide

## पहले ये Secret Keys Generate करो (Local Computer पर)

### Terminal/Command Prompt खोलो और ये commands run करो:

```bash
# Command 1: FLASK_SECRET_KEY generate karne ke liye
python -c "import secrets; print(secrets.token_hex(32))"
```
**Output कुछ ऐसा आएगा:** 
```
a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456
```
☝️ **इसे copy करके notepad में save कर लो!**

---

```bash
# Command 2: SECURITY_PASSWORD_SALT generate karne के लिए
python -c "import secrets; print(secrets.token_hex(16))"
```
**Output कुछ ऐसा आएगा:**
```
a1b2c3d4e5f6789012345678901234ab
```
☝️ **इसे भी copy करके notepad में save कर लो!**

---

## अब Render पर जाओ और ये Steps Follow करो:

### Step 1: PostgreSQL Database बनाओ

1. **Render Dashboard** खोलो
2. **New +** button पर click करो
3. **PostgreSQL** select करो
4. Form भरो:
   ```
   Name: cropio-db
   Database: cropio
   User: cropio
   Region: Singapore (या अपने closest region)
   PostgreSQL Version: 15 (default)
   Plan: FREE
   ```
5. **Create Database** पर click करो
6. Database बन जाने के बाद, **Internal Database URL** copy करो
   - यह कुछ ऐसा होगा: `postgresql://cropio:long_password@dpg-xxxxx:5432/cropio`
   - ☝️ **Notepad में save करो!**

---

### Step 2: Redis Database बनाओ (Upstash - Free)

1. नया tab खोलो: https://upstash.com/signup
2. Account बनाओ (Google से sign up कर सकते हो)
3. **Create Database** पर click करो
4. Form भरो:
   ```
   Name: cropio-redis
   Type: Regional
   Region: ap-south-1 (Mumbai) या closest
   ```
5. **Create** पर click करो
6. Database खुल जाने के बाद:
   - **REST API** section में जाओ
   - **UPSTASH_REDIS_REST_URL** के नीचे जो URL दिख रहा है उसे copy करो
   - Format होगा: `redis://default:long_password@us1-xxxxx.upstash.io:6379`
   - ☝️ **Notepad में save करो!**

---

### Step 3: Render पर Web Service बनाओ

1. Render Dashboard पर वापस जाओ
2. **New +** → **Web Service**
3. अपना **GitHub repository** connect करो
4. Settings भरो:
   ```
   Name: cropio
   Environment: Python 3
   Region: Singapore (database जैसा region)
   Branch: main
   ```
5. **Build Command** में लिखो:
   ```
   ./render-build.sh
   ```
6. **Start Command** में लिखो:
   ```
   gunicorn --config gunicorn_config.py app:app
   ```
7. **Plan** में **Free** select करो

---

### Step 4: Environment Variables Add करो

अब सबसे important part! **Environment** section में scroll down करो।

**"Add Environment Variable"** button दिखेगा। हर variable के लिए:
- Left side में **Key** (variable का नाम)
- Right side में **Value** (variable की value)

---

## 📋 EXACTLY ये Variables Add करो:

### Variable 1:
```
Key:   FLASK_SECRET_KEY
Value: <वो 64 character वाला key जो आपने पहले generate किया था>
```

### Variable 2:
```
Key:   DATABASE_URL
Value: <PostgreSQL का Internal URL जो आपने copy किया था>
```

### Variable 3:
```
Key:   REDIS_URL
Value: <Upstash से जो Redis URL copy किया था>
```

### Variable 4:
```
Key:   FLASK_ENV
Value: production
```

### Variable 5:
```
Key:   SESSION_TYPE
Value: redis
```

### Variable 6:
```
Key:   PERMANENT_SESSION_LIFETIME
Value: 86400
```

### Variable 7:
```
Key:   WTF_CSRF_ENABLED
Value: true
```

### Variable 8:
```
Key:   SECURITY_PASSWORD_SALT
Value: <वो 32 character वाला salt जो आपने generate किया था>
```

### Variable 9:
```
Key:   MAX_CONTENT_LENGTH
Value: 52428800
```

### Variable 10:
```
Key:   UPLOAD_FOLDER
Value: uploads
```

### Variable 11:
```
Key:   SITE_NAME
Value: Cropio
```

### Variable 12:
```
Key:   SUPPORT_EMAIL
Value: support@cropio.com
```
(या अपना email डाल सकते हो)

---

## 🎯 Visual Example (कैसे add करें):

```
┌─────────────────────────────────────────────────────────────┐
│  Environment Variables                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Key                          Value                          │
│  ┌─────────────────────┐    ┌──────────────────────────┐   │
│  │ FLASK_SECRET_KEY    │    │ a1b2c3d4e5f6...          │   │
│  └─────────────────────┘    └──────────────────────────┘   │
│                                                              │
│  ┌─────────────────────┐    ┌──────────────────────────┐   │
│  │ DATABASE_URL        │    │ postgresql://cropio:...  │   │
│  └─────────────────────┘    └──────────────────────────┘   │
│                                                              │
│  ┌─────────────────────┐    ┌──────────────────────────┐   │
│  │ REDIS_URL           │    │ redis://default:...      │   │
│  └─────────────────────┘    └──────────────────────────┘   │
│                                                              │
│  ┌─────────────────────┐    ┌──────────────────────────┐   │
│  │ FLASK_ENV           │    │ production               │   │
│  └─────────────────────┘    └──────────────────────────┘   │
│                                                              │
│  ... (aur bhi variables aise hi add karo)                   │
│                                                              │
│  [+ Add Environment Variable]                               │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Quick Checklist

Copy-paste करके check karo ki sab add kiya hai:

- [ ] `FLASK_SECRET_KEY` - Generated key
- [ ] `DATABASE_URL` - PostgreSQL internal URL
- [ ] `REDIS_URL` - Upstash Redis URL
- [ ] `FLASK_ENV` - production
- [ ] `SESSION_TYPE` - redis
- [ ] `PERMANENT_SESSION_LIFETIME` - 86400
- [ ] `WTF_CSRF_ENABLED` - true
- [ ] `SECURITY_PASSWORD_SALT` - Generated salt
- [ ] `MAX_CONTENT_LENGTH` - 52428800
- [ ] `UPLOAD_FOLDER` - uploads
- [ ] `SITE_NAME` - Cropio
- [ ] `SUPPORT_EMAIL` - support@cropio.com

**Total: 12 variables**

---

## 🚀 Step 5: Deploy करो!

सब variables add करने के बाद:

1. **Create Web Service** button पर click करो
2. Build process शुरू होगा (5-10 minutes लगेंगे)
3. Logs में देखते रहो - सब green होना चाहिए
4. Build complete होने पर URL मिलेगा

---

## 🔍 Optional Variables (बाद में add कर सकते हो)

### Email भेजने के लिए (Gmail):

```
Key:   MAIL_SERVER
Value: smtp.gmail.com

Key:   MAIL_PORT
Value: 587

Key:   MAIL_USE_TLS
Value: true

Key:   MAIL_USERNAME
Value: your-email@gmail.com

Key:   MAIL_PASSWORD
Value: <Gmail app password - 16 digit code>
```

**Gmail App Password कैसे बनाएं:**
1. Google Account → Security
2. 2-Step Verification ON करो
3. App Passwords → Generate
4. वो password यहां use करो

---

## 📱 After Deployment - Database Initialize करो

Deploy होने के बाद:

1. Render Dashboard → अपनी web service → **Shell** tab
2. ये commands एक-एक करके run करो:

```bash
# Command 1: Database schema बनाओ
flask db upgrade

# Command 2: Tables initialize करो
python -c "from models import init_database; init_database()"

# Command 3: Admin user बनाओ
python -c "
from models import db, User
from datetime import date, timedelta

admin = User(
    username='admin',
    email='admin@cropio.com',
    subscription_tier='premium',
    subscription_start=date.today(),
    subscription_end=date.today() + timedelta(days=365),
    email_verified=True,
    is_active=True,
    is_admin=True
)
admin.set_password('Admin@123')
db.session.add(admin)
db.session.commit()
print('Admin created!')
"
```

---

## ⚠️ Common Mistakes (ये galti mat karna):

❌ **DATABASE_URL में External URL use kiya**
✅ **Internal Database URL use karo**

❌ **REDIS_URL में typo**
✅ **Pura URL copy-paste karo**

❌ **SECRET_KEY chota (short) hai**
✅ **python command se hi generate karo**

❌ **Variables में space daal diya**
✅ **Exactly aise hi likho jaise bataya hai**

---

## 🆘 Problem Ho Toh:

### Build fail ho raha hai?
```bash
# Local check karo:
python check_render_ready.py
```

### Database connect nahi ho raha?
- Check: **Internal** Database URL use kiya?
- Check: Format sahi hai? `postgresql://` se start?

### Redis error aa raha hai?
- Check: Upstash database active hai?
- Check: URL format: `redis://default:pass@host:port`

---

**Bas! Ab sab ready hai. Create Web Service पर click karo!** 🎉

Agar कोई doubt हो तो पूछ लो! 💪

