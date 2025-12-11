#!/usr/bin/env python3
"""
Verification script to test the separation of PPTX to PDF and PDF to PPTX converters
"""
import requests
import os

def test_routes():
    """Test that both converter routes are accessible"""
    base_url = "http://localhost:5000"
    
    # Test PPTX to PDF converter (existing, now simplified)
    print("Testing PPTX to PDF converter route...")
    try:
        response = requests.get(f"{base_url}/convert/presentation/")
        if response.status_code == 200:
            print("✅ PPTX to PDF converter route is accessible")
            # Check if PDF to PPTX functionality has been removed
            if "PDF → PPTX" in response.text or "pdf-to-pptx" in response.text:
                print("❌ PDF to PPTX functionality still present in PPTX converter")
            else:
                print("✅ PDF to PPTX functionality successfully removed from PPTX converter")
        else:
            print(f"❌ PPTX to PDF converter route returned {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing PPTX to PDF converter: {e}")
    
    # Test PDF to PPTX converter (new, separate)
    print("\nTesting PDF to PPTX converter route...")
    try:
        response = requests.get(f"{base_url}/convert/pdf-to-pptx/")
        if response.status_code == 200:
            print("✅ PDF to PPTX converter route is accessible")
            # Check if it contains the expected functionality
            if "PDF to PowerPoint" in response.text and "conversion_mode" in response.text:
                print("✅ PDF to PPTX converter contains expected functionality")
            else:
                print("❌ PDF to PPTX converter missing expected functionality")
        else:
            print(f"❌ PDF to PPTX converter route returned {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing PDF to PPTX converter: {e}")

def test_status_endpoints():
    """Test status endpoints for both converters"""
    base_url = "http://localhost:5000"
    
    print("\nTesting status endpoints...")
    
    # Test PPTX to PDF status
    try:
        response = requests.get(f"{base_url}/convert/presentation/status")
        if response.status_code == 200:
            data = response.json()
            if 'features' in data and 'pptx_to_pdf' in data['features']:
                print("✅ PPTX to PDF status endpoint working correctly")
            else:
                print("❌ PPTX to PDF status endpoint missing expected data")
        else:
            print(f"❌ PPTX to PDF status endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing PPTX to PDF status: {e}")
    
    # Test PDF to PPTX status
    try:
        response = requests.get(f"{base_url}/convert/pdf-to-pptx/status")
        if response.status_code == 200:
            data = response.json()
            if 'features' in data and ('pdf_to_pptx_basic' in data['features'] or 'pdf_to_pptx_accurate' in data['features']):
                print("✅ PDF to PPTX status endpoint working correctly")
            else:
                print("❌ PDF to PPTX status endpoint missing expected data")
        else:
            print(f"❌ PDF to PPTX status endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing PDF to PPTX status: {e}")

def test_file_structure():
    """Test that all required files have been created"""
    print("\nTesting file structure...")
    
    files_to_check = [
        ("templates/pdf_presentation_converter.html", "PDF to PPTX HTML template"),
        ("static/css/pdf_presentation_converter.css", "PDF to PPTX CSS file"),
        ("static/js/pdf_presentation_converter.js", "PDF to PPTX JavaScript file"),
        ("routes/pdf_presentation_converter_routes.py", "PDF to PPTX routes"),
        ("utils/pdf_presentation_utils.py", "PDF to PPTX utilities"),
    ]
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"✅ {description} exists")
        else:
            print(f"❌ {description} missing at {file_path}")

if __name__ == "__main__":
    print("🔍 Testing PPTX to PDF and PDF to PPTX converter separation")
    print("=" * 60)
    
    # Note: These tests require the Flask app to be running
    print("📝 Note: Please start the Flask app first with 'python app.py'")
    print("   Then run this test script in another terminal")
    print()
    
    test_file_structure()
    
    # Uncomment these if you want to test the routes
    # (requires the Flask app to be running)
    # test_routes()
    # test_status_endpoints()
    
    print("\n✅ File structure verification complete!")
    print("💡 To test the web interface:")
    print("   1. Start the Flask app: python app.py")
    print("   2. Visit http://localhost:5000/convert/presentation/ for PPTX to PDF")
    print("   3. Visit http://localhost:5000/convert/pdf-to-pptx/ for PDF to PPTX")