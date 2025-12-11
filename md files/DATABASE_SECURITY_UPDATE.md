# Database Security Update Guide

## ⚠️ CRITICAL: Change Default Database Password

Your current database is using the default "root" password, which is a critical security vulnerability.

## Step 1: Generate Strong Database Password

Run this command to generate a secure password:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 2: Update PostgreSQL Password

### Option A: Using PostgreSQL Command Line
```sql
-- Connect as postgres superuser
psql -U postgres

-- Change password
ALTER USER postgres PASSWORD 'your_new_secure_password_here';

-- Exit
\q
```

### Option B: Using pgAdmin
1. Open pgAdmin
2. Connect to your PostgreSQL server
3. Right-click on "postgres" user
4. Select "Properties"
5. Go to "Definition" tab
6. Enter new password
7. Click "Save"

## Step 3: Update Environment Configuration

Update your `.env` file with the new password:

```bash
# Replace the current DATABASE_URL
DATABASE_URL=postgresql://postgres:your_new_secure_password_here@localhost:5432/cropio_dev

# Also update the standalone password variable
DB_PASSWORD=your_new_secure_password_here
```

## Step 4: Test Database Connection

Run this test to verify the connection:

```bash
python -c "
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)
connection = engine.connect()
print('✅ Database connection successful!')
connection.close()
"
```

## Step 5: Restart Application

After updating the password:

```bash
# Stop the application if running
# Update .env file with new password
# Restart the application
python app.py
```

## Security Best Practices

1. **Use a strong password**: At least 32 characters, random
2. **Restrict database access**: Only allow connections from localhost/app server
3. **Enable SSL**: For production, always use SSL connections
4. **Regular backups**: Ensure encrypted database backups
5. **Monitor access**: Log database connections and queries

## Production Considerations

For production deployment:

1. **Use environment-specific passwords**: Different for dev/staging/prod
2. **Use database connection pooling**: Configure appropriate pool sizes
3. **Enable query logging**: Monitor for suspicious activities
4. **Set up database firewall**: Restrict network access
5. **Regular password rotation**: Change passwords periodically

## Security Checklist

- [ ] Generated strong database password (32+ characters)
- [ ] Updated PostgreSQL user password
- [ ] Updated .env file with new password
- [ ] Tested database connection
- [ ] Restarted application
- [ ] Verified application functionality
- [ ] Documented password securely (password manager)
- [ ] Set calendar reminder for password rotation (quarterly)

## Emergency Recovery

If you get locked out:

1. Stop the application
2. Reset postgres password using system authentication:
   ```bash
   sudo -u postgres psql
   ALTER USER postgres PASSWORD 'new_password';
   ```
3. Update .env file
4. Restart application

---

⚠️ **IMPORTANT**: Never commit the new password to version control. Keep it in environment variables only.
