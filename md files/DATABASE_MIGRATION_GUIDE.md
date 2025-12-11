# Database Migration Guide for Cropio

## Flask-Migrate Setup Complete ✅

Your database migration system is now properly configured!

## Migration Commands

### Environment Setup
```bash
$env:FLASK_APP = "app.py"  # Windows PowerShell
# OR
export FLASK_APP=app.py    # Linux/macOS
```

### Common Migration Commands

#### 1. Create a New Migration
```bash
.\\venv\\Scripts\\python.exe -m flask db migrate -m "Description of changes"
```

#### 2. Apply Migrations
```bash
.\\venv\\Scripts\\python.exe -m flask db upgrade
```

#### 3. View Migration History
```bash
.\\venv\\Scripts\\python.exe -m flask db history
```

#### 4. View Current Migration
```bash
.\\venv\\Scripts\\python.exe -m flask db current
```

#### 5. Rollback to Previous Migration
```bash
.\\venv\\Scripts\\python.exe -m flask db downgrade
```

## When to Create Migrations

Create a new migration whenever you:
- Add new database tables
- Modify existing table columns
- Add/remove indexes
- Add/remove foreign key constraints
- Change column types

## Database Schema Changes Workflow

1. **Modify models.py** with your changes
2. **Generate migration**: `flask db migrate -m "Descriptive message"`
3. **Review migration file** in `migrations/versions/`
4. **Apply migration**: `flask db upgrade`
5. **Test your changes**

## Current Database Status

- ✅ Flask-Migrate initialized
- ✅ PostgreSQL connection working  
- ✅ All models detected
- ✅ Database tables already exist
- ✅ Migration system ready for future changes

## Production Deployment

For production deployments:
```bash
# Apply all migrations
flask db upgrade

# Or upgrade to specific revision
flask db upgrade <revision_id>
```

## Troubleshooting

### If you get "No changes detected"
This usually means your database is already in sync with your models.

### If migration fails
```bash
# Check current database state
flask db current

# Check what migrations are available
flask db history

# Force downgrade and re-upgrade if needed
flask db downgrade
flask db upgrade
```

### Reset migrations (CAUTION: Development only)
```bash
# Remove migrations folder
Remove-Item -Recurse -Force migrations

# Re-initialize
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Migration Files Location
- **Main folder**: `migrations/`
- **Version files**: `migrations/versions/`
- **Configuration**: `migrations/alembic.ini`
