# Cropio — All-in-One Online File Toolkit

**Cropio** is a comprehensive, all-in-one web application for file manipulation, built with Flask and modern frontend technologies. It provides a suite of powerful tools including file conversion, compression, image cropping, and a full-featured PDF editor, all wrapped in a sleek, responsive, and user-friendly interface.

---

## ✨ Main Features

- **Multi-Tool Interface**: A single application that houses multiple file processing utilities.
- **Modern UI/UX**: Clean, responsive design with dark mode, built using Tailwind CSS.
- **Drag & Drop Uploads**: Simple drag-and-drop file uploads for all tools.
- **Real-time Previews**: Interactive previews for images, PDFs, and cropping.
- **Backend Processing**: Powered by a modular Flask backend using libraries like Pillow and PyMuPDF.
- **Automatic Cleanup**: Background scheduler deletes temporary files after one hour to save server space.
- **Responsive Navigation**: Organized dropdown menus for desktop and collapsible mobile menu.
- **Intuitive Grouping**: Related tools grouped together for better user experience.

---

## 🧭 Navigation Structure

### Desktop Navigation
- **Converters** dropdown: Image, PDF, Document, Excel converters
- **Compressor**: File compression tool
- **Image Cropper**: Image and PDF cropping
- **PDF Tools** dropdown: PDF Editor, PDF Merge, PDF Signature, Secure PDF

### Mobile Navigation
- **Hamburger Menu**: Collapsible menu with organized sections
- **Converters Section**: All file conversion tools
- **Individual Tools**: Compressor, Image Cropper, Text & OCR
- **PDF Tools Section**: All PDF-related functionality grouped together

---

## 🛠️ Tools Included

### 1. File Converters
- **Image Converter**: Convert PNG, JPG, WEBP, BMP, TIFF files to various image formats, including PDF and ICO.
- **PDF Converter**: Convert PDF files into editable DOCX documents or CSV spreadsheets.
- **Document Converter**: Convert DOCX files into PDF or plain TXT files.
- **Excel Converter**: Convert XLSX or XLS spreadsheets into CSV or JSON format.

### 2. File Compressor
- **Supported Formats**: PNG, JPG, WEBP, and PDF.
- **Compression Levels**: Choose between Low, Medium, and High compression.
- **Batch Processing**: Upload and compress multiple files simultaneously.
- **Detailed Results**: Display original size, compressed size, and total percentage saved.

### 3. Image & PDF Cropper
- **Supported Formats**: PNG, JPG, WEBP, and PDF.
- **Interactive Preview**: Real-time cropping preview.
- **Aspect Ratio Control**: Lock crop box to standard ratios (16:9, 4:3, 1:1, etc.).
- **Multiple Output Formats**: Export cropped output as JPEG, PNG, WEBP, or PDF.

### 4. PDF Tools Suite
#### PDF Editor
- **PDF Rendering**: View all pages with a thumbnail sidebar.
- **Editing Tools**: Add text, draw freehand, and highlight.
- **Client-Side Editing**: Fast, local edits using PDF-lib.js and PDF.js.
- **Export Changes**: Download the modified PDF.

#### PDF Merge
- **Multiple File Support**: Combine multiple PDF files into one.
- **Page Order Control**: Rearrange pages before merging.
- **Batch Processing**: Handle multiple PDFs efficiently.

#### PDF Signature
- **Digital Signatures**: Add digital signatures to PDF documents.
- **Multiple Signature Types**: Support for various signature formats.
- **Secure Processing**: Client-side signature processing for security.

#### Secure PDF
- **Password Protection**: Add or remove password protection from PDFs.
- **Encryption**: Secure PDFs with various encryption levels.
- **Access Control**: Control document permissions and restrictions.

---

## ⚙️ Tech Stack

- **Backend**: Flask, Pillow, PyMuPDF, pdf2docx, pandas, APScheduler
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Libraries**: Cropper.js, PDF.js, PDF-lib.js

---

## 📂 Modular Flask Application Structure

### Directory Tree
```
converter1/
├── app.py                          # Main modular application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Python version specification
├── README.md                       # Project documentation
├── routes/                         # Route modules
│   ├── __init__.py
│   ├── main_routes.py
│   ├── image_converter_routes.py
│   ├── pdf_converter_routes.py
│   ├── document_converter_routes.py
│   ├── excel_converter_routes.py
│   ├── compressor_routes.py
│   ├── cropper_routes.py
│   ├── pdf_editor_routes.py
│   ├── pdf_merge_routes.py
│   ├── pdf_signature_routes.py
│   ├── secure_pdf_routes.py
│   ├── reverse_converter_routes.py
│   └── text_ocr_routes.py
├── static/
│   ├── base.css
│   ├── compressor.css
│   ├── converter.css
│   ├── cropper.css
│   ├── home.css
│   ├── pdf_editor.css
│   ├── pdf_merge.css
│   ├── pdf_signature.css
│   ├── secure_pdf.css
│   ├── style.css
│   └── js/
│       ├── theme.js
│       ├── index.js
│       ├── compressor.js
│       ├── cropper.js
│       ├── converter.js
│       ├── pdf_editor.js
│       ├── pdf_merge.js
│       ├── pdf_signature.js
│       ├── secure_pdf.js
│       └── main.js
├── templates/
│   ├── base.html
│   ├── layout.html
│   ├── index.html
│   ├── compressor.html
│   ├── cropper.html
│   ├── pdf_converter.html
│   ├── pdf_editor.html
│   ├── pdf_merge.html
│   ├── pdf_signature.html
│   ├── secure_pdf.html
│   └── text_ocr.html
├── utils/
│   ├── __init__.py
│   └── helpers.py
└── uploads/                      # Uploads directory
    ├── *.pdf                    # PDF uploads
    ├── *.jpg                    # Image uploads
    └── *.png                    # Signature files
```

### Route Modules Overview

- `main_routes.py` → Home page
- `image_converter_routes.py` → Image conversions
- `pdf_converter_routes.py` → PDF to DOCX/CSV
- `document_converter_routes.py` → DOCX to TXT
- `excel_converter_routes.py` → XLSX/XLS to CSV/JSON
- `compressor_routes.py` → Image and PDF compression
- `cropper_routes.py` → Image/PDF cropping
- `pdf_editor_routes.py` → PDF editing interface
- `pdf_merge_routes.py` → PDF merging functionality
- `pdf_signature_routes.py` → PDF digital signatures
- `secure_pdf_routes.py` → PDF password protection
- `text_ocr_routes.py` → OCR text extraction
- `reverse_converter_routes.py` → PDF to image conversion
- `file_serving_routes.py` → Downloads & previews

### JavaScript Modules

- `theme.js` — Dark/light toggle and mobile menu functionality
- `index.js` — Homepage interactivity
- `main.js` — Main application logic
- `compressor.js` — Compressor logic
- `cropper.js` — Image/PDF crop tool
- `converter.js` — Converter utilities
- `pdf_editor.js` — Full PDF editor with advanced features
- `pdf_merge.js` — PDF merging functionality
- `pdf_signature.js` — PDF signature tools
- `secure_pdf.js` — PDF security and encryption

### Configuration (config.py)
- Constants, path setup, file extension rules

### Utilities (utils/helpers.py)
- `allowed_file()` — File type check
- `compress_image()` / `compress_pdf()`
- `cleanup_files()` — Delete temporary files

---

## ▶️ How to Run

1. **Set up the environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

2. **Start the app**:
   ```bash
   python app.py
   ```

3. **Test all registered routes**:
   ```bash
   python test_routes.py
   ```

4. **Restore original monolithic file** (if needed):
   ```bash
   copy app_backup.py app.py  # On Unix use `cp app_backup.py app.py`
   ```

## 🌟 Additional Tools

### 5. Secure PDF
- **Password Protection**: Add or remove password protection from PDFs.
- **QR Code Unlock**: Unlock PDFs using QR codes for enhanced security.

### 6. Text & OCR
- **Extract Text**: Extract text from images and documents using OCR (Optical Character Recognition).

### Reverse Converter
- **Reverse Conversion**: Convert PDF back to images, retaining original quality.

---

## 🚀 Benefits of Modular Architecture

- **Maintainable**: Clearly separated responsibilities
- **Scalable**: Easily add more converters/editors
- **Testable**: Independent route testing
- **Debuggable**: Issues isolated by feature
- **Collaborative**: Multiple developers can contribute without conflict
- **Reusable**: Shared logic centralized in `utils/`

---

## ➕ Adding a New Route

1. Create a file in `routes/`, e.g., `new_converter_routes.py`
2. Define a `Blueprint`
3. Register it in `app.py`
4. Add frontend files if needed
5. Update UI templates

**Example:**
```python
# routes/new_converter_routes.py
from flask import Blueprint, render_template

new_converter_bp = Blueprint('new_converter', __name__)

@new_converter_bp.route('/new-converter')
def new_converter():
    return render_template('new_converter.html')
```

**Then in `app.py`:**
```python
from routes.new_converter_routes import new_converter_bp
app.register_blueprint(new_converter_bp)
```

## 🔧 Development & Contribution

### Contributing to Cropio
- Fork the repository
- Create a feature branch
- Commit your changes
- Push the branch
- Open a pull request

---

Made with 💻 using Flask + Tailwind + PDF-lib.js

---

## 🗃️ File Structure

### Routes:
- **PDF Converter**: `pdf_converter_routes.py`
- **Secure PDF**: `secure_pdf_routes.py`
- **Text & OCR**: `text_ocr_routes.py`
...

### Static Assets:
- **CSS**: Base styles in `base.css`, component-specific styles (`cropper.css`, `converter.css`)
- **JavaScript**: Core functionality in `theme.js`, page-specific logic (`compressor.js`, `pdf_editor.js`)

---

## 🚀 Getting Started

### Running the Application
Follow the setup guide and start using Cropio on your local development server, ensuring all dependencies are in place. Develop and test various components as needed.

---

🔗 **License**: MIT License. See `LICENSE` for more information.

---

🏆 **Acknowledgments**
- Open source projects
- Community contributors

---
- Owned by Himanshu