# Tesseract configuration helper
# This file helps configure Tesseract OCR for the Cropio application

import os
import sys

def configure_tesseract():
    """Configure Tesseract path for pytesseract"""
    tesseract_paths = [
        r'C:\Program Files\Tesseract-OCR',
        r'C:\Program Files (x86)\Tesseract-OCR',
    ]
    
    # Add Tesseract directory to PATH if not already there
    for path in tesseract_paths:
        if os.path.exists(path):
            if path not in os.environ.get('PATH', ''):
                os.environ['PATH'] += f";{path}"
            
            # Configure pytesseract
            try:
                import pytesseract
                pytesseract.pytesseract.pytesseract_cmd = os.path.join(path, 'tesseract.exe')
                return True
            except Exception as e:
                print(f"Error configuring pytesseract: {e}")
                return False
    
    return False

# Auto-configure on import
if __name__ != '__main__':
    configure_tesseract()
