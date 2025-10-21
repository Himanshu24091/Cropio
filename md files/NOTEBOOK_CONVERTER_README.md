# Jupyter Notebook Converter

A Flask web application that converts Jupyter Notebook (.ipynb) files to multiple formats including PDF, HTML, DOCX, TXT, Markdown, LaTeX, and reStructuredText.

## Features

- **Multiple Output Formats**: Convert to PDF, HTML, DOCX, TXT, Markdown, LaTeX, and RST
- **Drag & Drop Interface**: Easy file upload with drag and drop support
- **File Validation**: Validates .ipynb files and checks file size limits
- **Error Handling**: Comprehensive error handling for invalid or corrupted files
- **Clean UI**: Modern, responsive design with progress indicators
- **Direct Download**: Download converted files directly from the web interface
- **API Support**: RESTful API endpoints for programmatic access

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r notebook_requirements.txt
   ```

2. **Install System Dependencies** (for PDF conversion):
   
   **Windows:**
   - Install MiKTeX: https://miktex.org/download
   - Or install TeX Live: https://www.tug.org/texlive/windows.html
   
   **macOS:**
   ```bash
   brew install --cask mactex
   ```
   
   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt-get install texlive-xetex texlive-fonts-recommended texlive-plain-generic
   ```

3. **Install Pandoc** (for DOCX, TXT, RST conversion):
   
   **Windows:**
   - Download from: https://pandoc.org/installing.html
   
   **macOS:**
   ```bash
   brew install pandoc
   ```
   
   **Linux:**
   ```bash
   sudo apt-get install pandoc
   ```

## Integration with Existing Flask App

### Method 1: Add to Existing App

Add this to your main `app.py`:

```python
# Import the converter blueprint
from routes.converter import converter_bp

# Register the blueprint in your app
app.register_blueprint(converter_bp)

# Ensure upload and output folders exist
import os
os.makedirs('uploads', exist_ok=True)
os.makedirs('outputs', exist_ok=True)
```

### Method 2: Run Standalone

Run the dedicated notebook converter:

```bash
python notebook_converter_app.py
```

The application will be available at: `http://localhost:5001/notebook/`

## File Structure

```
converter/
├── routes/
│   └── converter.py              # Main conversion logic and routes
├── templates/
│   └── notebook_converter.html   # HTML template
├── static/
│   ├── notebook_converter.css    # Styling
│   └── js/
│       └── notebook_converter.js # Frontend JavaScript
├── uploads/                      # Temporary upload directory
├── outputs/                      # Converted files directory
├── notebook_converter_app.py     # Standalone Flask app
└── notebook_requirements.txt     # Python dependencies
```

## Usage

### Web Interface

1. Open the web interface in your browser
2. Upload a .ipynb file by:
   - Clicking the upload area and selecting a file
   - Dragging and dropping a file onto the upload area
3. Select your desired output format
4. Click "Convert Notebook"
5. Download the converted file when ready

### API Endpoints

**Convert Notebook:**
```
POST /notebook/api/convert
Content-Type: multipart/form-data

Form data:
- notebook_file: .ipynb file
- output_format: html|pdf|docx|markdown|txt|latex|rst

Response:
{
  "success": true,
  "download_url": "/notebook/download/filename.ext",
  "filename": "filename.ext",
  "format": "html"
}
```

**Download File:**
```
GET /notebook/download/<filename>
```

### Supported Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| HTML | .html | Web-ready format with interactive output |
| PDF | .pdf | Professional document format |
| DOCX | .docx | Microsoft Word compatible |
| Markdown | .md | Clean, readable text format |
| TXT | .txt | Plain text format |
| LaTeX | .tex | Academic publishing format |
| RST | .rst | reStructuredText format |

## Configuration

### Environment Variables

- `FLASK_ENV`: Set to `development` for debug mode
- `SECRET_KEY`: Set a secure secret key for production
- `MAX_CONTENT_LENGTH`: Maximum file upload size (default: 50MB)

### Customization

**Upload Limits:**
Edit the `MAX_CONTENT_LENGTH` in the Flask app configuration.

**Supported Formats:**
Modify the `SUPPORTED_FORMATS` dictionary in `routes/converter.py`.

**Styling:**
Customize `static/notebook_converter.css` for different themes.

## Troubleshooting

### Common Issues

1. **PDF Conversion Fails:**
   - Ensure LaTeX is installed and in your PATH
   - Try installing additional LaTeX packages if needed

2. **DOCX/TXT Conversion Fails:**
   - Ensure Pandoc is installed and accessible
   - Check that pypandoc can find your Pandoc installation

3. **File Upload Errors:**
   - Check file size limits
   - Ensure the file is a valid .ipynb file
   - Verify write permissions for uploads/ and outputs/ directories

4. **Module Import Errors:**
   - Ensure all dependencies are installed: `pip install -r notebook_requirements.txt`
   - Check Python path and virtual environment

### Debug Mode

Run with debug enabled to see detailed error messages:

```python
app.run(debug=True)
```

## Security Considerations

- File uploads are validated for type and size
- Temporary files are cleaned up after conversion
- Consider implementing rate limiting for production use
- Use HTTPS in production environments
- Regularly clean up old files from uploads/ and outputs/ directories

## License

This project is provided as-is for educational and development purposes.

## Contributing

Feel free to submit issues, fork the repository, and submit pull requests for any improvements.
