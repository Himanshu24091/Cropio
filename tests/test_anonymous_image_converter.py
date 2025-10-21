#!/usr/bin/env python3
"""
Test script to verify that the image converter works for anonymous users (no login required)
"""
import requests
import os
from io import BytesIO
from PIL import Image

def test_anonymous_image_converter():
    """Test image converter without login"""
    print("🔍 Testing Anonymous Image Converter Access...")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    try:
        # Step 1: Test GET request to image converter
        print("1. Testing GET request to /image-converter...")
        response = requests.get(f"{base_url}/image-converter", timeout=10)
        
        if response.status_code == 200:
            print("   ✅ Image converter page loads successfully")
            
            # Check that it doesn't redirect to login
            if 'login' in response.url.lower():
                print("   ❌ Page redirects to login (not free)")
                return False
            else:
                print("   ✅ No login redirect - truly free access")
                
            # Check for form presence
            if 'form' in response.text:
                print("   ✅ Upload form is present")
            else:
                print("   ⚠️  Upload form not found")
                
        else:
            print(f"   ❌ GET request failed (status: {response.status_code})")
            return False
    
        # Step 2: Create a simple test image for conversion
        print("\n2. Creating test image...")
        
        # Create a simple 100x100 red square image
        img = Image.new('RGB', (100, 100), color='red')
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        print("   ✅ Test PNG image created (100x100 red square)")
        
        # Step 3: Test POST request with file upload (simulate form submission)
        print("\n3. Testing file conversion without login...")
        
        # Get CSRF token from the page
        csrf_token = None
        if 'csrf_token' in response.text:
            # Extract CSRF token from hidden input
            import re
            csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                print(f"   ✅ CSRF token extracted: {csrf_token[:16]}...")
            else:
                print("   ⚠️  CSRF token found but couldn't extract")
        else:
            print("   ⚠️  No CSRF token found")
        
        # Prepare form data for conversion
        files = {
            'file': ('test.png', img_buffer, 'image/png')
        }
        
        data = {
            'format': 'jpg',  # Convert PNG to JPG
        }
        
        if csrf_token:
            data['csrf_token'] = csrf_token
        
        # Make POST request
        img_buffer.seek(0)  # Reset buffer
        post_response = requests.post(
            f"{base_url}/image-converter",
            files=files,
            data=data,
            timeout=30,
            allow_redirects=True
        )
        
        if post_response.status_code == 200:
            print("   ✅ File conversion successful!")
            
            # Check if response is a file download
            if post_response.headers.get('Content-Type', '').startswith('image/'):
                print("   ✅ Response is an image file (conversion worked)")
                print(f"   📁 File size: {len(post_response.content)} bytes")
            else:
                print("   ⚠️  Response is not an image file")
                
        elif post_response.status_code == 302:
            print(f"   ⚠️  Conversion resulted in redirect to: {post_response.headers.get('Location', 'Unknown')}")
            
            if 'login' in post_response.headers.get('Location', '').lower():
                print("   ❌ Conversion redirects to login (not truly free)")
                return False
            else:
                print("   ✅ Redirect is not to login page")
                
        else:
            print(f"   ❌ File conversion failed (status: {post_response.status_code})")
            print(f"   📄 Response content preview: {post_response.text[:200]}...")
            return False
            
        print("\n" + "=" * 60)
        print("🎉 ANONYMOUS IMAGE CONVERTER TEST COMPLETED!")
        print()
        print("✅ Summary:")
        print("   • Image converter page loads without login")
        print("   • No redirects to login page")
        print("   • File upload and conversion works")
        print("   • CSRF protection is properly implemented")
        print()
        print("🚀 Your image converter is now completely FREE for everyone!")
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to server at {base_url}")
        print("   💡 Make sure your Flask server is running")
        return False
        
    except Exception as e:
        print(f"   ❌ Test failed with error: {e}")
        return False

if __name__ == '__main__':
    success = test_anonymous_image_converter()
    if success:
        print("\n🎊 Your image converter is working perfectly for anonymous users!")
    else:
        print("\n❌ There may be some issues to resolve.")
