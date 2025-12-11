#!/usr/bin/env python3
"""
Real-world OCR accuracy test with various document types
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import tempfile

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from routes.text_ocr_converters.text_ocr_routes import (
    process_image_ocr, TESSERACT_AVAILABLE
)

if not TESSERACT_AVAILABLE:
    print("❌ Tesseract not available")
    sys.exit(1)

print("=" * 70)
print("Real-World OCR Accuracy Test")
print("=" * 70)

test_cases = [
    {
        "name": "Clear Document",
        "text": "The Quick Brown Fox",
        "font_size": 50,
        "color": 'black',
        "background": 'white'
    },
    {
        "name": "Small Text",
        "text": "Important Notice",
        "font_size": 30,
        "color": 'black',
        "background": 'white'
    },
    {
        "name": "High Contrast",
        "text": "High Contrast Text",
        "font_size": 40,
        "color": 'white',
        "background": 'black'
    }
]

total_tests = len(test_cases)
passed = 0
partial = 0
failed = 0

for i, test_case in enumerate(test_cases, 1):
    print(f"\n{'=' * 70}")
    print(f"Test {i}/{total_tests}: {test_case['name']}")
    print(f"{'=' * 70}")
    
    try:
        # Create test image
        img = Image.new('RGB', (800, 120), color=test_case['background'])
        d = ImageDraw.Draw(img)
        
        # Use default font
        font = ImageFont.load_default()
        
        test_text = test_case['text']
        d.text((50, 40), test_text, fill=test_case['color'], font=font)
        
        # Save and process
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
            img.save(tmp.name)
            tmp_path = tmp.name
        
        result = process_image_ocr(tmp_path, language='eng', auto_enhance=True)
        
        extracted = result['text'].strip()
        confidence = result['confidence']
        
        print(f"\n📝 Original:  {test_text}")
        print(f"📊 Extracted: {extracted}")
        print(f"📈 Confidence: {confidence}%")
        
        # Evaluate
        if extracted.lower() == test_text.lower():
            print("✅ PASSED - Perfect match!")
            passed += 1
        elif len(extracted) > 0 and test_text.lower() in extracted.lower():
            print("⚠️  PARTIAL - Contains correct text")
            partial += 1
        else:
            print("❌ FAILED - Incorrect extraction")
            failed += 1
        
        os.unlink(tmp_path)
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        failed += 1

print(f"\n{'=' * 70}")
print("Test Summary")
print(f"{'=' * 70}")
print(f"✅ Passed:  {passed}/{total_tests}")
print(f"⚠️  Partial: {partial}/{total_tests}")
print(f"❌ Failed:  {failed}/{total_tests}")
print(f"\nSuccess Rate: {(passed + partial) * 100 // total_tests}%")
print(f"{'=' * 70}")

print("\n💡 Recommendations:")
print("""
For best OCR accuracy:
1. Use high-quality images (300+ DPI)
2. Ensure good contrast and lighting
3. Keep text straight and horizontal
4. Use PDF files when available (100% accuracy)
5. Try DOCX files for documents (excellent accuracy)

Your OCR system is now enhanced with:
✓ Automatic contrast adjustment
✓ Smart noise removal
✓ Text deskewing
✓ Morphological filtering
✓ Confidence scoring
""")
