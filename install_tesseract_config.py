#!/usr/bin/env python3
"""
Script to help configure Tesseract OCR for Cropio application.
This script will:
1. Download Tesseract installer
2. Guide you through installation
3. Configure pytesseract to use it
"""

import os
import sys
import subprocess
import winreg
from pathlib import Path

def find_tesseract():
    """Try to find Tesseract installation"""
    common_paths = [
        r'C:\Program Files\Tesseract-OCR',
        r'C:\Program Files (x86)\Tesseract-OCR',
        r'C:\Users\{}\AppData\Local\Tesseract-OCR'.format(os.getenv('USERNAME')),
    ]
    
    # Check common installation paths
    for path in common_paths:
        tesseract_exe = os.path.join(path, 'tesseract.exe')
        if os.path.exists(tesseract_exe):
            return tesseract_exe
    
    # Check Windows Registry
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\UB-Mannheim\Tesseract-OCR') as key:
            path, _ = winreg.QueryValueEx(key, 'InstallationPath')
            tesseract_exe = os.path.join(path, 'tesseract.exe')
            if os.path.exists(tesseract_exe):
                return tesseract_exe
    except Exception as e:
        print(f"Registry check failed: {e}")
    
    return None

def configure_pytesseract():
    """Configure pytesseract with Tesseract path"""
    tesseract_path = find_tesseract()
    
    if tesseract_path:
        print(f"✅ Found Tesseract at: {tesseract_path}")
        
        # Create or update config file
        config_file = 'tesseract_config.py'
        with open(config_file, 'w') as f:
            f.write(f"""#!/usr/bin/env python3
# Tesseract Configuration for Cropio
# Auto-generated configuration file

TESSERACT_CMD = r'{tesseract_path}'
""")
        
        print(f"✅ Created configuration file: {config_file}")
        return True
    else:
        print("❌ Tesseract not found!")
        print("\n📥 Please download and install Tesseract OCR:")
        print("   1. Download from: https://github.com/UB-Mannheim/tesseract/releases")
        print("   2. Look for: tesseract-ocr-w64-setup-v5.x.x.exe")
        print("   3. Run the installer (default path is fine)")
        print("   4. Run this script again")
        return False

def main():
    print("=" * 60)
    print("Tesseract OCR Configuration for Cropio")
    print("=" * 60)
    
    print("\n🔍 Searching for Tesseract OCR installation...")
    
    if configure_pytesseract():
        print("\n✅ Configuration complete!")
        print("   You can now use Tesseract OCR in your application.")
    else:
        print("\n⚠️  Tesseract OCR needs to be installed.")
        print("\n📝 Quick Installation Steps:")
        print("   1. Go to: https://github.com/UB-Mannheim/tesseract/releases")
        print("   2. Download the latest Windows installer")
        print("   3. Run it and follow the installation wizard")
        print("   4. The default installation path is recommended")
        print("   5. Run this script again after installation")
        sys.exit(1)

if __name__ == '__main__':
    main()
