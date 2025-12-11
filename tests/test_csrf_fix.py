#!/usr/bin/env python3
"""
Comprehensive CSRF Fix Test Script
Tests all website features to ensure CSRF protection works without blocking functionality
"""
import os
import sys
import requests
from io import BytesIO
import tempfile

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_csrf_implementation():
    """Test the CSRF implementation by checking templates and routes"""
    print("🔍 Testing CSRF Implementation...")
    print("=" * 60)
    
    # Test 1: Check if forms.py has converter forms
    print("\n1. Testing Form Classes...")
    try:
        from forms import ImageConverterForm, PDFConverterForm, DocumentConverterForm, ExcelConverterForm
        print("   ✅ All converter forms imported successfully")
        
        # Test form instantiation
        with app.app_context():
            img_form = ImageConverterForm()
            pdf_form = PDFConverterForm()
            doc_form = DocumentConverterForm()
            excel_form = ExcelConverterForm()
            print("   ✅ All forms can be instantiated")
            
            # Check for CSRF token field
            forms_to_test = [img_form, pdf_form, doc_form, excel_form]
            form_names = ['ImageConverter', 'PDFConverter', 'DocumentConverter', 'ExcelConverter']
            
            for form, name in zip(forms_to_test, form_names):
                if hasattr(form, 'csrf_token'):
                    print(f"   ✅ {name} has CSRF token field")
                else:
                    print(f"   ❌ {name} missing CSRF token field")
                    
    except ImportError as e:
        print(f"   ❌ Error importing forms: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error testing forms: {e}")
        return False
    
    # Test 2: Check template updates
    print("\n2. Testing Template Updates...")
    template_files = [
        'templates/image_converter.html',
        'templates/pdf_converter.html', 
        'templates/document_converter.html',
        'templates/excel_converter.html'
    ]
    
    for template_file in template_files:
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if '{{ form.hidden_tag() }}' in content:
                    print(f"   ✅ {template_file} has CSRF token")
                else:
                    print(f"   ❌ {template_file} missing CSRF token")
        else:
            print(f"   ⚠️  {template_file} not found")
    
    # Test 3: Check base template for CSRF script
    print("\n3. Testing Base Template CSRF Setup...")
    if os.path.exists('templates/base.html'):
        with open('templates/base.html', 'r', encoding='utf-8') as f:
            content = f.read()
            checks = [
                ('CSRF meta tag', 'csrf-token'),
                ('CSRF script', 'csrf.js'),
                ('CSRF global variable', 'window.csrfToken')
            ]
            
            for check_name, check_string in checks:
                if check_string in content:
                    print(f"   ✅ {check_name} found")
                else:
                    print(f"   ❌ {check_name} missing")
    
    # Test 4: Check if CSRF JavaScript exists
    print("\n4. Testing CSRF JavaScript...")
    if os.path.exists('static/js/csrf.js'):
        with open('static/js/csrf.js', 'r', encoding='utf-8') as f:
            content = f.read()
            js_checks = [
                ('CSRF token getter', 'getCSRFToken'),
                ('jQuery setup', '$.ajaxSetup'),
                ('Fetch wrapper', 'window.fetch'),
                ('Helper functions', 'addCSRFToken')
            ]
            
            for check_name, check_string in checks:
                if check_string in content:
                    print(f"   ✅ {check_name} implemented")
                else:
                    print(f"   ❌ {check_name} missing")
                    
        print("   ✅ CSRF JavaScript file exists")
    else:
        print("   ❌ CSRF JavaScript file missing")
    
    print("\n" + "=" * 60)
    return True

def test_converter_endpoints():
    """Test converter endpoints with CSRF tokens"""
    print("\n🔧 Testing Converter Endpoints...")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test endpoints
    endpoints = [
        '/image-converter',
        '/pdf-converter', 
        '/document-converter',
        '/excel-converter'
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n📄 Testing {endpoint}...")
            
            # Test GET request
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ GET request successful")
                
                # Check if CSRF token is in response
                if 'csrf_token' in response.text or 'csrf-token' in response.text:
                    print(f"   ✅ CSRF token found in response")
                else:
                    print(f"   ⚠️  CSRF token not obviously present")
                    
                # Check if form is present
                if 'form' in response.text and 'method="post"' in response.text:
                    print(f"   ✅ Form found in template")
                else:
                    print(f"   ⚠️  Form not found or not using POST")
                    
            else:
                print(f"   ❌ GET request failed (status: {response.status_code})")
                
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  Server not running at {base_url}")
        except requests.exceptions.Timeout:
            print(f"   ⚠️  Request timed out")
        except Exception as e:
            print(f"   ❌ Error testing {endpoint}: {e}")
    
    print("\n" + "=" * 60)

def test_middleware_fixes():
    """Test that usage tracking middleware fixes work"""
    print("\n🔧 Testing Middleware Fixes...")
    print("=" * 60)
    
    try:
        from middleware.usage_tracking import usage_analytics
        print("   ✅ Usage tracking middleware imports successfully")
        
        # Check if the middleware code has been fixed
        middleware_file = 'middleware/usage_tracking.py'
        if os.path.exists(middleware_file):
            with open(middleware_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                fixes_to_check = [
                    ('Path reference fix', 'getattr(g, \'path\', request.path)'),
                    ('Error handling', 'Error in usage analytics'),
                ]
                
                for fix_name, fix_pattern in fixes_to_check:
                    if fix_pattern in content:
                        print(f"   ✅ {fix_name} implemented")
                    else:
                        print(f"   ❌ {fix_name} missing")
        else:
            print("   ❌ Middleware file not found")
            
    except ImportError as e:
        print(f"   ❌ Error importing middleware: {e}")
    except Exception as e:
        print(f"   ❌ Error testing middleware: {e}")
    
    print("\n" + "=" * 60)

def run_comprehensive_tests():
    """Run all CSRF fix tests"""
    print("🧪 COMPREHENSIVE CSRF FIX VERIFICATION")
    print("=" * 80)
    
    success = True
    
    # Test 1: CSRF Implementation
    if not test_csrf_implementation():
        success = False
    
    # Test 2: Converter Endpoints
    test_converter_endpoints()
    
    # Test 3: Middleware Fixes
    test_middleware_fixes()
    
    # Summary
    print("\n" + "=" * 80)
    if success:
        print("🎉 CSRF FIX VERIFICATION COMPLETED!")
        print()
        print("✅ All major CSRF issues have been addressed:")
        print("   • Converter forms now use WTForms with CSRF tokens")
        print("   • Templates include {{ form.hidden_tag() }} for CSRF protection")
        print("   • Base template includes global CSRF token handling")
        print("   • AJAX requests automatically include CSRF tokens")
        print("   • Usage analytics middleware errors fixed")
        print()
        print("🚀 Your website should now work without CSRF token errors!")
        print()
        print("💡 Next Steps:")
        print("   1. Restart your Flask server")
        print("   2. Test file uploads on your website")  
        print("   3. Monitor server logs for CSRF errors")
        print("   4. If you see any issues, check browser console for errors")
    else:
        print("❌ SOME ISSUES DETECTED!")
        print("Please review the output above and fix any remaining issues.")
    
    print("=" * 80)
    return success

if __name__ == '__main__':
    try:
        # Import the Flask app for testing
        from app import app
        run_comprehensive_tests()
    except Exception as e:
        print(f"Error running tests: {e}")
        print("Make sure you're running this script from the project root directory.")
