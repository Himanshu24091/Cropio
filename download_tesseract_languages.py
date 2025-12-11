#!/usr/bin/env python3
"""
Script to download additional language data for Tesseract OCR
"""

import os
import urllib.request
import urllib.error

TESSDATA_BEST_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/main/"
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tessdata'

# Languages to download (supports our application)
LANGUAGES = {
    'hin': 'Hindi',
    'spa': 'Spanish',
    'fra': 'French',
    'deu': 'German',
    'ara': 'Arabic',
    'chi_sim': 'Chinese Simplified',
    'jpn': 'Japanese',
    'kor': 'Korean',
    'rus': 'Russian',
}

def download_language(lang_code, lang_name):
    """Download language training data"""
    filename = f"{lang_code}.traineddata"
    filepath = os.path.join(TESSERACT_PATH, filename)
    
    # Skip if already exists
    if os.path.exists(filepath):
        print(f"✅ {lang_name} ({lang_code}) - Already installed")
        return True
    
    url = TESSDATA_BEST_URL + filename
    print(f"⏳ Downloading {lang_name} ({lang_code})...")
    
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"✅ {lang_name} ({lang_code}) - Downloaded successfully")
        return True
    except urllib.error.URLError as e:
        print(f"❌ {lang_name} ({lang_code}) - Failed to download: {e}")
        return False
    except Exception as e:
        print(f"❌ {lang_name} ({lang_code}) - Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Tesseract OCR Language Data Downloader")
    print("=" * 60)
    print(f"\n📁 Tesseract Path: {TESSERACT_PATH}")
    
    # Check if tessdata directory exists
    if not os.path.exists(TESSERACT_PATH):
        print(f"❌ Tesseract tessdata directory not found at: {TESSERACT_PATH}")
        return
    
    print("\n🌍 Available languages to download:")
    for code, name in LANGUAGES.items():
        print(f"   - {name} ({code})")
    
    print("\n📥 Starting downloads...\n")
    
    success_count = 0
    for lang_code, lang_name in LANGUAGES.items():
        if download_language(lang_code, lang_name):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Downloads complete! {success_count}/{len(LANGUAGES)} languages ready")
    print("=" * 60)

if __name__ == '__main__':
    main()
