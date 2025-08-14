# 🚀 Cropio — Complete Project Documentation
## Security-First File Processing Platform with Real-Time Analytics

**Current Status:** ✅ **Production-Ready Multi-Tool File Processor**  
**Future Vision:** 🎯 **Enterprise Security Analytics & Monitoring System**

**Cropio** is evolving from a comprehensive file manipulation toolkit into a security-first file processing platform with real-time threat detection, analytics, and monitoring capabilities. Built with Flask and modern technologies, it currently provides powerful file processing tools and is planned to expand into a complete security operations center.

---

## 📊 Project Status Overview

| **Phase** | **Status** | **Features** | **Timeline** |
|-----------|------------|--------------|-------------|
| **Phase 1** | ✅ **COMPLETE** | Core File Processing Tools | ✅ Done |
| **Phase 2** | 🔄 **NEXT** | Security Foundation & Real-time Analytics | 8-10 weeks |
| **Phase 3** | ⏳ **PLANNED** | Advanced Security & Enterprise Features | TBD |

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
- **Converters** dropdown: Image, PDF, Document, Excel, Notebook converters
- **Compressor**: File compression tool
- **Image Cropper**: Image and PDF cropping
- **PDF Tools** dropdown: PDF Editor, PDF Merge, PDF Signature, Secure PDF, PDF Page Delete

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
- **Notebook Converter**: Convert Jupyter notebooks (.ipynb) to HTML, PDF, DOCX, Markdown, LaTeX, TXT, and RST formats.

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

#### PDF Page Delete
- **Single & Multiple Page Selection**: Select individual or groups of pages.
- **Batch Processing**: Process multiple PDFs with deletion patterns.
- **Page Thumbnail Preview**: Visual selection of pages to delete.
- **Operation Modes**: "Delete Selected Pages" or "Keep Selected Pages"
- **Custom Range Selection**: Select all, odd, even, or custom page ranges.

#### Secure PDF
- **Password Protection**: Add or remove password protection from PDFs.
- **Encryption**: Secure PDFs with various encryption levels.
- **Access Control**: Control document permissions and restrictions.

---

## ⚙️ Tech Stack

- **Backend**: Flask, Pillow, PyMuPDF, pdf2docx, pandas, APScheduler, nbconvert, pypandoc
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Libraries**: Cropper.js, PDF.js, PDF-lib.js, nbformat, jupyter-core
- **Dependencies**: XeLaTeX, Pandoc, Tesseract OCR
- **Production**: Gunicorn, TeX Live, system libraries for image processing

---

## 📂 Modular Flask Application Structure

### Directory Tree
```
converter/
├── app.py                          # Main modular application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Python version specification
├── README.md                       # Project documentation
├── TESSERACT_SETUP.md              # OCR setup instructions
├── PDF_SETUP_GUIDE.md              # PDF conversion setup guide
├── render-build.sh                 # Enhanced build script with TeX Live
├── .gitignore                      # Git ignore file
├── routes/                         # Route modules
│   ├── __init__.py
│   ├── main_routes.py              # Home page routes
│   ├── image_converter_routes.py   # Image conversion routes
│   ├── pdf_converter_routes.py     # PDF to DOCX/CSV routes
│   ├── pdf_converter_routes_fixed.py # Fixed PDF routes
│   ├── document_converter_routes.py # DOCX to PDF/TXT routes
│   ├── excel_converter_routes.py    # Excel conversion routes
│   ├── compressor_routes.py        # File compression routes
│   ├── cropper_routes.py           # Image/PDF cropping routes
│   ├── pdf_editor_routes.py        # PDF editing routes
│   ├── pdf_merge_routes.py         # PDF merging routes
│   ├── pdf_page_delete_routes.py   # PDF page deletion routes
│   ├── pdf_signature_routes.py     # PDF signature routes
│   ├── secure_pdf_routes.py        # PDF security routes
│   ├── reverse_converter_routes.py # PDF to image routes
│   ├── text_ocr_routes.py          # OCR text extraction routes
│   ├── notebook_converter.py       # Jupyter notebook conversion routes
│   └── file_serving_routes.py      # File serving routes
├── static/                         # Static assets
│   ├── base.css                    # Base styling
│   ├── compressor.css              # Compressor styles
│   ├── converter.css               # Converter styles
│   ├── cropper.css                 # Cropper styles
│   ├── home.css                    # Homepage styles
│   ├── notebook_converter.css      # Notebook converter styles
│   ├── pdf_editor.css              # PDF editor styles
│   ├── pdf_merge.css               # PDF merge styles
│   ├── pdf_page_delete.css         # PDF page deletion styles
│   ├── pdf_page_delete_simple.css  # Simplified PDF page deletion styles
│   ├── pdf_signature.css           # PDF signature styles
│   ├── secure_pdf.css              # Secure PDF styles
│   ├── style.css                   # Global styles
│   └── js/                         # JavaScript files
│       ├── theme.js                # Theme and navigation
│       ├── index.js                # Homepage scripts
│       ├── main.js                 # Main application logic
│       ├── compressor.js           # Compressor logic
│       ├── converter.js            # Converter utilities
│       ├── cropper.js              # Cropping tool logic
│       ├── pdf_editor.js           # PDF editor logic
│       ├── pdf_editor_simple.js    # Simple PDF editor
│       ├── pdf_merge.js            # PDF merge logic
│       ├── pdf_page_delete.js      # PDF page deletion logic
│       ├── pdf_signature.js        # PDF signature logic
│       ├── secure_pdf.js           # PDF security logic
│       ├── notebook_converter.js   # Notebook converter logic
├── templates/                      # HTML templates
│   ├── base.html                   # Base template with navigation
│   ├── layout.html                 # Layout template
│   ├── index.html                  # Homepage
│   ├── compressor.html             # Compressor page
│   ├── convert_to_docx.html        # DOCX conversion page
│   ├── convert_to_pdf.html         # PDF conversion page
│   ├── cropper.html                # Cropper page
│   ├── document_converter.html     # Document converter page
│   ├── excel_converter.html        # Excel converter page
│   ├── image_converter.html        # Image converter page
│   ├── pdf_converter.html          # PDF converter page
│   ├── pdf_editor.html             # PDF editor page
│   ├── pdf_merge.html              # PDF merge page
│   ├── pdf_page_delete.html        # PDF page deletion page
│   ├── pdf_signature.html          # PDF signature page
│   ├── secure_pdf.html             # Secure PDF page
│   ├── text_ocr.html               # OCR text extraction page
│   └── notebook_converter.html     # Notebook converter page
└── utils/                          # Utility modules
    ├── __init__.py
    └── helpers.py                  # Helper functions
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
- `pdf_page_delete_routes.py` → PDF page deletion functionality
- `pdf_signature_routes.py` → PDF digital signatures
- `secure_pdf_routes.py` → PDF password protection
- `text_ocr_routes.py` → OCR text extraction
- `reverse_converter_routes.py` → PDF to image conversion
- `notebook_converter.py` → Jupyter notebook conversion
- `file_serving_routes.py` → Downloads & previews

### JavaScript Modules

- `theme.js` — Dark/light toggle and mobile menu functionality
- `index.js` — Homepage interactivity
- `main.js` — Main application logic
- `compressor.js` — Compressor logic
- `cropper.js` — Image/PDF crop tool
- `converter.js` — Converter utilities
- `pdf_editor.js` — Full PDF editor with advanced features
- `pdf_editor_simple.js` — Simple PDF editor
- `pdf_merge.js` — PDF merging functionality
- `pdf_page_delete.js` — PDF page deletion functionality
- `pdf_signature.js` — PDF signature tools
- `secure_pdf.js` — PDF security and encryption
- `notebook_converter.js` — Notebook conversion and validation

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

### 7. Jupyter Notebook Converter
- **Multiple Output Formats**: Convert .ipynb files to HTML, PDF, DOCX, Markdown, LaTeX, TXT, and RST.
- **Smart Validation**: Automatic notebook validation and format recommendations.
- **Enhanced Error Handling**: Clear error messages with helpful troubleshooting guidance.
- **Production Ready**: Full deployment support with automatic dependency installation.
- **PDF Requirements**: Intelligent PDF conversion with XeLaTeX dependency management.
- **Interactive Features**: Real-time format selection and file validation.

### Reverse Converter
- **Reverse Conversion**: Convert PDF back to images, retaining original quality.

---

## 🚀 Benefits of Architecture

### **Current Benefits**
- **Maintainable**: Clearly separated responsibilities
- **Scalable**: Easily add more converters/editors
- **Testable**: Independent route testing
- **Debuggable**: Issues isolated by feature
- **Collaborative**: Multiple developers can contribute without conflict
- **Reusable**: Shared logic centralized in `utils/`

### **Future Benefits**
- **Secure**: Real-time threat detection and prevention
- **Monitored**: Complete visibility into system operations
- **Isolated**: Sandboxed processing prevents malicious files from affecting the system
- **Enterprise-Ready**: Audit trails, alerts, and comprehensive reporting
- **Scalable**: Microservice architecture allows for horizontal scaling

---

# 📋 FUTURE ROADMAP: Security Integration

## **PHASE 2: Foundation & Core Security Setup**
**Duration:** 8-10 weeks (Solo with AI assistance)
**Focus:** Database, Security Middleware, Real-time Dashboard

### **Week 1-2: Database & Security Architecture**

#### **Database Integration**
- Project structure enhancement
- PostgreSQL database integration
- Tables: `sec_request_log`, `sec_blocklist`, `file_metadata`, `users`
- Alembic migration setup

#### **Security Middleware Implementation**
- Request logging middleware
- IP extraction and validation
- Basic security headers
- Redis connection for real-time events

#### **File Quarantine System**
- Enhanced file validation (MIME, size, extension)
- Quarantine directory structure
- python-magic, Pillow, and pikepdf integration
- Secure file processing pipeline

### **Week 3-5: Real-time Features & Advanced Security**

#### **WebSocket Infrastructure**
- Flask-SocketIO integration
- Real-time event publishing system
- Client-side WebSocket connections
- Live dashboard frontend with real-time updates

#### **Security Detectors & Rules Engine**
- Real-time detector service
- Rule engine for security patterns
- Failed login and upload abuse detection
- Auto-blocking algorithms and risk scoring

#### **Sandboxed Processing**
- Docker-based worker containers
- Resource limits and isolation
- Malware scanning integration
- Metadata extraction and sanitization

### **Week 6-8: Production Readiness**

#### **Testing & Security Hardening**
- Comprehensive test suite
- Security audit and vulnerability scanning
- OWASP compliance checks
- Penetration testing

#### **Deployment & Monitoring**
- Production Docker configuration
- CI/CD pipeline setup
- Monitoring with Prometheus/Grafana
- Alert system integration

#### **Documentation & Optimization**
- Performance tuning
- Complete system documentation
- Troubleshooting guides
- Final security review

---

## 🖥️ PLANNED ADMIN DASHBOARD

The future admin dashboard will include:

### **1. Main Dashboard**
┌─────────────────────────────────────────────────────────┐
│  CROPIO SECURITY COMMAND CENTER                         │
├─────────────────────────────────────────────────────────┤
│  📊 REAL-TIME METRICS (Auto-refreshing every 5 seconds) │
│  ┌─────────────────┬─────────────────┬─────────────────┐ │
│  │ Active Requests │   Files Queued  │  Threats Today  │ │
│  │      1,247      │       23        │       5         │ │
│  └─────────────────┴─────────────────┴─────────────────┘ │
│                                                         │
│  📈 LIVE TRAFFIC GRAPH (Chart.js, WebSocket updates)    │
│  [Real-time line graph showing requests per minute]     │
│                                                         │
│  🚨 LIVE ALERTS FEED                                    │
│  [Scrolling feed of security events as they happen]    │
│                                                         │
│  ⚡ QUICK ACTIONS                                       │
│  [Block IP] [Emergency Stop] [System Status]           │
└─────────────────────────────────────────────────────────┘

### **2. Security Monitoring**
- Geographic threat visualization
- Attack pattern analysis
- Risk score trending
- Top offenders list

### **3. Live Logs**
- Real-time log streaming
- Advanced filtering options
- Export capabilities

### **4. File Processing Monitor**
- Processing pipeline status
- Live file status updates
- Worker monitoring
- Storage usage tracking

### **5. Blocklist Management**
- Quick block interface
- Active blocks management
- Block statistics
- Bulk operations

### **6. System Monitoring**
- System metrics (CPU, memory, disk, network)
- Service status tracking
- Database performance
- Maintenance actions

---

## ➕ Adding a New Feature

1. Create a file in `routes/`, e.g., `new_feature_routes.py`
2. Define a `Blueprint`
3. Register it in `app.py`
4. Add frontend files if needed
5. Update UI templates

**Example:**
```python
# routes/new_feature_routes.py
from flask import Blueprint, render_template

new_feature_bp = Blueprint('new_feature', __name__)

@new_feature_bp.route('/new-feature')
def new_feature():
    return render_template('new_feature.html')
```

**Then in `app.py`:**
```python
from routes.new_feature_routes import new_feature_bp
app.register_blueprint(new_feature_bp)
```

## 🚀 Getting Started with Security Development

To begin implementing the security features outlined in Phase 2:

1. **Set up the database**:
   ```bash
   # Install PostgreSQL dependencies
   pip install psycopg2-binary sqlalchemy alembic

   # Initialize Alembic
   alembic init migrations

   # Create your first migration
   alembic revision --autogenerate -m "Initial tables"

   # Run the migration
   alembic upgrade head
   ```

2. **Implement request logging middleware**:
   - Create a new middleware module in `utils/security_middleware.py`
   - Register the middleware in `app.py`
   - Set up the database logging mechanism

3. **Set up WebSocket infrastructure**:
   - Install Flask-SocketIO
   - Create event handlers for different security events
   - Implement the client-side JavaScript for real-time updates

## 🔧 Development & Contribution

### Contributing to Cropio
- Fork the repository
- Create a feature branch
- Commit your changes
- Push the branch
- Open a pull request

---

Made with 💻 using Flask + Tailwind + PDF-lib.js + PostgreSQL + Redis + WebSockets

---

🔗 **License**: MIT License. See `LICENSE` for more information.

---

🏆 **Acknowledgments**
- Open source projects
- Community contributors

---
- Owned by Himanshu
