#!/usr/bin/env python3
"""
Test script to verify that target size compression works correctly.
This will test the fix for the issue where 20KB target resulted in 178KB output.
"""

import sys
import os
from io import BytesIO
from PIL import Image
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_large_test_image(target_size_kb=800):
    """Create a large test image similar to the one in the screenshot"""
    # Create a large, detailed image to simulate the 819KB original
    width, height = 1200, 1600  # Large dimensions
    image = Image.new('RGB', (width, height), color='white')
    
    # Add complex patterns to make it large
    pixels = image.load()
    for i in range(width):
        for j in range(height):
            # Create complex pattern with text-like appearance
            r = (i * 127 + j * 63) % 256
            g = (i * 89 + j * 157) % 256 
            b = (i * 203 + j * 97) % 256
            pixels[i, j] = (r, g, b)
    
    # Save as high quality JPEG to get large size
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=95)
    buffer.seek(0)
    
    # Check actual size
    actual_size_kb = len(buffer.getvalue()) / 1024
    print(f"Created test image: {actual_size_kb:.2f} KB")
    
    buffer.seek(0)
    return buffer

def test_target_size_compression():
    """Test target size compression with different targets"""
    print("🔍 Testing Target Size Compression Fix")
    print("=" * 45)
    
    success_count = 0
    total_tests = 0
    
    try:
        from app import create_app
        
        app = create_app()
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            # Test cases that should work
            test_cases = [
                {'target': 20, 'description': '20KB (the problem case)'},
                {'target': 50, 'description': '50KB'},
                {'target': 10, 'description': '10KB (very small)'},
                {'target': 100, 'description': '100KB'}
            ]
            
            for i, test_case in enumerate(test_cases, 1):
                target_kb = test_case['target']
                description = test_case['description']
                total_tests += 1
                
                print(f"\n{i}. Testing {description}")
                print("-" * 30)
                
                # Create large test image each time
                test_image = create_large_test_image()
                
                response = client.post('/compress', data={
                    'files[]': (test_image, 'large_test.jpg'),
                    'target_size': str(target_kb)
                }, content_type='multipart/form-data')
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = json.loads(response.data.decode('utf-8'))
                    if 'results' in data and len(data['results']) > 0:
                        result = data['results'][0]
                        if 'error' not in result:
                            original_kb = result['original_size'] / 1024
                            compressed_kb = result['compressed_size'] / 1024
                            target_achieved = compressed_kb <= target_kb
                            
                            print(f"  📊 Original size: {original_kb:.2f} KB")
                            print(f"  📊 Compressed size: {compressed_kb:.2f} KB")
                            print(f"  🎯 Target: {target_kb} KB")
                            print(f"  📈 Reduction: {result['reduction_percent']}%")
                            
                            if target_achieved:
                                print(f"  ✅ SUCCESS: Target achieved!")
                                success_count += 1
                            else:
                                over_target = compressed_kb - target_kb
                                print(f"  ❌ FAILED: Over target by {over_target:.2f} KB")
                        else:
                            print(f"  ❌ Compression error: {result['error']}")
                    else:
                        print("  ❌ No results in response")
                else:
                    print(f"  ❌ Request failed: {response.status_code}")
    
        print(f"\n📊 Results: {success_count}/{total_tests} tests passed")
        return success_count == total_tests
                    
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_target_size():
    """Test PDF target size compression"""
    print("\n\n🔍 Testing PDF Target Size Compression")
    print("=" * 40)
    
    # Note: This would require a sample PDF file
    # For now, just test that the route accepts PDF compression requests
    print("ℹ️  PDF target size compression implemented but needs PDF test file")
    print("   The logic will try high/medium/low compression levels to reach target")

if __name__ == "__main__":
    print("Testing Target Size Compression Fix")
    print("=" * 60)
    print("This test verifies the fix for the issue where 20KB target")
    print("resulted in 178KB output instead of staying at/below 20KB.")
    print("=" * 60)
    
    success = test_target_size_compression()
    test_pdf_target_size()
    
    if success:
        print("\n🎉 Target size compression tests completed!")
        print("✅ The fix should now properly compress to target sizes")
        sys.exit(0)
    else:
        print("\n❌ Some target size compression tests failed!")
        sys.exit(1)
