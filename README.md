# 🚀 Cropio — Advanced Multi-Format File Conversion & Processing Platform

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

**A professional-grade SaaS platform for file conversion, processing, and manipulation**

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [API](#api-reference) • [Deployment](#deployment)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Security](#security)
- [Deployment](#deployment)
- [Testing](#testing)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)

---

## 🎯 Overview

**Cropio** is an enterprise-grade file conversion and processing platform built with Flask, designed to handle 40+ file conversion types, advanced document processing, and secure file manipulation. The platform features a modern architecture with comprehensive security, role-based access control, usage tracking, and scalable deployment options.

### 🌟 Key Highlights

- **40+ Conversion Types** across images, documents, PDFs, videos, and more
- **Production-Ready Security** with advanced threat detection and CSRF protection
- **SaaS Architecture** with user management, subscriptions, and usage tracking
- **Modern UI/UX** with responsive design and dark mode support
- **RESTful API** for programmatic access and integrations
- **Enterprise Features** including admin dashboard, audit logging, and analytics

---

## ✨ Features

### 🖼️ Image Processing & Conversion

<details>
<summary><b>Standard Image Converter</b></summary>

- **Formats**: PNG, JPG, JPEG, WEBP, BMP, TIFF, GIF, ICO, SVG
- **Features**:
  - Batch conversion with queue management
  - Quality adjustment (50-100%)
  - Resolution scaling and optimization
  - Metadata preservation options
  - Preview generation
</details>

<details>
<summary><b>RAW Image Processing</b> ⭐ NEW</summary>

- **Formats**: DNG, CR2, CR3, NEF, ARW, RW2
- **Features**:
  - Smart file format detection (content-based, not extension-based)
  - Advanced metadata extraction (EXIF, IPTC, XMP)
  - Bidirectional conversion (RAW ↔ JPG/PNG/TIFF)
  - Exposure and contrast adjustments
  - Preview generation with thumbnails
  - Professional photography workflow support
</details>

<details>
<summary><b>HEIC/HEIF Converter</b> ⭐ NEW</summary>

- **Apple Format Support**: HEIC, HEIF
- **Features**:
  - HEIC → JPG/PNG conversion
  - JPG/PNG → HEIC conversion
  - Batch processing
  - Metadata preservation
  - Quality optimization
  - iOS compatibility mode
</details>

<details>
<summary><b>GIF Processing Suite</b> ⭐ NEW</summary>

- **GIF to MP4 Video**:
  - Frame rate control
  - Quality settings
  - Size optimization
  - Smooth playback conversion

- **GIF to PNG Sequence**:
  - Individual frame extraction
  - Frame numbering and organization
  - Quality preservation
  - ZIP archive output

- **PNG Sequence to GIF**:
  - Custom frame timing
  - Loop control (infinite or count-based)
  - Optimization and dithering
  - Color palette management
</details>

<details>
<summary><b>Image Cropper & Editor</b></summary>

- **Interactive Cropping**:
  - Real-time preview with Cropper.js
  - Aspect ratio presets (16:9, 4:3, 1:1, custom)
  - Pixel-perfect precision
  - Zoom and pan controls

- **Output Options**:
  - Multiple format support (JPEG, PNG, WEBP, PDF, BMP, TIFF)
  - Quality adjustment
  - Resolution settings
  - Batch cropping capabilities
</details>

<details>
<summary><b>Image Compression</b></summary>

- **Compression Modes**:
  - Quality-based (High, Medium, Low)
  - Target size-based (5KB - 1MB)
  - Lossless optimization

- **Features**:
  - Batch compression
  - Compression statistics
  - Before/after comparison
  - Size reduction metrics
</details>

### 📄 Document Processing & Conversion

<details>
<summary><b>PDF Processing Suite</b></summary>

- **PDF to DOCX/TXT/CSV**:
  - Advanced text extraction with layout preservation
  - OCR fallback for scanned PDFs
  - Table detection and extraction
  - Multi-page processing
  - Formatting preservation

- **PDF to Images**:
  - Page-by-page extraction
  - Resolution control
  - Format options (PNG, JPG, TIFF)
  - Batch processing

- **Structured Text Analysis**:
  - JSON output with document structure
  - Heading detection
  - Paragraph segmentation
  - Font and style analysis
</details>

<details>
<summary><b>Document Conversion</b></summary>

- **DOCX Processing**:
  - DOCX → PDF (formatting preservation)
  - DOCX → TXT (plain text extraction)
  - DOCX → HTML (web-ready format)
  - DOCX → Markdown
  - Style and formatting retention

- **Advanced Features**:
  - Header/footer handling
  - Image extraction
  - Table conversion
  - Footnote processing
</details>

<details>
<summary><b>Excel/Spreadsheet Converter</b></summary>

- **Formats**: XLSX, XLS, ODS
- **Output Options**:
  - CSV (comma-separated values)
  - JSON (structured data)
  - HTML (table format)
  - PDF (formatted document)
  - XML (data export)

- **Features**:
  - Multiple sheet handling
  - Formula preservation
  - Data validation
  - Chart extraction
  - Conditional formatting
</details>

<details>
<summary><b>PowerPoint/Presentation Converter</b></summary>

- **Formats**: PPTX, PPT, ODP
- **Conversions**:
  - PPTX → PDF (high quality)
  - PDF → PPTX (reverse conversion)
  - PPTX → Images (slide by slide)
  - PPTX → HTML5 (web presentations)

- **Features**:
  - Animation preservation
  - Transition handling
  - Notes extraction
  - Master slide processing
</details>

<details>
<summary><b>Jupyter Notebook Converter</b></summary>

- **Output Formats**:
  - HTML (with syntax highlighting)
  - PDF (via XeLaTeX)
  - DOCX (editable document)
  - Markdown (GitHub-ready)
  - LaTeX (academic format)
  - Python (.py script)
  - ReStructuredText (.rst)

- **Features**:
  - Code syntax highlighting
  - Output preservation
  - Markdown cell rendering
  - Metadata extraction
  - Smart validation
  - Error handling with detailed messages
</details>

<details>
<summary><b>Markdown ↔ HTML Converter</b> ⭐ NEW</summary>

- **Features**:
  - Bidirectional conversion
  - Live preview mode
  - Syntax highlighting for code blocks
  - Table support
  - GitHub Flavored Markdown
  - Custom CSS styling
  - HTML sanitization
  - Link validation
</details>

<details>
<summary><b>LaTeX ↔ PDF Converter</b> ⭐ NEW</summary>

- **LaTeX to PDF**:
  - XeLaTeX compilation
  - Bibliography support (BibTeX, BibLaTeX)
  - Mathematical equations
  - Custom document classes
  - Package management
  - Error reporting with line numbers

- **PDF to LaTeX**:
  - Text extraction
  - Structure detection
  - Math equation recognition
  - Table extraction
  - Figure handling
</details>

### 🔍 Advanced PDF Tools

<details>
<summary><b>PDF Editor</b></summary>

- **Annotation Tools**:
  - Text annotations with custom fonts
  - Freehand drawing (pen tool)
  - Highlighting with transparency
  - Shapes (rectangles, circles, arrows)
  - Eraser tool

- **Page Manipulation**:
  - Rotate pages (90°, 180°, 270°)
  - Split PDFs by page ranges
  - Extract specific pages
  - Reorder pages with drag-and-drop

- **Advanced Features**:
  - Watermark addition (text/image)
  - Image insertion with positioning
  - Compression options
  - Client-side processing for privacy
  - Auto-save functionality
</details>

<details>
<summary><b>PDF Merge</b></summary>

- **Features**:
  - Multiple file combining
  - Drag-and-drop page reordering
  - Page thumbnail preview
  - Bookmark preservation
  - Metadata merging
  - Table of contents generation
  - Batch processing
</details>

<details>
<summary><b>PDF Page Management</b></summary>

- **Delete Pages**:
  - Visual page selection with thumbnails
  - Range selection (odd, even, custom)
  - Multi-select mode
  - Batch delete

- **Keep Pages**:
  - Inverse selection
  - Extract to new PDF
  - Page range specification
</details>

<details>
<summary><b>PDF Security</b></summary>

- **Password Protection**:
  - Add/remove passwords
  - User password vs owner password
  - Encryption levels (40-bit to 256-bit AES)

- **Permissions**:
  - Allow/deny printing
  - Allow/deny copying
  - Allow/deny modification
  - Allow/deny form filling

- **QR Code Unlock**: ⭐ UNIQUE
  - Generate QR codes for PDF access
  - Secure unlock mechanism
  - Time-limited access codes
</details>

<details>
<summary><b>PDF Digital Signatures</b></summary>

- **Features**:
  - Digital signature creation
  - Certificate management
  - Signature verification
  - Multiple signature formats
  - Timestamp addition
  - Signature validation
</details>

<details>
<summary><b>PowerBI to PDF Converter</b> ⭐ ENTERPRISE</summary>

- **Features**:
  - PowerBI report conversion
  - Dashboard to PDF
  - Interactive element handling
  - Layout preservation
  - High-resolution output
  - Automated scheduling support
</details>

### 🌐 Web Content Processing

<details>
<summary><b>HTML to PDF with Screenshots</b> ⭐ NEW</summary>

- **Features**:
  - Full web page capture
  - Custom page sizes (A4, Letter, Legal, Custom)
  - Margin control
  - CSS styling preservation
  - JavaScript rendering support
  - Print media CSS
  - Background graphics
  - Header/footer customization
</details>

<details>
<summary><b>YAML ↔ JSON Converter</b> ⭐ NEW</summary>

- **Features**:
  - Bidirectional conversion
  - Syntax validation
  - Error highlighting with line numbers
  - Format beautification
  - Comment preservation (YAML)
  - Schema validation support
  - Minification options
</details>

### 🔍 OCR & Text Processing

<details>
<summary><b>Text & OCR Extraction</b></summary>

- **OCR Features**:
  - Multi-language support (11+ languages)
  - Confidence scoring
  - Layout analysis
  - Table detection
  - Handwriting recognition (limited)

- **Output Formats**:
  - Plain text (.txt)
  - Searchable PDF
  - DOCX with formatting
  - JSON with structure
  - HTML with markup

- **Languages Supported**:
  - English, Spanish, French, German, Italian
  - Portuguese, Russian, Chinese, Japanese, Korean
  - Arabic (experimental)
</details>

### 👥 User Management & Authentication

<details>
<summary><b>Authentication System</b></summary>

- **User Features**:
  - Email/password registration
  - Email verification with tokens
  - Secure login with bcrypt/Argon2 hashing
  - Password reset via email
  - Remember me functionality
  - Session management with security

- **Security Features**:
  - CSRF protection
  - Rate limiting (login attempts)
  - Account lockout after failed attempts
  - IP-based suspicious activity detection
  - Session fixation protection
  - Two-factor authentication (2FA) ready
</details>

<details>
<summary><b>User Dashboard</b></summary>

- **Features**:
  - Conversion history tracking
  - Usage statistics and analytics
  - Daily quota monitoring
  - File size limits display
  - Profile management
  - Subscription details
  - Download history
</details>

<details>
<summary><b>Role-Based Access Control (RBAC)</b></summary>

- **Roles**:
  - **Guest**: Limited access, no registration
  - **User**: Free tier with daily limits
  - **Premium**: Unlimited conversions, larger files
  - **Staff**: Content management access
  - **Admin**: Full system control

- **Permissions**:
  - Access control per feature
  - File size limits per role
  - Daily conversion quotas
  - API access levels
  - Advanced feature gates
</details>

### 📊 Admin Dashboard

<details>
<summary><b>User Management</b></summary>

- **Features**:
  - User list with search/filter
  - User role assignment
  - Account activation/deactivation
  - Account locking/unlocking
  - User statistics
  - Bulk operations
</details>

<details>
<summary><b>Analytics & Monitoring</b></summary>

- **Metrics**:
  - Total conversions (by type)
  - User registrations (daily/weekly/monthly)
  - Popular conversion types
  - Storage usage
  - Processing time statistics
  - Error rates

- **Visualizations**:
  - Line charts for trends
  - Pie charts for distribution
  - Bar charts for comparisons
  - Real-time data updates
</details>

<details>
<summary><b>System Monitoring</b></summary>

- **Features**:
  - Error log viewer
  - Security audit logs
  - Performance logs
  - Request logs
  - File operation logs
  - Export capabilities (CSV, JSON)
</details>

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer (Browser)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Web UI      │  │  REST API    │  │  WebSocket   │     │
│  │  (HTML/CSS)  │  │  Clients     │  │  Clients     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                   Application Layer (Flask)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Security Middleware                      │  │
│  │  • CSRF Protection  • Rate Limiting  • Auth         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Routes     │  │  Middleware  │  │   Core       │     │
│  │  • Main      │  │  • Usage     │  │  • Auth      │     │
│  │  • API       │  │    Tracking  │  │  • Error     │     │
│  │  • Auth      │  │  • Logging   │  │  • File Mgr  │     │
│  │  • Admin     │  │  • Session   │  │  • Logging   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 Conversion Engines                    │  │
│  │  • Image Processor  • PDF Processor  • OCR Engine   │  │
│  │  • Doc Converter    • Video Processor • RAW Handler │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  PostgreSQL  │  │    Redis     │  │  File        │     │
│  │  • Users     │  │  • Sessions  │  │  Storage     │     │
│  │  • Usage     │  │  • Cache     │  │  • Uploads   │     │
│  │  • History   │  │  • Queues    │  │  • Outputs   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Request Flow                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  Rate Limiter   │ ──► Block excessive requests
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  CSRF Guard     │ ──► Validate CSRF tokens
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Auth Check     │ ──► Verify user identity
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Input Validator │ ──► Sanitize all inputs
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  File Scanner   │ ──► Check for malware
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Permission Check│ ──► Verify user permissions
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Process        │ ──► Execute request
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Audit Log      │ ──► Log security events
         └─────────────────┘
```

### Modular File Structure

```
cropio/
├── 📄 Core Application Files
│   ├── app.py                          # Application entry point & Flask app factory
│   ├── config.py                       # Configuration management (Dev/Prod/Test)
│   ├── models.py                       # SQLAlchemy database models
│   ├── forms.py                        # WTForms validation forms
│   ├── db_manager.py                   # Database management CLI utility
│   ├── check_backends.py               # Backend validation utilities
│   └── .env.example                    # Environment variables template
│
├── 🔧 core/                            # Core Functionality Modules
│   ├── __init__.py
│   ├── auth_security.py                # Authentication & security (Argon2, 2FA, sessions)
│   ├── error_handlers.py               # Global error handling & monitoring
│   ├── file_manager.py                 # Secure file operations & validation
│   └── logging_config.py               # Structured logging system
│
├── 🛤️ routes/                          # Flask Blueprint Routes
│   ├── __init__.py                     # Blueprint registration
│   ├── main_routes.py                  # Homepage & main navigation
│   ├── auth_routes.py                  # User authentication (login/register/verify)
│   ├── dashboard_routes.py             # User dashboard & profile
│   ├── admin.py                        # Admin panel & user management
│   ├── api_routes.py                   # REST API endpoints
│   ├── health_routes.py                # Health check endpoints
│   ├── file_serving_routes.py          # File downloads & previews
│   ├── reverse_converter_routes.py     # PDF to image conversion
│   ├── heic_jpg_routes.py              # Legacy HEIC route (duplicate)
│   ├── latex_pdf_routes.py             # Legacy LaTeX route
│   └── yaml_json_routes.py             # Legacy YAML route
│   │
│   ├── 🖼️ image/                       # Image Processing Routes
│   │   ├── __init__.py
│   │   ├── raw_jpg_routes.py           # RAW (DNG/CR2/NEF) to JPG conversion
│   │   ├── heic_jpg_routes.py          # HEIC/HEIF to JPG conversion
│   │   ├── gif_mp4_routes.py           # GIF to MP4 video conversion
│   │   └── gif_png_sequence_routes.py  # GIF ↔ PNG sequence conversion
│   │
│   ├── 🖼️ image_converter/             # Standard Image Converters
│   │   ├── __init__.py
│   │   ├── image_converter_routes.py   # Standard image format conversion
│   │   └── image_cropper_routes.py     # Image & PDF cropping tool
│   │
│   ├── 📄 document/                    # Document Processing Routes
│   │   ├── __pycache__/
│   │   └── markdown_html_converter_routes.py  # Markdown ↔ HTML conversion
│   │
│   ├── 📄 document_converter/          # Document Converters
│   │   ├── __pycache__/
│   │   └── document_converter_routes.py       # DOCX to PDF/TXT conversion
│   │
│   ├── 📊 excel_converter/             # Excel Processing Routes
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   └── excel_converter_routes.py          # Excel to CSV/JSON/PDF
│   │
│   ├── 📋 pdf_converters/              # PDF Processing Routes
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── pdf_converter_routes.py            # PDF to DOCX/CSV/Images
│   │   ├── pdf_editor_routes.py               # PDF editing interface
│   │   ├── pdf_merge_routes.py                # PDF merging functionality
│   │   ├── pdf_page_delete_routes.py          # PDF page deletion
│   │   ├── pdf_signature_routes.py            # PDF digital signatures
│   │   ├── secure_pdf_routes.py               # PDF password protection
│   │   ├── pdf_presentation_converter_routes.py  # PDF to PPTX conversion
│   │   └── powerbi_converter_routes.py        # PowerBI to PDF conversion
│   │
│   ├── 📊 presentation_converter/      # Presentation Routes
│   │   ├── __pycache__/
│   │   └── presentation_converter_routes.py   # PPTX to PDF conversion
│   │
│   ├── 📓 notebook_converter/          # Jupyter Notebook Routes
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   └── notebook_converter_routes.py       # Jupyter to HTML/PDF/DOCX
│   │
│   ├── 📁 file_compressor/             # File Compression Routes
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   └── file_compressor_routes.py          # Image & PDF compression
│   │
│   ├── 🔍 text_ocr_converters/         # OCR Processing Routes
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── text_ocr_routes.py                 # OCR text extraction
│   │   └── text_ocr_routes_full.py            # Extended OCR functionality
│   │
│   └── 🌐 web_code/                    # Web Content Processing Routes
│       ├── __pycache__/
│       ├── html_pdf_snapshot_routes.py        # HTML to PDF with screenshots
│       ├── yaml_json_routes.py                # YAML ↔ JSON conversion
│       └── html_pdf_routes.py.backup          # Backup file
│
├── 🔧 utils/                           # Utility Functions & Processors
│   ├── __init__.py
│   ├── helpers.py                      # General helper functions
│   ├── email_service.py                # Email sending & verification
│   ├── latex_utils.py                  # LaTeX processing utilities
│   ├── permissions.py                  # Permission checking utilities
│   ├── security.py                     # Security helper functions
│   ├── usage_utils.py                  # Usage calculation utilities
│   └── auth_decorators.py              # Authentication decorators
│   │
│   ├── 🖼️ image/                       # Image Processing Utilities
│   │   ├── __pycache__/
│   │   ├── gif_processor.py            # GIF processing & conversion
│   │   ├── heic_processor.py           # HEIC/HEIF image processing
│   │   └── raw_processor.py            # RAW image processing (DNG/CR2/NEF)
│   │
│   ├── 🖼️ image_converter/             # Image Converter Utilities
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── image_converter_utils.py    # Standard image conversion utilities
│   │   └── image_cropper_utils.py      # Image cropping utilities
│   │
│   ├── 📄 document/                    # Document Processing Utilities
│   │   └── __pycache__/
│   │
│   ├── 📄 document_converter/          # Document Converter Utilities
│   │   ├── __pycache__/
│   │   └── document_converter_utils.py # DOCX conversion utilities
│   │
│   ├── 📊 excel_converter/             # Excel Processing Utilities
│   │   ├── __pycache__/
│   │   └── excel_utils.py              # Excel conversion utilities
│   │
│   ├── 📋 pdf_converters/              # PDF Processing Utilities
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── powerbi_utils.py            # PowerBI to PDF conversion (1126 lines)
│   │   ├── pdf_presentation_utils.py   # PDF to PPTX utilities
│   │   └── secure_pdf_utils.py         # PDF security utilities
│   │
│   ├── 📊 presentation_converter/      # Presentation Utilities
│   │   ├── __pycache__/
│   │   └── presentation_utils.py       # PPTX conversion utilities
│   │
│   ├── 📓 notebook_converter/          # Notebook Processing Utilities
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   └── notebook_utils.py           # Jupyter notebook conversion utilities
│   │
│   ├── 📁 file_compressor/             # Compression Utilities
│   │   ├── __pycache__/
│   │   └── file_compressor_utils.py    # File compression utilities
│   │
│   ├── 🔍 text_ocr_converters/         # OCR Utilities
│   │   ├── __pycache__/
│   │   └── text_ocr_utils.py           # OCR processing utilities
│   │
│   ├── 🎬 video/                       # Video Processing Utilities
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── ffmpeg_utils.py             # FFmpeg wrapper utilities
│   │   └── gif_mp4_processor.py        # GIF to MP4 conversion
│   │
│   └── 🌐 web_code/                    # Web Content Processing Utilities
│       ├── __init__.py
│       ├── __pycache__/
│       ├── html_pdf_snapshot_utils.py  # Web screenshot utilities
│       ├── setup_validator.py          # Setup validation utilities
│       └── yaml_processor.py           # YAML/JSON processing
│
├── 🔒 security/                        # Universal Security Framework
│   ├── __init__.py                     # Security framework initialization
│   ├── logging.py                      # Security logging
│   │
│   ├── config/                         # Security Configuration
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── security_config.py          # Security settings
│   │   └── constants.py                # Security constants
│   │
│   ├── core/                           # Core Security Modules
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── decorators.py               # Security decorators (rate_limit, validate_file)
│   │   ├── validators.py               # Input validation functions
│   │   ├── validators_extended.py      # Extended validators
│   │   ├── sanitizers.py               # Data sanitization functions
│   │   ├── sanitizers_extended.py      # Extended sanitizers
│   │   ├── exceptions.py               # Security exception classes
│   │   ├── error_handlers.py           # Security error handlers
│   │   ├── access_control.py           # Access control & permissions
│   │   ├── audit.py                    # Audit logging
│   │   ├── crypto.py                   # Cryptography utilities
│   │   └── rate_limiter.py             # Rate limiting implementation
│   │
│   ├── auth_security/                  # Authentication Security
│   ├── file_security/                  # File Security Modules
│   ├── web_security/                   # Web Security Modules
│   ├── utils/                          # Security Utilities
│   │
│   └── tests/                          # Security Tests
│       ├── __init__.py
│       ├── fixtures/                   # Test fixtures
│       └── malware_samples/            # Malware test samples
│
├── 🔄 middleware/                      # Application Middleware
│   ├── __init__.py
│   ├── __pycache__/
│   ├── usage_tracker.py                # Usage tracking & quota enforcement
│   └── usage_tracking.py               # Legacy usage tracking (deprecated)
│
├── 🎨 templates/                       # Jinja2 HTML Templates
│   ├── base.html                       # Base template with navigation
│   ├── layout.html                     # Main layout template
│   ├── index.html                      # Homepage template
│   ├── convert_to_docx.html            # Legacy converter template
│   │
│   ├── auth/                           # Authentication Templates
│   │   ├── login.html                  # User login form
│   │   ├── register.html               # User registration form
│   │   ├── profile.html                # User profile page
│   │   ├── edit_profile.html           # Profile editing form
│   │   ├── change_password.html        # Password change form
│   │   ├── delete_account.html         # Account deletion form
│   │   ├── settings.html               # User settings page
│   │   ├── request_password_reset.html # Password reset request
│   │   └── reset_password.html         # Password reset form
│   │
│   ├── user_dashboard/                 # User Dashboard Templates
│   │   ├── dashboard.html              # Main dashboard
│   │   ├── history.html                # Conversion history
│   │   ├── subscription.html           # Subscription management
│   │   ├── profile.html                # Profile overview
│   │   └── edit_profile.html           # Profile editing
│   │
│   ├── admin/                          # Admin Panel Templates
│   │   ├── dashboard.html              # Admin main dashboard
│   │   └── users.html                  # User management interface
│   │
│   ├── converters/                     # Converter Templates (Legacy)
│   │   ├── heic_jpg.html               # HEIC to JPG converter
│   │   ├── latex_pdf.html              # LaTeX to PDF converter
│   │   └── yaml_json.html              # YAML/JSON converter
│   │
│   ├── document/                       # Document Processing Templates
│   │   ├── latex_pdf.html              # LaTeX to PDF interface
│   │   └── markdown_html_converter.html # Markdown/HTML interface
│   │
│   ├── document_converter/             # Document Converter Templates
│   │   └── document_converter.html     # DOCX conversion interface
│   │
│   ├── excel_converter/                # Excel Converter Templates
│   │   └── excel_converter.html        # Excel conversion interface
│   │
│   ├── file_compressor/                # Compression Templates
│   │   └── file_compressor.html        # File compressor interface
│   │
│   ├── image/                          # Image Processing Templates
│   │   ├── raw_jpg.html                # RAW image conversion
│   │   ├── heic_jpg.html               # HEIC conversion (organized)
│   │   ├── heic_jpg_converter.html     # HEIC converter (legacy)
│   │   ├── gif_mp4.html                # GIF to MP4 conversion
│   │   └── gif_png_sequence.html       # GIF to PNG sequence
│   │
│   ├── image_converter/                # Image Converter Templates
│   │   ├── image_converter.html        # Standard image conversion
│   │   └── image_cropper.html          # Image/PDF cropper
│   │
│   ├── notebook_converter/             # Notebook Templates
│   │   └── notebook_converter.html     # Jupyter notebook converter
│   │
│   ├── pdf_converters/                 # PDF Tool Templates
│   │   ├── pdf_converter.html          # PDF to DOCX/CSV conversion
│   │   ├── pdf_editor.html             # PDF editor interface
│   │   ├── pdf_merge.html              # PDF merger interface
│   │   ├── pdf_page_delete.html        # PDF page delete interface
│   │   ├── pdf_signature.html          # PDF signature interface
│   │   ├── secure_pdf.html             # Secure PDF interface
│   │   ├── pdf_presentation_converter.html  # PDF to PPTX
│   │   ├── powerbi_converter.html      # PowerBI to PDF
│   │   └── convert_to_pdf.html         # Convert to PDF
│   │
│   ├── presentation_converter/         # Presentation Templates
│   │   └── presentation_converter.html # PPTX conversion interface
│   │
│   ├── text_ocr_converters/            # OCR Templates
│   │   ├── text_ocr.html               # OCR text extraction
│   │   └── debug_test.html             # Debug test template
│   │
│   ├── web_code/                       # Web Code Processing Templates
│   │   ├── html_pdf_snapshot.html      # HTML screenshot to PDF
│   │   ├── yaml_json.html              # YAML/JSON conversion
│   │   └── html_pdf.html               # HTML to PDF (legacy)
│   │
│   └── errors/                         # Error Page Templates
│       ├── 400.html                    # Bad request
│       ├── 403.html                    # Access forbidden
│       ├── 404.html                    # Page not found
│       ├── 413.html                    # File too large
│       ├── 429.html                    # Rate limit exceeded
│       └── 500.html                    # Internal server error
│
├── 🎨 static/                          # Static Assets (CSS/JS)
│   ├── favicon.ico                     # Website favicon
│   ├── base.css                        # Base application styling
│   ├── style.css                       # Global styles
│   ├── home.css                        # Homepage styles
│   │
│   ├── css/                            # Feature-Specific Stylesheets
│   │   ├── converter.css               # File converter styles
│   │   ├── compressor.css              # File compressor styles
│   │   ├── cropper.css                 # Image cropper styles
│   │   ├── notebook_converter.css      # Notebook converter styles
│   │   ├── pdf_editor.css              # PDF editor styles
│   │   ├── pdf_merge.css               # PDF merge styles
│   │   ├── pdf_page_delete.css         # PDF page delete styles
│   │   ├── pdf_signature.css           # PDF signature styles
│   │   ├── secure_pdf.css              # Secure PDF styles
│   │   ├── phase-1-5.css               # Phase 1.5 features styles
│   │   │
│   │   ├── auth/                       # Authentication Styles
│   │   │   └── auth.css                # Login/register form styles
│   │   │
│   │   ├── user_dashboard/             # Dashboard Styles
│   │   │   ├── dashboard.css           # Main dashboard styles
│   │   │   └── profile.css             # User profile styles
│   │   │
│   │   ├── document/                   # Document Processing Styles
│   │   │   ├── latex_pdf.css           # LaTeX to PDF styles
│   │   │   └── markdown_html_converter.css # Markdown/HTML styles
│   │   │
│   │   ├── image/                      # Image Processing Styles
│   │   │   ├── raw_jpg.css             # RAW image conversion styles
│   │   │   ├── heic_jpg.css            # HEIC conversion styles
│   │   │   ├── gif_mp4.css             # GIF to MP4 styles
│   │   │   └── gif_png_sequence.css    # GIF to PNG sequence styles
│   │   │
│   │   ├── web_code/                   # Web Code Processing Styles
│   │   │   ├── html_pdf_snapshot.css   # HTML screenshot styles
│   │   │   └── yaml_json.css           # YAML/JSON conversion styles
│   │   │
│   │   └── themes/                     # Theme-specific Styles
│   │       └── css/
│   │           └── yaml_json_theme.css # YAML/JSON theme
│   │
│   └── js/                             # JavaScript Modules
│       ├── main.js                     # Core application logic
│       ├── theme.js                    # Theme switching & navigation
│       ├── index.js                    # Homepage interactivity
│       ├── converter.js                # File conversion utilities
│       ├── compressor.js               # File compression interface
│       ├── cropper.js                  # Image cropping interface
│       ├── notebook_converter.js       # Notebook conversion interface
│       ├── pdf_editor.js               # Full PDF editor with advanced features
│       ├── pdf_editor_simple.js        # Simple PDF editor
│       ├── pdf_merge.js                # PDF merging functionality
│       ├── pdf_page_delete.js          # PDF page deletion functionality
│       ├── pdf_signature.js            # PDF signature tools
│       ├── secure_pdf.js               # PDF security and encryption
│       │
│       ├── auth/                       # Authentication Scripts
│       │   └── auth.js                 # Login/register form handling
│       │
│       ├── user_dashboard/             # Dashboard Scripts
│       │   └── profile.js              # User profile management
│       │
│       ├── document/                   # Document Processing Scripts
│       │   ├── latex_pdf.js            # LaTeX to PDF interface
│       │   └── markdown_html_converter.js # Markdown/HTML interface
│       │
│       ├── image/                      # Image Processing Scripts
│       │   ├── raw_jpg.js              # RAW image conversion interface
│       │   ├── heic_jpg.js             # HEIC conversion interface
│       │   ├── gif_mp4.js              # GIF to MP4 interface
│       │   ├── gif_png_sequence.js     # GIF to PNG sequence interface
│       │   └── gif_png_sequence_new.js # Enhanced GIF sequence interface
│       │
│       └── web_code/                   # Web Code Processing Scripts
│           ├── html_pdf_snapshot.js    # HTML screenshot interface
│           └── yaml_json.js            # YAML/JSON conversion interface
│
├── 🗄️ database/                        # Database Management System
│   ├── README.md                       # Database documentation
│   ├── __init__.py                     # Database module initialization
│   ├── db_config.py                    # Database configuration & utilities
│   │
│   ├── schemas/                        # Database Schema Files
│   │   ├── database_schema.sql         # Main PostgreSQL schema definition
│   │   └── database_schema_ascii.txt   # ASCII representation of schema
│   │
│   ├── migrations/                     # Database Migration Files
│   │   └── [timestamp]_[name].sql      # Timestamped migration files
│   │
│   └── scripts/                        # Database Utility Scripts
│       └── init_db.py                  # Database initialization script
│
├── 🔄 migrations/                      # Alembic Database Migrations
│   ├── __pycache__/
│   ├── alembic.ini                     # Alembic configuration
│   ├── env.py                          # Migration environment
│   ├── README                          # Migration instructions
│   ├── script.py.mako                  # Migration template
│   └── versions/                       # Migration version files
│       └── [migration_files].py
│
├── 📝 logs/                            # Application Logs
│   ├── cropio.log                      # Main application log
│   ├── errors.log                      # Error log (ERROR level)
│   ├── security_audit.log              # Security events & audit trail
│   └── performance.log                 # Performance metrics & slow queries
│
├── 📤 uploads/                         # Temporary File Uploads
│   └── [uploaded_files]                # User uploaded files (auto-cleanup)
│
├── 📦 outputs/                         # Processed Output Files
│   └── [converted_files]               # Converted/processed files (auto-cleanup)
│
├── 🗂️ temp/                            # Temporary Processing Files
│   ├── gif_mp4/                        # GIF to MP4 temp files
│   └── pdf_editor/                     # PDF editor temp files
│
├── 📦 compressed/                      # Compressed Files Output
│   └── [compressed_files]              # Compressed output files
│
├── 🧪 tests/                           # Test Suite
│   ├── __init__.py
│   ├── integration_phase1.py           # Phase 1 integration tests
│   └── smoke_auth_routes.py            # Authentication smoke tests
│
├── ⚙️ config/                          # Configuration Files
│   └── html_pdf_config.json            # HTML to PDF configuration
│
├── 📋 Requirements file/               # Dependency Files
│   ├── requirements-dev.txt            # Development dependencies
│   └── requirements_html_pdf.txt       # HTML to PDF specific requirements
│
├── 📄 md files/                        # Documentation & Guides
│   ├── Cropio_readme.md                # Project overview
│   ├── DEPLOYMENT.md                   # Deployment guide
│   ├── SECURITY_CHECKLIST.md           # Security checklist
│   ├── DATABASE_MIGRATION_GUIDE.md     # Database migration guide
│   ├── MANUAL_TESTING_CHECKLIST.md     # Testing checklist
│   ├── PRODUCTION_DEPLOYMENT_CHECKLIST.md
│   ├── SECURITY_FRAMEWORK_STATUS.md
│   ├── PHASE_1_5_IMPLEMENTATION_SUMMARY.md
│   └── [other documentation files]
│
├── 🐳 bin/                             # Binary Executables
│   ├── ffmpeg.exe                      # FFmpeg for video processing
│   ├── ffplay.exe                      # FFmpeg player
│   └── ffprobe.exe                     # FFmpeg probe
│
├── 📊 puml/                            # PlantUML Diagrams
│   ├── cropio_system_architecture.puml
│   ├── cropio_security_architecture.puml
│   ├── database_schema_uml.puml
│   ├── DATABASE_UML_README.md
│   └── .gitignore
│
├── 💾 instance/                        # Instance-Specific Files
│   └── cropio.db                       # SQLite database (development)
│
├── 🔐 backup_before_security_migration_*/ # Backup Folders
│   └── [backup files]                  # Historical backups
│
├── 📦 venv/                            # Virtual Environment
│   └── [python packages]               # Isolated Python environment
│
├── 📄 Root Configuration Files
│   ├── requirements.txt                # Production dependencies (180 packages)
│   ├── requirements_document_converter.txt # Document converter deps
│   ├── runtime.txt                     # Python version specification
│   ├── .env.example                    # Environment variables template
│   ├── .gitignore                      # Git ignore patterns
│   ├── Dockerfile                      # Docker container configuration
│   ├── docker-compose.yml              # Multi-service Docker setup
│   ├── render-build.sh                 # Render.com deployment script
│   ├── run_app.bat                     # Windows batch file for running app
│   ├── WARP.md                         # WARP configuration
│   └── README.md                       # This comprehensive documentation
│
└── 🔧 Utility Scripts
    ├── db_manager.py                   # Database management CLI
    ├── check_backends.py               # Backend validation
    ├── debug_400_error.py              # Debug utility
    ├── fix_converter_routes.py         # Route fixing utility
    ├── migrate_security.py             # Security migration script
    ├── monitoring_config.py            # Monitoring configuration
    ├── production_readiness_test.py    # Production readiness check
    ├── security_audit.py               # Security audit tool
    ├── setup_weasyprint.py             # WeasyPrint setup
    ├── excel_test_manual.csv           # Test data
    └── sample_notebook.ipynb           # Sample Jupyter notebook
```

---

## 🛠️ Technology Stack

### Backend Technologies

| Category | Technologies |
|----------|-------------|
| **Framework** | Flask 3.0.0, Werkzeug 3.0.1 |
| **Database** | PostgreSQL (production), SQLAlchemy 2.0.23 |
| **Authentication** | Flask-Login 0.6.3, bcrypt 4.1.2, Argon2 |
| **Security** | Flask-SeaSurf (CSRF), Flask-Limiter (rate limiting) |
| **Caching** | Redis 5.0.1, hiredis 2.2.3 |
| **Email** | Flask-Mail 0.9.1 |
| **Task Queue** | Celery 5.3.4, APScheduler 3.10.4 |
| **Migrations** | Flask-Migrate 4.0.5, Alembic 1.13.0 |

### File Processing Libraries

| Type | Libraries |
|------|-----------|
| **Image Processing** | Pillow 10.1.0, rawpy 0.25.1, pillow-heif 0.13.1 |
| **PDF Processing** | PyMuPDF 1.23.8, pdf2docx 0.5.6, PyPDF2 3.0.1, pdfplumber 0.10.3 |
| **Video Processing** | imageio 2.33.1, imageio-ffmpeg 0.4.9, opencv-python 4.8.1.78 |
| **Document Processing** | python-docx 1.1.0, openpyxl 3.1.2, pandas 2.1.4 |
| **OCR** | pytesseract 0.3.10 |
| **Web to PDF** | weasyprint 60.2, selenium 4.16.0, pdfkit 1.0.0 |
| **Markdown/LaTeX** | markdown 3.5.1, pypandoc 1.13, nbconvert 7.16.4 |
| **Config Processing** | PyYAML 6.0.1, ruamel.yaml 0.18.5 |

### Frontend Technologies

| Type | Technologies |
|------|-------------|
| **UI Framework** | Tailwind CSS 3.x |
| **JavaScript** | Vanilla JS (ES6+) |
| **PDF Handling** | PDF.js, PDF-lib.js |
| **Image Cropping** | Cropper.js |
| **Charts** | Chart.js (planned) |

### Security & Monitoring

| Category | Tools |
|----------|-------|
| **File Security** | python-magic 0.4.27, filetype 1.2.0 |
| **Monitoring** | Sentry SDK 1.39.2, Prometheus Flask Exporter 0.23.0 |
| **2FA** | pyotp 2.9.0 |
| **Cryptography** | cryptography 41.0.8, PyJWT 2.8.0 |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12+ (or SQLite for development)
- Redis (optional, for caching)
- FFmpeg (for video processing)
- Tesseract OCR (for text extraction)
- wkhtmltopdf (for HTML to PDF)
- Pandoc (for document conversion)
- LaTeX distribution (for LaTeX processing)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/cropio.git
cd cropio
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# Required: DATABASE_URL, FLASK_SECRET_KEY
# Optional: MAIL_SERVER, REDIS_URL
```

### 5. Initialize Database

```bash
# Initialize database tables
python db_manager.py init

# Or use Flask migrations
flask db upgrade
```

### 6. Install System Dependencies

**Windows (using Chocolatey)**:
```powershell
choco install ffmpeg tesseract wkhtmltopdf pandoc miktex
```

**macOS (using Homebrew)**:
```bash
brew install ffmpeg tesseract-ocr wkhtmltopdf pandoc mactex
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg tesseract-ocr wkhtmltopdf pandoc \
    texlive-latex-recommended texlive-xetex texlive-fonts-recommended
```

### 7. Run Application

```bash
# Development mode
python app.py

# Production mode (with Gunicorn)
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app
```

### 8. Access Application

- **Local**: http://localhost:5000
- **Default Admin**: username: `admin`, password: `admin123` (⚠️ **Change in production!**)

---

## 📦 Installation

### Detailed Installation Guide

#### Step 1: System Requirements

Ensure your system meets these requirements:

- **Python**: 3.8, 3.9, 3.10, or 3.11
- **RAM**: Minimum 2GB (4GB recommended)
- **Disk Space**: 2GB for application + dependencies
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 20.04+

#### Step 2: Database Setup

**PostgreSQL (Recommended for Production)**:

```bash
# Install PostgreSQL
# Ubuntu
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/

# Create database
sudo -u postgres psql
CREATE DATABASE cropio_production;
CREATE USER cropio_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE cropio_production TO cropio_user;
\q
```

**SQLite (Development Only)**:

No setup required - automatically created on first run.

#### Step 3: Environment Configuration

Create `.env` file in project root:

```bash
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production  # or 'development'
FLASK_SECRET_KEY=your-super-secret-key-here-min-32-chars

# Database Configuration
DATABASE_URL=postgresql://cropio_user:your_password@localhost:5432/cropio_production
# For SQLite (dev only):
# DATABASE_URL=sqlite:///instance/cropio.db

# Email Configuration (for password reset, verification)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=noreply@cropio.com

# Security Configuration
SESSION_TIMEOUT=3600  # 1 hour in seconds
MAX_CONTENT_LENGTH=524288000  # 500MB in bytes

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/1

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379/1

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_DIR=logs

# Payment Gateway (optional)
RAZORPAY_KEY_ID=your-razorpay-key
RAZORPAY_KEY_SECRET=your-razorpay-secret
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key

# Monitoring (optional)
SENTRY_DSN=your-sentry-dsn
```

#### Step 4: Dependency Installation

```bash
# Upgrade pip
pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Verify installation
python -c "import flask; print(flask.__version__)"
```

#### Step 5: Database Migration

```bash
# View database structure
python db_manager.py structure

# Initialize database
python db_manager.py init

# Using Flask-Migrate (alternative)
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

#### Step 6: System Dependencies

**FFmpeg** (for video/GIF processing):
```bash
# Verify installation
ffmpeg -version
```

**Tesseract OCR** (for text extraction):
```bash
# Verify installation
tesseract --version
```

**wkhtmltopdf** (for HTML to PDF):
```bash
# Verify installation
wkhtmltopdf --version
```

**Pandoc** (for document conversion):
```bash
# Verify installation
pandoc --version
```

**LaTeX** (for LaTeX processing):
```bash
# Verify installation
xelatex --version
pdflatex --version
```

---

## ⚙️ Configuration

### Configuration Files

#### 1. `config.py` - Main Configuration

```python
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/cropio_dev'
    # ... other dev settings

class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # ... other production settings
```

#### 2. Environment Variables (`.env`)

Key configurations:

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `production` or `development` |
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@host:5432/db` |
| `FLASK_SECRET_KEY` | Secret key for sessions | 32+ character random string |
| `MAIL_SERVER` | Email server host | `smtp.gmail.com` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/1` |
| `MAX_CONTENT_LENGTH` | Maximum upload size (bytes) | `524288000` (500MB) |
| `SESSION_TIMEOUT` | Session timeout (seconds) | `3600` (1 hour) |

#### 3. Security Configuration

```python
# Security headers
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-XSS-Protection': '1; mode=block',
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}

# Rate limiting
RATELIMIT_STORAGE_URL = 'redis://localhost:6379/1'
RATELIMIT_HEADERS_ENABLED = True

# Session security
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

#### 4. File Processing Configuration

```python
# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'gif', 'heic', 'raw'},
    'pdf': {'pdf'},
    'document': {'docx', 'doc', 'odt'},
    'excel': {'xlsx', 'xls', 'csv'},
    # ... more formats
}

# File size limits (bytes)
MAX_FILE_SIZE_FREE = 52428800  # 50MB
MAX_FILE_SIZE_PREMIUM = 5368709120  # 5GB

# Processing timeouts
REQUEST_TIMEOUT = 120  # 2 minutes for large files
```

---

## 📖 Usage

### Web Interface

#### 1. User Registration & Login

```
1. Navigate to /register
2. Fill in email, username, password
3. Verify email (check inbox)
4. Login at /login
```

#### 2. Converting Files

**Image Conversion Example**:
```
1. Go to /image-converter
2. Upload image file (drag & drop or browse)
3. Select output format (PNG, JPG, WEBP, etc.)
4. Adjust quality settings
5. Click "Convert"
6. Download converted file
```

**PDF to DOCX Conversion**:
```
1. Go to /pdf-converter
2. Upload PDF file
3. Select "DOCX" as output format
4. Click "Convert"
5. Download editable Word document
```

#### 3. Advanced Tools

**PDF Editor**:
```
1. Go to /pdf-editor
2. Upload PDF file
3. Use tools:
   - Text tool: Click to add text
   - Draw tool: Freehand drawing
   - Highlight tool: Select and highlight
4. Click "Save" to download edited PDF
```

**Image Cropper**:
```
1. Go to /image-cropper
2. Upload image
3. Adjust crop area (drag corners)
4. Select aspect ratio (optional)
5. Choose output format
6. Click "Crop & Download"
```

### API Usage

#### Authentication

```bash
# Login to get session cookie
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email": "user@example.com", "password": "password123"}'
```

#### File Conversion API

**HEIC to JPG**:
```bash
curl -X POST http://localhost:5000/api/heic-convert \
  -F "file=@image.heic" \
  -F "conversion_type=heic_to_jpg" \
  -F "quality=95"
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully converted image.heic",
  "download_url": "/heic-jpg/download/converted_image.jpg",
  "stats": {
    "output_format": "JPEG",
    "converted_size": "2.45 MB",
    "processing_time": "< 1s",
    "compression_ratio": "35.2%"
  }
}
```

**Get File Info**:
```bash
curl -X POST http://localhost:5000/api/heic-info \
  -F "file=@image.heic"
```

**Response**:
```json
{
  "success": true,
  "info": {
    "width": 4032,
    "height": 3024,
    "format": "HEIC",
    "color_mode": "RGB",
    "has_exif": true,
    "size": 3567890,
    "dimensions": "4032 × 3024"
  }
}
```

#### Usage Monitoring

```bash
# Get user usage stats
curl -X GET http://localhost:5000/api/usage-update \
  -H "Cookie: session=your_session_cookie"
```

**Response**:
```json
{
  "conversions_used": 3,
  "daily_limit": "unlimited",
  "percentage": 0,
  "can_convert": true,
  "time_until_reset": "18h 42m",
  "quota_exceeded": false
}
```

### Python SDK (Programmatic Usage)

```python
from cropio_client import CropioClient

# Initialize client
client = CropioClient(
    base_url='http://localhost:5000',
    api_key='your_api_key'  # Optional
)

# Login
client.login('user@example.com', 'password123')

# Convert HEIC to JPG
result = client.convert_heic(
    input_file='image.heic',
    output_format='jpg',
    quality=95
)

print(f"Converted file: {result['download_url']}")
print(f"Compression: {result['stats']['compression_ratio']}")

# Batch conversion
results = client.batch_convert(
    files=['image1.heic', 'image2.heic', 'image3.heic'],
    output_format='jpg',
    quality=90
)

for result in results:
    print(f"Converted: {result['original']} -> {result['converted']}")
```

---

## 🔌 API Reference

### Base URL

```
Development: http://localhost:5000
Production: https://your-domain.com
```

### Authentication

All authenticated endpoints require session cookie or API key.

**Headers**:
```
Cookie: session=your_session_cookie
# OR
Authorization: Bearer your_api_key
```

### Endpoints

#### Image Processing APIs

**HEIC Conversion**:
```http
POST /api/heic-convert
Content-Type: multipart/form-data

Parameters:
- file: File (HEIC/HEIF image)
- conversion_type: String ("heic_to_jpg" or "jpg_to_heic")
- quality: Integer (50-100, default: 95)
- output_format: String ("jpeg" or "png", default: "jpeg")
- preserve_metadata: Boolean (default: false)

Response: 200 OK
{
  "success": true,
  "message": "Successfully converted",
  "download_url": "/path/to/converted/file",
  "stats": {...}
}
```

**Get File Info**:
```http
POST /api/heic-info
Content-Type: multipart/form-data

Parameters:
- file: File (any image format)

Response: 200 OK
{
  "success": true,
  "info": {
    "width": 4032,
    "height": 3024,
    "format": "HEIC",
    ...
  }
}
```

**Preview Converted File**:
```http
GET /api/preview-converted/{filename}

Response: 200 OK
{
  "success": true,
  "preview": "data:image/jpeg;base64,...",
  "format": "JPEG"
}
```

#### User Management APIs

**Get User Status**:
```http
GET /api/user-status

Response: 200 OK
{
  "authenticated": true,
  "username": "john_doe",
  "is_premium": false,
  "usage": {
    "conversions_used": 3,
    "daily_limit": 5,
    "percentage": 60,
    "can_convert": true
  }
}
```

**Update Usage**:
```http
GET /api/usage-update
Requires: Authentication

Response: 200 OK
{
  "conversions_used": 3,
  "daily_limit": 5,
  "can_convert": true,
  "time_until_reset": "18h 42m"
}
```

### Error Responses

**400 Bad Request**:
```json
{
  "success": false,
  "error": "Invalid file type. Allowed: heic, heif, jpg, jpeg, png"
}
```

**401 Unauthorized**:
```json
{
  "error": "Authentication required"
}
```

**413 Payload Too Large**:
```json
{
  "success": false,
  "error": "File too large. Maximum size: 50MB",
  "max_size_mb": 50,
  "file_size_mb": 75.5
}
```

**429 Too Many Requests**:
```json
{
  "success": false,
  "error": "Too many requests. Please slow down.",
  "retry_after": 60
}
```

**500 Internal Server Error**:
```json
{
  "success": false,
  "error": "File processing failed. Please try again."
}
```

### Rate Limits

| Endpoint | Free Users | Premium Users |
|----------|------------|---------------|
| `/api/heic-info` | 30/minute | 120/minute |
| `/api/heic-convert` | 20/minute | 100/minute |
| `/api/preview-converted` | 60/minute | 240/minute |
| Authentication | 5/minute | N/A |

---

## 🔒 Security

### Security Framework

Cropio implements a comprehensive, multi-layered security framework:

#### 1. Input Validation & Sanitization

- **Filename Validation**: Prevents path traversal attacks
- **Content Validation**: Deep file content inspection
- **MIME Type Verification**: Ensures file matches claimed type
- **File Size Limits**: Role-based size restrictions
- **Malware Scanning**: Pattern-based threat detection

#### 2. Authentication & Authorization

- **Password Security**:
  - Bcrypt/Argon2 hashing
  - Minimum 8 characters with complexity requirements
  - Password strength validator
  - Common password blacklist
  - Keyboard pattern detection

- **Session Management**:
  - Secure session cookies (HttpOnly, Secure, SameSite)
  - Session fixation protection
  - IP-based validation
  - User-agent verification
  - Automatic session expiration

- **Account Security**:
  - Progressive lockout after failed attempts
  - Suspicious IP detection
  - Email verification required
  - Two-factor authentication (2FA) ready

#### 3. CSRF Protection

- Flask-SeaSurf integration
- Token validation on all state-changing requests
- Double-submit cookie pattern
- Automatic token rotation

#### 4. Rate Limiting

- IP-based rate limiting
- User-based quotas
- Endpoint-specific limits
- Automatic blocking of abusive IPs
- Graceful degradation

#### 5. File Security

```python
# File validation process
┌─────────────────────┐
│  Upload File        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Sanitize Filename  │ ──► Remove dangerous characters
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Validate Extension │ ──► Check allowed types
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Check File Size    │ ──► Enforce size limits
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Scan Magic Bytes   │ ──► Detect file signature
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Verify MIME Type   │ ──► Match content to extension
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Malware Scan       │ ──► Pattern matching
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Process or Reject  │
└─────────────────────┘
```

#### 6. Security Headers

Automatic security headers on all responses:

```python
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'
```

#### 7. Audit Logging

All security events are logged:

- Login attempts (successful/failed)
- Account lockouts
- Suspicious IP activity
- File upload security violations
- Admin actions
- Permission changes
- Session anomalies

Log location: `logs/security_audit.log`

#### 8. Database Security

- SQL injection prevention (SQLAlchemy ORM)
- Prepared statements
- Connection pooling with timeouts
- Encrypted passwords (never plain text)
- Database connection encryption (TLS)

### Security Best Practices

#### For Administrators

1. **Change Default Credentials**:
   ```bash
   # Change admin password immediately
   flask shell
   >>> from models import User
   >>> admin = User.query.filter_by(username='admin').first()
   >>> admin.set_password('new_secure_password_here')
   >>> db.session.commit()
   ```

2. **Use Environment Variables**:
   - Never commit `.env` file to version control
   - Use strong, unique secret keys
   - Rotate keys periodically

3. **Enable HTTPS**:
   ```bash
   # Use HTTPS in production
   SESSION_COOKIE_SECURE = True
   PREFERRED_URL_SCHEME = 'https'
   ```

4. **Monitor Security Logs**:
   ```bash
   tail -f logs/security_audit.log
   ```

5. **Regular Updates**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

#### For Users

1. **Use Strong Passwords**: Minimum 8 characters, mix of upper/lower/numbers/symbols
2. **Enable 2FA**: When available
3. **Verify Email**: Complete email verification
4. **Avoid Public Computers**: Don't save sessions on shared devices
5. **Report Suspicious Activity**: Contact support immediately

### Vulnerability Reporting

If you discover a security vulnerability, please email:
**security@cropio.com**

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We take security seriously and will respond within 48 hours.

---

## 🚀 Deployment

### Production Deployment Options

#### Option 1: Traditional Server Deployment (Ubuntu/Debian)

**Step 1: Prepare Server**

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y python3.10 python3.10-venv python3-pip \
    postgresql postgresql-contrib redis-server nginx supervisor \
    ffmpeg tesseract-ocr wkhtmltopdf pandoc texlive-xetex

# Create application user
sudo adduser --system --group --home /var/www/cropio cropio
```

**Step 2: Setup Application**

```bash
# Clone repository
sudo su - cropio
cd /var/www/cropio
git clone https://github.com/yourusername/cropio.git app
cd app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

**Step 3: Configure PostgreSQL**

```bash
sudo -u postgres psql
CREATE DATABASE cropio_production;
CREATE USER cropio_user WITH PASSWORD 'your_secure_password';
ALTER ROLE cropio_user SET client_encoding TO 'utf8';
ALTER ROLE cropio_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE cropio_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE cropio_production TO cropio_user;
\q
```

**Step 4: Configure Environment**

```bash
# Create .env file
cat > /var/www/cropio/app/.env << EOF
FLASK_ENV=production
FLASK_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://cropio_user:your_secure_password@localhost/cropio_production
REDIS_URL=redis://localhost:6379/1
# Add other environment variables
EOF

# Set permissions
chmod 600 .env
```

**Step 5: Initialize Database**

```bash
source venv/bin/activate
python db_manager.py init
# Or
flask db upgrade
```

**Step 6: Configure Gunicorn**

Create `/etc/supervisor/conf.d/cropio.conf`:

```ini
[program:cropio]
directory=/var/www/cropio/app
command=/var/www/cropio/app/venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile /var/log/cropio/access.log \
    --error-logfile /var/log/cropio/error.log \
    app:app
user=cropio
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/cropio/stderr.log
stdout_logfile=/var/log/cropio/stdout.log
```

**Step 7: Configure Nginx**

Create `/etc/nginx/sites-available/cropio`:

```nginx
upstream cropio_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # File upload size limit
    client_max_body_size 500M;

    # Proxy settings
    location / {
        proxy_pass http://cropio_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for large files
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
        send_timeout 300;
    }

    # Static files
    location /static {
        alias /var/www/cropio/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Logs
    access_log /var/log/nginx/cropio-access.log;
    error_log /var/log/nginx/cropio-error.log;
}
```

**Step 8: Enable and Start Services**

```bash
# Create log directories
sudo mkdir -p /var/log/cropio
sudo chown cropio:cropio /var/log/cropio

# Enable nginx site
sudo ln -s /etc/nginx/sites-available/cropio /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Start application
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start cropio

# Enable services on boot
sudo systemctl enable nginx
sudo systemctl enable postgresql
sudo systemctl enable redis-server
sudo systemctl enable supervisor
```

**Step 9: Setup SSL with Let's Encrypt**

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

#### Option 2: Docker Deployment

**Step 1: Create Dockerfile**

Already included in the project:

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    ffmpeg \
    tesseract-ocr \
    wkhtmltopdf \
    pandoc \
    texlive-xetex \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 cropio && chown -R cropio:cropio /app
USER cropio

# Expose port
EXPOSE 8000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:app"]
```

**Step 2: Create docker-compose.yml**

Already included in the project:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://cropio:password@db:5432/cropio
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./logs:/app/logs

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=cropio
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=cropio
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
```

**Step 3: Deploy with Docker Compose**

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Initialize database
docker-compose exec web python db_manager.py init

# Stop services
docker-compose down

# Update application
git pull
docker-compose build
docker-compose up -d
```

#### Option 3: Platform as a Service (PaaS)

**Heroku Deployment**:

```bash
# Install Heroku CLI
# Create Heroku app
heroku create cropio-app

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis addon
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set FLASK_SECRET_KEY=$(openssl rand -hex 32)

# Deploy
git push heroku main

# Initialize database
heroku run python db_manager.py init

# Open app
heroku open
```

**Render Deployment**:

1. Connect GitHub repository
2. Create Web Service
3. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT app:app`
4. Add PostgreSQL database
5. Set environment variables
6. Deploy

### Performance Optimization

#### 1. Enable Caching

```python
# Install Flask-Caching
pip install Flask-Caching

# In app.py
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': os.environ.get('REDIS_URL')
})

# Cache expensive operations
@cache.cached(timeout=300)
def get_conversion_stats():
    # Expensive database query
    pass
```

#### 2. Use CDN for Static Files

```python
# Configure CDN URL
CDN_URL = 'https://cdn.your-domain.com'

# In templates
<link href="{{ url_for('static', filename='css/base.css', _external=True, _scheme='https') }}">
```

#### 3. Optimize Database Queries

```python
# Use eager loading
users = User.query.options(
    joinedload(User.conversions),
    joinedload(User.usage_records)
).all()

# Index frequently queried fields
class User(db.Model):
    email = db.Column(db.String(120), index=True, unique=True)
    created_at = db.Column(db.DateTime, index=True)
```

#### 4. Background Task Processing

```python
# Configure Celery
from celery import Celery

celery = Celery(
    app.name,
    broker=app.config['REDIS_URL'],
    backend=app.config['REDIS_URL']
)

# Background task
@celery.task
def process_large_file(file_path):
    # Heavy processing
    pass

# In route
@app.route('/convert', methods=['POST'])
def convert():
    task = process_large_file.delay(file_path)
    return jsonify({'task_id': task.id})
```

### Monitoring & Maintenance

#### 1. Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/admin/monitoring/health
```

#### 2. Log Monitoring

```bash
# View application logs
tail -f logs/cropio.log

# View error logs
tail -f logs/errors.log

# View security logs
tail -f logs/security_audit.log
```

#### 3. Performance Monitoring

```bash
# View performance metrics
tail -f logs/performance.log

# Database query performance
psql -d cropio_production -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

#### 4. Backup Strategy

```bash
# Database backup script (cronjob)
#!/bin/bash
BACKUP_DIR="/backups/cropio"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
pg_dump cropio_production > "$BACKUP_DIR/db_$DATE.sql"

# Backup uploads
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" /var/www/cropio/app/uploads

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

# Add to crontab
# 0 2 * * * /path/to/backup_script.sh
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/integration_phase1.py

# Run with coverage
python -m pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Test configuration
├── integration_phase1.py       # Integration tests
├── smoke_auth_routes.py        # Authentication tests
├── test_converters.py          # Converter tests
├── test_security.py            # Security tests
└── test_api.py                 # API tests
```

### Manual Testing Checklist

See `md files/MANUAL_TESTING_CHECKLIST.md` for comprehensive manual testing procedures.

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### How to Contribute

1. **Fork the Repository**
   ```bash
   git clone https://github.com/yourusername/cropio.git
   cd cropio
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make Changes**
   - Write clean, documented code
   - Follow PEP 8 style guide
   - Add tests for new features
   - Update documentation

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add amazing feature"
   ```

5. **Push to Branch**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Open Pull Request**
   - Describe changes clearly
   - Reference any related issues
   - Ensure all tests pass

### Code Style

```python
# Follow PEP 8
# Use type hints
def convert_image(input_path: str, output_format: str) -> str:
    """
    Convert image to specified format.
    
    Args:
        input_path: Path to input image
        output_format: Desired output format
        
    Returns:
        Path to converted image
    """
    # Implementation
    pass

# Use docstrings for all functions/classes
# Keep functions focused and small
# Write self-documenting code
```

### Reporting Bugs

**Create an issue** with:
- **Title**: Clear, concise description
- **Description**: Detailed explanation
- **Steps to Reproduce**: Numbered steps
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, browser
- **Screenshots**: If applicable
- **Logs**: Error messages/stack traces

### Feature Requests

**Create an issue** with:
- **Title**: Feature name
- **Description**: What and why
- **Use Case**: How it would be used
- **Alternatives**: Other solutions considered
- **Additional Context**: Any other information

---

## 🗺️ Roadmap

### ✅ Phase 1: Core Foundation (COMPLETED)
- [x] Database models (User, Subscription, Usage)
- [x] User authentication (login, register, email verification)
- [x] PostgreSQL setup with Alembic migrations
- [x] Security framework (CSRF, rate limiting, headers)
- [x] Email services (Flask-Mail, verification)

### ✅ Phase 1.5: Advanced File Processing (COMPLETED)
- [x] RAW image processing (DNG, CR2, NEF)
- [x] HEIC image support (Apple HEIC to JPG)
- [x] Video/GIF processing (GIF to MP4, PNG sequence)
- [x] Advanced document processing
- [x] Configuration file processing (YAML/JSON)
- [x] HTML to PDF with screenshots

### ✅ Phase 2: User Management (COMPLETED - 95%)
- [x] User dashboard
- [x] Usage tracking middleware
- [x] Admin interface
- [x] Conversion history
- [x] Role-based access control
- [ ] Payment integration (PENDING)

### 🔄 Phase 3: Premium Features (IN PROGRESS - 15%)
- [ ] Payment gateway integration (Razorpay/Stripe)
- [ ] AI background removal (OpenCV-based)
- [ ] Advanced OCR (multi-language)
- [x] Batch processing (basic support)
- [ ] Subscription management
- [ ] Invoice generation

### 📋 Phase 4: Enterprise Features (PLANNED)
- [ ] API keys and programmatic access
- [ ] Webhook notifications
- [ ] Advanced analytics dashboard
- [ ] Team/organization accounts
- [ ] Custom branding options
- [ ] White-label solution

### 🚀 Phase 5: Scalability & Performance (PLANNED)
- [ ] Microservices architecture
- [ ] Kubernetes deployment
- [ ] CDN integration
- [ ] Multi-region support
- [ ] Load balancing
- [ ] Auto-scaling

### 🔮 Future Enhancements (PLANNED)
- [ ] Mobile applications (iOS/Android)
- [ ] Browser extensions
- [ ] Desktop applications (Electron)
- [ ] AI-powered compression
- [ ] Real-time collaboration
- [ ] Version control for files
- [ ] Template marketplace
- [ ] Integration marketplace (Zapier, IFTTT)

### Community Requests
Vote on features at: https://github.com/yourusername/cropio/discussions

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Cropio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👥 Team & Credits

### Core Team
- **Himanshu** - Creator & Lead Developer

### Contributors
See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the full list of contributors.

### Acknowledgments

We would like to thank:
- **Open Source Community** for the amazing libraries and tools
- **Flask Team** for the excellent web framework
- **Contributors** for their valuable contributions
- **Users** for feedback and bug reports

### Built With

This project uses these amazing open-source libraries:
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Pillow](https://python-pillow.org/) - Image processing
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [Tailwind CSS](https://tailwindcss.com/) - CSS framework
- [Cropper.js](https://fengyuanchen.github.io/cropperjs/) - Image cropping
- [PDF.js](https://mozilla.github.io/pdf.js/) - PDF rendering
- And many more (see [requirements.txt](requirements.txt))

---

## 📞 Support & Contact

### Getting Help

- **Documentation**: This README and `md files/` directory
- **Issues**: [GitHub Issues](https://github.com/yourusername/cropio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cropio/discussions)
- **Email**: support@cropio.com

### Stay Updated

- **Star** this repository to get notified of updates
- **Watch** for release announcements
- **Follow** on Twitter: [@CropioApp](https://twitter.com/CropioApp)

### Professional Support

For enterprise support, custom development, or consulting:
- **Email**: enterprise@cropio.com
- **Website**: https://cropio.com/enterprise

---

## 📊 Statistics

![GitHub stars](https://img.shields.io/github/stars/yourusername/cropio?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/cropio?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/yourusername/cropio?style=social)
![GitHub contributors](https://img.shields.io/github/contributors/yourusername/cropio)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/yourusername/cropio)
![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/cropio)

---

<div align="center">

**Made with ❤️ by the Cropio Team**

[⬆ Back to Top](#-cropio--advanced-multi-format-file-conversion--processing-platform)

</div>
