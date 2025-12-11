#!/usr/bin/env python3
"""
Simple script to download Tesseract language files
Run this with admin privileges if installing to Program Files
"""

import os
import sys
import urllib.request
from pathlib import Path

TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/main/"
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tessdata'

# Create temp directory if we can't write to Program Files
TEMP_PATH = Path.home() / 'AppData' / 'Local' / 'Tesseract-OCR' / 'tessdata'
TEMP_PATH.mkdir(parents=True, exist_ok=True)

print("📥 Tesseract Language Downloader")
print("=" * 50)

languages = {
    'hin.traineddata': 'Hindi',
    'spa.traineddata': 'Spanish', 
    'fra.traineddata': 'French',
}

# Try Program Files first, fall back to temp
target_path = TESSERACT_PATH if os.access(os.path.dirname(TESSERACT_PATH), os.W_OK) else str(TEMP_PATH)
print(f"\n📁 Download path: {target_path}\n")

for filename, lang_name in languages.items():
    filepath = os.path.join(target_path, filename)
    
    if os.path.exists(filepath):
        print(f"✅ {lang_name} - Already installed")
        continue
    
    url = TESSDATA_URL + filename
    print(f"⏳ Downloading {lang_name}...")
    
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"✅ {lang_name} - Downloaded")
    except Exception as e:
        print(f"❌ {lang_name} - Failed: {e}")

print("\n✅ Done!")
