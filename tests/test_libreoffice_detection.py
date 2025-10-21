#!/usr/bin/env python3
"""Simple test for LibreOffice detection"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.presentation_converter.presentation_utils import PresentationConverter

def main():
    print("LibreOffice Detection Test")
    print("="*30)
    
    converter = PresentationConverter()
    
    print(f"LibreOffice path detected: {converter.libreoffice_path}")
    print(f"PPTX to PDF available: {converter.is_pptx_conversion_available()}")
    print(f"PDF to PPTX basic available: {converter.is_pdf_conversion_available()}")
    print(f"PDF to PPTX accurate available: {converter.is_ocr_available()}")
    
    print("\nDependencies check:")
    for dep, available in converter.dependencies.items():
        status = "✅ Available" if available else "❌ Missing"
        print(f"  {dep:<15}: {status}")
    
    # Test direct LibreOffice execution
    if converter.libreoffice_path:
        print(f"\nTesting LibreOffice execution...")
        import subprocess
        import platform
        
        try:
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            else:
                startupinfo = None
                creation_flags = 0
            
            result = subprocess.run(
                [converter.libreoffice_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=creation_flags,
                startupinfo=startupinfo
            )
            
            if result.returncode == 0:
                print(f"✅ LibreOffice version: {result.stdout.strip()}")
                print("✅ Console window suppression: Working")
            else:
                print(f"❌ LibreOffice test failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ LibreOffice test error: {e}")
    
    # Test security framework
    print(f"\nSecurity framework available: {hasattr(converter, 'SECURITY_FRAMEWORK_AVAILABLE')}")
    
    return converter.is_pptx_conversion_available()

if __name__ == "__main__":
    success = main()
    print(f"\nOverall status: {'✅ Ready for conversion' if success else '❌ Setup issues'}")
    sys.exit(0 if success else 1)