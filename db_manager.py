#!/usr/bin/env python3
"""
Database Manager - Convenient database operations from project root
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from database.db_config import DatabaseConfig, db_config

def init_database():
    """Initialize the database"""
    init_script = db_config.get_init_script_path()
    print(f"Running database initialization script: {init_script}")
    
    # Execute the init script
    exec(open(init_script).read())

def create_migration(migration_name: str):
    """Create a new migration file"""
    migration_path = db_config.create_migration_file(migration_name)
    print(f"Created migration file: {migration_path}")
    return migration_path

def list_migrations():
    """List all available migrations"""
    migrations = db_config.list_migrations()
    if migrations:
        print("Available migrations:")
        for migration in migrations:
            print(f"  - {migration}")
    else:
        print("No migrations found")
    return migrations

def show_database_structure():
    """Show the database folder structure"""
    from database.db_config import SCHEMAS_DIR, MIGRATIONS_DIR, SCRIPTS_DIR
    
    print("Database folder structure:")
    print(f"📁 database/")
    print(f"  📁 schemas/")
    for file in SCHEMAS_DIR.glob('*'):
        print(f"    📄 {file.name}")
    print(f"  📁 migrations/")
    for file in MIGRATIONS_DIR.glob('*'):
        print(f"    📄 {file.name}")
    print(f"  📁 scripts/")
    for file in SCRIPTS_DIR.glob('*'):
        print(f"    📄 {file.name}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Management Utility")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize the database')
    
    # Migration commands
    migrate_parser = subparsers.add_parser('migrate', help='Migration operations')
    migrate_subparsers = migrate_parser.add_subparsers(dest='migrate_action')
    
    create_migration_parser = migrate_subparsers.add_parser('create', help='Create a new migration')
    create_migration_parser.add_argument('name', help='Migration name')
    
    list_migration_parser = migrate_subparsers.add_parser('list', help='List all migrations')
    
    # Structure command
    structure_parser = subparsers.add_parser('structure', help='Show database folder structure')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_database()
    elif args.command == 'migrate':
        if args.migrate_action == 'create':
            create_migration(args.name)
        elif args.migrate_action == 'list':
            list_migrations()
    elif args.command == 'structure':
        show_database_structure()
    else:
        parser.print_help()
