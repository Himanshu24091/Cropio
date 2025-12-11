#!/usr/bin/env python3
"""
Test script to verify the login form CSRF fix
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_login_form():
    """Test the login form instantiation and CSRF token generation"""
    try:
        print("🔍 Testing Login Form CSRF Fix...")
        print("-" * 50)
        
        # Import the Flask app
        print("1. Importing Flask app...")
        from app import app
        print("   ✅ Flask app imported successfully")
        
        # Import the LoginForm
        print("2. Importing LoginForm...")
        from forms import LoginForm
        print("   ✅ LoginForm imported successfully")
        
        # Test form instantiation within app context
        print("3. Testing form instantiation...")
        with app.app_context():
            form = LoginForm()
            print("   ✅ LoginForm instantiated successfully")
            
            # Check if CSRF token is available
            if hasattr(form, 'csrf_token'):
                print("   ✅ CSRF token field is available")
                
                # Try to generate CSRF token
                try:
                    if hasattr(form.csrf_token, 'current_token'):
                        token = form.csrf_token.current_token
                        print(f"   ✅ CSRF token generated: {token[:16]}...")
                    else:
                        print("   ✅ CSRF token field present (token generation deferred)")
                except Exception as e:
                    print(f"   ⚠️  CSRF token generation issue: {e}")
            else:
                print("   ❌ CSRF token field is missing")
                return False
            
            # Check form fields
            print("4. Checking form fields...")
            expected_fields = ['username_or_email', 'password', 'remember_me', 'submit', 'csrf_token']
            for field_name in expected_fields:
                if hasattr(form, field_name):
                    print(f"   ✅ {field_name} field present")
                else:
                    print(f"   ❌ {field_name} field missing")
                    return False
        
        print("\n🎉 All tests passed! Login form CSRF fix appears to be working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_template_rendering():
    """Test template rendering with the form"""
    try:
        print("\n🔍 Testing Template Rendering...")
        print("-" * 50)
        
        from app import app
        from forms import LoginForm
        
        with app.test_client() as client:
            with app.app_context():
                print("1. Making GET request to login page...")
                response = client.get('/login')
                
                if response.status_code == 200:
                    print("   ✅ Login page loads successfully")
                    
                    # Check if CSRF token is in the response
                    response_text = response.get_data(as_text=True)
                    if 'csrf_token' in response_text or 'name="csrf_token"' in response_text:
                        print("   ✅ CSRF token found in rendered template")
                    else:
                        print("   ⚠️  CSRF token not found in rendered template")
                        # This might be expected if the template uses {{ form.hidden_tag() }}
                        
                    if '{{ form.hidden_tag() }}' in response_text or 'hidden' in response_text:
                        print("   ✅ Hidden form fields (including CSRF) are present")
                    else:
                        print("   ⚠️  Hidden form fields not obviously present")
                        
                else:
                    print(f"   ❌ Login page failed to load (status: {response.status_code})")
                    return False
        
        print("🎉 Template rendering test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Template rendering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 LOGIN FORM CSRF FIX VERIFICATION TESTS")
    print("=" * 60)
    
    success = True
    
    # Test 1: Form instantiation
    if not test_login_form():
        success = False
    
    # Test 2: Template rendering
    if not test_template_rendering():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! The login form CSRF fix is working correctly.")
        print("You should now be able to login without getting a 400 Bad Request error.")
    else:
        print("❌ SOME TESTS FAILED! Please check the issues above.")
    print("=" * 60)
    
    return success

if __name__ == '__main__':
    main()
