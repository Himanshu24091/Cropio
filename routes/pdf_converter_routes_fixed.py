# routes/pdf_converter_routes.py
import os
import json
import re
from io import BytesIO
from flask import Blueprint, render_template, request, flash, redirect, send_file, current_app
import fitz
import pandas as pd
from pdf2docx import Converter
from werkzeug.utils import secure_filename
from utils.helpers import allowed_file

pdf_converter_bp = Blueprint('pdf_converter', __name__)

@pdf_converter_bp.route('/pdf-converter', methods=['GET', 'POST'])
def pdf_converter():
    from config import ALLOWED_CONVERTER_EXTENSIONS

    allowed_extensions = ALLOWED_CONVERTER_EXTENSIONS['pdf']
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Detect file type
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            output_format = request.form.get('format')
            
            # Check if it's a PDF file (existing functionality)
            if file_ext == 'pdf' and allowed_file(file.filename, allowed_extensions):
                try:
                    if output_format == 'docx':
                        docx_file = f"{filepath.rsplit('.', 1)[0]}.docx"
                        cv = Converter(filepath)
                        cv.convert(docx_file, start=0, end=None)
                        cv.close()
                        flash('Successfully converted to DOCX!', 'success')
                        return send_file(docx_file, as_attachment=True)
                    elif output_format == 'csv':
                        doc = fitz.open(filepath)
                        text = ""
                        for page in doc:
                            text += page.get_text()
                        df = pd.DataFrame([x.split() for x in text.split('\n') if x.strip()])
                        csv_buffer = BytesIO()
                        df.to_csv(csv_buffer, index=False)
                        csv_buffer.seek(0)
                        flash('Successfully converted to CSV!', 'success')
                        return send_file(csv_buffer, as_attachment=True, download_name=f"{filename.rsplit('.', 1)[0]}.csv")
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
                    current_app.logger.error(f"Error converting PDF: {e}")
                    flash(f"Error converting PDF. Please try again.", 'error')
                    return redirect(request.url)
            
            # Handle reverse conversion (TO PDF)
            elif file_ext in ['txt', 'md', 'markdown', 'html', 'htm', 'csv', 'json', 'xml', 'yaml', 'yml', 'xlsx', 'xls']:
                try:
                    from routes.reverse_converter_routes import convert_file_to_pdf
                    pdf_buffer = convert_file_to_pdf(filepath, filename, file_ext)
                    
                    if pdf_buffer:
                        flash('Successfully converted to PDF!', 'success')
                        return send_file(
                            pdf_buffer, 
                            as_attachment=True, 
                            download_name=f"{filename.rsplit('.', 1)[0]}.pdf"
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
    
    return render_template('pdf_converter.html')

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
