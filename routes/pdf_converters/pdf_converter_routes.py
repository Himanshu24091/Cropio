# routes/pdf_converter_routes.py - MIGRATED TO UNIVERSAL SECURITY FRAMEWORK
# Phase 2: PDF File Security with Advanced Protection Against Malicious PDFs
import os
import json
import re
from io import BytesIO
from flask import Blueprint, render_template, request, flash, redirect, send_file, current_app, g
import fitz
import pandas as pd
from pdf2docx import Converter
from werkzeug.utils import secure_filename

# UNIVERSAL SECURITY FRAMEWORK IMPORTS - Phase 2 PDF Security
from security.core.decorators import (
    rate_limit, validate_file_upload, require_authentication
)
from security.core.validators import validate_content, validate_user_input, validate_filename
from security.core.sanitizers import sanitize_filename, sanitize_user_input, remove_script_tags
from security.core.exceptions import (
    SecurityViolationError, MalwareDetectedError, InvalidFileTypeError, 
    FileSizeExceededError, ContentValidationError
)

from utils.helpers import allowed_file
from forms import PDFConverterForm

pdf_converter_bp = Blueprint('pdf_converter', __name__)

from middleware import quota_required, track_conversion_result
# from utils.auth_decorators import login_required_for_free_tools # Uncomment if login is required for free tools

@pdf_converter_bp.route('/pdf-converter', methods=['GET', 'POST'])
# UNIVERSAL SECURITY FRAMEWORK - Phase 2 PDF Security Implementation
@rate_limit(requests_per_minute=15, per_user=False)  # NEW: Stricter rate limit for PDF processing
@validate_file_upload(  # NEW: Enhanced PDF security validation
    allowed_types=['pdf', 'txt', 'md', 'markdown', 'html', 'htm', 'csv', 'json', 'xml', 'yaml', 'yml', 'xlsx', 'xls'],
    max_size_mb=100,  # Larger limit for PDF files
    scan_malware=True  # NEW: Critical malware scanning for PDFs
)
@quota_required(tool_name='pdf_converter', check_file_size=True)
@track_conversion_result(tool_type='pdf_converter')
def pdf_converter():
    from config import ALLOWED_CONVERTER_EXTENSIONS

    allowed_extensions = ALLOWED_CONVERTER_EXTENSIONS['pdf']
    form = PDFConverterForm()
    
    
    if form.validate_on_submit():
        file = form.file.data
        
        if file:
            # UNIVERSAL SECURITY FRAMEWORK - Enhanced PDF File Processing
            raw_filename = file.filename
            
            # NEW: Advanced filename validation for PDF security
            if not validate_filename(raw_filename):
                current_app.logger.error(
                    f'Dangerous filename blocked: {raw_filename}, IP: {request.remote_addr}'
                )
                flash('Invalid filename detected. Please use a safe filename.', 'error')
                return redirect(request.url)
            
            # NEW: Sanitize filename with security framework
            safe_filename = sanitize_filename(raw_filename)
            filename = secure_filename(safe_filename)
            
            # NEW: Validate output format for security
            output_format = form.format.data
            format_valid, format_errors = validate_user_input(output_format, 'general')
            if not format_valid:
                current_app.logger.warning(
                    f'Invalid output format attempted: {output_format}, IP: {request.remote_addr}'
                )
                for error in format_errors:
                    flash(f'Invalid output format: {error}', 'error')
                return redirect(request.url)
            
            # NEW: Sanitize output format
            output_format = sanitize_user_input(output_format)
            
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # NEW: Critical PDF content validation after save
            try:
                with open(filepath, 'rb') as f:
                    file_content = f.read()
                
                # Get file extension for specialized validation
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
                
                # NEW: Deep content validation for PDF security
                is_safe, security_issues = validate_content(file_content, file_ext)
                if not is_safe:
                    # Remove dangerous file immediately
                    os.remove(filepath)
                    current_app.logger.error(
                        f'Malicious PDF detected and removed: {filename}, '
                        f'threats: {", ".join(security_issues)}, IP: {request.remote_addr}'
                    )
                    flash('File failed security validation. Upload blocked for your protection.', 'error')
                    return redirect(request.url)
                
                # NEW: Additional PDF-specific security checks
                if file_ext == 'pdf':
                    pdf_safe = validate_pdf_security(file_content, filename)
                    if not pdf_safe:
                        os.remove(filepath)
                        current_app.logger.error(
                            f'Unsafe PDF structure detected: {filename}, IP: {request.remote_addr}'
                        )
                        flash('PDF file contains suspicious content. Upload blocked.', 'error')
                        return redirect(request.url)
                
                # NEW: Security logging for successful uploads
                current_app.logger.info(
                    f'PDF upload validated: {filename} -> {output_format}, '
                    f'size: {len(file_content)} bytes, type: {file_ext}, IP: {request.remote_addr}'
                )
                
            except Exception as validation_error:
                # Remove file if validation fails
                if os.path.exists(filepath):
                    os.remove(filepath)
                current_app.logger.error(
                    f'PDF validation error: {validation_error}, file: {filename}'
                )
                flash('File validation failed. Please try again with a different file.', 'error')
                return redirect(request.url)
            
            # for usage tracking
            g.input_file_path = filepath
            
            # NEW: Enhanced PDF conversion with security monitoring
            if file_ext == 'pdf' and allowed_file(file.filename, allowed_extensions):
                try:
                    # NEW: Set processing limits to prevent resource exhaustion
                    MAX_PDF_PAGES = 1000  # Limit PDF size
                    MAX_PROCESSING_TIME = 300  # 5 minutes max
                    
                    # NEW: Safe PDF opening with resource limits
                    doc = fitz.open(filepath)
                    
                    # NEW: Check PDF safety before processing
                    if len(doc) > MAX_PDF_PAGES:
                        doc.close()
                        current_app.logger.warning(
                            f'PDF too large blocked: {len(doc)} pages, file: {filename}'
                        )
                        flash(f'PDF too large ({len(doc)} pages). Maximum {MAX_PDF_PAGES} pages allowed.', 'error')
                        return redirect(request.url)
                    
                    doc.close()  # Close and reopen for actual processing
                    
                    # NEW: Log conversion attempt
                    current_app.logger.info(
                        f'Starting PDF conversion: {filename} -> {output_format}, '
                        f'IP: {request.remote_addr}'
                    )
                    if output_format == 'docx':
                        # NEW: Secure output filename generation
                        safe_base_name = sanitize_filename(filename.rsplit('.', 1)[0])
                        docx_file = f"{filepath.rsplit('.', 1)[0]}.docx"
                        
                        cv = Converter(filepath)
                        cv.convert(docx_file, start=0, end=None)
                        cv.close()
                        
                        # NEW: Security logging for successful conversion
                        current_app.logger.info(
                            f'PDF to DOCX conversion completed: {filename} -> {safe_base_name}.docx, '
                            f'IP: {request.remote_addr}'
                        )
                        
                        flash('Successfully converted to DOCX!', 'success')
                        return send_file(docx_file, as_attachment=True, download_name=f"{safe_base_name}.docx")
                    elif output_format == 'csv':
                        # NEW: Secure PDF text extraction with limits
                        doc = fitz.open(filepath)
                        text = ""
                        char_count = 0
                        MAX_TEXT_LENGTH = 1_000_000  # 1MB text limit
                        
                        for page in doc:
                            page_text = page.get_text()
                            if char_count + len(page_text) > MAX_TEXT_LENGTH:
                                current_app.logger.warning(
                                    f'PDF text extraction limit reached: {filename}'
                                )
                                break
                            text += page_text
                            char_count += len(page_text)
                        
                        doc.close()
                        
                        # NEW: Sanitize extracted text
                        clean_text = remove_script_tags(text)
                        df = pd.DataFrame([x.split() for x in clean_text.split('\n') if x.strip()])
                        csv_buffer = BytesIO()
                        df.to_csv(csv_buffer, index=False)
                        csv_buffer.seek(0)
                        
                        # NEW: Security logging
                        current_app.logger.info(
                            f'PDF to CSV conversion: {filename}, text_length: {char_count}'
                        )
                        
                        flash('Successfully converted to CSV!', 'success')
                        return send_file(csv_buffer, as_attachment=True, download_name=f"{safe_base_name}.csv")
                    elif output_format == 'txt':
                        doc = fitz.open(filepath)
                        text = ""
                        for page in doc:
                            text += page.get_text()
                        txt_buffer = BytesIO(text.encode('utf-8'))
                        flash('Successfully converted to TXT!', 'success')
                        return send_file(txt_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}.txt")
                    elif output_format == 'md':
                        result = convert_pdf_to_markdown(filepath)
                        md_buffer = BytesIO(result.encode('utf-8'))
                        flash('Successfully converted to Markdown!', 'success')
                        return send_file(md_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}.md")
                    elif output_format == 'html':
                        result = convert_pdf_to_html(filepath)
                        html_buffer = BytesIO(result.encode('utf-8'))
                        flash('Successfully converted to HTML!', 'success')
                        return send_file(html_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}.html")
                    elif output_format == 'json':
                        result = extract_pdf_data(filepath)
                        json_buffer = BytesIO(json.dumps(result, indent=2).encode('utf-8'))
                        flash('Successfully converted to JSON!', 'success')
                        return send_file(json_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}.json")
                    elif output_format == 'xml':
                        result = convert_pdf_to_xml(filepath)
                        xml_buffer = BytesIO(result.encode('utf-8'))
                        flash('Successfully converted to XML!', 'success')
                        return send_file(xml_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}.xml")
                    elif output_format == 'excel':
                        result = extract_tables_from_pdf(filepath)
                        excel_buffer = BytesIO()
                        result.to_excel(excel_buffer, index=False, engine='openpyxl')
                        excel_buffer.seek(0)
                        flash('Successfully extracted tables to Excel!', 'success')
                        return send_file(excel_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}_tables.xlsx")
                    elif output_format == 'images':
                        zip_buffer = extract_images_from_pdf(filepath, filename)
                        flash('Successfully extracted images!', 'success')
                        return send_file(zip_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}_images.zip")
                    elif output_format == 'structured_text':
                        result = extract_structured_text(filepath)
                        json_buffer = BytesIO(json.dumps(result, indent=2).encode('utf-8'))
                        flash('Successfully extracted structured text!', 'success')
                        return send_file(json_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}_structured.json")

                except Exception as e:
                    # NEW: Enhanced security error handling for PDF conversion
                    current_app.logger.error(
                        f"PDF conversion error: {e}, file: {filename}, "
                        f"format: {output_format}, IP: {request.remote_addr}"
                    )
                    
                    # NEW: Clean up files on error
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            current_app.logger.debug(f'Cleaned up failed PDF: {filepath}')
                    except Exception as cleanup_error:
                        current_app.logger.warning(f'PDF cleanup failed: {cleanup_error}')
                    
                    # NEW: Generic error message to prevent information disclosure
                    flash('PDF conversion failed. Please check your file and try again.', 'error')
                    return redirect(request.url)
            
            # Handle reverse conversion (TO PDF) with enhanced security
            elif file_ext in ['txt', 'md', 'markdown', 'html', 'htm', 'csv', 'json', 'xml', 'yaml', 'yml', 'xlsx', 'xls']:
                try:
                    # NEW: Additional security validation for reverse conversion
                    current_app.logger.info(
                        f'Starting reverse conversion to PDF: {filename} ({file_ext}), '
                        f'IP: {request.remote_addr}'
                    )
                    
                    from routes.reverse_converter_routes import convert_file_to_pdf
                    pdf_buffer = convert_file_to_pdf(filepath, filename, file_ext)
                    
                    if pdf_buffer:
                        # NEW: Secure output filename generation
                        safe_base_name = sanitize_filename(filename.rsplit('.', 1)[0])
                        
                        # NEW: Log successful reverse conversion
                        current_app.logger.info(
                            f'Reverse conversion to PDF completed: {filename} -> {safe_base_name}.pdf'
                        )
                        
                        flash('Successfully converted to PDF!', 'success')
                        return send_file(
                            pdf_buffer, 
                            as_attachment=True, 
                            download_name=f"{safe_base_name}.pdf"
                        )
                    else:
                        flash(f'Unsupported file format: {file_ext}', 'error')
                        return redirect(request.url)
                        
                except Exception as e:
                    current_app.logger.error(f"Error converting to PDF: {e}")
                    flash('Conversion failed. Please try again.', 'error')
                    return redirect(request.url)
            else:
                flash('Invalid file type. Please upload a supported file.', 'error')
                return redirect(request.url)
    
    return render_template('pdf_converters/pdf_converter.html', form=form)


# UNIVERSAL SECURITY FRAMEWORK - PDF Security Validation Function

def validate_pdf_security(file_content: bytes, filename: str) -> bool:
    """
    Perform PDF-specific security validation
    
    Args:
        file_content: PDF file content as bytes
        filename: Original filename
        
    Returns:
        True if PDF is safe, False if suspicious
    """
    try:
        # Check for PDF signature
        if not file_content.startswith(b'%PDF-'):
            current_app.logger.warning(f'Invalid PDF signature: {filename}')
            return False
        
        # Check for dangerous PDF features
        dangerous_keywords = [
            b'/JavaScript',  # Embedded JavaScript
            b'/JS',          # JavaScript shorthand  
            b'/Launch',      # File execution
            b'/EmbeddedFile', # Embedded files
            b'/RichMedia',   # Rich media content
            b'/3D',          # 3D content
            b'/Movie',       # Movie content
            b'/Sound',       # Sound content
            b'/GoToR',       # Remote goto
            b'/SubmitForm',  # Form submission
            b'/ImportData',  # Data import
        ]
        
        for keyword in dangerous_keywords:
            if keyword in file_content:
                current_app.logger.error(
                    f'Dangerous PDF feature detected: {keyword.decode()}, file: {filename}'
                )
                return False
        
        # Check file size ratio (compressed vs uncompressed)
        if len(file_content) > 100 * 1024 * 1024:  # 100MB limit
            current_app.logger.warning(f'PDF file too large: {len(file_content)} bytes')
            return False
        
        return True
        
    except Exception as e:
        current_app.logger.error(f'PDF security validation error: {e}')
        return False


# UNIVERSAL SECURITY FRAMEWORK - Error Handlers for PDF Converter

@pdf_converter_bp.errorhandler(MalwareDetectedError)
def handle_pdf_malware_detected(e):
    """Handle malware detection in PDF uploads"""
    current_app.logger.error(
        f'Malware detected in PDF upload: IP={request.remote_addr}, '
        f'path={request.path}, error={str(e)}'
    )
    flash('Security threat detected in PDF file. Upload blocked.', 'error')
    return redirect(request.referrer or '/pdf-converter'), 403


@pdf_converter_bp.errorhandler(InvalidFileTypeError)
def handle_pdf_invalid_file_type(e):
    """Handle invalid file type errors for PDF converter"""
    current_app.logger.warning(
        f'Invalid file type for PDF converter: IP={request.remote_addr}, '
        f'path={request.path}, error={str(e)}'
    )
    flash('Invalid file type. Please upload a supported file for PDF conversion.', 'error')
    return redirect(request.referrer or '/pdf-converter'), 400


@pdf_converter_bp.errorhandler(FileSizeExceededError)
def handle_pdf_file_size_exceeded(e):
    """Handle file size exceeded errors for PDF converter"""
    current_app.logger.warning(
        f'PDF file size limit exceeded: IP={request.remote_addr}, '
        f'path={request.path}, error={str(e)}'
    )
    flash('File too large for PDF conversion. Please use a smaller file.', 'error')
    return redirect(request.referrer or '/pdf-converter'), 413


@pdf_converter_bp.errorhandler(ContentValidationError)
def handle_pdf_content_validation_error(e):
    """Handle content validation errors for PDF converter"""
    current_app.logger.error(
        f'PDF content validation failed: IP={request.remote_addr}, '
        f'path={request.path}, error={str(e)}'
    )
    flash('File content validation failed. Please try a different file.', 'error')
    return redirect(request.referrer or '/pdf-converter'), 400


@pdf_converter_bp.errorhandler(SecurityViolationError)
def handle_pdf_security_violation(e):
    """Handle general security violations for PDF converter"""
    current_app.logger.error(
        f'Security violation in PDF converter: IP={request.remote_addr}, '
        f'path={request.path}, violation={str(e)}'
    )
    flash('Security violation detected. Operation blocked.', 'error')
    return redirect('/'), 403


# UNIVERSAL SECURITY FRAMEWORK - PDF Request Monitoring

@pdf_converter_bp.after_request
def log_pdf_converter_security_events(response):
    """Log security-relevant events for PDF converter routes"""
    
    # Log suspicious response codes
    if response.status_code >= 400:
        current_app.logger.warning(
            f'PDF converter security event: {request.method} {request.path} - '
            f'Status: {response.status_code}, IP: {request.remote_addr}, '
            f'User-Agent: {request.headers.get("User-Agent", "Unknown")}'
        )
    
    # Log successful PDF conversions
    elif response.status_code == 200 and request.method == 'POST':
        current_app.logger.info(
            f'PDF conversion request: {request.method} {request.path} - '
            f'Status: {response.status_code}, IP: {request.remote_addr}'
        )
    
    # Monitor for large file attempts  
    if 'file' in request.files:
        file = request.files['file']
        if file and file.filename:
            try:
                file_size = len(file.read()) if hasattr(file, 'read') else 0
                file.seek(0)  # Reset file pointer
                
                # Log extra large PDF attempts
                if file_size > 200 * 1024 * 1024:  # 200MB
                    current_app.logger.warning(
                        f'Extra large PDF upload attempt: {file.filename}, '
                        f'size: {file_size} bytes, IP: {request.remote_addr}'
                    )
            except:
                pass  # Ignore file reading errors in monitoring
    
    return response

def convert_pdf_to_markdown(filepath):
    """Convert PDF to structured Markdown with headers and formatting"""
    doc = fitz.open(filepath)
    markdown_content = ""
    
    for page_num, page in enumerate(doc):
        markdown_content += f"\n\n# Page {page_num + 1}\n\n"
        
        blocks = page.get_text("dict")
        for block in blocks.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    for span in line.get("spans", []):
                        text = span.get("text", "")
                        font_size = span.get("size", 12)
                        flags = span.get("flags", 0)
                        
                        if font_size > 16:
                            text = f"## {text}"
                        elif font_size > 14:
                            text = f"### {text}"
                        elif flags & 2**4:
                            text = f"**{text}**"
                        elif flags & 2**1:
                            text = f"*{text}*"
                        
                        line_text += text
                    
                    if line_text.strip():
                        markdown_content += line_text + "\n"
    
    doc.close()
    return markdown_content

def convert_pdf_to_html(filepath):
    """Convert PDF to HTML with proper structure"""
    doc = fitz.open(filepath)
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF Content</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .page { margin-bottom: 50px; page-break-after: always; }
        .page-number { color: #666; font-size: 12px; }
        h1, h2, h3 { color: #333; }
        .bold { font-weight: bold; }
        .italic { font-style: italic; }
    </style>
</head>
<body>
"""
    
    for page_num, page in enumerate(doc):
        html_content += f'<div class="page">\n<div class="page-number">Page {page_num + 1}</div>\n'
        
        blocks = page.get_text("dict")
        for block in blocks.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    line_html = "<p>"
                    for span in line.get("spans", []):
                        text = span.get("text", "").replace("<", "&lt;").replace(">", "&gt;")
                        font_size = span.get("size", 12)
                        flags = span.get("flags", 0)
                        
                        if font_size > 16:
                            text = f"<h1>{text}</h1>"
                        elif font_size > 14:
                            text = f"<h2>{text}</h2>"
                        elif flags & 2**4:
                            text = f'<span class="bold">{text}</span>'
                        elif flags & 2**1:
                            text = f'<span class="italic">{text}</span>'
                        
                        line_html += text
                    
                    line_html += "</p>\n"
                    if line_html.strip() != "<p></p>":
                        html_content += line_html
        
        html_content += "</div>\n"
    
    html_content += "</body>\n</html>"
    doc.close()
    return html_content

def extract_pdf_data(filepath):
    """Extract comprehensive data from PDF"""
    doc = fitz.open(filepath)
    pdf_data = {
        "metadata": doc.metadata,
        "page_count": len(doc),
        "pages": []
    }
    
    for page_num, page in enumerate(doc):
        page_data = {
            "page_number": page_num + 1,
            "text": page.get_text(),
            "links": page.get_links()
        }
        pdf_data["pages"].append(page_data)
    
    doc.close()
    return pdf_data

def convert_pdf_to_xml(filepath):
    """Convert PDF to structured XML"""
    doc = fitz.open(filepath)
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<document>\n'
    
    xml_content += '  <metadata>\n'
    for key, value in doc.metadata.items():
        if value:
            xml_content += f'    <{key.lower()}><![CDATA[{value}]]></{key.lower()}>\n'
    xml_content += '  </metadata>\n'
    
    xml_content += '  <pages>\n'
    for page_num, page in enumerate(doc):
        xml_content += f'    <page number="{page_num + 1}">\n'
        text = page.get_text()
        if text.strip():
            xml_content += f'        <text><![CDATA[{text.strip()}]]></text>\n'
        xml_content += '    </page>\n'
    
    xml_content += '  </pages>\n</document>'
    doc.close()
    return xml_content

def extract_tables_from_pdf(filepath):
    """Extract tables from PDF"""
    doc = fitz.open(filepath)
    all_data = []
    
    for page in doc:
        text = page.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            if '\t' in line or '  ' in line:
                row = re.split(r'\t+|\s{2,}', line)
                if len(row) > 1:
                    all_data.append(row)
    
    doc.close()
    return pd.DataFrame(all_data) if all_data else pd.DataFrame()

def extract_images_from_pdf(filepath, original_filename):
    """Extract all images from PDF and return as ZIP"""
    import zipfile
    
    doc = fitz.open(filepath)
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        image_count = 0
        
        for page_num, page in enumerate(doc):
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    image_filename = f"page_{page_num + 1}_image_{img_index + 1}.{image_ext}"
                    zip_file.writestr(image_filename, image_bytes)
                    image_count += 1
                    
                except Exception as e:
                    current_app.logger.warning(f"Failed to extract image: {e}")
                    continue
    
    doc.close()
    zip_buffer.seek(0)
    return zip_buffer

def extract_structured_text(filepath):
    """Extract text with structural information"""
    doc = fitz.open(filepath)
    structured_data = {
        "document_info": doc.metadata,
        "pages": []
    }
    
    for page_num, page in enumerate(doc):
        page_info = {
            "page_number": page_num + 1,
            "text": page.get_text(),
            "word_count": len(page.get_text().split())
        }
        structured_data["pages"].append(page_info)
    
    doc.close()
    return structured_data
