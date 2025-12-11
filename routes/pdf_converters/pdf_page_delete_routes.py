# routes/pdf_page_delete_routes.py
import os
import json
from io import BytesIO
from flask import Blueprint, render_template, request, jsonify, send_file, current_app, flash, redirect
import fitz  # PyMuPDF
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file

pdf_page_delete_bp = Blueprint('pdf_page_delete', __name__)

@pdf_page_delete_bp.route('/pdf-page-delete')
def pdf_page_delete_page():
    """Renders the PDF page deletion interface"""
    return render_template('pdf_converters/pdf_page_delete.html')

@pdf_page_delete_bp.route('/upload-pdf-for-deletion', methods=['POST'])
def upload_pdf_for_deletion():
    """Upload PDF and return page information for deletion interface"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename, {'pdf'}):
            return jsonify({'error': 'Please upload a valid PDF file'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Open PDF and get page information
        doc = fitz.open(filepath)
        pages_info = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Generate thumbnail for each page
            pix = page.get_pixmap(matrix=fitz.Matrix(0.3, 0.3))  # Small thumbnail
            thumbnail_filename = f"thumb_{filename}_{page_num}.png"
            thumbnail_path = os.path.join(current_app.config['UPLOAD_FOLDER'], thumbnail_filename)
            pix.save(thumbnail_path)
            
            # Get basic page info
            page_info = {
                'page_number': page_num + 1,
                'thumbnail_url': f'/preview/{thumbnail_filename}',
                'page_size': f"{int(page.rect.width)} x {int(page.rect.height)}",
                'rotation': page.rotation
            }
            pages_info.append(page_info)

        doc.close()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'total_pages': len(pages_info),
            'pages': pages_info
        })

    except Exception as e:
        current_app.logger.error(f"Error uploading PDF for deletion: {e}")
        return jsonify({'error': 'Failed to process PDF file'}), 500

@pdf_page_delete_bp.route('/delete-pdf-pages', methods=['POST'])
def delete_pdf_pages():
    """Delete selected pages from PDF"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        pages_to_delete = data.get('pages_to_delete', [])
        operation_type = data.get('operation_type', 'delete')  # 'delete' or 'keep'
        
        if not filename or not pages_to_delete:
            return jsonify({'error': 'Missing filename or pages to delete'}), 400

        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'PDF file not found'}), 404

        # Open the PDF
        doc = fitz.open(filepath)
        total_pages = len(doc)
        
        # Convert page numbers to 0-based index
        pages_indices = [int(p) - 1 for p in pages_to_delete]
        
        if operation_type == 'delete':
            # Delete specified pages (in reverse order to maintain indices)
            for page_index in sorted(pages_indices, reverse=True):
                if 0 <= page_index < total_pages:
                    doc.delete_page(page_index)
        else:  # operation_type == 'keep'
            # Keep only specified pages
            pages_to_keep = [i for i in range(total_pages) if (i + 1) in [int(p) for p in pages_to_delete]]
            # Delete all other pages (in reverse order)
            for page_index in reversed(range(total_pages)):
                if page_index not in pages_to_keep:
                    doc.delete_page(page_index)

        # Check if any pages remain
        if len(doc) == 0:
            doc.close()
            return jsonify({'error': 'Cannot create an empty PDF. At least one page must remain.'}), 400

        # Save the modified PDF
        output_buffer = BytesIO()
        doc.save(output_buffer)
        doc.close()
        
        output_buffer.seek(0)
        
        # Generate output filename
        base_name = filename.rsplit('.', 1)[0]
        output_filename = f"{base_name}_pages_{operation_type}d.pdf"
        
        return send_file(
            output_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=output_filename
        )

    except Exception as e:
        current_app.logger.error(f"Error deleting PDF pages: {e}")
        return jsonify({'error': 'Failed to process page deletion'}), 500

@pdf_page_delete_bp.route('/get-pdf-info/<filename>')
def get_pdf_info(filename):
    """Get detailed information about PDF pages"""
    try:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'PDF file not found'}), 404

        doc = fitz.open(filepath)
        pages_info = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get page statistics
            text_length = len(page.get_text())
            image_count = len(page.get_images())
            
            page_info = {
                'page_number': page_num + 1,
                'size': f"{int(page.rect.width)} x {int(page.rect.height)}",
                'rotation': page.rotation,
                'text_length': text_length,
                'image_count': image_count,
                'has_content': text_length > 0 or image_count > 0
            }
            pages_info.append(page_info)

        doc.close()
        
        return jsonify({
            'success': True,
            'total_pages': len(pages_info),
            'pages': pages_info
        })

    except Exception as e:
        current_app.logger.error(f"Error getting PDF info: {e}")
        return jsonify({'error': 'Failed to get PDF information'}), 500

@pdf_page_delete_bp.route('/batch-delete-pages', methods=['POST'])
def batch_delete_pages():
    """Batch delete pages from multiple PDFs"""
    try:
        files = request.files.getlist('files[]')
        delete_pattern = request.form.get('delete_pattern', 'custom')
        custom_pages = request.form.get('custom_pages', '')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400

        results = []
        processed_files = []
        
        for file in files:
            if not allowed_file(file.filename, {'pdf'}):
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': 'Invalid file type'
                })
                continue

            try:
                # Save uploaded file
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # Open PDF
                doc = fitz.open(filepath)
                total_pages = len(doc)
                
                # Determine pages to delete based on pattern
                pages_to_delete = []
                
                if delete_pattern == 'first':
                    pages_to_delete = [0] if total_pages > 1 else []
                elif delete_pattern == 'last':
                    pages_to_delete = [total_pages - 1] if total_pages > 1 else []
                elif delete_pattern == 'even':
                    pages_to_delete = [i for i in range(1, total_pages, 2)]
                elif delete_pattern == 'odd':
                    pages_to_delete = [i for i in range(0, total_pages, 2)]
                elif delete_pattern == 'custom' and custom_pages:
                    # Parse custom page ranges (e.g., "1,3,5-7")
                    pages_to_delete = parse_page_ranges(custom_pages, total_pages)

                # Delete pages if any specified and at least one page remains
                if pages_to_delete and len(pages_to_delete) < total_pages:
                    for page_index in sorted(pages_to_delete, reverse=True):
                        if 0 <= page_index < total_pages:
                            doc.delete_page(page_index)
                    
                    # Save modified PDF
                    output_filename = f"batch_deleted_{filename}"
                    output_path = os.path.join(current_app.config['COMPRESSED_FOLDER'], output_filename)
                    doc.save(output_path)
                    
                    processed_files.append({
                        'filename': output_filename,
                        'original_name': filename,
                        'path': output_path
                    })
                    
                    results.append({
                        'filename': filename,
                        'success': True,
                        'pages_deleted': len(pages_to_delete),
                        'pages_remaining': len(doc),
                        'download_url': f'/download/{output_filename}'
                    })
                else:
                    results.append({
                        'filename': filename,
                        'success': False,
                        'error': 'No valid pages to delete or would result in empty PDF'
                    })

                doc.close()

            except Exception as e:
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'results': results,
            'processed_count': len([r for r in results if r['success']])
        })

    except Exception as e:
        current_app.logger.error(f"Error in batch delete: {e}")
        return jsonify({'error': 'Failed to process batch deletion'}), 500

def parse_page_ranges(page_string, total_pages):
    """Parse page ranges like '1,3,5-7,10' into list of page indices (0-based)"""
    pages = []
    parts = page_string.replace(' ', '').split(',')
    
    for part in parts:
        if '-' in part:
            # Handle range like "5-7"
            try:
                start, end = map(int, part.split('-'))
                for i in range(max(1, start), min(total_pages + 1, end + 1)):
                    pages.append(i - 1)  # Convert to 0-based
            except ValueError:
                continue
        else:
            # Handle single page like "3"
            try:
                page = int(part)
                if 1 <= page <= total_pages:
                    pages.append(page - 1)  # Convert to 0-based
            except ValueError:
                continue
    
    return list(set(pages))  # Remove duplicates
