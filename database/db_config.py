"""
Database Configuration - Centralized database settings and utilities
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Database folder structure
DATABASE_ROOT = Path(__file__).parent
SCHEMAS_DIR = DATABASE_ROOT / 'schemas'
MIGRATIONS_DIR = DATABASE_ROOT / 'migrations'
SCRIPTS_DIR = DATABASE_ROOT / 'scripts'

class DatabaseConfig:
    """Centralized database configuration management"""
    
    def __init__(self):
        self.ensure_directories()
    
    @staticmethod
    def ensure_directories():
        """Ensure all database directories exist"""
        for directory in [SCHEMAS_DIR, MIGRATIONS_DIR, SCRIPTS_DIR]:
            directory.mkdir(exist_ok=True)
    
    @staticmethod
    def get_schema_path() -> Path:
        """Get path to database schema file"""
        return SCHEMAS_DIR / 'database_schema.sql'
    
    @staticmethod
    def get_init_script_path() -> Path:
        """Get path to database initialization script"""
        return SCRIPTS_DIR / 'init_db.py'
    
    @staticmethod
    def get_migration_path(migration_name: str) -> Path:
        """Get path for a migration file"""
        return MIGRATIONS_DIR / f"{migration_name}.sql"
    
    @staticmethod
    def list_migrations() -> list:
        """List all migration files"""
        if not MIGRATIONS_DIR.exists():
            return []
        return [f.name for f in MIGRATIONS_DIR.glob('*.sql')]
    
    @staticmethod
    def get_database_url(environment: str = 'development') -> str:
        """Get database URL for specified environment"""
        if environment == 'production':
            return os.environ.get('PRODUCTION_DATABASE_URL', 
                                os.environ.get('DATABASE_URL'))
        else:
            return os.environ.get('DATABASE_URL', 
                                'postgresql://postgres:root@localhost:5432/cropio_dev')
    
    @staticmethod
    def create_migration_file(migration_name: str, content: str = '') -> Path:
        """Create a new migration file"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{migration_name}.sql"
        migration_path = MIGRATIONS_DIR / filename
        
        if not content:
            content = f"""-- Migration: {migration_name}
-- Created: {datetime.now().isoformat()}
-- Description: Add your migration description here

-- Add your SQL commands here
"""
        
        migration_path.write_text(content, encoding='utf-8')
        return migration_path

# Initialize database configuration when module is imported
db_config = DatabaseConfig()
