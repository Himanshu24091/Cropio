#!/usr/bin/env python3
"""Test the OCR optimizations and fixes"""

import sys
import os
import time
import tempfile

sys.path.insert(0, os.getcwd())

from routes.text_ocr_converters.text_ocr_routes import export_to_pdf, export_to_txt, export_to_docx

print("=" * 60)
print("OCR Optimization Tests")
print("=" * 60)

# Test 1: PDF Export with special characters
print("\n1️⃣  Testing PDF export with problematic text...")
test_text = """This is a test of the OCR enhancement.
It contains multiple paragraphs.

Special characters: <>&\"'
Line breaks and
multiple lines
should work fine now.

More text here with various characters: @#$%^&*()"""

try:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as f:
        pdf_path = f.name
    
    start = time.time()
    result = export_to_pdf(test_text, pdf_path)
    elapsed = time.time() - start
    
    if result and os.path.exists(pdf_path):
        size = os.path.getsize(pdf_path)
        print(f"✅ PDF export successful!")
        print(f"   Size: {size} bytes")
        print(f"   Time: {elapsed:.2f}s")
        os.remove(pdf_path)
    else:
        print(f"❌ PDF export failed")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: TXT Export
print("\n2️⃣  Testing TXT export...")
try:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
        txt_path = f.name
    
    result = export_to_txt(test_text, txt_path)
    if result and os.path.exists(txt_path):
        size = os.path.getsize(txt_path)
        print(f"✅ TXT export successful! Size: {size} bytes")
        os.remove(txt_path)
    else:
        print(f"❌ TXT export failed")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: DOCX Export
print("\n3️⃣  Testing DOCX export...")
try:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as f:
        docx_path = f.name
    
    result = export_to_docx(test_text, docx_path)
    if result and os.path.exists(docx_path):
        size = os.path.getsize(docx_path)
        print(f"✅ DOCX export successful! Size: {size} bytes")
        os.remove(docx_path)
    else:
        print(f"❌ DOCX export failed")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ All tests completed!")
print("=" * 60)
