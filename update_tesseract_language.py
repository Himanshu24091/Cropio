#!/usr/bin/env python3
"""
Download English language data for Tesseract from GitHub
This will significantly improve OCR accuracy
"""

import os
import urllib.request
import urllib.error
import shutil
from pathlib import Path

TESSERACT_PATH = Path(r'C:\Program Files\Tesseract-OCR\tessdata')
LANG_FILE = 'eng.traineddata'
LANG_PATH = TESSERACT_PATH / LANG_FILE

# URL for the best quality language data
GITHUB_URL = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/main/"

print("=" * 70)
print("Tesseract Language Data Downloader")
print("=" * 70)

if not TESSERACT_PATH.exists():
    print(f"❌ Tesseract directory not found: {TESSERACT_PATH}")
    exit(1)

print(f"\n📁 Tesseract Path: {TESSERACT_PATH}")

# Check if current file is the fast version
current_size = 0
if LANG_PATH.exists():
    current_size = LANG_PATH.stat().st_size / (1024 * 1024)
    print(f"📦 Current eng.traineddata: {current_size:.2f} MB")

# Download best quality version
print(f"\n⏳ Downloading better quality language data from GitHub...")
print(f"   This provides MUCH better accuracy than the default version")

url = GITHUB_URL + LANG_FILE
temp_file = TESSERACT_PATH / "eng_temp.traineddata"

try:
    print(f"📥 Downloading from: {url}")
    
    # Create a custom progress bar
    def download_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(downloaded * 100 / total_size, 100)
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            print(f'   [{bar}] {percent:.1f}%', end='\r')
    
    # Download with progress
    urllib.request.urlretrieve(url, str(temp_file), download_progress)
    print()  # New line after progress
    
    new_size = temp_file.stat().st_size / (1024 * 1024)
    print(f"✅ Downloaded: {new_size:.2f} MB")
    
    # Backup old version
    if LANG_PATH.exists():
        backup_path = TESSERACT_PATH / "eng.traineddata.backup"
        shutil.copy2(LANG_PATH, backup_path)
        print(f"💾 Backed up old version to: eng.traineddata.backup")
    
    # Replace with new version
    shutil.move(str(temp_file), str(LANG_PATH))
    print(f"✅ Updated eng.traineddata successfully!")
    
    print("\n" + "=" * 70)
    print("📊 Benefits of the best quality language data:")
    print("   • Much higher accuracy for text recognition")
    print("   • Better handling of various fonts and styles")
    print("   • Improved performance on degraded documents")
    print("   • Support for more edge cases")
    print("=" * 70)
    
except urllib.error.URLError as e:
    print(f"❌ Download failed: {e}")
    if temp_file.exists():
        os.unlink(temp_file)
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    if temp_file.exists():
        os.unlink(temp_file)
    exit(1)

print("\n✅ Language data update complete!")
print("   Your OCR accuracy should be significantly better now.")
