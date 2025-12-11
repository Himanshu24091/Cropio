#!/usr/bin/env python3
"""
Test script to verify Tesseract OCR is working with the Cropio setup
"""

import sys
import os

# Add project root
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 60)
print("Tesseract OCR Configuration Test")
print("=" * 60)

# Test 1: Import the routes module
print("\n1️⃣  Testing route imports...")
try:
    from routes.text_ocr_converters.text_ocr_routes import TESSERACT_AVAILABLE, PIL_AVAILABLE
    print("✅ Routes module imported successfully")
except Exception as e:
    print(f"❌ Failed to import routes: {e}")
    sys.exit(1)

# Test 2: Check Tesseract availability
print("\n2️⃣  Checking Tesseract availability...")
if TESSERACT_AVAILABLE:
    print("✅ Tesseract is available")
else:
    print("❌ Tesseract is NOT available")

# Test 3: Check PIL availability
print("\n3️⃣  Checking PIL availability...")
if PIL_AVAILABLE:
    print("✅ PIL/Pillow is available")
else:
    print("❌ PIL/Pillow is NOT available")

# Test 4: Try a simple OCR operation
if TESSERACT_AVAILABLE and PIL_AVAILABLE:
    print("\n4️⃣  Testing OCR functionality...")
    try:
        import pytesseract
        from PIL import Image, ImageDraw
        
        # Create a test image
        img = Image.new('RGB', (200, 50), color='white')
        d = ImageDraw.Draw(img)
        d.text((10, 10), 'Cropio Test', fill='black')
        
        # Try OCR
        text = pytesseract.image_to_string(img)
        if text.strip():
            print(f"✅ OCR working! Extracted: '{text.strip()}'")
        else:
            print("⚠️  OCR returned empty result")
    except Exception as e:
        print(f"❌ OCR test failed: {e}")

print("\n" + "=" * 60)
print("✅ Configuration check complete!")
print("=" * 60)
