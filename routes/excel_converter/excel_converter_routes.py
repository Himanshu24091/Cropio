# routes/excel_converter/excel_converter_routes.py - EXCEL CONVERTER ROUTES
# Dedicated routes for Excel file conversion
from flask import Blueprint, request, render_template, jsonify, current_app, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import os
import shutil
import tempfile
import time
from datetime import datetime

# Universal Security Framework Imports
from security.core.decorators import (
    rate_limit, validate_file_upload, require_authentication
)
from security.core.validators import validate_content, validate_user_input, validate_filename
from security.core.sanitizers import sanitize_filename, sanitize_user_input
from security.core.exceptions import (
    SecurityViolationError, MalwareDetectedError, InvalidFileTypeError,
    FileSizeExceededError, RateLimitExceededError
)

# Core utilities
from core.file_manager import FileManager
from core.logging_config import setup_logging

# Import Excel conversion utilities
from utils.excel_converter.excel_utils import ExcelConverter

# Create Excel converter blueprint
excel_converter_bp = Blueprint('excel_converter', __name__, url_prefix='/convert/excel')

# Configuration
EXCEL_EXTENSIONS = {'xls', 'xlsx', 'xlsm'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
TEMP_CLEANUP_DELAY = 3600  # 1 hour

# Initialize logging
import logging
logger = logging.getLogger(__name__)

def allowed_file(filename, allowed_extensions):
    """Check if file has allowed extension with enhanced security"""
    if not filename or not validate_filename(filename):
        return False
    
    safe_filename = sanitize_filename(filename)
    return '.' in safe_filename and \
           safe_filename.rsplit('.', 1)[1].lower() in allowed_extensions

@excel_converter_bp.route('/', methods=['GET'])
def excel_converter():
    """Excel converter page"""
    try:
        return render_template('excel_converter/excel_converter.html')
    except Exception as e:
        logger.error(f'Error rendering excel converter page: {e}')
        return render_template('errors/500.html'), 500

@excel_converter_bp.route('/', methods=['POST'])
@rate_limit(requests_per_minute=15, per_user=False)  # Rate limit for conversions
@validate_file_upload(
    allowed_types=['xls', 'xlsx', 'xlsm'],
    max_size_mb=50,
    scan_malware=True
)
def convert_excel():
    """Handle Excel conversion requests"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Validate file extension
        if not allowed_file(file.filename, EXCEL_EXTENSIONS):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Only Excel files (.xls, .xlsx, .xlsm) are allowed.'
            }), 400

        # Enhanced security validation
        raw_filename = file.filename
        if not validate_filename(raw_filename):
            logger.warning(f'Invalid filename blocked: {raw_filename}, IP: {request.remote_addr}')
            return jsonify({
                'success': False,
                'error': 'Invalid filename. Please use a safe filename.'
            }), 400
            
        # Special handling for ODS conversions - check file size early
        output_format = request.form.get('output_format', 'csv')
        if output_format == 'ods':
            file_size = len(file.read())
            file.seek(0)  # Reset file pointer
            
            if file_size > 10 * 1024 * 1024:  # 10MB limit for ODS
                logger.warning(f'Large file attempted for ODS conversion: {file_size / (1024*1024):.1f}MB, IP: {request.remote_addr}')
                return jsonify({
                    'success': False,
                    'error': f'File too large for ODS conversion ({file_size / (1024*1024):.1f}MB). Please use a file smaller than 10MB or try a different format like CSV or JSON.'
                }), 400

        # Sanitize filename
        safe_filename = sanitize_filename(raw_filename)
        filename = secure_filename(safe_filename)

        # Create temporary directory for this conversion
        temp_dir = tempfile.mkdtemp(prefix='excel_converter_')
        temp_input = os.path.join(temp_dir, f'input_{filename}')

        try:
            # Save uploaded file
            file.save(temp_input)

            # Deep file content validation
            with open(temp_input, 'rb') as f:
                file_content = f.read()
            
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
            is_safe, security_issues = validate_content(file_content, file_ext)
            
            if not is_safe:
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.error(f'Malicious file detected: {filename}, issues: {", ".join(security_issues)}, IP: {request.remote_addr}')
                return jsonify({
                    'success': False,
                    'error': 'File failed security validation.'
                }), 400

            # Special validation for CSV format - only allow single sheet
            if output_format == 'csv':
                selected_sheets = request.form.get('selected_sheets', 'first')
                manual_sheets = request.form.get('manual_sheets', '').strip()
                
                # Check if multiple sheets are being requested for CSV
                if selected_sheets == 'all':
                    logger.warning(f'All sheets selection attempted for CSV format, IP: {request.remote_addr}')
                    return jsonify({
                        'success': False,
                        'error': 'CSV format only supports single sheet conversion. Please select "Convert first sheet only" or use a different format like JSON for multiple sheets.'
                    }), 400
                elif selected_sheets == 'manual':
                    # Validate manual sheet selection for CSV
                    if not manual_sheets:
                        logger.warning(f'Empty manual sheet selection for CSV format, IP: {request.remote_addr}')
                        return jsonify({
                            'success': False,
                            'error': 'Please enter a sheet number for manual selection or choose a different option.'
                        }), 400
                    
                    # Parse manual sheets to check for multiple selection
                    if ',' in manual_sheets or '-' in manual_sheets:
                        logger.warning(f'Multiple sheet selection attempted for CSV format: {manual_sheets}, IP: {request.remote_addr}')
                        return jsonify({
                            'success': False,
                            'error': 'CSV format only supports single sheet conversion. Please enter only one sheet number (e.g., "1" or "3") or use a different format like JSON for multiple sheets.'
                        }), 400
                    
                    # Additional validation: check if the manual input is a single valid number
                    import re
                    if not re.match(r'^\d+$', manual_sheets.strip()):
                        logger.warning(f'Invalid manual sheet format for CSV: {manual_sheets}, IP: {request.remote_addr}')
                        return jsonify({
                            'success': False,
                            'error': 'CSV format only supports single sheet number. Please enter one sheet number (e.g., "1" or "3").'
                        }), 400
                    
                    # If we reach here, manual_sheets is a valid single number
                    logger.info(f'Valid manual sheet selection for CSV: {manual_sheets}, IP: {request.remote_addr}')

            # Process conversion
            result = convert_excel_internal(temp_input, temp_dir, request.form)

            if result['success']:
                # Log successful conversion
                logger.info(f'Successful excel conversion: {filename}, IP: {request.remote_addr}')
                
                # Send file and schedule cleanup
                def remove_temp_files():
                    time.sleep(TEMP_CLEANUP_DELAY)
                    shutil.rmtree(temp_dir, ignore_errors=True)
                
                # Note: In production, use a proper task queue like Celery for cleanup
                import threading
                cleanup_thread = threading.Thread(target=remove_temp_files)
                cleanup_thread.daemon = True
                cleanup_thread.start()
                
                return send_file(
                    result['output_path'],
                    as_attachment=True,
                    download_name=result['filename'],
                    mimetype=result['mimetype']
                )
            else:
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                # Provide user-friendly error messages for common issues
                error_msg = result.get('error', 'Conversion failed')
                
                # Handle ODS timeout specifically
                if 'timed out' in error_msg.lower() and output_format == 'ods':
                    user_error = 'Request timed out. Please try again with a smaller file or use CSV/JSON format for large files.'
                elif 'too large' in error_msg.lower():
                    user_error = 'File too large for conversion. Please use a smaller file.'
                elif output_format == 'ods' and 'conversion failed' in error_msg.lower():
                    user_error = 'ODS conversion failed. Please try CSV or JSON format instead.'
                else:
                    user_error = error_msg
                
                return jsonify({
                    'success': False,
                    'error': user_error
                }), 500

        except Exception as processing_error:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error(f'Conversion processing error: {processing_error}, file: {filename}')
            return jsonify({
                'success': False,
                'error': 'File processing failed. Please try again.'
            }), 500

    except SecurityViolationError as sve:
        logger.warning(f'Security violation in excel conversion: {sve}, IP: {request.remote_addr}')
        return jsonify({
            'success': False,
            'error': 'Security validation failed'
        }), 400
    except RateLimitExceededError:
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded. Please wait before trying again.'
        }), 429
    except Exception as e:
        logger.error(f'General excel conversion error: {e}, IP: {request.remote_addr}')
        return jsonify({
            'success': False,
            'error': 'Conversion request failed. Please check your request and try again.'
        }), 500

def convert_excel_internal(input_path, temp_dir, form_data):
    """Convert Excel file internally"""
    try:
        # Debug logging of form data
        logger.info(f"Form data received: {dict(form_data)}")
        
        # Get conversion parameters
        output_format = form_data.get('output_format', 'csv')
        preserve_formatting = form_data.get('preserve_formatting') == 'on'
        include_headers = form_data.get('include_headers') == 'on'
        convert_formulas = form_data.get('convert_formulas') == 'on'
        preserve_dates = form_data.get('preserve_dates') == 'on'
        selected_sheets = form_data.get('selected_sheets', 'all')
        
        # Handle manual sheet selection
        if selected_sheets == 'manual':
            manual_sheets = form_data.get('manual_sheets', '').strip()
            if manual_sheets:
                selected_sheets = manual_sheets
            else:
                selected_sheets = 'all'  # Fallback
        
        # Format-specific options
        csv_delimiter = form_data.get('csv_delimiter', ',')
        csv_encoding = form_data.get('csv_encoding', 'utf-8')
        tsv_encoding = form_data.get('tsv_encoding', 'utf-8')
        pdf_page_size = form_data.get('pdf_page_size', 'A4')
        pdf_orientation = form_data.get('pdf_orientation', 'portrait')

        # Enhanced debug logging
        logger.info(f"Raw form data received: {dict(form_data)}")
        logger.info(f"Parsed parameters - Format: '{output_format}', Headers: {include_headers}, Formulas: {convert_formulas}, Dates: {preserve_dates}, Sheets: {selected_sheets}")
        
        # Validate parameters
        if output_format not in ['csv', 'tsv', 'json', 'html', 'txt', 'xml', 'ods', 'pdf']:
            logger.warning(f"Invalid output format '{output_format}', defaulting to CSV")
            output_format = 'csv'

        # Initialize converter
        converter = ExcelConverter()
        
        # Check if the requested format is available
        format_availability = {
            'csv': converter.is_csv_conversion_available(),
            'tsv': converter.is_tsv_conversion_available(),
            'json': converter.is_json_conversion_available(), 
            'html': converter.is_html_conversion_available(),
            'txt': converter.is_txt_conversion_available(),
            'xml': converter.is_xml_conversion_available(),
            'ods': converter.is_ods_conversion_available(),
            'pdf': converter.is_pdf_conversion_available()
        }
        
        if not format_availability[output_format]:
            logger.error(f"{output_format.upper()} conversion not available - dependencies missing")
            return {
                'success': False,
                'error': f'{output_format.upper()} conversion is not available due to missing dependencies'
            }
        
        # Set output path
        base_name = os.path.splitext(os.path.basename(input_path))[0]

        # Set appropriate file extension based on format
        # Note: CSV format now only supports single sheet conversion
        extensions = {
            'csv': '.csv',
            'tsv': '.tsv',
            'json': '.json',
            'html': '.html',
            'txt': '.txt',
            'xml': '.xml',
            'ods': '.ods',
            'pdf': '.pdf'
        }
        
        output_filename = f"{base_name}_converted{extensions[output_format]}"
        output_path = os.path.join(temp_dir, output_filename)

        # Prepare conversion options
        conversion_options = {
            'preserve_formatting': preserve_formatting,
            'include_headers': include_headers,
            'convert_formulas': convert_formulas,
            'preserve_dates': preserve_dates,
            'selected_sheets': selected_sheets,
            'csv_delimiter': csv_delimiter,
            'csv_encoding': csv_encoding,
            'tsv_encoding': tsv_encoding,
            'pdf_page_size': pdf_page_size,
            'pdf_orientation': pdf_orientation
        }

        # Perform conversion based on output format
        success = False
        
        if output_format == 'csv':
            # Filter out format-specific options for CSV conversion
            csv_specific_params = {
                'preserve_formatting', 'include_headers', 'convert_formulas', 
                'preserve_dates', 'selected_sheets', 'csv_delimiter', 'csv_encoding'
            }
            csv_options = {k: v for k, v in conversion_options.items() if k in csv_specific_params}
            success = converter.excel_to_csv(
                input_path=input_path,
                output_path=output_path,
                **csv_options
            )
        elif output_format == 'tsv':
            # Filter out format-specific options for TSV conversion
            tsv_specific_params = {
                'preserve_formatting', 'include_headers', 'convert_formulas', 
                'preserve_dates', 'selected_sheets', 'tsv_encoding'
            }
            tsv_options = {k: v for k, v in conversion_options.items() if k in tsv_specific_params}
            success = converter.excel_to_tsv(
                input_path=input_path,
                output_path=output_path,
                **tsv_options
            )
        elif output_format == 'json':
            # Filter out format-specific options for JSON conversion
            json_specific_params = {
                'preserve_formatting', 'include_headers', 'convert_formulas', 
                'preserve_dates', 'selected_sheets'
            }
            json_options = {k: v for k, v in conversion_options.items() if k in json_specific_params}
            success = converter.excel_to_json(
                input_path=input_path,
                output_path=output_path,
                **json_options
            )
        elif output_format == 'html':
            # Filter out format-specific options for HTML conversion
            html_specific_params = {
                'preserve_formatting', 'include_headers', 'convert_formulas', 
                'preserve_dates', 'selected_sheets'
            }
            html_options = {k: v for k, v in conversion_options.items() if k in html_specific_params}
            success = converter.excel_to_html(
                input_path=input_path,
                output_path=output_path,
                **html_options
            )
        elif output_format == 'txt':
            # Filter out format-specific options for TXT conversion
            txt_specific_params = {
                'preserve_formatting', 'include_headers', 'convert_formulas', 
                'preserve_dates', 'selected_sheets'
            }
            txt_options = {k: v for k, v in conversion_options.items() if k in txt_specific_params}
            success = converter.excel_to_txt(
                input_path=input_path,
                output_path=output_path,
                **txt_options
            )
        elif output_format == 'xml':
            # Filter out format-specific options for XML conversion
            xml_specific_params = {
                'preserve_formatting', 'include_headers', 'convert_formulas', 
                'preserve_dates', 'selected_sheets'
            }
            xml_options = {k: v for k, v in conversion_options.items() if k in xml_specific_params}
            success = converter.excel_to_xml(
                input_path=input_path,
                output_path=output_path,
                **xml_options
            )
        elif output_format == 'ods':
            # Filter out format-specific options for ODS conversion
            ods_specific_params = {
                'preserve_formatting', 'include_headers', 'convert_formulas', 
                'preserve_dates', 'selected_sheets'
            }
            ods_options = {k: v for k, v in conversion_options.items() if k in ods_specific_params}
            success = converter.excel_to_ods(
                input_path=input_path,
                output_path=output_path,
                **ods_options
            )
        elif output_format == 'pdf':
            # Filter out format-specific options for PDF conversion
            pdf_specific_params = {
                'preserve_formatting', 'include_headers', 'convert_formulas', 
                'preserve_dates', 'selected_sheets', 'pdf_page_size', 'pdf_orientation'
            }
            pdf_options = {k: v for k, v in conversion_options.items() if k in pdf_specific_params}
            success = converter.excel_to_pdf(
                input_path=input_path,
                output_path=output_path,
                **pdf_options
            )

        if success and os.path.exists(output_path):
            # Determine MIME type based on format
            # Note: For JSON downloads, use 'application/octet-stream' to avoid conflict 
            # with error responses that use 'application/json'
            mime_types = {
                'csv': 'text/csv',  # CSV now only supports single sheet
                'tsv': 'text/tab-separated-values',
                'json': 'application/octet-stream',  # file download
                'html': 'text/html',
                'txt': 'text/plain',
                'xml': 'application/xml',
                'ods': 'application/vnd.oasis.opendocument.spreadsheet',
                'pdf': 'application/pdf'
            }
            
            file_size = os.path.getsize(output_path)
            logger.info(f"Conversion successful: {output_format.upper()} file created, size: {file_size} bytes")
            
            return {
                'success': True,
                'output_path': output_path,
                'filename': output_filename,
                'mimetype': mime_types.get(output_format, 'application/octet-stream')
            }
        else:
            # Enhanced error reporting
            error_details = []
            
            if not success:
                error_details.append('Conversion method returned False')
            
            if not os.path.exists(output_path):
                error_details.append('Output file was not created')
            else:
                file_size = os.path.getsize(output_path)
                error_details.append(f'Output file exists but is {file_size} bytes')
            
            logger.error(f"Excel to {output_format.upper()} conversion failed: {'; '.join(error_details)}")
            
            return {
                'success': False,
                'error': f'Excel to {output_format.upper()} conversion failed: {", ".join(error_details)}'
            }

    except Exception as e:
        logger.error(f'Excel conversion error: {e}')
        return {
            'success': False,
            'error': f'Conversion error: {str(e)}'
        }

@excel_converter_bp.route('/analyze', methods=['POST'])
@rate_limit(requests_per_minute=20, per_user=False)
@validate_file_upload(
    allowed_types=['xls', 'xlsx', 'xlsm'],
    max_size_mb=50,
    scan_malware=True
)
def analyze_excel():
    """Analyze Excel file to get sheet information"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Validate file extension
        if not allowed_file(file.filename, EXCEL_EXTENSIONS):
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Only Excel files (.xls, .xlsx, .xlsm) are allowed.'
            }), 400

        # Create temporary directory for analysis
        temp_dir = tempfile.mkdtemp(prefix='excel_analysis_')
        temp_input = os.path.join(temp_dir, f'analysis_{secure_filename(file.filename)}')

        try:
            # Save uploaded file
            file.save(temp_input)

            # Initialize converter and analyze
            converter = ExcelConverter()
            analysis_result = converter.analyze_excel_file(temp_input)

            # Clean up temp file
            shutil.rmtree(temp_dir, ignore_errors=True)

            if analysis_result['success']:
                return jsonify(analysis_result)
            else:
                return jsonify({
                    'success': False,
                    'error': analysis_result.get('error', 'Analysis failed')
                }), 500

        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error(f'Excel analysis error: {e}')
            return jsonify({
                'success': False,
                'error': 'File analysis failed'
            }), 500

    except Exception as e:
        logger.error(f'Excel analysis request error: {e}')
        return jsonify({
            'success': False,
            'error': 'Analysis request failed'
        }), 500

@excel_converter_bp.route('/status', methods=['GET'])
def conversion_status():
    """Check conversion status and system health"""
    try:
        converter = ExcelConverter()
        status = {
            'service': 'online',
            'timestamp': datetime.now().isoformat(),
            'features': {
                'excel_to_csv': converter.is_csv_conversion_available(),
                'excel_to_tsv': converter.is_tsv_conversion_available(),
                'excel_to_json': converter.is_json_conversion_available(),
                'excel_to_html': converter.is_html_conversion_available(),
                'excel_to_txt': converter.is_txt_conversion_available(),
                'excel_to_xml': converter.is_xml_conversion_available(),
                'excel_to_ods': converter.is_ods_conversion_available(),
                'excel_to_pdf': converter.is_pdf_conversion_available()
            },
            'limits': {
                'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
                'supported_formats': {
                    'input': list(EXCEL_EXTENSIONS),
                    'output': ['csv', 'tsv', 'json', 'html', 'txt', 'xml', 'ods', 'pdf']
                }
            }
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f'Status check error: {e}')
        return jsonify({
            'service': 'error',
            'error': 'Status check failed'
        }), 500

@excel_converter_bp.route('/formats', methods=['GET'])
def supported_formats():
    """Get list of supported input and output formats"""
    try:
        return jsonify({
            'input_formats': {
                'xls': {
                    'name': 'Excel 97-2003 Workbook',
                    'description': 'Legacy Excel format for older versions',
                    'mime_type': 'application/vnd.ms-excel'
                },
                'xlsx': {
                    'name': 'Excel Workbook',
                    'description': 'Modern Excel format with enhanced features',
                    'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                },
                'xlsm': {
                    'name': 'Excel Macro-Enabled Workbook',
                    'description': 'Excel format with macro support',
                    'mime_type': 'application/vnd.ms-excel.sheet.macroEnabled.12'
                }
            },
            'output_formats': {
                'csv': {
                    'name': 'CSV (Comma-Separated Values)',
                    'description': 'Plain text format for tabular data',
                    'mime_type': 'text/csv'
                },
                'tsv': {
                    'name': 'TSV (Tab-Separated Values)',
                    'description': 'Plain text format using tabs as delimiters',
                    'mime_type': 'text/tab-separated-values'
                },
                'json': {
                    'name': 'JSON',
                    'description': 'Structured data format for APIs and web applications',
                    'mime_type': 'application/json'
                },
                'html': {
                    'name': 'HTML Table',
                    'description': 'Web-ready table format for display',
                    'mime_type': 'text/html'
                },
                'txt': {
                    'name': 'Plain Text',
                    'description': 'Simple text representation of data',
                    'mime_type': 'text/plain'
                },
                'xml': {
                    'name': 'XML',
                    'description': 'Hierarchical markup format for data exchange',
                    'mime_type': 'application/xml'
                },
                'ods': {
                    'name': 'ODS (OpenDocument Spreadsheet)',
                    'description': 'Open standard spreadsheet format',
                    'mime_type': 'application/vnd.oasis.opendocument.spreadsheet'
                },
                'pdf': {
                    'name': 'PDF (Portable Document Format)',
                    'description': 'Professional document format for sharing',
                    'mime_type': 'application/pdf'
                }
            }
        })
    except Exception as e:
        logger.error(f'Formats endpoint error: {e}')
        return jsonify({
            'error': 'Failed to retrieve format information'
        }), 500

@excel_converter_bp.errorhandler(413)
def file_too_large(e):
    """Handle file size exceeded errors"""
    return jsonify({
        'success': False,
        'error': f'File size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit'
    }), 413

@excel_converter_bp.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@excel_converter_bp.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f'Internal server error in excel converter: {e}')
    return render_template('errors/500.html'), 500