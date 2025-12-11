"""
Database Migration: Add Password Alert Fields
Run this script to add password strength tracking fields to the User table
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db

def upgrade():
    """Add password alert tracking fields to User table"""
    print("Adding password alert fields to User table...")
    
    app = create_app()
    with app.app_context():
        try:
            # Add columns using raw SQL for PostgreSQL
            with db.engine.connect() as conn:
                # Add password_alert_dismissed_at column
                conn.execute(db.text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS password_alert_dismissed_at TIMESTAMP
                """))
                print("[OK] Added password_alert_dismissed_at column")
                
                # Add password_strength_checked column
                conn.execute(db.text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS password_strength_checked BOOLEAN DEFAULT FALSE
                """))
                print("[OK] Added password_strength_checked column")
                
                # Add last_password_change column for tracking
                conn.execute(db.text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS last_password_change TIMESTAMP
                """))
                print("[OK] Added last_password_change column")
                
                conn.commit()
            
            print("[SUCCESS] Migration completed successfully!")
            
        except Exception as e:
            print(f"[ERROR] Migration failed: {e}")
            raise


def downgrade():
    """Remove password alert tracking fields from User table"""
    print("Removing password alert fields from User table...")
    
    app = create_app()
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE users DROP COLUMN IF EXISTS password_alert_dismissed_at'))
                conn.execute(db.text('ALTER TABLE users DROP COLUMN IF EXISTS password_strength_checked'))
                conn.execute(db.text('ALTER TABLE users DROP COLUMN IF EXISTS last_password_change'))
                conn.commit()
            
            print("[SUCCESS] Downgrade completed successfully!")
            
        except Exception as e:
            print(f"[ERROR] Downgrade failed: {e}")
            raise


if __name__ == '__main__':
    print("=" * 60)
    print("Running Migration: Add Password Alert Fields")
    print("=" * 60)
    upgrade()
