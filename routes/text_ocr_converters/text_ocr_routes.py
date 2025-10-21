from flask import Blueprint, request, render_template, flash, send_file, current_app, jsonify, redirect, url_for
import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
import json

text_ocr_bp = Blueprint('text_ocr', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'docx'}
SUPPORTED_LANGUAGES = {
    'auto': 'Auto-detect',
    'eng': 'English',
    'hin': 'Hindi',
    'spa': 'Spanish',
    'fra': 'French',
    'deu': 'German',
    'ara': 'Arabic',
    'chi_sim': 'Chinese (Simplified)',
    'jpn': 'Japanese',
    'kor': 'Korean',
    'rus': 'Russian'
}

EXPORT_FORMATS = {
    'txt': {'extension': '.txt', 'mime_type': 'text/plain'},
    'json': {'extension': '.json', 'mime_type': 'application/json'}
}

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_text_file(file_path):
    """Process plain text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return {
            'text': text.strip(),
            'confidence': 100,
            'language': 'English',
            'word_count': len(text.split())
        }
    except Exception as e:
        return {
            'error': f"Text processing failed: {str(e)}",
            'text': '',
            'confidence': 0,
            'language': 'Unknown',
            'word_count': 0
        }

def export_to_txt(text, output_path):
    """Export text to TXT format"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return True
    except:
        return False

def export_to_json(ocr_result, output_path):
    """Export OCR result to JSON format"""
    try:
        json_data = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'confidence': ocr_result['confidence'],
                'language': ocr_result['language'],
                'word_count': ocr_result['word_count']
            },
            'text': ocr_result['text'],
            'paragraphs': ocr_result['text'].split('\n\n')
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"JSON export failed: {str(e)}")
        return False

@text_ocr_bp.route('/text-ocr')
@text_ocr_bp.route('/text-ocr/')
def text_ocr():
    """Display the text & OCR processor page"""
    return render_template('text_ocr_converters/text_ocr.html')

@text_ocr_bp.route('/text-ocr', methods=['POST'])
@text_ocr_bp.route('/text-ocr/', methods=['POST'])
def process_ocr():
    """Handle OCR processing"""
    try:
        # Check if file was uploaded
        if 'ocr_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('text_ocr.text_ocr'))
        
        file = request.files['ocr_file']
        language = request.form.get('language', 'auto')
        output_format = request.form.get('output_format', 'txt')
        
        # Validate file
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('text_ocr.text_ocr'))
        
        if not allowed_file(file.filename):
            flash('Currently only TXT files are supported in this simplified version', 'error')
            return redirect(url_for('text_ocr.text_ocr'))
        
        if output_format not in EXPORT_FORMATS:
            flash('Invalid output format selected', 'error')
            return redirect(url_for('text_ocr.text_ocr'))
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        base_name = os.path.splitext(filename)[0]
        file_extension = os.path.splitext(filename)[1].lower()
        
        # Save uploaded file
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(upload_path)
        
        # Process file based on type
        if file_extension == '.txt':
            ocr_result = process_text_file(upload_path)
        else:
            ocr_result = {
                'error': 'This file type requires additional OCR dependencies. Currently only TXT files are supported.',
                'text': '',
                'confidence': 0,
                'language': 'Unknown',
                'word_count': 0
            }
        
        # Clean up uploaded file
        os.remove(upload_path)
        
        # Check for errors
        if 'error' in ocr_result:
            flash(ocr_result['error'], 'error')
            return redirect(url_for('text_ocr.text_ocr'))
        
        # Export to requested format
        output_extension = EXPORT_FORMATS[output_format]['extension']
        output_filename = f"{base_name}_processed_{unique_id}{output_extension}"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        
        export_success = False
        if output_format == 'txt':
            export_success = export_to_txt(ocr_result['text'], output_path)
        elif output_format == 'json':
            export_success = export_to_json(ocr_result, output_path)
        
        if not export_success:
            flash('Export failed. Please try again.', 'error')
            return redirect(url_for('text_ocr.text_ocr'))
        
        # Return success response with results
        flash(f'Text processing successful! {ocr_result["word_count"]} words processed.', 'success')
        return render_template('text_ocr_converters/text_ocr.html', 
                             ocr_result=ocr_result,
                             download_file=output_filename,
                             output_format=output_format)
        
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('text_ocr.text_ocr'))

@text_ocr_bp.route('/ocr-download/<filename>')
def download_file(filename):
    """Download processed file"""
    try:
        file_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            flash('File not found', 'error')
            return redirect(url_for('text_ocr.text_ocr'))
        
        # Determine mime type from filename
        file_extension = os.path.splitext(filename)[1].lower()
        mime_type = 'application/octet-stream'  # default
        
        for format_info in EXPORT_FORMATS.values():
            if format_info['extension'] == file_extension:
                mime_type = format_info['mime_type']
                break
        
        return send_file(file_path, 
                        as_attachment=True,
                        download_name=filename,
                        mimetype=mime_type)
        
    except Exception as e:
        flash(f'Download failed: {str(e)}', 'error')
        return redirect(url_for('text_ocr.text_ocr'))

@text_ocr_bp.route('/api/ocr', methods=['POST'])
def api_ocr():
    """API endpoint for OCR processing"""
    try:
        if 'ocr_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['ocr_file']
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Currently only TXT files are supported'}), 400
        
        # Process file
        unique_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{unique_id}_{filename}")
        file.save(upload_path)
        
        # Get file extension
        file_extension = os.path.splitext(filename)[1].lower()
        
        # Process based on file type
        if file_extension == '.txt':
            ocr_result = process_text_file(upload_path)
        else:
            ocr_result = {'error': 'Unsupported file type'}
        
        os.remove(upload_path)
        
        if 'error' in ocr_result:
            return jsonify({'error': ocr_result['error']}), 500
        
        # Return JSON response
        return jsonify({
            'success': True,
            'text': ocr_result['text'],
            'confidence': ocr_result['confidence'],
            'language': ocr_result['language'],
            'word_count': ocr_result['word_count']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500