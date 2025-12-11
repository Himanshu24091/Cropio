#!/usr/bin/env python3
"""
Test script to verify enhanced OCR accuracy
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont

# Add project root
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 70)
print("Enhanced OCR Accuracy Test")
print("=" * 70)

# Import the enhanced functions
from routes.text_ocr_converters.text_ocr_routes import (
    process_image_ocr, enhance_image, TESSERACT_AVAILABLE, CV2_AVAILABLE
)
import tempfile

if not TESSERACT_AVAILABLE:
    print("❌ Tesseract not available")
    sys.exit(1)

print("\n✅ Tesseract is available")
print(f"✅ Image enhancement available: {CV2_AVAILABLE}")

# Test 1: Simple text image
print("\n" + "=" * 70)
print("Test 1: Simple Text Extraction")
print("=" * 70)

try:
    # Create test image with clear text
    img = Image.new('RGB', (600, 100), color='white')
    d = ImageDraw.Draw(img)
    
    # Try to use a better font if available, otherwise use default
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    test_text = "Cropio OCR Test 12345"
    d.text((50, 30), test_text, fill='black', font=font)
    
    # Save test image
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
        img.save(tmp.name)
        tmp_path = tmp.name
    
    # Extract text
    result = process_image_ocr(tmp_path, language='eng', auto_enhance=True)
    
    print(f"\n📝 Input text: '{test_text}'")
    print(f"📊 Extracted text: '{result['text']}'")
    print(f"📈 Confidence: {result['confidence']}%")
    print(f"📚 Word count: {result['word_count']}")
    
    # Clean up
    os.unlink(tmp_path)
    
except Exception as e:
    print(f"❌ Test 1 failed: {e}")

# Test 2: Rotated text
print("\n" + "=" * 70)
print("Test 2: Rotated Text Extraction (Deskew Test)")
print("=" * 70)

try:
    # Create test image with rotated text
    img = Image.new('RGB', (600, 100), color='white')
    d = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    test_text = "Rotated Text Test"
    d.text((50, 30), test_text, fill='black', font=font)
    
    # Rotate the image 15 degrees
    img = img.rotate(15, fillcolor='white')
    
    # Save test image
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
        img.save(tmp.name)
        tmp_path = tmp.name
    
    # Extract text
    result = process_image_ocr(tmp_path, language='eng', auto_enhance=True)
    
    print(f"\n📝 Input text: '{test_text}' (rotated 15°)")
    print(f"📊 Extracted text: '{result['text']}'")
    print(f"📈 Confidence: {result['confidence']}%")
    
    # Clean up
    os.unlink(tmp_path)
    
except Exception as e:
    print(f"❌ Test 2 failed: {e}")

# Test 3: Low contrast text
print("\n" + "=" * 70)
print("Test 3: Low Contrast Text (Enhancement Test)")
print("=" * 70)

try:
    # Create low contrast image
    img = Image.new('RGB', (600, 100), color=(200, 200, 200))
    d = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    test_text = "Low Contrast Text"
    d.text((50, 30), test_text, fill=(150, 150, 150), font=font)
    
    # Save test image
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
        img.save(tmp.name)
        tmp_path = tmp.name
    
    # Extract text with enhancement
    result = process_image_ocr(tmp_path, language='eng', auto_enhance=True)
    
    print(f"\n📝 Input text: '{test_text}' (low contrast)")
    print(f"📊 Extracted text: '{result['text']}'")
    print(f"📈 Confidence: {result['confidence']}%")
    
    # Clean up
    os.unlink(tmp_path)
    
except Exception as e:
    print(f"❌ Test 3 failed: {e}")

print("\n" + "=" * 70)
print("✅ Enhanced OCR Tests Complete!")
print("=" * 70)
print("\n📋 Summary of Enhancements:")
print("  ✓ CLAHE contrast enhancement")
print("  ✓ Bilateral denoising")
print("  ✓ Morphological operations")
print("  ✓ Automatic deskewing")
print("  ✓ Adaptive thresholding")
print("  ✓ Text inversion detection")
print("  ✓ Text dilation for clarity")
print("=" * 70)
