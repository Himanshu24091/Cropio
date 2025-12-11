# Modular Flask Application Structure

This document explains the new modular structure of the Cropio converter application.

## Directory Structure

```
converter1/
├── app.py                          # Main application file (modular)
├── app_backup.py                   # Backup of original monolithic app.py
├── config.py                       # Configuration settings
├── test_routes.py                  # Route testing script
├── requirements.txt                # Python dependencies
├── runtime.txt                     # Python version specification
├── routes/                         # Route modules
│   ├── __init__.py
│   ├── main_routes.py              # Index/home page routes
│   ├── image_converter_routes.py   # Image conversion routes
│   ├── pdf_converter_routes.py     # PDF conversion routes
│   ├── document_converter_routes.py # Document conversion routes
│   ├── excel_converter_routes.py   # Excel conversion routes
│   ├── compressor_routes.py        # File compression routes
│   ├── cropper_routes.py           # Image cropping routes
│   ├── pdf_editor_routes.py        # PDF editor routes
│   └── file_serving_routes.py      # File download/preview routes
├── utils/                          # Utility functions
│   ├── __init__.py
│   └── helpers.py                  # Helper functions (compression, file validation, etc.)
├── static/                         # Static assets
│   ├── css/                        # Stylesheets
│   └── js/                         # JavaScript files (separated by functionality)
│       ├── theme.js                # Theme toggle functionality
│       ├── index.js                # Index page functionality
│       ├── compressor.js           # Compressor page functionality
│       ├── cropper.js              # Cropper page functionality
│       ├── converter.js            # Generic converter functionality
│       ├── pdf_editor.js           # PDF editor functionality
│       └── pdf_editor_simple.js    # Simplified PDF editor
└── templates/                      # HTML templates
    ├── base.html                   # Base template (updated with modular JS)
    ├── layout.html                 # Layout for converter pages
    ├── index.html                  # Home page
    ├── compressor.html             # File compressor page
    ├── cropper.html                # Image cropper page
    ├── pdf_editor.html             # PDF editor page
    └── [converter templates]       # Various converter templates
```

## Route Modules

### 1. main_routes.py
- **Route**: `/`
- **Function**: Renders the home page
- **Blueprint**: `main_bp`

### 2. image_converter_routes.py
- **Route**: `/image-converter`
- **Function**: Handles image format conversion (PNG, JPG, WEBP, etc.)
- **Blueprint**: `image_converter_bp`

### 3. pdf_converter_routes.py
- **Route**: `/pdf-converter`
- **Function**: Converts PDF to DOCX, CSV
- **Blueprint**: `pdf_converter_bp`

### 4. document_converter_routes.py
- **Route**: `/document-converter`
- **Function**: Converts DOCX to TXT
- **Blueprint**: `document_converter_bp`

### 5. excel_converter_routes.py
- **Route**: `/excel-converter`
- **Function**: Converts Excel files to CSV or JSON
- **Blueprint**: `excel_converter_bp`

### 6. compressor_routes.py
- **Routes**: `/compressor`, `/compress`
- **Function**: Compresses images and PDF files
- **Blueprint**: `compressor_bp`

### 7. cropper_routes.py
- **Routes**: `/image-cropper`, `/pdf-to-image-preview`, `/crop-image`
- **Function**: Crops images and PDF pages
- **Blueprint**: `cropper_bp`

### 8. pdf_editor_routes.py
- **Route**: `/pdf-editor`
- **Function**: Renders PDF editor interface
- **Blueprint**: `pdf_editor_bp`

### 9. file_serving_routes.py
- **Routes**: `/download/<filename>`, `/preview/<filename>`
- **Function**: Serves files for download and preview
- **Blueprint**: `file_serving_bp`

## JavaScript Modules

The JavaScript has been separated into focused modules:

- **theme.js**: Theme toggle functionality (loaded on all pages)
- **index.js**: File preview and interaction for converter pages
- **compressor.js**: File compression interface logic
- **cropper.js**: Image cropping interface logic
- **converter.js**: Generic converter functionality for file handling
- **pdf_editor.js**: Full PDF editor functionality
- **pdf_editor_simple.js**: Simplified PDF editor implementation

## Configuration (config.py)

Contains all application constants:
- File extension allowlists
- Directory setup functions
- Path configurations

## Utilities (utils/helpers.py)

Contains helper functions:
- `allowed_file()`: File validation
- `compress_image()`: Image compression
- `compress_pdf()`: PDF compression
- `cleanup_files()`: Background file cleanup

## How to Run

1. **Using the new modular app**:
   ```bash
   python app.py
   ```

2. **Testing all routes**:
   ```bash
   python test_routes.py
   ```

3. **Reverting to original structure** (if needed):
   ```bash
   copy app_backup.py app.py
   ```

## Benefits of This Structure

1. **Maintainability**: Each route group is in its own file
2. **Scalability**: Easy to add new converters or features
3. **Testing**: Each module can be tested independently
4. **Debugging**: Easier to locate and fix issues
5. **Team Development**: Multiple developers can work on different modules
6. **Code Reuse**: Common functionality is centralized in utils/

## Adding New Routes

To add a new converter:

1. Create a new file in `routes/` (e.g., `new_converter_routes.py`)
2. Define your blueprint and routes
3. Import and register the blueprint in `app.py`
4. Add corresponding JavaScript file if needed
5. Update templates to link to the new JavaScript

Example:
```python
# routes/new_converter_routes.py
from flask import Blueprint, render_template

new_converter_bp = Blueprint('new_converter', __name__)

@new_converter_bp.route('/new-converter')
def new_converter():
    return render_template('new_converter.html')
```

Then in `app.py`:
```python
from routes.new_converter_routes import new_converter_bp
# ...
app.register_blueprint(new_converter_bp)
```
