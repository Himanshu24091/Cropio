# routes/pdf_editor_routes.py
"""
Professional PDF Editor Routes
Enhanced with advanced security, comprehensive features, and robust error handling
"""

import os
import uuid
import json
import base64
import tempfile
import shutil
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

from flask import Blueprint, render_template, request, jsonify, send_file, current_app, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import fitz  # PyMuPDF for advanced PDF operations
from PIL import Image

# Security and utilities
from utils.security import csrf
from middleware.usage_tracker import track_conversion, check_file_size_limit
from forms import PDFEditorForm
from core.logging_config import cropio_logger

# Create Blueprint
pdf_editor_bp = Blueprint('pdf_editor', __name__)

# Configuration Constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_PAGES = 500  # Maximum pages per PDF
ALLOWED_EXTENSIONS = {'pdf'}
UPLOAD_FOLDER = 'temp/pdf_editor'
SESSION_TIMEOUT = 3600  # 1 hour

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('temp/pdf_editor/processed', exist_ok=True)

# Security Functions
def validate_session():
    """Validate user session and rate limiting"""
    if 'pdf_editor_session' not in session:
        session['pdf_editor_session'] = {
            'id': str(uuid.uuid4()),
            'created_at': datetime.now().isoformat(),
            'operations_count': 0,
            'last_activity': datetime.now().isoformat()
        }
    
    # Check session timeout
    last_activity = datetime.fromisoformat(session['pdf_editor_session']['last_activity'])
    if datetime.now() - last_activity > timedelta(seconds=SESSION_TIMEOUT):
        session.pop('pdf_editor_session', None)
        return False
    
    # Update last activity
    session['pdf_editor_session']['last_activity'] = datetime.now().isoformat()
    
    # Rate limiting - max 100 operations per session
    if session['pdf_editor_session']['operations_count'] > 100:
        return False
    
    return True

def increment_operation_count():
    """Increment operation count for rate limiting"""
    if 'pdf_editor_session' in session:
        session['pdf_editor_session']['operations_count'] += 1
        session.permanent = True

def allowed_file(filename):
    """Enhanced file validation with security checks"""
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return False
    
    # Additional security: check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    return True

def sanitize_filename(filename):
    """Sanitize filename for security"""
    if not filename:
        return f"document_{uuid.uuid4().hex[:8]}.pdf"
    
    # Remove path components and invalid characters
    filename = os.path.basename(filename)
    filename = "".join(c for c in filename if c.isalnum() or c in '._- ')
    
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    
    return filename[:100]  # Limit length

# PDF Processing Functions
def get_pdf_metadata(file_path):
    """Extract comprehensive PDF metadata with security checks"""
    try:
        doc = fitz.open(file_path)
        
        # Security check: ensure PDF is not corrupted or malicious
        if doc.page_count == 0:
            doc.close()
            return None
        
        if doc.page_count > MAX_PAGES:
            doc.close()
            return {'error': f'PDF too large. Maximum {MAX_PAGES} pages allowed.'}
        
        metadata = {
            'pages': doc.page_count,
            'title': doc.metadata.get('title', '').strip()[:200],
            'author': doc.metadata.get('author', '').strip()[:100],
            'subject': doc.metadata.get('subject', '').strip()[:200],
            'creator': doc.metadata.get('creator', '').strip()[:100],
            'producer': doc.metadata.get('producer', '').strip()[:100],
            'creation_date': doc.metadata.get('creationDate', ''),
            'modification_date': doc.metadata.get('modDate', ''),
            'encrypted': doc.is_encrypted,
            'file_size': os.path.getsize(file_path),
            'page_sizes': []
        }
        
        # Get page dimensions for first few pages
        for i in range(min(5, doc.page_count)):
            page = doc[i]
            rect = page.rect
            metadata['page_sizes'].append({
                'width': int(rect.width),
                'height': int(rect.height)
            })
        
        doc.close()
        return metadata
        
    except Exception as e:
        cropio_logger.error(f"Error extracting PDF metadata: {str(e)}")
        return None

def extract_pdf_text(file_path, page_num=None, max_chars=10000):
    """Extract text from PDF with limits for security"""
    try:
        doc = fitz.open(file_path)
        text_content = []
        total_chars = 0
        
        start_page = page_num if page_num is not None else 0
        end_page = (page_num + 1) if page_num is not None else doc.page_count
        
        for i in range(start_page, min(end_page, doc.page_count)):
            if total_chars >= max_chars:
                break
                
            page = doc[i]
            page_text = page.get_text()
            
            # Limit text length for security
            if total_chars + len(page_text) > max_chars:
                page_text = page_text[:max_chars - total_chars]
            
            text_content.append({
                'page': i + 1,
                'text': page_text,
                'char_count': len(page_text)
            })
            
            total_chars += len(page_text)
        
        doc.close()
        return text_content
        
    except Exception as e:
        cropio_logger.error(f"Error extracting PDF text: {str(e)}")
        return []

def apply_pdf_modifications(file_path, annotations_data, page_operations, session_id):
    """Apply page operations (deletion, rotation) and annotations to PDF with enhanced security and validation"""
    try:
        # Open source document in read-only mode first to prevent corruption
        source_doc = fitz.open(file_path)
        
        # Create output filename
        output_filename = f"edited_{session_id}_{uuid.uuid4().hex[:8]}.pdf"
        output_path = os.path.join(UPLOAD_FOLDER, 'processed', output_filename)
        
        # Create a new document to ensure clean structure
        output_doc = fitz.open()  # Create new empty document
        
        cropio_logger.info(f"Processing PDF with {source_doc.page_count} pages, {len(page_operations)} page operations")
        
        # Step 1: Apply page operations (deletions) to determine which pages to include
        pages_to_include = list(range(source_doc.page_count))  # 0-based page indices
        deleted_pages = set()
        
        # Process page deletions
        for operation in page_operations:
            if operation.get('type') == 'delete':
                page_index = operation.get('pageIndex')  # Should be 0-based from frontend
                if page_index is not None and 0 <= page_index < source_doc.page_count:
                    deleted_pages.add(page_index)
                    cropio_logger.info(f"Marking page {page_index + 1} for deletion")
        
        # Remove deleted pages from inclusion list
        pages_to_include = [i for i in pages_to_include if i not in deleted_pages]
        cropio_logger.info(f"Pages to include after deletions: {len(pages_to_include)} pages")
        
        if not pages_to_include:
            source_doc.close()
            raise ValueError("Cannot delete all pages - at least one page must remain")
        
        # Step 2: Copy remaining pages to output document
        page_mapping = {}  # old_page_index -> new_page_index
        new_page_index = 0
        
        for old_page_index in pages_to_include:
            # Copy the page from source to output
            output_doc.insert_pdf(source_doc, from_page=old_page_index, to_page=old_page_index)
            page_mapping[old_page_index] = new_page_index
            cropio_logger.info(f"Copied page {old_page_index + 1} -> new page {new_page_index + 1}")
            new_page_index += 1
        
        # Step 3: Apply annotations to the appropriate pages in the output document
        annotation_count = 0
        max_annotations = 1000  # Security limit
        
        for page_num_str, annotations in annotations_data.items():
            # Convert 1-based page number from frontend to 0-based index
            original_page_index = int(page_num_str) - 1
            
            # Check if this page still exists after deletions
            if original_page_index in page_mapping:
                new_page_index = page_mapping[original_page_index]
                output_page = output_doc[new_page_index]
                output_page_rect = output_page.rect
                
                cropio_logger.info(f"Applying annotations to page {original_page_index + 1} (now page {new_page_index + 1})")
                
                for annotation in annotations:
                    if annotation_count >= max_annotations:
                        cropio_logger.warning(f"Reached maximum annotation limit of {max_annotations}")
                        break
                    
                    # Validate annotation data
                    if not isinstance(annotation, dict) or 'type' not in annotation:
                        cropio_logger.warning("Invalid annotation data structure")
                        continue
                    
                    annotation_type = annotation.get('type')
                    
                    try:
                        if annotation_type == 'text':
                            text = str(annotation.get('text', ''))[:500]  # Limit text length
                            x = max(0, min(float(annotation.get('x', 0)), output_page_rect.width))
                            y = max(0, min(float(annotation.get('y', 0)), output_page_rect.height))
                            font_size = max(8, min(int(annotation.get('fontSize', 16)), 72))
                            color = validate_color(annotation.get('color', '#000000'))
                            
                            if text.strip():  # Only add non-empty text
                                output_page.insert_text(
                                    (x, y), text,
                                    fontsize=font_size,
                                    color=hex_to_rgb(color)
                                )
                                annotation_count += 1
                            
                        elif annotation_type in ['draw', 'pen', 'highlighter']:
                            path = annotation.get('path', [])
                            if len(path) > 1 and len(path) <= 10000:  # Limit path complexity
                                color = validate_color(annotation.get('color', '#FF0000'))
                                
                                # Get stroke width from annotation or use defaults
                                if annotation_type == 'highlighter':
                                    line_width = max(int(annotation.get('strokeWidth', 20)), 15)
                                else:
                                    line_width = max(1, min(int(annotation.get('strokeWidth', 3)), 20))
                                
                                # Draw path as connected lines
                                for i in range(1, len(path)):
                                    p1 = path[i-1]
                                    p2 = path[i]
                                    
                                    x1 = max(0, min(float(p1.get('x', 0)), output_page_rect.width))
                                    y1 = max(0, min(float(p1.get('y', 0)), output_page_rect.height))
                                    x2 = max(0, min(float(p2.get('x', 0)), output_page_rect.width))
                                    y2 = max(0, min(float(p2.get('y', 0)), output_page_rect.height))
                                    
                                    output_page.draw_line((x1, y1), (x2, y2),
                                                         color=hex_to_rgb(color), width=line_width)
                                
                                annotation_count += 1
                        
                        elif annotation_type == 'rectangle':
                            x = max(0, min(float(annotation.get('x', 0)), output_page_rect.width))
                            y = max(0, min(float(annotation.get('y', 0)), output_page_rect.height))
                            width = max(1, min(float(annotation.get('width', 100)), output_page_rect.width - x))
                            height = max(1, min(float(annotation.get('height', 50)), output_page_rect.height - y))
                            color = validate_color(annotation.get('color', '#0000FF'))
                            line_width = max(1, min(int(annotation.get('lineWidth', 2)), 20))
                            
                            rect = fitz.Rect(x, y, x + width, y + height)
                            output_page.draw_rect(rect, color=hex_to_rgb(color), width=line_width)
                            annotation_count += 1
                        
                        elif annotation_type == 'circle':
                            center_x = max(0, min(float(annotation.get('centerX', annotation.get('x', 0))), output_page_rect.width))
                            center_y = max(0, min(float(annotation.get('centerY', annotation.get('y', 0))), output_page_rect.height))
                            radius = max(5, min(float(annotation.get('radius', 50)), min(output_page_rect.width, output_page_rect.height) / 2))
                            color = validate_color(annotation.get('color', '#00FF00'))
                            line_width = max(1, min(int(annotation.get('lineWidth', 2)), 20))
                            
                            output_page.draw_circle((center_x, center_y), radius, color=hex_to_rgb(color), width=line_width)
                            annotation_count += 1
                        
                    except (ValueError, KeyError, TypeError) as e:
                        cropio_logger.warning(f"Error processing individual annotation: {str(e)}")
                        continue
            else:
                cropio_logger.info(f"Page {original_page_index + 1} was deleted, skipping annotations")
        
        # Close source document
        source_doc.close()
        
        # Save output document
        final_page_count = output_doc.page_count
        output_doc.save(output_path, garbage=0, deflate=False, clean=False, pretty=False, incremental=False)
        output_doc.close()
        
        cropio_logger.info(f"Successfully applied {len(page_operations)} page operations and {annotation_count} annotations. Final PDF has {final_page_count} pages")
        
        # Verify the output file was created correctly
        if os.path.exists(output_path):
            verify_doc = fitz.open(output_path)
            actual_pages = verify_doc.page_count
            verify_doc.close()
            
            cropio_logger.info(f"Output PDF verification: {actual_pages} pages")
            
            if actual_pages == 0:
                cropio_logger.error("Output PDF is empty - save operation failed")
                return None
                
            return output_path
        else:
            cropio_logger.error("Output file was not created")
            return None
        
    except Exception as e:
        cropio_logger.error(f"Error applying PDF modifications: {str(e)}", exc_info=True)
        return None

def apply_annotations(file_path, annotations_data, session_id):
    """Apply annotations to PDF with enhanced security and validation - FIXED VERSION"""
    try:
        # Open source document in read-only mode first to prevent corruption
        source_doc = fitz.open(file_path)
        
        # Create output filename
        output_filename = f"annotated_{session_id}_{uuid.uuid4().hex[:8]}.pdf"
        output_path = os.path.join(UPLOAD_FOLDER, 'processed', output_filename)
        
        # Create a new document to ensure clean structure
        output_doc = fitz.open()  # Create new empty document
        
        annotation_count = 0
        max_annotations = 1000  # Security limit
        
        cropio_logger.info(f"Processing PDF with {source_doc.page_count} pages")
        
        # Process each page in the source document
        for page_idx in range(source_doc.page_count):
            # Copy the entire page from source to output
            output_doc.insert_pdf(source_doc, from_page=page_idx, to_page=page_idx)
            
            # Get the copied page for annotation
            output_page = output_doc[page_idx]
            output_page_rect = output_page.rect
            
            # Check if this page has annotations (convert to 1-based for lookup)
            page_num_str = str(page_idx + 1)
            
            if page_num_str in annotations_data:
                cropio_logger.info(f"Applying annotations to page {page_idx + 1}")
                annotations = annotations_data[page_num_str]
                
                for annotation in annotations:
                    if annotation_count >= max_annotations:
                        cropio_logger.warning(f"Reached maximum annotation limit of {max_annotations}")
                        break
                    
                    # Validate annotation data
                    if not isinstance(annotation, dict) or 'type' not in annotation:
                        cropio_logger.warning("Invalid annotation data structure")
                        continue
                    
                    annotation_type = annotation.get('type')
                    cropio_logger.info(f"Processing annotation type: {annotation_type}")
                    
                    try:
                        if annotation_type == 'text':
                            text = str(annotation.get('text', ''))[:500]  # Limit text length
                            x = max(0, min(float(annotation.get('x', 0)), output_page_rect.width))
                            y = max(0, min(float(annotation.get('y', 0)), output_page_rect.height))
                            font_size = max(8, min(int(annotation.get('fontSize', 16)), 72))
                            color = validate_color(annotation.get('color', '#000000'))
                            
                            if text.strip():  # Only add non-empty text
                                output_page.insert_text(
                                    (x, y), text,
                                    fontsize=font_size,
                                    color=hex_to_rgb(color)
                                )
                                annotation_count += 1
                                cropio_logger.info(f"Applied text annotation: '{text}' at ({x}, {y}) with font size {font_size}")
                            
                        elif annotation_type in ['draw', 'pen', 'highlighter']:
                            path = annotation.get('path', [])
                            if len(path) > 1 and len(path) <= 10000:  # Limit path complexity
                                color = validate_color(annotation.get('color', '#FF0000'))
                                
                                # Get stroke width from annotation or use defaults
                                if annotation_type == 'highlighter':
                                    line_width = max(int(annotation.get('strokeWidth', 20)), 15)  # Use strokeWidth from frontend
                                else:
                                    line_width = max(1, min(int(annotation.get('strokeWidth', 3)), 20))  # Use strokeWidth from frontend
                                
                                # Draw path as connected lines
                                for i in range(1, len(path)):
                                    p1 = path[i-1]
                                    p2 = path[i]
                                    
                                    x1 = max(0, min(float(p1.get('x', 0)), output_page_rect.width))
                                    y1 = max(0, min(float(p1.get('y', 0)), output_page_rect.height))
                                    x2 = max(0, min(float(p2.get('x', 0)), output_page_rect.width))
                                    y2 = max(0, min(float(p2.get('y', 0)), output_page_rect.height))
                                    
                                    output_page.draw_line((x1, y1), (x2, y2),
                                                         color=hex_to_rgb(color), width=line_width)
                                
                                annotation_count += 1
                                cropio_logger.info(f"Applied {annotation_type} annotation with {len(path)} points")
                        
                        elif annotation_type == 'rectangle':
                            x = max(0, min(float(annotation.get('x', 0)), output_page_rect.width))
                            y = max(0, min(float(annotation.get('y', 0)), output_page_rect.height))
                            width = max(1, min(float(annotation.get('width', 100)), output_page_rect.width - x))
                            height = max(1, min(float(annotation.get('height', 50)), output_page_rect.height - y))
                            color = validate_color(annotation.get('color', '#0000FF'))
                            line_width = max(1, min(int(annotation.get('lineWidth', 2)), 20))
                            
                            rect = fitz.Rect(x, y, x + width, y + height)
                            output_page.draw_rect(rect, color=hex_to_rgb(color), width=line_width)
                            annotation_count += 1
                        
                        elif annotation_type == 'circle':
                            center_x = max(0, min(float(annotation.get('centerX', annotation.get('x', 0))), output_page_rect.width))
                            center_y = max(0, min(float(annotation.get('centerY', annotation.get('y', 0))), output_page_rect.height))
                            radius = max(5, min(float(annotation.get('radius', 50)), min(output_page_rect.width, output_page_rect.height) / 2))
                            color = validate_color(annotation.get('color', '#00FF00'))
                            line_width = max(1, min(int(annotation.get('lineWidth', 2)), 20))
                            
                            output_page.draw_circle((center_x, center_y), radius, color=hex_to_rgb(color), width=line_width)
                            annotation_count += 1
                        
                        else:
                            cropio_logger.warning(f"Unsupported annotation type: {annotation_type}")
                    
                    except (ValueError, KeyError, TypeError) as e:
                        cropio_logger.warning(f"Error processing individual annotation: {str(e)}")
                        continue
            
            else:
                cropio_logger.info(f"No annotations for page {page_idx + 1}")
        
        # Close source document
        source_doc.close()
        
        # Save output document with minimal processing to prevent corruption
        # Use incremental=False and garbage=0 to prevent page duplication issues
        final_page_count = output_doc.page_count
        output_doc.save(output_path, garbage=0, deflate=False, clean=False, pretty=False, incremental=False)
        output_doc.close()
        
        cropio_logger.info(f"Successfully applied {annotation_count} annotations to PDF with {final_page_count} pages")
        
        # Verify the output file was created correctly
        if os.path.exists(output_path):
            # Quick verification: check if page count is correct
            verify_doc = fitz.open(output_path)
            actual_pages = verify_doc.page_count
            verify_doc.close()
            
            cropio_logger.info(f"Output PDF verification: {actual_pages} pages")
            
            if actual_pages == 0:
                cropio_logger.error("Output PDF is empty - save operation failed")
                return None
                
            return output_path
        else:
            cropio_logger.error("Output file was not created")
            return None
        
    except Exception as e:
        cropio_logger.error(f"Error applying annotations: {str(e)}", exc_info=True)
        return None

def validate_color(color_str):
    """Validate and sanitize color values"""
    if not isinstance(color_str, str):
        return '#000000'
    
    # Remove any non-hex characters
    color_str = ''.join(c for c in color_str if c in '0123456789ABCDEFabcdef#')
    
    if not color_str.startswith('#'):
        color_str = '#' + color_str
    
    if len(color_str) == 7:
        return color_str
    
    return '#000000'

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple for PyMuPDF"""
    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            return (0, 0, 0)
        return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))
    except (ValueError, TypeError):
        return (0, 0, 0)

# Routes
@pdf_editor_bp.route('/pdf-editor')
def pdf_editor_page():
    """Main PDF Editor page with security validation"""
    if not validate_session():
        session.clear()
        return render_template('pdf_converters/pdf_editor.html', error="Session expired. Please refresh.")
    
    form = PDFEditorForm()
    return render_template('pdf_converters/pdf_editor.html', form=form)

@pdf_editor_bp.route('/pdf-editor/upload', methods=['POST'])
@csrf.exempt
@track_conversion('pdf_edit', 'pdf_editor')
def upload_pdf():
    """Enhanced PDF upload with comprehensive security"""
    try:
        # Session validation
        if not validate_session():
            return jsonify({'error': 'Session expired', 'code': 'SESSION_EXPIRED'}), 401
        
        increment_operation_count()
        
        # File validation
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided', 'code': 'NO_FILE'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected', 'code': 'EMPTY_FILENAME'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PDF files allowed.', 'code': 'INVALID_TYPE'}), 400
        
        # File size validation
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'error': f'File too large. Maximum size: {MAX_FILE_SIZE//1024//1024}MB',
                'code': 'FILE_TOO_LARGE'
            }), 413
        
        if file_size < 100:  # Minimum valid PDF size
            return jsonify({'error': 'Invalid PDF file', 'code': 'INVALID_PDF'}), 400
        
        # Generate secure filename
        original_filename = sanitize_filename(file.filename)
        session_id = session['pdf_editor_session']['id']
        unique_filename = f"{session_id}_{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file securely
        file.save(file_path)
        
        # Validate PDF and extract metadata
        pdf_metadata = get_pdf_metadata(file_path)
        if not pdf_metadata:
            os.remove(file_path)
            return jsonify({'error': 'Invalid or corrupted PDF file', 'code': 'CORRUPTED_PDF'}), 400
        
        if 'error' in pdf_metadata:
            os.remove(file_path)
            return jsonify({'error': pdf_metadata['error'], 'code': 'PDF_TOO_LARGE'}), 413
        
        # Store file info in session
        file_id = uuid.uuid4().hex
        session[f'pdf_file_{file_id}'] = {
            'filename': unique_filename,
            'original_name': original_filename,
            'upload_time': datetime.now().isoformat(),
            'file_size': file_size
        }
        
        cropio_logger.info(f"PDF uploaded successfully: {original_filename}, {file_size} bytes")
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'filename': original_filename,
            'metadata': pdf_metadata,
            'upload_time': datetime.now().isoformat()
        })
        
    except Exception as e:
        cropio_logger.error(f"PDF upload error: {str(e)}")
        return jsonify({'error': 'Upload failed due to server error', 'code': 'SERVER_ERROR'}), 500

@pdf_editor_bp.route('/pdf-editor/process', methods=['POST'])
@csrf.exempt
@track_conversion('pdf_edit', 'pdf_editor')
def process_pdf():
    """Process PDF with annotations and enhanced security"""
    try:
        # Session and data validation
        if not validate_session():
            return jsonify({'error': 'Session expired', 'code': 'SESSION_EXPIRED'}), 401
        
        increment_operation_count()
        
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid request data', 'code': 'INVALID_DATA'}), 400
        
        file_id = data.get('file_id')
        annotations = data.get('annotations', {})
        page_operations = data.get('page_operations', [])
        operation = data.get('operation', 'annotate')
        
        if not file_id or f'pdf_file_{file_id}' not in session:
            return jsonify({'error': 'File not found or session expired', 'code': 'FILE_NOT_FOUND'}), 404
        
        # Get file info and validate
        file_info = session[f'pdf_file_{file_id}']
        file_path = os.path.join(UPLOAD_FOLDER, file_info['filename'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File no longer available', 'code': 'FILE_MISSING'}), 404
        
        # Validate annotations data
        if not isinstance(annotations, dict) or len(annotations) > 500:  # Max 500 pages
            return jsonify({'error': 'Invalid annotations data', 'code': 'INVALID_ANNOTATIONS'}), 400
        
        # Validate page operations data
        if not isinstance(page_operations, list) or len(page_operations) > 1000:  # Max 1000 operations
            return jsonify({'error': 'Invalid page operations data', 'code': 'INVALID_PAGE_OPERATIONS'}), 400
        
        cropio_logger.info(f"Processing PDF with {len(annotations)} annotated pages and {len(page_operations)} page operations")
        
        # Process based on operation type
        if operation == 'annotate':
            if not annotations and not page_operations:
                # No annotations or page operations - return original file info
                return jsonify({
                    'success': True,
                    'download_type': 'original',
                    'download_url': f'/pdf-editor/download/{file_id}/original',
                    'filename': file_info['original_name']
                })
            
            # Apply page operations and annotations
            session_id = session['pdf_editor_session']['id']
            output_path = apply_pdf_modifications(file_path, annotations, page_operations, session_id)
            
            if not output_path:
                return jsonify({'error': 'Failed to process annotations', 'code': 'PROCESSING_ERROR'}), 500
            
            # Store processed file info
            processed_filename = os.path.basename(output_path)
            session[f'processed_{file_id}'] = {
                'filename': processed_filename,
                'original_file_id': file_id,
                'created_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'download_type': 'annotated',
                'download_url': f'/pdf-editor/download/{file_id}/processed',
                'filename': f"edited_{file_info['original_name']}",
                'annotation_count': sum(len(anns) for anns in annotations.values()),
                'page_operations_count': len(page_operations)
            })
        
        else:
            return jsonify({'error': 'Unsupported operation', 'code': 'UNSUPPORTED_OPERATION'}), 400
            
    except Exception as e:
        cropio_logger.error(f"PDF processing error: {str(e)}")
        return jsonify({'error': 'Processing failed due to server error', 'code': 'SERVER_ERROR'}), 500

@pdf_editor_bp.route('/pdf-editor/download/<file_id>/<download_type>')
def download_pdf(file_id, download_type):
    """Secure PDF download with session validation"""
    try:
        # Session validation
        if not validate_session():
            return jsonify({'error': 'Session expired'}), 401
        
        if f'pdf_file_{file_id}' not in session:
            return jsonify({'error': 'File not found'}), 404
        
        file_info = session[f'pdf_file_{file_id}']
        
        if download_type == 'original':
            # Download original file
            file_path = os.path.join(UPLOAD_FOLDER, file_info['filename'])
            download_name = file_info['original_name']
            
        elif download_type == 'processed':
            # Download processed file
            if f'processed_{file_id}' not in session:
                return jsonify({'error': 'Processed file not found'}), 404
            
            processed_info = session[f'processed_{file_id}']
            file_path = os.path.join(UPLOAD_FOLDER, 'processed', processed_info['filename'])
            download_name = f"edited_{file_info['original_name']}"
            
        else:
            return jsonify({'error': 'Invalid download type'}), 400
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not available'}), 404
        
        increment_operation_count()
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        cropio_logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Download failed'}), 500

@pdf_editor_bp.route('/pdf-editor/extract-text', methods=['POST'])
@csrf.exempt
def extract_text():
    """Extract text from PDF with security limits"""
    try:
        if not validate_session():
            return jsonify({'error': 'Session expired'}), 401
        
        increment_operation_count()
        
        data = request.get_json()
        file_id = data.get('file_id')
        page_num = data.get('page_num')  # Optional: specific page
        
        if not file_id or f'pdf_file_{file_id}' not in session:
            return jsonify({'error': 'File not found'}), 404
        
        file_info = session[f'pdf_file_{file_id}']
        file_path = os.path.join(UPLOAD_FOLDER, file_info['filename'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not available'}), 404
        
        text_content = extract_pdf_text(file_path, page_num)
        
        return jsonify({
            'success': True,
            'text': text_content,
            'total_pages': len(text_content)
        })
        
    except Exception as e:
        cropio_logger.error(f"Text extraction error: {str(e)}")
        return jsonify({'error': 'Text extraction failed'}), 500

@pdf_editor_bp.route('/pdf-editor/info', methods=['POST'])
@csrf.exempt
def get_pdf_info():
    """Get detailed PDF information"""
    try:
        if not validate_session():
            return jsonify({'error': 'Session expired'}), 401
        
        data = request.get_json()
        file_id = data.get('file_id')
        
        if not file_id or f'pdf_file_{file_id}' not in session:
            return jsonify({'error': 'File not found'}), 404
        
        file_info = session[f'pdf_file_{file_id}']
        file_path = os.path.join(UPLOAD_FOLDER, file_info['filename'])
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not available'}), 404
        
        metadata = get_pdf_metadata(file_path)
        if not metadata:
            return jsonify({'error': 'Failed to get PDF information'}), 500
        
        return jsonify({
            'success': True,
            'info': metadata
        })
        
    except Exception as e:
        cropio_logger.error(f"PDF info error: {str(e)}")
        return jsonify({'error': 'Failed to get PDF information'}), 500

@pdf_editor_bp.route('/pdf-editor/cleanup', methods=['POST'])
@csrf.exempt
def cleanup_files():
    """Manual cleanup of user's temporary files"""
    try:
        if not validate_session():
            return jsonify({'error': 'Session expired'}), 401
        
        session_id = session['pdf_editor_session']['id']
        cleanup_count = 0
        
        # Remove files from session
        keys_to_remove = []
        for key in session.keys():
            if key.startswith('pdf_file_') or key.startswith('processed_'):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            session.pop(key, None)
            cleanup_count += 1
        
        # Clean up actual files (files older than 1 hour)
        current_time = datetime.now()
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.startswith(session_id):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                try:
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if current_time - file_time > timedelta(hours=1):
                        os.remove(file_path)
                        cleanup_count += 1
                except Exception:
                    pass
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {cleanup_count} items'
        })
        
    except Exception as e:
        cropio_logger.error(f"Cleanup error: {str(e)}")
        return jsonify({'error': 'Cleanup failed'}), 500

# Error handlers specific to PDF editor
@pdf_editor_bp.errorhandler(413)
def file_too_large(error):
    return jsonify({
        'error': f'File too large. Maximum size: {MAX_FILE_SIZE//1024//1024}MB',
        'code': 'FILE_TOO_LARGE'
    }), 413

@pdf_editor_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'Bad request',
        'code': 'BAD_REQUEST'
    }), 400
