#!/usr/bin/env python3
"""
Initialize PostgreSQL database for Cropio
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from app import create_app
    from models import db, User, UsageTracking, ConversionHistory, UserRole, UserSession, init_database
    
    print("🚀 Initializing Cropio database...")
    app = create_app()
    
    with app.app_context():
        # Check database connection
        print("🔗 Testing database connection...")
        with db.engine.connect() as conn:
            conn.execute(db.text("SELECT 1"))
        print("✅ Database connection successful!")
        
        # Check existing tables
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print(f"\n📋 Existing tables: {existing_tables}")
        
        # Create all tables
        print("🔧 Creating/updating database tables...")
        db.create_all()
        
        # Check tables again
        updated_tables = db.inspect(db.engine).get_table_names()
        print(f"✅ Current tables: {updated_tables}")
        
        # Check if we can query users
        try:
            user_count = User.query.count()
            print(f"👥 Total users: {user_count}")
        except Exception as e:
            print(f"⚠️  Could not count users: {e}")
        
        print("🎉 Database initialization complete!")

except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
