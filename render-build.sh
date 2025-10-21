#!/usr/bin/env bash
# Build script for Cropio deployment - Optimized for Render Free Tier
set -o errexit  # Exit on error

echo "🚀 Starting Cropio build process (Render Free Tier Optimized)..."

# Render free tier has read-only filesystem for apt
# Only install lightweight essential dependencies
echo "📦 Installing minimal system dependencies..."

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip

# For Render free tier, install with reduced memory footprint
echo "📦 Installing packages (this may take a while on free tier)..."
pip install -r requirements.txt --no-cache-dir

# Create necessary directories for file processing
echo "📁 Creating application directories..."
mkdir -p uploads outputs compressed temp logs

# Set environment for production
echo "⚙️ Configuring for production..."
export FLASK_ENV=production

# Display system info
echo "ℹ️ System Information:"
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"
echo "Available memory: $(free -h 2>/dev/null || echo 'N/A')"

# Note about disabled features on free tier
echo "⚠️ Note: On Render free tier, the following features are limited:"
echo "   - LaTeX/PDF conversion (no TeX Live)"
echo "   - Pandoc conversion (no Pandoc)"
echo "   - OCR functionality (no Tesseract)"
echo "   - Video processing (no FFmpeg)"
echo "   For full functionality, upgrade to Render paid tier or use alternative deployment."

echo "🎉 Cropio build completed successfully!"
