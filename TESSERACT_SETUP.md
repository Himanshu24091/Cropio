# Tesseract OCR Setup Guide

## For Windows Users

### Step 1: Download Tesseract
1. Go to https://github.com/UB-Mannheim/tesseract/wiki
2. Download the latest Windows installer (tesseract-ocr-w64-setup-v5.x.x.exe)
3. Run the installer and install to the default location: `C:\Program Files\Tesseract-OCR\`

### Step 2: Add to System PATH
1. Add `C:\Program Files\Tesseract-OCR\` to your system PATH environment variable
2. Or uncomment and adjust the path in `routes/text_ocr_routes.py`:
   ```python
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### Step 3: Install Language Packs (Optional)
- During installation, you can select additional language packs
- Default English (eng) is usually sufficient for most use cases

## For macOS Users

### Using Homebrew:
```bash
brew install tesseract
```

### Using MacPorts:
```bash
sudo port install tesseract
```

## For Linux Users

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install tesseract-ocr
```

### CentOS/RHEL:
```bash
sudo yum install tesseract
```

### Arch Linux:
```bash
sudo pacman -S tesseract
```

## Verify Installation

Run the following command in your terminal/command prompt:
```bash
tesseract --version
```

You should see version information if Tesseract is properly installed.

## Troubleshooting

If you encounter issues:

1. **Windows**: Ensure the path is correct in the text_ocr_routes.py file
2. **macOS/Linux**: Tesseract should be automatically detected in the system PATH
3. **Permission Issues**: Ensure the uploads folder has proper write permissions

## Supported Image Formats for OCR

- PNG
- JPEG/JPG
- TIFF/TIF
- BMP
- GIF
- WEBP

## Tips for Better OCR Results

1. Use high-resolution images (300 DPI or higher)
2. Ensure good contrast between text and background
3. Avoid skewed or rotated text when possible
4. Clean images work better than noisy ones
