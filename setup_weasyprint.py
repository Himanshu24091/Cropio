#!/usr/bin/env python3
"""
Setup script to configure WeasyPrint on Windows
This helps fix the DLL loading issues for WeasyPrint
"""

import os
import sys
import platform

def setup_weasyprint_windows():
    """Set up WeasyPrint DLL directories for Windows"""
    
    if platform.system() != 'Windows':
        print("This script is only needed on Windows.")
        return
    
    # Common MSYS2 installation paths
    msys2_paths = [
        r"C:\msys64\mingw64\bin",
        r"C:\msys64\mingw32\bin",
        r"C:\msys2\mingw64\bin",
        r"C:\msys2\mingw32\bin",
        r"C:\tools\msys64\mingw64\bin",
        r"C:\tools\msys2\mingw64\bin"
    ]
    
    # Check which paths exist
    existing_paths = []
    for path in msys2_paths:
        if os.path.exists(path):
            existing_paths.append(path)
            print(f"✓ Found MSYS2 path: {path}")
    
    if not existing_paths:
        print("\n⚠️  MSYS2 installation not found in common locations.")
        print("\nTo use WeasyPrint for PDF generation, you need to:")
        print("1. Install MSYS2 from https://www.msys2.org/")
        print("2. In MSYS2 terminal, run: pacman -S mingw-w64-x86_64-pango")
        print("3. Add the MSYS2 bin directory to WEASYPRINT_DLL_DIRECTORIES")
        return
    
    # Set the environment variable
    dll_dirs = ";".join(existing_paths)
    os.environ['WEASYPRINT_DLL_DIRECTORIES'] = dll_dirs
    
    print(f"\n✅ Set WEASYPRINT_DLL_DIRECTORIES to: {dll_dirs}")
    
    # Try to import weasyprint to test
    try:
        import weasyprint
        print("✅ WeasyPrint imported successfully!")
        return True
    except Exception as e:
        print(f"⚠️  WeasyPrint import still failing: {e}")
        print("\nYou may need to install Pango in MSYS2:")
        print("1. Open MSYS2 terminal")
        print("2. Run: pacman -S mingw-w64-x86_64-pango")
        return False

def add_to_app_startup():
    """Add WeasyPrint setup to app.py startup"""
    print("\nTo automatically set up WeasyPrint when starting your app,")
    print("add this to the beginning of your app.py file:\n")
    print("# Configure WeasyPrint DLL directories on Windows")
    print("import os")
    print("import platform")
    print("if platform.system() == 'Windows':")
    print("    os.environ['WEASYPRINT_DLL_DIRECTORIES'] = r'C:\\msys64\\mingw64\\bin'")
    print()

if __name__ == "__main__":
    print("WeasyPrint Windows Setup")
    print("========================\n")
    
    success = setup_weasyprint_windows()
    
    if not success:
        add_to_app_startup()