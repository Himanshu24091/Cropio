#!/usr/bin/env bash
# Build script for Cropio deployment with Notebook Converter support
set -o errexit  # Exit on error

echo "🚀 Starting Cropio build process..."

# Check if we can write to apt lists (for local development)
if [ -w "/var/lib/apt/lists" ] 2>/dev/null; then
    echo "📦 Updating system packages..."
    apt-get update
    
    # Install system dependencies
    echo "🖼️ Installing system dependencies..."
    apt-get install -y libgl1-mesa-glx
    
    # Install TeX Live for PDF conversion (nbconvert requirement)
    echo "📄 Installing TeX Live for PDF support..."
    apt-get install -y texlive-xetex texlive-fonts-recommended texlive-latex-extra
    
    # Install Pandoc for document conversion
    echo "📝 Installing Pandoc for document conversion..."
    apt-get install -y pandoc
    
    # Install Tesseract for OCR functionality
    echo "🔍 Installing Tesseract OCR..."
    apt-get install -y tesseract-ocr tesseract-ocr-eng
    
    # Install additional image processing libraries
    echo "🖼️ Installing image processing libraries..."
    apt-get install -y libjpeg-dev libpng-dev libtiff-dev libwebp-dev
else
    echo "⚠️ Read-only filesystem detected (likely Render environment)"
    echo "📦 Skipping apt-get operations - relying on Python packages"
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories for file processing
echo "📁 Creating application directories..."
mkdir -p uploads outputs compressed

# Verify critical installations
echo "✅ Verifying installations..."
echo "XeLaTeX: $(which xelatex || echo 'Not found')"
echo "Pandoc: $(which pandoc || echo 'Not found')"
echo "Tesseract: $(which tesseract || echo 'Not found')"

echo "🎉 Cropio build completed successfully!"
