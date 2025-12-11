"""
Database Module - Centralized database utilities and path management
"""
import os
from pathlib import Path

# Database folder paths
DATABASE_ROOT = Path(__file__).parent
SCHEMAS_DIR = DATABASE_ROOT / 'schemas'
MIGRATIONS_DIR = DATABASE_ROOT / 'migrations'
SCRIPTS_DIR = DATABASE_ROOT / 'scripts'

# Database file paths
DATABASE_SCHEMA_SQL = SCHEMAS_DIR / 'database_schema.sql'
DATABASE_SCHEMA_ASCII = SCHEMAS_DIR / 'database_schema_ascii.txt'
INIT_DB_SCRIPT = SCRIPTS_DIR / 'init_db.py'

def get_database_path(filename: str, subfolder: str = '') -> Path:
    """
    Get the full path for a database file
    
    Args:
        filename: Name of the database file
        subfolder: Subfolder within database directory ('schemas', 'migrations', 'scripts')
    
    Returns:
        Path object for the database file
    """
    if subfolder:
        return DATABASE_ROOT / subfolder / filename
    return DATABASE_ROOT / filename

def ensure_database_dirs():
    """Ensure all database directories exist"""
    for directory in [SCHEMAS_DIR, MIGRATIONS_DIR, SCRIPTS_DIR]:
        directory.mkdir(exist_ok=True)

def get_schema_file() -> Path:
    """Get the path to the main database schema file"""
    return DATABASE_SCHEMA_SQL

def get_init_script() -> Path:
    """Get the path to the database initialization script"""
    return INIT_DB_SCRIPT

# Ensure directories exist when module is imported
ensure_database_dirs()
