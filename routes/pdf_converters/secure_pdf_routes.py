# routes/secure_pdf_routes.py
import os
import json
import uuid
import time
from io import BytesIO
from flask import Blueprint, render_template, request, flash, redirect, send_file, current_app, jsonify, url_for
import PyPDF2
import qrcode
from PIL import Image
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file

secure_pdf_bp = Blueprint('secure_pdf', __name__)

# In-memory storage for QR unlock tokens (in production, use Redis or database)
qr_unlock_tokens = {}

@secure_pdf_bp.route('/secure-pdf', methods=['GET', 'POST'])
def secure_pdf():
    """Main route for PDF security operations"""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'protect':
            return protect_pdf()
        elif action == 'unlock':
            return unlock_pdf()
        elif action == 'generate_qr':
            return generate_qr_unlock()
        elif action == 'qr_unlock':
            return qr_unlock_pdf()
    
    return render_template('pdf_converters/secure_pdf.html')

def protect_pdf():
    """Protect a PDF with password"""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    password = request.form.get('password')
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    if not password:
        flash('Password is required', 'error')
        return redirect(request.url)
    
    if not file.filename.lower().endswith('.pdf'):
        flash('Please select a PDF file', 'error')
        return redirect(request.url)
    
    try:
        # Read the uploaded PDF
        pdf_reader = PyPDF2.PdfReader(file)
        pdf_writer = PyPDF2.PdfWriter()
        
        # Copy all pages to the writer
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Encrypt the PDF with the password
        pdf_writer.encrypt(password)
        
        # Create output buffer
        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        
        # Generate filename
        original_name = secure_filename(file.filename)
        protected_name = f"protected_{original_name}"
        
        flash('PDF successfully protected with password!', 'success')
        return send_file(
            output_buffer,
            as_attachment=True,
            download_name=protected_name,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error protecting PDF: {e}")
        flash('Error protecting PDF. Please try again.', 'error')
        return redirect(request.url)

def unlock_pdf():
    """Unlock a password-protected PDF"""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    password = request.form.get('unlock_password')
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    if not password:
        flash('Password is required to unlock PDF', 'error')
        return redirect(request.url)
    
    if not file.filename.lower().endswith('.pdf'):
        flash('Please select a PDF file', 'error')
        return redirect(request.url)
    
    try:
        # Read the encrypted PDF
        pdf_reader = PyPDF2.PdfReader(file)
        
        # Check if PDF is encrypted
        if not pdf_reader.is_encrypted:
            flash('This PDF is not password protected', 'info')
            return redirect(request.url)
        
        # Try to decrypt with provided password
        if not pdf_reader.decrypt(password):
            flash('Incorrect password. Please try again.', 'error')
            return redirect(request.url)
        
        # Create new PDF writer without encryption
        pdf_writer = PyPDF2.PdfWriter()
        
        # Copy all pages to the writer
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Create output buffer
        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        
        # Generate filename
        original_name = secure_filename(file.filename)
        unlocked_name = f"unlocked_{original_name}"
        
        flash('PDF successfully unlocked!', 'success')
        return send_file(
            output_buffer,
            as_attachment=True,
            download_name=unlocked_name,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error unlocking PDF: {e}")
        flash('Error unlocking PDF. Please check the password and try again.', 'error')
        return redirect(request.url)

def generate_qr_unlock():
    """Generate QR code for PDF unlock"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['file']
    password = request.form.get('qr_password')
    
    if file.filename == '' or not password:
        return jsonify({'error': 'File and password are required'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Please select a PDF file'}), 400
    
    try:
        # Verify the PDF can be unlocked with the password
        pdf_reader = PyPDF2.PdfReader(file)
        
        if not pdf_reader.is_encrypted:
            return jsonify({'error': 'This PDF is not password protected'}), 400
        
        if not pdf_reader.decrypt(password):
            return jsonify({'error': 'Incorrect password'}), 400
        
        # Generate unique token
        token = str(uuid.uuid4())
        
        # Store file data and password temporarily (in production, use secure storage)
        file.seek(0)  # Reset file pointer
        qr_unlock_tokens[token] = {
            'filename': secure_filename(file.filename),
            'password': password,
            'pdf_data': file.read(),
            'created_at': time.time()
        }
        
        # Generate QR code with unlock URL
        unlock_url = url_for('secure_pdf.qr_unlock_pdf', token=token, _external=True)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(unlock_url)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = BytesIO()
        qr_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Save QR image temporarily
        qr_filename = f"qr_unlock_{token}.png"
        qr_path = os.path.join(current_app.config['UPLOAD_FOLDER'], qr_filename)
        
        with open(qr_path, 'wb') as f:
            f.write(img_buffer.getvalue())
        
        return jsonify({
            'success': True,
            'qr_url': url_for('file_serving.serve_file', filename=qr_filename),
            'unlock_url': unlock_url,
            'token': token,
            'expires_in': '1 hour'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating QR code: {e}")
        return jsonify({'error': 'Error generating QR code'}), 500

@secure_pdf_bp.route('/qr-unlock/<token>')
def qr_unlock_pdf(token=None):
    """Unlock PDF using QR code token"""
    if not token:
        token = request.args.get('token')
    
    if not token or token not in qr_unlock_tokens:
        flash('Invalid or expired unlock token', 'error')
        return redirect(url_for('secure_pdf.secure_pdf'))
    
    try:
        token_data = qr_unlock_tokens[token]
        
        # Check if token is expired (1 hour)
        if time.time() - token_data['created_at'] > 3600:
            del qr_unlock_tokens[token]
            flash('Unlock token has expired', 'error')
            return redirect(url_for('secure_pdf.secure_pdf'))
        
        # Create PDF reader from stored data
        pdf_data = BytesIO(token_data['pdf_data'])
        pdf_reader = PyPDF2.PdfReader(pdf_data)
        
        # Decrypt with stored password
        if not pdf_reader.decrypt(token_data['password']):
            flash('Error unlocking PDF', 'error')
            return redirect(url_for('secure_pdf.secure_pdf'))
        
        # Create unlocked PDF
        pdf_writer = PyPDF2.PdfWriter()
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Create output buffer
        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        
        # Clean up token
        del qr_unlock_tokens[token]
        
        # Generate filename
        unlocked_name = f"qr_unlocked_{token_data['filename']}"
        
        return send_file(
            output_buffer,
            as_attachment=True,
            download_name=unlocked_name,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error unlocking PDF with QR: {e}")
        flash('Error unlocking PDF', 'error')
        return redirect(url_for('secure_pdf.secure_pdf'))

@secure_pdf_bp.route('/check-pdf-security', methods=['POST'])
def check_pdf_security():
    """Check if a PDF is password protected"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Not a PDF file'}), 400
    
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        
        return jsonify({
            'is_encrypted': pdf_reader.is_encrypted,
            'page_count': len(pdf_reader.pages) if not pdf_reader.is_encrypted else None,
            'metadata': pdf_reader.metadata if not pdf_reader.is_encrypted else None
        })
        
    except Exception as e:
        current_app.logger.error(f"Error checking PDF security: {e}")
        return jsonify({'error': 'Error analyzing PDF'}), 500

# Cleanup expired tokens periodically
def cleanup_expired_tokens():
    """Remove expired QR unlock tokens"""
    current_time = time.time()
    expired_tokens = [
        token for token, data in qr_unlock_tokens.items()
        if current_time - data['created_at'] > 3600
    ]
    
    for token in expired_tokens:
        del qr_unlock_tokens[token]
    
    current_app.logger.info(f"Cleaned up {len(expired_tokens)} expired QR tokens")

# Cleanup function is available for manual use or can be scheduled separately
# In production, this should be called periodically by the background scheduler
