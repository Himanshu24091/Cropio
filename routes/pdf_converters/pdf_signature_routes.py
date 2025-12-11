# routes/pdf_signature_routes.py
import os
import base64
import uuid
import time
import json
from io import BytesIO
from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
import tempfile
from datetime import datetime

pdf_signature_bp = Blueprint('pdf_signature', __name__)

ALLOWED_EXTENSIONS = {'pdf'}
SIGNATURE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions

def get_pdf_info(pdf_path):
    """Get PDF information including page count and dimensions"""
    try:
        doc = fitz.open(pdf_path)
        pages_info = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            rect = page.rect
            pages_info.append({
                'page_number': page_num + 1,
                'width': rect.width,
                'height': rect.height
            })
        
        doc.close()
        return {
            'success': True,
            'page_count': len(pages_info),
            'pages': pages_info
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def generate_pdf_preview(pdf_path, page_num=0, dpi=150):
    """Generate base64 encoded preview of PDF page"""
    try:
        doc = fitz.open(pdf_path)
        if page_num >= len(doc):
            page_num = 0
        
        page = doc[page_num]
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        doc.close()
        
        # Convert to base64
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        current_app.logger.error(f"Error generating PDF preview: {e}")
        return None

@pdf_signature_bp.route('/pdf-signature')
def pdf_signature():
    """Main PDF signature page"""
    return render_template('pdf_converters/pdf_signature.html')

@pdf_signature_bp.route('/api/pdf-signature/upload', methods=['POST'])
def upload_pdf():
    """Handle PDF file upload and return preview info"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename, ALLOWED_EXTENSIONS):
        return jsonify({'error': 'Please upload a PDF file'}), 400
    
    try:
        # Save uploaded PDF
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        upload_dir = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)
        
        # Get PDF info
        pdf_info = get_pdf_info(filepath)
        if not pdf_info['success']:
            return jsonify({'error': 'Failed to process PDF'}), 500
        
        # Generate preview for first page
        preview_url = generate_pdf_preview(filepath, 0)
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'original_name': filename,
            'page_count': pdf_info['page_count'],
            'pages': pdf_info['pages'],
            'preview_url': preview_url
        })
        
    except Exception as e:
        current_app.logger.error(f"Error uploading PDF: {e}")
        return jsonify({'error': 'Failed to upload PDF'}), 500

@pdf_signature_bp.route('/api/pdf-signature/preview/<filename>/<int:page_num>')
def get_page_preview(filename, page_num):
    """Get preview of specific PDF page"""
    try:
        upload_dir = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
        filepath = os.path.join(upload_dir, secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        preview_url = generate_pdf_preview(filepath, page_num - 1)
        if preview_url:
            return jsonify({
                'success': True,
                'preview_url': preview_url,
                'page_number': page_num
            })
        else:
            return jsonify({'error': 'Failed to generate preview'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error generating page preview: {e}")
        return jsonify({'error': 'Failed to generate preview'}), 500

@pdf_signature_bp.route('/api/pdf-signature/upload-signature', methods=['POST'])
def upload_signature():
    """Handle signature image upload"""
    if 'signature' not in request.files:
        return jsonify({'error': 'No signature file uploaded'}), 400
    
    file = request.files['signature']
    if file.filename == '':
        return jsonify({'error': 'No signature file selected'}), 400
    
    if not allowed_file(file.filename, SIGNATURE_EXTENSIONS):
        return jsonify({'error': 'Please upload an image file (PNG, JPG, JPEG, GIF)'}), 400
    
    try:
        # Process and save signature
        signature_id = str(uuid.uuid4())
        upload_dir = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
        signature_filename = f"signature_{signature_id}.png"
        signature_path = os.path.join(upload_dir, signature_filename)
        
        # Convert to PNG and save
        img = Image.open(file.stream)
        # Make background transparent if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Remove white background (make transparent)
        data = img.getdata()
        new_data = []
        for item in data:
            # Change all white (also shades of white) pixels to transparent
            if item[0] > 200 and item[1] > 200 and item[2] > 200:
                new_data.append((255, 255, 255, 0))  # Transparent
            else:
                new_data.append(item)
        
        img.putdata(new_data)
        img.save(signature_path, 'PNG')
        
        # Convert to base64 for preview
        with open(signature_path, 'rb') as f:
            signature_data = base64.b64encode(f.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'signature_id': signature_id,
            'signature_filename': signature_filename,
            'signature_data': f"data:image/png;base64,{signature_data}"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error uploading signature: {e}")
        return jsonify({'error': 'Failed to process signature'}), 500

@pdf_signature_bp.route('/api/pdf-signature/save-drawn', methods=['POST'])
def save_drawn_signature():
    """Save drawn signature from canvas"""
    try:
        data = request.get_json()
        if not data or 'signature_data' not in data:
            return jsonify({'error': 'No signature data provided'}), 400
        
        signature_data = data['signature_data']
        # Remove data URL prefix
        if signature_data.startswith('data:image/png;base64,'):
            signature_data = signature_data.replace('data:image/png;base64,', '')
        
        # Decode base64 image
        signature_bytes = base64.b64decode(signature_data)
        
        # Save signature
        signature_id = str(uuid.uuid4())
        upload_dir = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
        signature_filename = f"signature_{signature_id}.png"
        signature_path = os.path.join(upload_dir, signature_filename)
        
        with open(signature_path, 'wb') as f:
            f.write(signature_bytes)
        
        return jsonify({
            'success': True,
            'signature_id': signature_id,
            'signature_filename': signature_filename,
            'signature_data': f"data:image/png;base64,{signature_data}"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error saving drawn signature: {e}")
        return jsonify({'error': 'Failed to save signature'}), 500

@pdf_signature_bp.route('/api/pdf-signature/apply', methods=['POST'])
def apply_signature():
    """Apply signature to PDF at specified position"""
    try:
        data = request.get_json()
        required_fields = ['pdf_filename', 'signature_filename', 'page_number', 'x', 'y', 'width', 'height']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        upload_dir = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
        
        # Get file paths
        pdf_path = os.path.join(upload_dir, secure_filename(data['pdf_filename']))
        signature_path = os.path.join(upload_dir, secure_filename(data['signature_filename']))
        
        if not os.path.exists(pdf_path) or not os.path.exists(signature_path):
            return jsonify({'error': 'PDF or signature file not found'}), 404
        
        # Apply signature to PDF
        signed_pdf_path = apply_signature_to_pdf(
            pdf_path=pdf_path,
            signature_path=signature_path,
            page_number=int(data['page_number']) - 1,  # Convert to 0-based index
            x=float(data['x']),
            y=float(data['y']),
            width=float(data['width']),
            height=float(data['height'])
        )
        
        if signed_pdf_path and os.path.exists(signed_pdf_path):
            # Return the signed PDF file directly
            try:
                return send_file(
                    signed_pdf_path,
                    as_attachment=True,
                    download_name=f"signed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mimetype='application/pdf'
                )
            finally:
                # Clean up temporary file after sending
                try:
                    os.remove(signed_pdf_path)
                except:
                    pass
        else:
            return jsonify({'error': 'Failed to apply signature'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error applying signature: {e}")
        return jsonify({'error': 'Failed to apply signature'}), 500

def apply_signature_to_pdf(pdf_path, signature_path, page_number, x, y, width, height):
    """Apply signature to PDF using PyMuPDF"""
    try:
        # Open PDF
        doc = fitz.open(pdf_path)
        
        if page_number >= len(doc):
            doc.close()
            return None
        
        page = doc[page_number]
        
        # Open signature image
        signature_img = Image.open(signature_path)
        
        # Convert PIL image to bytes
        img_buffer = BytesIO()
        signature_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Convert coordinates (from web page coordinates to PDF coordinates)
        page_rect = page.rect
        pdf_x = x
        pdf_y = page_rect.height - y - height  # PDF coordinates are bottom-up
        
        # Create rectangle for signature placement
        signature_rect = fitz.Rect(pdf_x, pdf_y, pdf_x + width, pdf_y + height)
        
        # Insert image
        page.insert_image(signature_rect, stream=img_buffer.getvalue())
        
        # Save signed PDF
        output_path = pdf_path.replace('.pdf', '_signed_temp.pdf')
        doc.save(output_path)
        doc.close()
        
        return output_path
        
    except Exception as e:
        current_app.logger.error(f"Error applying signature to PDF: {e}")
        return None

@pdf_signature_bp.route('/api/pdf-signature/download/<filename>')
def download_signed_pdf(filename):
    """Download signed PDF"""
    try:
        upload_dir = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
        filepath = os.path.join(upload_dir, secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Set download name
        download_name = 'signed_document.pdf'
        if filename.startswith('signed_pdf_'):
            download_name = f"signed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error downloading signed PDF: {e}")
        return jsonify({'error': 'Failed to download file'}), 500

@pdf_signature_bp.route('/api/pdf-signature/text-signature', methods=['POST'])
def create_text_signature():
    """Create signature from typed text"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text']
        font_size = data.get('font_size', 40)
        font_style = data.get('font_style', 'script')  # script, cursive, elegant
        
        # Create signature image from text
        signature_id = str(uuid.uuid4())
        upload_dir = current_app.config.get('UPLOAD_FOLDER', tempfile.gettempdir())
        signature_filename = f"signature_{signature_id}.png"
        signature_path = os.path.join(upload_dir, signature_filename)
        
        # Create image with text
        img_width = len(text) * font_size + 100
        img_height = font_size + 50
        
        img = Image.new('RGBA', (img_width, img_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to use a script-like font (this will fall back to default if not available)
            if font_style == 'script':
                font = ImageFont.truetype("arial.ttf", font_size)
            elif font_style == 'cursive':
                font = ImageFont.truetype("comic.ttf", font_size)
            else:
                font = ImageFont.truetype("times.ttf", font_size)
        except:
            # Fall back to default font
            font = ImageFont.load_default()
        
        # Draw text in dark color
        draw.text((50, 25), text, fill=(0, 0, 0, 255), font=font)
        
        # Save signature
        img.save(signature_path, 'PNG')
        
        # Convert to base64 for preview
        with open(signature_path, 'rb') as f:
            signature_data = base64.b64encode(f.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'signature_id': signature_id,
            'signature_filename': signature_filename,
            'signature_data': f"data:image/png;base64,{signature_data}"
        })
        
    except Exception as e:
        current_app.logger.error(f"Error creating text signature: {e}")
        return jsonify({'error': 'Failed to create text signature'}), 500
