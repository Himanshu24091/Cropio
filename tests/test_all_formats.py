#!/usr/bin/env python3
"""
Comprehensive test script for notebook converter formats
Tests actual conversion with sample notebook for all formats
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.notebook_converter.notebook_utils import NotebookConverter

def test_all_formats_with_sample():
    """Test all conversion formats with the sample notebook"""
    print("🧪 Testing All Notebook Conversion Formats")
    print("=" * 60)
    
    # Use the sample notebook we created
    sample_notebook = "sample_notebook.ipynb"
    if not os.path.exists(sample_notebook):
        print(f"❌ Sample notebook not found: {sample_notebook}")
        return False
    
    print(f"📓 Using sample notebook: {sample_notebook}")
    
    # Initialize converter
    try:
        converter = NotebookConverter()
        print("✅ NotebookConverter initialized")
    except Exception as e:
        print(f"❌ Failed to initialize converter: {e}")
        return False
    
    # Test all formats
    formats_to_test = ['html', 'pdf', 'docx', 'markdown']
    results = {}
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")
        
        for format_name in formats_to_test:
            print(f"\n🔄 Testing {format_name.upper()} conversion...")
            
            # Check availability first
            availability_map = {
                'html': converter.is_html_conversion_available(),
                'pdf': converter.is_pdf_conversion_available(),
                'docx': converter.is_docx_conversion_available(),
                'markdown': converter.is_markdown_conversion_available()
            }
            
            if not availability_map[format_name]:
                print(f"⚠️  {format_name.upper()} conversion not available - dependencies missing")
                results[format_name] = {'success': False, 'error': 'Dependencies missing'}
                continue
            
            # Prepare output file
            extensions = {'html': '.html', 'pdf': '.pdf', 'docx': '.docx', 'markdown': '.md'}
            output_filename = f"sample_converted_{format_name}{extensions[format_name]}"
            output_path = os.path.join(temp_dir, output_filename)
            
            try:
                # Perform conversion
                if format_name == 'html':
                    success = converter.notebook_to_html(sample_notebook, output_path)
                elif format_name == 'pdf':
                    success = converter.notebook_to_pdf(sample_notebook, output_path)
                elif format_name == 'docx':
                    success = converter.notebook_to_docx(sample_notebook, output_path)
                elif format_name == 'markdown':
                    success = converter.notebook_to_markdown(sample_notebook, output_path)
                
                if success and os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"✅ {format_name.upper()} conversion successful!")
                    print(f"   📄 File: {output_filename}")
                    print(f"   📊 Size: {file_size:,} bytes")
                    
                    # Copy to outputs directory for inspection
                    outputs_dir = "outputs"
                    if not os.path.exists(outputs_dir):
                        os.makedirs(outputs_dir)
                    
                    final_path = os.path.join(outputs_dir, output_filename)
                    shutil.copy2(output_path, final_path)
                    print(f"   📋 Copied to: {final_path}")
                    
                    results[format_name] = {
                        'success': True, 
                        'file_size': file_size, 
                        'output_path': final_path
                    }
                else:
                    print(f"❌ {format_name.upper()} conversion failed")
                    results[format_name] = {'success': False, 'error': 'Conversion failed'}
                    
            except Exception as e:
                print(f"❌ {format_name.upper()} conversion error: {e}")
                results[format_name] = {'success': False, 'error': str(e)}
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 CONVERSION SUMMARY")
    print(f"{'='*60}")
    
    successful_formats = []
    failed_formats = []
    
    for format_name, result in results.items():
        if result['success']:
            successful_formats.append(format_name)
            size_info = f" ({result['file_size']:,} bytes)" if 'file_size' in result else ""
            print(f"✅ {format_name.upper():<10} - SUCCESS{size_info}")
        else:
            failed_formats.append(format_name)
            error_info = f" - {result['error']}" if 'error' in result else ""
            print(f"❌ {format_name.upper():<10} - FAILED{error_info}")
    
    print(f"\n📈 Results: {len(successful_formats)}/{len(formats_to_test)} formats working")
    
    if successful_formats:
        print(f"✅ Working: {', '.join(successful_formats).upper()}")
    
    if failed_formats:
        print(f"❌ Failed: {', '.join(failed_formats).upper()}")
        return False
    
    return len(failed_formats) == 0

def test_mime_types():
    """Test MIME type handling"""
    print(f"\n{'='*60}")
    print("🔍 TESTING MIME TYPES")
    print(f"{'='*60}")
    
    from routes.notebook_converter.notebook_converter_routes import convert_notebook_internal
    
    # Mock form data for each format
    formats = {
        'html': {'output_format': 'html'},
        'pdf': {'output_format': 'pdf'},
        'docx': {'output_format': 'docx'},
        'markdown': {'output_format': 'markdown'}
    }
    
    expected_mimes = {
        'html': 'text/html',
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'markdown': 'text/markdown'
    }
    
    sample_notebook = "sample_notebook.ipynb"
    if not os.path.exists(sample_notebook):
        print(f"❌ Sample notebook not found: {sample_notebook}")
        return False
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for format_name, form_data in formats.items():
            print(f"\n📋 Testing {format_name.upper()} MIME type...")
            
            # Mock form data object
            class MockFormData:
                def __init__(self, data):
                    self.data = data
                
                def get(self, key, default=None):
                    return self.data.get(key, default)
            
            mock_form = MockFormData(form_data)
            
            try:
                result = convert_notebook_internal(sample_notebook, temp_dir, mock_form)
                
                if result['success']:
                    returned_mime = result.get('mimetype', 'NOT SET')
                    expected_mime = expected_mimes[format_name]
                    
                    if returned_mime == expected_mime:
                        print(f"✅ {format_name.upper()} MIME type correct: {returned_mime}")
                    else:
                        print(f"❌ {format_name.upper()} MIME type wrong:")
                        print(f"   Expected: {expected_mime}")
                        print(f"   Got:      {returned_mime}")
                else:
                    print(f"❌ {format_name.upper()} conversion failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ {format_name.upper()} MIME test error: {e}")

if __name__ == "__main__":
    print("🚀 Starting comprehensive notebook converter test...")
    
    # Test all formats
    all_formats_work = test_all_formats_with_sample()
    
    # Test MIME types
    test_mime_types()
    
    print(f"\n{'='*60}")
    if all_formats_work:
        print("🎉 ALL TESTS PASSED! All formats are working correctly.")
        print("📝 Check the 'outputs' directory to inspect the converted files.")
    else:
        print("⚠️  Some formats failed. Check the logs above for details.")
    print(f"{'='*60}")