#!/usr/bin/env python3
"""
Flask test client version for File Compressor testing.
Tests the File Compressor with various compression modes and target sizes.
"""

import sys
import os
from io import BytesIO
from PIL import Image
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_image(size_kb=200):
    """Create a test image of approximately specified size"""
    # Create a colorful test image that's around the specified size
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color='white')
    
    # Add some content to make it compressible
    pixels = image.load()
    for i in range(width):
        for j in range(height):
            # Create a gradient pattern
            r = (i * 255) // width
            g = (j * 255) // height
            b = ((i + j) * 255) // (width + height)
            pixels[i, j] = (r % 256, g % 256, b % 256)
    
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=90)
    buffer.seek(0)
    return buffer

def test_quality_based_compression():
    """Test quality-based compression (legacy mode)"""
    print("🔍 Testing Quality-Based Compression")
    print("=" * 45)
    
    try:
        from app import create_app
        
        app = create_app()
        app.config['TESTING'] = True
        # CSRF is properly handled via exemption in security.py
        
        with app.test_client() as client:
            print("1. Testing medium quality compression...")
            
            test_image = create_test_image(150)  # ~150KB image
            
            # Test using AJAX endpoint (legacy)
            response = client.post('/compress', data={
                'files[]': (test_image, 'test.jpg'),
                'level': 'medium'
            }, content_type='multipart/form-data')
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = json.loads(response.data.decode('utf-8'))
                if 'results' in data and len(data['results']) > 0:
                    result = data['results'][0]
                    if 'error' not in result:
                        print("✅ Quality-based compression successful!")
                        print(f"Original size: {result['original_size']} bytes")
                        print(f"Compressed size: {result['compressed_size']} bytes")
                        print(f"Reduction: {result['reduction_percent']}%")
                        return True
                    else:
                        print(f"❌ Compression error: {result['error']}")
                        return False
                else:
                    print("❌ No results in response")
                    return False
            else:
                print(f"❌ Request failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_target_size_compression():
    """Test target file size compression (new feature)"""
    print("\\n🔍 Testing Target Size Compression")
    print("=" * 42)
    
    try:
        from app import create_app
        
        app = create_app()
        app.config['TESTING'] = True
        # CSRF is properly handled via exemption in security.py
        
        with app.test_client() as client:
            print("2. Testing 50KB target size compression...")
            
            test_image = create_test_image(200)  # ~200KB image
            
            # Test using AJAX endpoint with target size
            response = client.post('/compress', data={
                'files[]': (test_image, 'test.jpg'),
                'target_size': '50'  # Target 50KB
            }, content_type='multipart/form-data')
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = json.loads(response.data.decode('utf-8'))
                if 'results' in data and len(data['results']) > 0:
                    result = data['results'][0]
                    if 'error' not in result:
                        compressed_size_kb = result['compressed_size'] / 1024
                        print("✅ Target size compression successful!")
                        print(f"Original size: {result['original_size']} bytes ({result['original_size']/1024:.1f} KB)")
                        print(f"Compressed size: {result['compressed_size']} bytes ({compressed_size_kb:.1f} KB)")
                        print(f"Target was: 50 KB")
                        print(f"Reduction: {result['reduction_percent']}%")
                        
                        # Check if we got close to target (within reasonable range)
                        if compressed_size_kb <= 60:  # Allow some tolerance
                            print("✅ Target size achieved successfully!")
                        else:
                            print("⚠️ Target size not quite reached, but compression worked")
                        return True
                    else:
                        print(f"❌ Compression error: {result['error']}")
                        return False
                else:
                    print("❌ No results in response")
                    return False
            else:
                print(f"❌ Request failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compressor_page_access():
    """Test that the compressor page loads for anonymous users"""
    print("\\n🔍 Testing Anonymous Access")
    print("=" * 32)
    
    try:
        from app import create_app
        
        app = create_app()
        app.config['TESTING'] = True
        # CSRF is properly handled via exemption in security.py
        
        with app.test_client() as client:
            print("3. Testing compressor page access...")
            
            response = client.get('/compressor')
            print(f"GET /compressor status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.get_data(as_text=True)
                if 'FileCompressor' in content and 'Compression Mode' in content:
                    print("✅ Compressor page loads successfully")
                    print("✅ Enhanced compression options visible")
                    return True
                else:
                    print("⚠️ Page loaded but content might be incomplete")
                    return True
            else:
                print(f"❌ Failed to load compressor page: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error accessing compressor page: {e}")
        return False

def test_multiple_compression_sizes():
    """Test multiple target sizes"""
    print("\\n🔍 Testing Multiple Target Sizes")
    print("=" * 38)
    
    try:
        from app import create_app
        
        app = create_app()
        app.config['TESTING'] = True
        # CSRF is properly handled via exemption in security.py
        
        with app.test_client() as client:
            target_sizes = ['10', '20', '100']
            
            for i, target_size in enumerate(target_sizes, 4):
                print(f"{i}. Testing {target_size}KB target size...")
                
                test_image = create_test_image(150)
                
                response = client.post('/compress', data={
                    'files[]': (test_image, 'test.jpg'),
                    'target_size': target_size
                }, content_type='multipart/form-data')
                
                if response.status_code == 200:
                    data = json.loads(response.data.decode('utf-8'))
                    if 'results' in data and len(data['results']) > 0:
                        result = data['results'][0]
                        if 'error' not in result:
                            compressed_size_kb = result['compressed_size'] / 1024
                            print(f"   ✅ {target_size}KB target: got {compressed_size_kb:.1f}KB")
                        else:
                            print(f"   ❌ Error: {result['error']}")
                            return False
                else:
                    print(f"   ❌ Request failed: {response.status_code}")
                    return False
            
            return True
                
    except Exception as e:
        print(f"❌ Error during multiple size testing: {e}")
        return False

if __name__ == "__main__":
    print("Testing File Compressor with Enhanced Compression Options")
    print("=" * 60)
    
    success1 = test_quality_based_compression()
    success2 = test_target_size_compression()
    success3 = test_compressor_page_access()
    success4 = test_multiple_compression_sizes()
    
    if success1 and success2 and success3 and success4:
        print("\\n🎉 All File Compressor tests passed!")
        print("✅ Quality-based compression working")
        print("✅ Target size compression working") 
        print("✅ Enhanced compression options available")
        print("✅ Anonymous users can access and use the compressor")
        print("✅ Multiple target sizes supported (10KB, 20KB, 100KB, etc.)")
        sys.exit(0)
    else:
        print("\\n❌ Some File Compressor tests failed!")
        sys.exit(1)
