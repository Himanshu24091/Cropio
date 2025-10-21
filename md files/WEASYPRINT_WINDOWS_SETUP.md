# WeasyPrint Setup for Windows (HTML PDF Converter)

## Current Status
- ✅ **ReportLab Backend**: Working (basic HTML support)
- ⚠️  **WeasyPrint Backend**: Installed but missing dependencies
- ❌ **PDFKit Backend**: Missing wkhtmltopdf binary

## To Enable WeasyPrint (Best CSS Support)

WeasyPrint provides the best HTML/CSS rendering but requires GTK libraries on Windows.

### Method 1: Using MSYS2 (Recommended)

1. **Install MSYS2**:
   - Download from: https://www.msys2.org/
   - Run the installer with default options

2. **Install Pango dependencies**:
   ```bash
   # In MSYS2 terminal:
   pacman -S mingw-w64-x86_64-pango
   ```

3. **Set Windows environment variable**:
   ```cmd
   # In Command Prompt:
   set WEASYPRINT_DLL_DIRECTORIES=C:\msys64\mingw64\bin
   
   # Or permanently via System Properties > Environment Variables
   ```

4. **Test WeasyPrint**:
   ```cmd
   python -c "import weasyprint; print('WeasyPrint working!')"
   ```

### Method 2: Using Conda (Alternative)

```bash
conda install weasyprint -c conda-forge
```

### Method 3: Docker (For Production)

If setting up GTK libraries is complex, consider using Docker:

```dockerfile
FROM python:3.9-slim
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libharfbuzz-subset0
# ... rest of your app
```

## To Enable PDFKit (Good CSS + JavaScript Support)

1. **Install wkhtmltopdf**:
   - Download from: https://wkhtmltopdf.org/downloads.html
   - Add to PATH or specify path in config

2. **Test PDFKit**:
   ```python
   import pdfkit
   pdfkit.from_url('http://google.com', 'test.pdf')
   ```

## Backend Priority
1. **WeasyPrint** - Best CSS support, no JavaScript
2. **PDFKit** - Good CSS + JavaScript support  
3. **ReportLab** - Basic HTML, most compatible (current fallback)
4. **Selenium** - Full modern web support (requires Chrome/ChromeDriver)

## Troubleshooting PDF Viewer Issues

If PDFs generate but don't display in browser:

1. **Try different PDF viewer**:
   - Download PDF file directly
   - Open in Adobe Reader, Chrome, Edge, etc.

2. **Check PDF content**:
   ```python
   # Test if PDF is valid
   python -c "from utils.web_code.html_pdf_snapshot_utils import HTMLPDFProcessor; p = HTMLPDFProcessor(); info = p.get_pdf_info('uploads/yourfile.pdf'); print(info)"
   ```

3. **Browser compatibility**:
   - Some browsers block PDF display from localhost
   - Try accessing via 127.0.0.1 instead of localhost
   - Check browser console for errors

## Current Backend Status

Your converter is working with ReportLab backend. To check current status:

```python
from utils.web_code.html_pdf_snapshot_utils import HTMLPDFProcessor
processor = HTMLPDFProcessor()
print("Backend:", processor.get_current_backend())
print("Available:", processor.get_supported_backends())
```
