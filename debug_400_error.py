#!/usr/bin/env python3
"""
Debug the 400 error by testing the actual Flask app directly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from io import BytesIO
from PIL import Image
import tempfile

def test_direct_route():
    """Test the route directly using Flask's test client"""
    print("🔍 Direct Route Testing...")
    print("=" * 50)
    
    with app.test_client() as client:
        with app.app_context():
            # Test 1: GET request
            print("1. Testing GET request...")
            get_response = client.get('/image-converter')
            print(f"   Status: {get_response.status_code}")
            
            if get_response.status_code == 200:
                print("   ✅ GET request successful")
                
                # Extract CSRF token from the response
                response_text = get_response.data.decode()
                if 'csrf_token' in response_text:
                    print("   ✅ CSRF token present in response")
                    
                    # Extract actual token value
                    import re
                    csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response_text)
                    if csrf_match:
                        csrf_token = csrf_match.group(1)
                        print(f"   ✅ CSRF token extracted: {csrf_token[:16]}...")
                        
                        # Test 2: POST request with proper data
                        print("\n2. Testing POST request...")
                        
                        # Create test image
                        img = Image.new('RGB', (50, 50), color='green')
                        img_buffer = BytesIO()
                        img.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        
                        # Prepare form data
                        data = {
                            'format': 'jpg',
                            'csrf_token': csrf_token
                        }
                        
                        # Make POST request with file
                        data['file'] = (img_buffer, 'test.png', 'image/png')
                        post_response = client.post('/image-converter', 
                                                  data=data,
                                                  content_type='multipart/form-data',
                                                  buffered=True,
                                                  follow_redirects=False)
                        
                        print(f"   Status: {post_response.status_code}")
                        
                        if post_response.status_code == 400:
                            print("   ❌ Still getting 400 error")
                            print(f"   Response data preview: {post_response.data.decode()[:200]}...")
                            
                            # Try without file to see if that's the issue
                            print("\n3. Testing POST without file...")
                            post_no_file = client.post('/image-converter',
                                                     data={'format': 'jpg', 'csrf_token': csrf_token},
                                                     follow_redirects=False)
                            print(f"   Status without file: {post_no_file.status_code}")
                            
                        elif post_response.status_code == 200:
                            print("   ✅ POST request successful!")
                            content_type = post_response.headers.get('Content-Type', '')
                            print(f"   Content-Type: {content_type}")
                            
                        else:
                            print(f"   Status: {post_response.status_code}")
                            if post_response.status_code == 302:
                                location = post_response.headers.get('Location', '')
                                print(f"   Redirect to: {location}")
                                
                    else:
                        print("   ❌ Could not extract CSRF token")
                else:
                    print("   ❌ No CSRF token in response")
            else:
                print(f"   ❌ GET failed with status {get_response.status_code}")

def test_form_validation():
    """Test form validation specifically"""
    print("\n🔍 Form Validation Testing...")
    print("=" * 50)
    
    from forms import ImageConverterForm
    
    with app.app_context():
        # Create a request context for testing
        with app.test_request_context('/', method='POST'):
            form = ImageConverterForm()
            print(f"   Form created: {type(form)}")
            print(f"   Form fields: {list(form._fields.keys())}")
            
            # Check if we can create the form without errors
            if hasattr(form, 'csrf_token'):
                print("   ✅ CSRF token field exists")
            else:
                print("   ❌ CSRF token field missing")

if __name__ == '__main__':
    print("🧪 DEBUGGING 400 ERROR")
    print("=" * 60)
    
    test_direct_route()
    test_form_validation()
    
    print("\n" + "=" * 60)
    print("Debug session complete.")
    print("If still getting 400 errors, the issue might be in Flask configuration")
    print("or middleware interference.")
    print("=" * 60)
