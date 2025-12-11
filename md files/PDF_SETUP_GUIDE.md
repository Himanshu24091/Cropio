# PDF Conversion Setup Guide for Cropio Notebook Converter

## Overview
To convert Jupyter notebooks to PDF format, you need to install XeLaTeX (part of a TeX distribution). This is a one-time setup that will enable PDF conversion for all notebooks.

## Quick Setup for Windows

### Option 1: MiKTeX (Recommended for Windows)
1. **Download MiKTeX**:
   - Visit: https://miktex.org/download
   - Download the installer for Windows
   - Choose the "Basic MiKTeX Installer"

2. **Install MiKTeX**:
   - Run the downloaded installer
   - Accept the license agreement
   - Choose "Install MiKTeX for anyone who uses this computer"
   - Select installation directory (default is fine)
   - Allow automatic package installation: **Yes**

3. **Verify Installation**:
   ```cmd
   xelatex --version
   ```
   If successful, you'll see version information.

### Option 2: TeX Live (Alternative)
1. **Download TeX Live**:
   - Visit: https://www.tug.org/texlive/windows.html
   - Download install-tl-windows.exe

2. **Install TeX Live**:
   - Run the installer as Administrator
   - Choose "Install TeX Live to hard disk"
   - Installation may take 30-60 minutes (it's a large distribution)

## After Installation

### Restart Your System
After installing either MiKTeX or TeX Live, **restart your computer** to ensure the PATH is updated.

### Test PDF Conversion
1. Go to Cropio Notebook Converter
2. Upload a simple .ipynb file
3. Select "PDF" as output format
4. Click "Convert Notebook"

## Alternative Formats (No Setup Required)

If you don't want to install TeX, these formats work immediately:

- **HTML** - Best for viewing notebooks in browsers
- **Markdown** - Clean text format, perfect for documentation
- **DOCX** - Microsoft Word compatible
- **LaTeX** - Source code for academic papers
- **TXT** - Plain text version
- **RST** - ReStructuredText format

## Troubleshooting

### Common Issues:

1. **"xelatex not found" error**:
   - Restart your computer after installation
   - Check if TeX is in your PATH: `echo $PATH` (Linux/Mac) or `echo %PATH%` (Windows)

2. **"Permission denied" errors**:
   - Run command prompt as Administrator during installation
   - Ensure MiKTeX can install packages automatically

3. **Package missing errors**:
   - MiKTeX will usually download missing packages automatically
   - If not, open MiKTeX Console and update packages

### Manual PATH Setup (if needed):
If XeLaTeX still isn't found after installation:

**Windows**:
1. Open "Environment Variables" in System Properties
2. Add to PATH: `C:\Program Files\MiKTeX\miktex\bin\x64\`
3. Restart command prompt/application

## File Size Notes

- **PDF files** are typically larger than HTML
- **HTML format** preserves interactive plots and styling better
- **Markdown** is smallest and most portable

## Support

If you continue having issues:
1. Try HTML format first (works without any setup)
2. Check the error message in Cropio for specific guidance
3. Verify your .ipynb file is valid by opening it in Jupyter

---

*This guide is part of the Cropio file processing platform. For more converters and tools, visit the main Cropio application.*
