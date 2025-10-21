#!/usr/bin/env python3
"""
Test the image converter fixes
"""
import requests
from io import BytesIO
from PIL import Image
import re

def test_image_conversion():
    """Test image conversion with proper format handling"""
    print("🧪 Testing Image Converter Fixes...")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    try:
        # Step 1: Get the page and extract CSRF token
        print("1. Getting page and CSRF token...")
        response = requests.get(f"{base_url}/image-converter", timeout=10)
        
        if response.status_code != 200:
            print(f"   ❌ Failed to load page (status: {response.status_code})")
            return False
            
        # Extract CSRF token
        csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', response.text)
        if not csrf_match:
            print("   ❌ Could not extract CSRF token")
            return False
            
        csrf_token = csrf_match.group(1)
        print(f"   ✅ CSRF token extracted: {csrf_token[:16]}...")
        
        # Step 2: Create test image
        print("\n2. Creating test image...")
        img = Image.new('RGB', (100, 100), color='blue')
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        print("   ✅ Created 100x100 blue PNG image")
        
        # Step 3: Test conversion to JPG (the format that was failing)
        print("\n3. Testing PNG to JPG conversion...")
        
        files = {
            'file': ('test.png', img_buffer, 'image/png')
        }
        
        data = {
            'format': 'jpg',
            'csrf_token': csrf_token
        }
        
        img_buffer.seek(0)  # Reset buffer
        
        post_response = requests.post(
            f"{base_url}/image-converter",
            files=files,
            data=data,
            timeout=30,
            allow_redirects=False  # Don't follow redirects to see exact response
        )
        
        print(f"   📊 Response status: {post_response.status_code}")
        
        if post_response.status_code == 200:
            # Check if we got an image file
            content_type = post_response.headers.get('Content-Type', '')
            if content_type.startswith('image/'):
                print(f"   ✅ Conversion successful! Received {content_type}")
                print(f"   📁 Output file size: {len(post_response.content)} bytes")
                
                # Verify it's a valid JPEG
                try:
                    output_img = Image.open(BytesIO(post_response.content))
                    print(f"   ✅ Output format: {output_img.format}")
                    print(f"   ✅ Output size: {output_img.size}")
                    
                    if output_img.format == 'JPEG':
                        print("   🎉 JPG conversion working perfectly!")
                        return True
                    else:
                        print(f"   ⚠️  Expected JPEG, got {output_img.format}")
                        
                except Exception as e:
                    print(f"   ❌ Could not verify output image: {e}")
                    
            else:
                print(f"   ❌ Expected image, got {content_type}")
                print(f"   📄 Response preview: {post_response.text[:200]}...")
                
        elif post_response.status_code == 302:
            # Check if it's redirecting back to the same page (likely with flash message)
            location = post_response.headers.get('Location', '')
            print(f"   📍 Redirecting to: {location}")
            
            # Follow the redirect to see the flash message
            redirect_response = requests.get(location if location.startswith('http') else f"{base_url}{location}")
            if 'Error converting image' in redirect_response.text:
                print("   ❌ Still getting conversion errors")
            else:
                print("   ✅ Redirect successful, no obvious errors")
                
        else:
            print(f"   ❌ Conversion failed with status {post_response.status_code}")
            print(f"   📄 Response: {post_response.text[:200]}...")
            
        return False
        
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to server. Make sure Flask is running.")
        return False
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

if __name__ == '__main__':
    success = test_image_conversion()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 IMAGE CONVERTER FIXES WORKING!")
        print("✅ CSRF tokens working")
        print("✅ JPG format conversion working") 
        print("✅ No more 'JPG' format errors")
    else:
        print("❌ Still some issues to resolve")
        print("Check the Flask server logs for more details")
    print("=" * 50)
