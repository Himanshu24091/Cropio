#!/usr/bin/env bash
# Simplified Build script for Render deployment - Python packages only
set -o errexit  # Exit on error

echo "🚀 Starting Cropio simplified build process..."

# Only install Python dependencies - no system packages
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories for file processing
echo "📁 Creating application directories..."
mkdir -p uploads outputs compressed

# Verify Python package installations
echo "✅ Verifying Python package installations..."
python -c "import nbconvert; print(f'nbconvert: {nbconvert.__version__}')" || echo "nbconvert: Not available"
python -c "import pypandoc; print(f'pypandoc: {pypandoc.__version__}')" || echo "pypandoc: Not available"
python -c "import flask; print(f'Flask: {flask.__version__}')" || echo "Flask: Not available"
python -c "import PIL; print(f'Pillow: {PIL.__version__}')" || echo "Pillow: Not available"

echo "📝 Note: Using Python-only dependencies for maximum compatibility"
echo "🎉 Cropio simplified build completed successfully!"
