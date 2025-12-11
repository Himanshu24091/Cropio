# Database Management

This folder contains all database-related files for the Cropio application.

## Folder Structure

```
database/
├── README.md              # This documentation file
├── __init__.py            # Database module initialization
├── db_config.py           # Database configuration and utilities
├── schemas/               # Database schema files
│   ├── database_schema.sql          # Main database schema
│   └── database_schema_ascii.txt    # ASCII representation of schema
├── migrations/            # Database migration files
│   └── [timestamp]_[migration_name].sql
└── scripts/              # Database utility scripts
    └── init_db.py        # Database initialization script
```

## Usage

### From Project Root

You can use the `db_manager.py` script from the project root to manage database operations:

```bash
# Show database structure
python db_manager.py structure

# Initialize the database
python db_manager.py init

# Create a new migration
python db_manager.py migrate create add_new_table

# List all migrations
python db_manager.py migrate list
```

### Direct Access

You can also import database utilities directly:

```python
from database.db_config import DatabaseConfig, db_config

# Get paths
schema_path = db_config.get_schema_path()
init_script_path = db_config.get_init_script_path()

# Create migration
migration_path = db_config.create_migration_file('add_user_preferences')
```

## Configuration

The database configuration is managed through:
- `.env` file for environment variables
- `config.py` for Flask configuration
- `database/db_config.py` for database-specific settings

## Best Practices

1. **Schema Changes**: Always create migration files for schema changes
2. **File Organization**: Place database files in appropriate subfolders:
   - `schemas/` - Schema definitions and documentation
   - `migrations/` - Database migrations
   - `scripts/` - Utility scripts and initialization
3. **Version Control**: Commit all database files to version control
4. **Documentation**: Update this README when adding new database components

## Adding New Database Files

When creating new database-related files, use the provided utilities:

```python
from database.db_config import db_config

# For migration files
migration_path = db_config.create_migration_file('your_migration_name')

# For custom paths
custom_path = db_config.get_database_path('my_file.sql', 'schemas')
```

This ensures proper organization and maintains consistency across the project.
