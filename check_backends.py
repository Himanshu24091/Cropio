#!/usr/bin/env python3
"""
Check HTML to PDF backend availability
"""

def check_backend(module_name):
    """Check if a backend module is available"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def main():
    backends = {
        'weasyprint': 'WeasyPrint - Best CSS support',
        'pdfkit': 'PDFKit (wkhtmltopdf) - Fast processing', 
        'selenium': 'Selenium - JavaScript support'
    }
    
    available_count = 0
    
    for module, description in backends.items():
        if check_backend(module):
            print(f"✅ {description}: Available")
            available_count += 1
        else:
            print(f"❌ {description}: Not installed")
    
    print(f"\nTotal available backends: {available_count}/3")
    
    if available_count == 0:
        print("\n⚠️  No PDF backends available! Install at least one:")
        print("   pip install weasyprint")
        print("   pip install pdfkit")
        print("   pip install selenium")

if __name__ == "__main__":
    main()
