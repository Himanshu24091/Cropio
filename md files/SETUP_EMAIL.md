# Email Configuration Setup Guide

## Quick Email Setup for Cropio

### Step 1: Enable 2-Factor Authentication on Gmail
1. Go to your Google Account settings
2. Enable 2-Factor Authentication

### Step 2: Generate App Password
1. Go to Google Account → Security → 2-Step Verification → App passwords
2. Select "Mail" and your device
3. Copy the generated 16-character password

### Step 3: Update .env file
Open `.env` file and update:
```bash
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-character-app-password
```

### Step 4: Test Email (Optional)
Run this command to test email functionality:
```bash
python -c "
import os
from utils.email_service import mail
from flask import Flask
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
    print('✅ Email configured successfully!')
else:
    print('❌ Please set MAIL_USERNAME and MAIL_PASSWORD in .env file')
"
```

## Alternative Email Providers

### Using Outlook/Hotmail:
```bash
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
```

### Using Custom SMTP:
```bash
MAIL_SERVER=your-smtp-server.com
MAIL_PORT=587
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-password
```

## Security Notes
- Never commit .env file to version control
- Use App Passwords, not regular passwords
- Consider using environment variables in production
