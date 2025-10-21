#!/usr/bin/env python3
"""
Pre-deployment checker for Render
Validates that all required configurations are in place
"""

import os
import sys
from pathlib import Path

def check_file_exists(filename, required=True):
    """Check if a file exists"""
    exists = Path(filename).exists()
    status = "[OK]" if exists else ("[FAIL]" if required else "[WARN]")
    print(f"{status} {filename}: {'Found' if exists else 'Missing'}")
    return exists

def check_requirements():
    """Check if requirements.txt is valid"""
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
            print(f"[OK] requirements.txt: {len(lines)} packages")
            
            # Check for problematic versions
            for line in lines:
                if 'cryptography==41.0.8' in line:
                    print("[FAIL] Found cryptography==41.0.8 (doesn't exist, should be 42.0.8+)")
                    return False
        return True
    except Exception as e:
        print(f"[FAIL] Error reading requirements.txt: {e}")
        return False

def check_build_script():
    """Check if build script is executable"""
    script = Path('render-build.sh')
    if script.exists():
        content = script.read_text(encoding='utf-8')
        has_shebang = content.startswith('#!/')
        has_errexit = 'set -o errexit' in content or 'set -e' in content
        
        print(f"[OK] render-build.sh exists")
        print(f"  {'[OK]' if has_shebang else '[WARN]'} Shebang: {has_shebang}")
        print(f"  {'[OK]' if has_errexit else '[WARN]'} Error handling: {has_errexit}")
        return True
    else:
        print("[FAIL] render-build.sh not found")
        return False

def check_gunicorn_config():
    """Check Gunicorn configuration"""
    if Path('gunicorn_config.py').exists():
        with open('gunicorn_config.py', 'r', encoding='utf-8') as f:
            content = f.read()
            has_workers = 'workers' in content
            has_bind = 'bind' in content
            
            print(f"[OK] gunicorn_config.py exists")
            print(f"  {'[OK]' if has_workers else '[FAIL]'} Workers configured: {has_workers}")
            print(f"  {'[OK]' if has_bind else '[FAIL]'} Bind configured: {has_bind}")
            return has_workers and has_bind
    else:
        print("[WARN] gunicorn_config.py not found (will use defaults)")
        return True

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    compatible = version.major == 3 and version.minor >= 11
    status = "[OK]" if compatible else "[WARN]"
    print(f"{status} Python version: {version.major}.{version.minor}.{version.micro}")
    if not compatible:
        print("  [WARN] Render requires Python 3.11+, check runtime.txt")
    return compatible

def check_runtime_txt():
    """Check runtime.txt for Python version"""
    if Path('runtime.txt').exists():
        with open('runtime.txt', 'r', encoding='utf-8') as f:
            runtime = f.read().strip()
            print(f"[OK] runtime.txt: {runtime}")
            if not runtime.startswith('python-3.11'):
                print("  [WARN] Consider using python-3.11.x for best compatibility")
        return True
    else:
        print("[FAIL] runtime.txt not found (required for Render)")
        return False

def check_app_entry():
    """Check if app.py exists and has app object"""
    if Path('app.py').exists():
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            has_app = 'app = ' in content or 'def create_app' in content
            has_flask = 'from flask import' in content or 'import flask' in content
            
            print(f"[OK] app.py exists")
            print(f"  {'[OK]' if has_flask else '[FAIL]'} Flask imported: {has_flask}")
            print(f"  {'[OK]' if has_app else '[WARN]'} App object found: {has_app}")
            return has_flask and has_app
    else:
        print("[FAIL] app.py not found")
        return False

def check_env_example():
    """Check for .env.example"""
    if Path('.env.example').exists():
        print("[OK] .env.example exists (reference for environment variables)")
        return True
    else:
        print("[WARN] .env.example not found (recommended for documentation)")
        return True

def print_env_checklist():
    """Print environment variables checklist"""
    print("\nRequired Render Environment Variables:")
    required_vars = [
        'FLASK_SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'FLASK_ENV',
    ]
    
    for var in required_vars:
        print(f"   [ ] {var}")
    
    print("\nGenerate secrets with:")
    print("   python -c \"import secrets; print(secrets.token_hex(32))\"")

def main():
    """Run all checks"""
    print("Cropio - Render Deployment Pre-flight Check\n")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("runtime.txt", check_runtime_txt),
        ("requirements.txt", check_requirements),
        ("Build Script", check_build_script),
        ("Gunicorn Config", check_gunicorn_config),
        ("App Entry Point", check_app_entry),
        (".env.example", check_env_example),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n--- {name} ---")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Error during check: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    
    # Check additional files
    print("\nAdditional Files:")
    check_file_exists('RENDER_DEPLOYMENT.md', required=False)
    check_file_exists('.renderignore', required=False)
    check_file_exists('.gitignore', required=False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} checks passed")
    
    if all(results):
        print("\n[SUCCESS] All checks passed! Ready to deploy to Render.")
        print("\nNext steps:")
        print("   1. Push code to GitHub/GitLab")
        print("   2. Create PostgreSQL database on Render")
        print("   3. Create Redis instance (Upstash or Redis Cloud)")
        print("   4. Create Web Service on Render")
        print("   5. Set environment variables")
        print("   6. Deploy!")
        print("\nSee RENDER_DEPLOYMENT.md for detailed instructions")
        return 0
    else:
        print("\n[WARNING] Some checks failed. Please fix the issues above.")
        print("   See RENDER_DEPLOYMENT.md for help")
        return 1
    
    # Print environment checklist
    print_env_checklist()

if __name__ == '__main__':
    sys.exit(main())

