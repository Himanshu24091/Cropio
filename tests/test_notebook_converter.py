#!/usr/bin/env python3
"""
Test script for Notebook Converter functionality
This script tests all dependencies and conversion methods
"""
import os
import sys
import json
import tempfile
from pathlib import Path

# Add the project root to path
sys.path.insert(0, os.path.dirname(__file__))

def test_dependencies():
    """Test all required dependencies"""
    print("=== Testing Dependencies ===")
    
    dependencies = {
        'nbconvert': False,
        'nbformat': False,
        'docx': False,
        'bs4': False,
        'weasyprint': False,
        'pandoc': False
    }
    
    # Test nbconvert
    try:
        import nbconvert
        from nbconvert import HTMLExporter, MarkdownExporter, PDFExporter
        dependencies['nbconvert'] = True
        print("✅ nbconvert: Available")
        print(f"   Version: {nbconvert.__version__}")
    except ImportError as e:
        print(f"❌ nbconvert: {e}")
    
    # Test nbformat
    try:
        import nbformat
        dependencies['nbformat'] = True
        print("✅ nbformat: Available")
        print(f"   Version: {nbformat.__version__}")
    except ImportError as e:
        print(f"❌ nbformat: {e}")
    
    # Test python-docx
    try:
        from docx import Document
        dependencies['docx'] = True
        print("✅ python-docx: Available")
    except ImportError as e:
        print(f"❌ python-docx: {e}")
    
    # Test BeautifulSoup4
    try:
        from bs4 import BeautifulSoup
        dependencies['bs4'] = True
        print("✅ BeautifulSoup4: Available")
    except ImportError as e:
        print(f"❌ BeautifulSoup4: {e}")
    
    # Test weasyprint
    try:
        import weasyprint
        dependencies['weasyprint'] = True
        print("✅ weasyprint: Available")
    except (ImportError, OSError) as e:
        print(f"❌ weasyprint: {e}")
    
    # Test pandoc
    try:
        import pandoc
        dependencies['pandoc'] = True
        print("✅ pandoc: Available")
    except ImportError as e:
        print(f"❌ pandoc: {e}")
    
    return dependencies

def create_test_notebook():
    """Create a simple test notebook"""
    import nbformat
    
    # Create a simple notebook
    nb = nbformat.v4.new_notebook()
    
    # Add markdown cell
    markdown_cell = nbformat.v4.new_markdown_cell(
        source="# Test Notebook\n\nThis is a test notebook for conversion testing.\n\n## Section 1\n\nSome **bold** text and *italic* text."
    )
    nb.cells.append(markdown_cell)
    
    # Add code cell
    code_cell = nbformat.v4.new_code_cell(
        source="print('Hello, World!')\nx = 42\nprint(f'The answer is {x}')"
    )
    # Add output to code cell
    code_cell.outputs = [
        nbformat.v4.new_output(
            output_type='stream',
            name='stdout',
            text='Hello, World!\nThe answer is 42\n'
        )
    ]
    nb.cells.append(code_cell)
    
    # Add another markdown cell
    markdown_cell2 = nbformat.v4.new_markdown_cell(
        source="## Section 2\n\nThis section contains some mathematical expressions:\n\n$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$"
    )
    nb.cells.append(markdown_cell2)
    
    return nb

def test_notebook_converter():
    """Test the NotebookConverter class"""
    print("\n=== Testing NotebookConverter ===")
    
    try:
        from utils.notebook_converter.notebook_utils import NotebookConverter
        
        converter = NotebookConverter()
        print("✅ NotebookConverter imported successfully")
        
        # Check availability of different formats
        formats = {
            'PDF': converter.is_pdf_conversion_available(),
            'HTML': converter.is_html_conversion_available(),
            'DOCX': converter.is_docx_conversion_available(),
            'Markdown': converter.is_markdown_conversion_available()
        }
        
        print("\nFormat availability:")
        for format_name, available in formats.items():
            status = "✅" if available else "❌"
            print(f"   {status} {format_name}: {'Available' if available else 'Not Available'}")
        
        return converter, formats
        
    except ImportError as e:
        print(f"❌ Failed to import NotebookConverter: {e}")
        return None, {}

def test_conversions():
    """Test actual conversions"""
    print("\n=== Testing Conversions ===")
    
    # Import dependencies
    try:
        import nbformat
    except ImportError:
        print("❌ nbformat not available for testing")
        return
    
    converter, formats = test_notebook_converter()
    if not converter:
        return
    
    # Create test notebook
    test_nb = create_test_notebook()
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save test notebook
        input_path = os.path.join(temp_dir, "test_notebook.ipynb")
        with open(input_path, 'w', encoding='utf-8') as f:
            nbformat.write(test_nb, f)
        
        print(f"Created test notebook: {input_path}")
        
        # Test each conversion format
        test_results = {}
        
        if formats.get('HTML', False):
            html_path = os.path.join(temp_dir, "test_output.html")
            try:
                success = converter.notebook_to_html(input_path, html_path)
                test_results['HTML'] = success and os.path.exists(html_path)
                if test_results['HTML']:
                    print("✅ HTML conversion: Success")
                    print(f"   Output file size: {os.path.getsize(html_path)} bytes")
                else:
                    print("❌ HTML conversion: Failed")
            except Exception as e:
                print(f"❌ HTML conversion error: {e}")
                test_results['HTML'] = False
        
        if formats.get('Markdown', False):
            md_path = os.path.join(temp_dir, "test_output.md")
            try:
                success = converter.notebook_to_markdown(input_path, md_path)
                test_results['Markdown'] = success and os.path.exists(md_path)
                if test_results['Markdown']:
                    print("✅ Markdown conversion: Success")
                    print(f"   Output file size: {os.path.getsize(md_path)} bytes")
                else:
                    print("❌ Markdown conversion: Failed")
            except Exception as e:
                print(f"❌ Markdown conversion error: {e}")
                test_results['Markdown'] = False
        
        if formats.get('DOCX', False):
            docx_path = os.path.join(temp_dir, "test_output.docx")
            try:
                success = converter.notebook_to_docx(input_path, docx_path)
                test_results['DOCX'] = success and os.path.exists(docx_path)
                if test_results['DOCX']:
                    print("✅ DOCX conversion: Success")
                    print(f"   Output file size: {os.path.getsize(docx_path)} bytes")
                else:
                    print("❌ DOCX conversion: Failed")
            except Exception as e:
                print(f"❌ DOCX conversion error: {e}")
                test_results['DOCX'] = False
        
        if formats.get('PDF', False):
            pdf_path = os.path.join(temp_dir, "test_output.pdf")
            try:
                success = converter.notebook_to_pdf(input_path, pdf_path)
                test_results['PDF'] = success and os.path.exists(pdf_path)
                if test_results['PDF']:
                    print("✅ PDF conversion: Success")
                    print(f"   Output file size: {os.path.getsize(pdf_path)} bytes")
                else:
                    print("❌ PDF conversion: Failed")
            except Exception as e:
                print(f"❌ PDF conversion error: {e}")
                test_results['PDF'] = False
        
        return test_results

def main():
    """Main test function"""
    print("🔍 Notebook Converter Diagnostic Test")
    print("=" * 50)
    
    # Test dependencies
    deps = test_dependencies()
    
    # Test converter
    results = test_conversions()
    
    print("\n=== Summary ===")
    if results:
        working_formats = [fmt for fmt, status in results.items() if status]
        failing_formats = [fmt for fmt, status in results.items() if not status]
        
        print(f"✅ Working formats: {', '.join(working_formats) if working_formats else 'None'}")
        print(f"❌ Failing formats: {', '.join(failing_formats) if failing_formats else 'None'}")
        
        if failing_formats:
            print("\n🔧 Recommendations:")
            for fmt in failing_formats:
                if fmt == 'PDF':
                    print("   - PDF: Check if LaTeX is installed (required for PDF conversion)")
                elif fmt == 'HTML':
                    print("   - HTML: Check nbconvert installation and HTMLExporter")
                elif fmt == 'Markdown':
                    print("   - Markdown: Check nbconvert installation and MarkdownExporter") 
                elif fmt == 'DOCX':
                    print("   - DOCX: Check python-docx and BeautifulSoup4 installation")
    else:
        print("❌ No conversion tests were performed due to missing dependencies")

if __name__ == "__main__":
    main()