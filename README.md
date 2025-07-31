so Cropio
Cropio is a comprehensive, all-in-one web application for file manipulation, built with Flask and modern frontend technologies. It provides a suite of powerful tools including file conversion, compression, image cropping, and a full-featured PDF editor, all wrapped in a sleek, responsive, and user-friendly interface.

✨ Main Features
Multi-Tool Interface: A single application that houses multiple file processing utilities.

Modern UI/UX: Clean, responsive design with a dark mode, built with Tailwind CSS.

Drag & Drop: Intuitive drag-and-drop file uploads for all tools.

Real-time Previews: Interactive previews for images, PDFs, and cropping.

Backend Processing: Powered by a robust Flask backend using libraries like Pillow and PyMuPDF.

Automatic Cleanup: A background scheduler automatically deletes temporary files after one hour to save server space.

🛠️ Tools Included
1. File Converters
A collection of tools to convert files from one format to another.

Image Converter: Convert PNG, JPG, WEBP, BMP, TIFF files to various image formats, including PDF and ICO.

PDF Converter: Convert PDF files into editable DOCX documents or CSV spreadsheets.

Document Converter: Convert DOCX files into PDF or plain TXT files.

Excel Converter: Convert XLSX or XLS spreadsheets into CSV or JSON format.

2. File Compressor
Reduce the file size of your images and PDFs without significant quality loss.

Supported Formats: PNG, JPG, WEBP, and PDF.

Compression Levels: Choose between Low, Medium, and High compression to balance size and quality.

Batch Processing: Upload and compress multiple files at once.

Detailed Results: See the original size, compressed size, and the total percentage saved for each file.

3. Image & PDF Cropper
A precise tool for cropping images and the first page of PDF documents.

Supported Formats: PNG, JPG, WEBP, and PDF.

Interactive Preview: A real-time preview window shows exactly what you're cropping.

Aspect Ratio Control: Lock the crop box to standard ratios like 16:9, 4:3, 1:1, or use Free form.

Multiple Output Formats: Download the final cropped image as a JPEG, PNG, WEBP, or even a PDF.

4. PDF EditX
A client-side PDF editor to make changes directly in your browser.

PDF Rendering: Upload a PDF and view all its pages with a thumbnail sidebar for easy navigation.

Editing Tools:

Add Text: Place new text boxes anywhere on a page.

Draw: Freehand drawing tool for annotations.

Highlight: Add highlight rectangles over text.

Client-Side Processing: Edits are handled in the browser using PDF-lib.js and PDF.js for a fast and responsive experience.

Download Edited PDF: Save your changes and download the new, modified PDF file.

🚀 Tech Stack
Backend: Flask, Pillow, PyMuPDF, pdf2docx, pandas, APScheduler

Frontend: HTML5, Tailwind CSS, JavaScript

Libraries: Cropper.js, PDF.js, PDF-lib.js

📂 Project Structure
cropio/
|
|-- app.py                   # Main Flask application
|-- requirements.txt         # Python dependencies
|-- uploads/                 # Temporary folder for original files
|-- compressed/              # Temporary folder for compressed files
|
|-- static/
|   |-- css/
|   |   `-- style.css        # Custom CSS styles
|   `-- js/
|       |-- main.js          # JS for converters, compressor, cropper
|       `-- pdf_editor.js    # Dedicated JS for the PDF Editor
|
`-- templates/
    |-- base.html            # Main layout with navbar and footer
    |-- layout.html          # Layout for simple converter pages
    |-- index.html           # Homepage
    |-- image_converter.html
    |-- pdf_converter.html
    |-- document_converter.html
    |-- excel_converter.html
    |-- compressor.html      # UI for the File Compressor
    |-- cropper.html         # UI for the Image Cropper
    `-- pdf_editor.html      # UI for the PDF Editor


⚙️ Setup and Installation
Clone or download the project.

Navigate to the project directory:

cd cropio


Create and activate a virtual environment (recommended):

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
py -m venv venv
.\venv\Scripts\activate


Install the required dependencies:

pip install -r requirements.txt


▶️ How to Run
Once the installation is complete, run the Flask application:

python app.py