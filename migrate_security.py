#!/usr/bin/env python3
"""
Security Framework Migration Script
This script helps migrate your application from the old security system to the new framework.
"""

import os
import shutil
import sys
from datetime import datetime
import re

def create_backup():
    """Create a backup of the current application before migration"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_before_security_migration_{timestamp}"
    
    print(f"Creating backup in {backup_dir}...")
    
    # Files and directories to backup
    items_to_backup = [
        'app.py',
        'routes/',
        'utils/security.py',
        'config/',
        'requirements.txt'
    ]
    
    os.makedirs(backup_dir, exist_ok=True)
    
    for item in items_to_backup:
        if os.path.exists(item):
            if os.path.isfile(item):
                shutil.copy2(item, backup_dir)
                print(f"✓ Backed up {item}")
            elif os.path.isdir(item):
                target_dir = os.path.join(backup_dir, os.path.basename(item))
                if not os.path.exists(target_dir):
                    shutil.copytree(item, target_dir)
                    print(f"✓ Backed up {item}")
                else:
                    print(f"⚠ Warning: {target_dir} already exists, skipping...")
        else:
            print(f"⚠ Warning: {item} not found, skipping...")
    
    print(f"✓ Backup completed: {backup_dir}")
    return backup_dir

def check_dependencies():
    """Check if required dependencies are available"""
    print("Checking dependencies...")
    
    required_packages = [
        'flask',
        'redis',  # For rate limiting
        'wtforms',  # For CSRF
        'PIL',  # For image processing (Pillow)
        'fitz'  # For PDF processing (PyMuPDF)
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} is NOT installed")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install", ' '.join(missing_packages))
        return False
    
    return True

def analyze_current_security():
    """Analyze the current security implementation"""
    print("\nAnalyzing current security implementation...")
    
    # Check for old security system
    old_security_file = 'utils/security.py'
    if os.path.exists(old_security_file):
        print("✓ Found old security system (utils/security.py)")
        with open(old_security_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'csrf' in content.lower():
                print("  - CSRF protection detected")
            if 'rate_limit' in content.lower():
                print("  - Rate limiting detected")
            if 'security' in content.lower():
                print("  - Security headers detected")
    else:
        print("⚠ Old security file not found")
    
    # Check security framework
    security_init = 'security/__init__.py'
    if os.path.exists(security_init):
        print("✓ New security framework detected")
    else:
        print("✗ New security framework not found - please install first")
        return False
    
    return True

def find_routes_to_migrate():
    """Find route files that need migration"""
    print("\nScanning for route files...")
    
    route_files = []
    routes_dir = 'routes'
    
    if os.path.exists(routes_dir):
        for file in os.listdir(routes_dir):
            if file.endswith('.py') and file != '__init__.py':
                route_path = os.path.join(routes_dir, file)
                route_files.append(route_path)
                print(f"Found: {route_path}")
    else:
        print("⚠ Routes directory not found")
    
    # Also check main application file
    if os.path.exists('app.py'):
        route_files.append('app.py')
        print("Found: app.py")
    
    return route_files

def analyze_route_file(file_path):
    """Analyze a route file for security migration needs"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    analysis = {
        'file': file_path,
        'has_old_csrf': 'from utils.security import csrf' in content,
        'has_file_uploads': '@' in content and 'files' in content,
        'has_forms': 'request.form' in content,
        'has_json_data': 'request.json' in content,
        'needs_authentication': 'login' in content.lower() or 'auth' in content.lower(),
        'has_admin_routes': 'admin' in content.lower(),
        'priority': 'low'
    }
    
    # Determine priority
    if analysis['has_admin_routes'] or analysis['needs_authentication']:
        analysis['priority'] = 'high'
    elif analysis['has_file_uploads'] or analysis['has_forms']:
        analysis['priority'] = 'medium'
    
    return analysis

def create_migration_plan(route_files):
    """Create a migration plan based on route analysis"""
    print("\nCreating migration plan...")
    
    high_priority = []
    medium_priority = []
    low_priority = []
    
    for route_file in route_files:
        analysis = analyze_route_file(route_file)
        
        if analysis['priority'] == 'high':
            high_priority.append(analysis)
        elif analysis['priority'] == 'medium':
            medium_priority.append(analysis)
        else:
            low_priority.append(analysis)
    
    # Print migration plan
    print("\n" + "="*60)
    print("SECURITY MIGRATION PLAN")
    print("="*60)
    
    if high_priority:
        print("\n📋 PHASE 1 - HIGH PRIORITY (Critical Routes):")
        for item in high_priority:
            print(f"  • {item['file']}")
            if item['has_old_csrf']:
                print("    - Remove old CSRF imports")
            if item['has_file_uploads']:
                print("    - Add file validation decorators")
            if item['needs_authentication']:
                print("    - Add authentication decorators")
    
    if medium_priority:
        print("\n📋 PHASE 2 - MEDIUM PRIORITY (Processing Routes):")
        for item in medium_priority:
            print(f"  • {item['file']}")
            if item['has_file_uploads']:
                print("    - Add comprehensive file validation")
            if item['has_forms']:
                print("    - Add input validation")
    
    if low_priority:
        print("\n📋 PHASE 3 - LOW PRIORITY (Utility Routes):")
        for item in low_priority:
            print(f"  • {item['file']}")
    
    return {
        'high': high_priority,
        'medium': medium_priority, 
        'low': low_priority
    }

def update_app_initialization():
    """Update the main application file to use new security framework"""
    app_file = 'app.py'
    
    if not os.path.exists(app_file):
        print("⚠ app.py not found, skipping initialization update")
        return False
    
    print(f"\nUpdating {app_file} security initialization...")
    
    with open(app_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already migrated
    if 'from security import init_security' in content:
        print("✓ App already migrated to new security framework")
        return True
    
    # Remove old security imports and initialization
    old_patterns = [
        r'from utils\.security import.*\n',
        r'csrf\.init_app\(app\)\n',
        r'app\.config\.from_object\(SecurityConfig\)\n'
    ]
    
    for pattern in old_patterns:
        content = re.sub(pattern, '', content)
    
    # Add new security import and initialization
    if 'from security import init_security' not in content:
        # Find a good place to add the import (after other imports)
        import_section = re.search(r'(from flask import.*?\n)', content)
        if import_section:
            new_import = import_section.group(1) + 'from security import init_security\n'
            content = content.replace(import_section.group(1), new_import)
        
        # Add initialization after app creation
        app_creation = re.search(r'(app = Flask\(__name__\).*?\n)', content)
        if app_creation:
            new_init = app_creation.group(1) + '\n# Initialize security framework\ninit_security(app)\n'
            content = content.replace(app_creation.group(1), new_init)
    
    # Write updated content
    with open(app_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Updated app.py with new security initialization")
    return True

def create_env_template():
    """Create environment variable template"""
    env_template = """.env.security_template
# Security Framework Configuration
# Copy these to your .env file and update values

# Required: Secret key for CSRF and session security
SECRET_KEY=your-very-long-random-secret-key-here

# Optional: Redis for advanced rate limiting (use memory:// for simple in-memory)
REDIS_URL=redis://localhost:6379/0

# Optional: Malware scanning with ClamAV
ENABLE_MALWARE_SCAN=false
CLAMD_HOST=localhost
CLAMD_PORT=3310

# Optional: Enhanced logging
SECURITY_LOG_LEVEL=INFO
SECURITY_LOG_FILE=logs/security.log
"""
    
    with open('.env.security_template', 'w') as f:
        f.write(env_template)
    
    print("✓ Created .env.security_template with configuration examples")

def main():
    """Main migration function"""
    print("Security Framework Migration Tool")
    print("="*40)
    
    # Step 1: Create backup
    try:
        backup_dir = create_backup()
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False
    
    # Step 2: Check dependencies
    if not check_dependencies():
        print("\n❌ Missing dependencies. Please install them before continuing.")
        return False
    
    # Step 3: Analyze current security
    if not analyze_current_security():
        print("\n❌ Security analysis failed. Please ensure the new security framework is installed.")
        return False
    
    # Step 4: Find routes to migrate
    route_files = find_routes_to_migrate()
    if not route_files:
        print("\n⚠ No route files found to migrate")
        return False
    
    # Step 5: Create migration plan
    migration_plan = create_migration_plan(route_files)
    
    # Step 6: Start migration
    print("\n" + "="*60)
    print("STARTING MIGRATION")
    print("="*60)
    
    # Update app initialization first
    if update_app_initialization():
        print("✓ Phase 0: Updated main application initialization")
    
    # Create environment template
    create_env_template()
    
    print("\n🎉 Migration preparation completed!")
    print("\nNext steps:")
    print("1. Review the migration plan above")
    print("2. Update your .env file using .env.security_template")
    print("3. Follow the detailed migration guide (SECURITY_MIGRATION_GUIDE.md)")
    print("4. Use the cropper route example (routes/cropper_routes_MIGRATED_EXAMPLE.py)")
    print("5. Test each phase thoroughly before proceeding to the next")
    
    print(f"\n💾 Your original code is backed up in: {backup_dir}")
    print("\n⚠️  Remember: Migrate incrementally and test at each step!")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if success:
            print("\n✅ Migration preparation successful!")
            sys.exit(0)
        else:
            print("\n❌ Migration preparation failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)