# routes/pdf_merge_routes.py
import os
import tempfile
from flask import Blueprint, render_template, request, jsonify, current_app, flash, send_file
from werkzeug.utils import secure_filename
from pypdf import PdfWriter, PdfReader
import fitz  # PyMuPDF for preview thumbnails
import base64
from io import BytesIO
from datetime import datetime

pdf_merge_bp = Blueprint('pdf_merge', __name__)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_pdf_thumbnail(pdf_bytes, page_num=0):
    """Generate thumbnail for PDF first page"""
    try:
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if page_num >= len(pdf_doc):
            page_num = 0
        
        page = pdf_doc[page_num]
        # Get page as image (150 DPI for thumbnail)
        mat = fitz.Matrix(150/72, 150/72)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        pdf_doc.close()
        
        # Convert to base64 for frontend
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return None

@pdf_merge_bp.route('/pdf-merge')
def pdf_merge():
    return render_template('pdf_converters/pdf_merge.html')

@pdf_merge_bp.route('/api/pdf-merge/upload', methods=['POST'])
def upload_pdf_files():
    """Handle multiple PDF file uploads and return file info with thumbnails"""
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400
    
    files = request.files.getlist('files[]')
    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No files selected'}), 400
    
    uploaded_files = []
    upload_dir = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
    
    for file in files:
        if file and allowed_file(file.filename):
            try:
                # Secure filename and save
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"{timestamp}_{filename}"
                filepath = os.path.join(upload_dir, unique_filename)
                
                file.save(filepath)
                
                # Read file for thumbnail generation
                with open(filepath, 'rb') as f:
                    pdf_bytes = f.read()
                
                # Get file info
                file_size = os.path.getsize(filepath)
                thumbnail = get_pdf_thumbnail(pdf_bytes)
                
                # Get page count
                try:
                    with fitz.open(filepath) as pdf_doc:
                        page_count = len(pdf_doc)
                except:
                    page_count = 1
                
                file_info = {
                    'id': unique_filename.replace('.', '_'),  # Safe ID for frontend
                    'filename': filename,
                    'unique_filename': unique_filename,
                    'size': file_size,
                    'size_formatted': format_file_size(file_size),
                    'page_count': page_count,
                    'thumbnail': thumbnail
                }
                
                uploaded_files.append(file_info)
                
            except Exception as e:
                print(f"Error processing file {file.filename}: {e}")
                continue
    
    if not uploaded_files:
        return jsonify({'error': 'No valid PDF files were uploaded'}), 400
    
    return jsonify({
        'success': True,
        'files': uploaded_files,
        'message': f'Successfully uploaded {len(uploaded_files)} PDF file(s)'
    })

@pdf_merge_bp.route('/api/pdf-merge/merge', methods=['POST'])
def merge_pdfs():
    """Merge PDFs in the specified order"""
    try:
        data = request.get_json()
        if not data or 'file_order' not in data:
            return jsonify({'error': 'No file order specified'}), 400
        
        file_order = data['file_order']
        if not file_order:
            return jsonify({'error': 'At least one file is required'}), 400
        
        upload_dir = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
        writer = PdfWriter()
        
        # Track valid files for cleanup
        valid_files = []
        
        # Add files to writer in specified order
        for unique_filename in file_order:
            filepath = os.path.join(upload_dir, unique_filename)
            
            if os.path.exists(filepath) and allowed_file(filepath):
                try:
                    reader = PdfReader(filepath)
                    # Add all pages from the current PDF to the writer
                    for page in reader.pages:
                        writer.add_page(page)
                    valid_files.append(filepath)
                except Exception as e:
                    print(f"Error adding {filepath} to writer: {e}")
                    continue
        
        if not valid_files:
            return jsonify({'error': 'No valid PDF files found for merging'}), 400
        
        # Create output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"merged_pdf_{timestamp}.pdf"
        output_path = os.path.join(upload_dir, output_filename)
        
        # Write merged PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        # Get merged file info
        file_size = os.path.getsize(output_path)
        
        # Generate preview thumbnail
        with open(output_path, 'rb') as f:
            pdf_bytes = f.read()
        thumbnail = get_pdf_thumbnail(pdf_bytes)
        
        # Get page count
        try:
            with fitz.open(output_path) as pdf_doc:
                total_pages = len(pdf_doc)
        except:
            total_pages = len(valid_files)  # Fallback estimate
        
        return jsonify({
            'success': True,
            'output_file': output_filename,
            'file_size': file_size,
            'file_size_formatted': format_file_size(file_size),
            'total_pages': total_pages,
            'thumbnail': thumbnail,
            'message': f'Successfully merged {len(valid_files)} PDF files'
        })
        
    except Exception as e:
        print(f"Error merging PDFs: {e}")
        return jsonify({'error': 'Failed to merge PDF files'}), 500

@pdf_merge_bp.route('/api/pdf-merge/download/<filename>')
def download_merged_pdf(filename):
    """Download the merged PDF file"""
    try:
        upload_dir = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
        filepath = os.path.join(upload_dir, secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Set download name without timestamp prefix
        download_name = filename
        if filename.startswith('merged_pdf_'):
            download_name = 'merged_document.pdf'
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        print(f"Error downloading file: {e}")
        return jsonify({'error': 'Failed to download file'}), 500

@pdf_merge_bp.route('/api/pdf-merge/preview/<filename>')
def preview_merged_pdf(filename):
    """Get preview thumbnail of merged PDF"""
    try:
        upload_dir = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
        filepath = os.path.join(upload_dir, secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        with open(filepath, 'rb') as f:
            pdf_bytes = f.read()
        
        thumbnail = get_pdf_thumbnail(pdf_bytes)
        
        if thumbnail:
            return jsonify({
                'success': True,
                'thumbnail': thumbnail
            })
        else:
            return jsonify({'error': 'Failed to generate preview'}), 500
            
    except Exception as e:
        print(f"Error generating preview: {e}")
        return jsonify({'error': 'Failed to generate preview'}), 500

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"
