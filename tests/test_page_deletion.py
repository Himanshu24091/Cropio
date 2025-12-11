#!/usr/bin/env python3
"""
Test script to verify page deletion functionality in PDF editor
"""

import fitz
import tempfile
import os
from routes.pdf_editor_routes import apply_pdf_modifications

def create_test_pdf(num_pages=5):
    """Create a test PDF with specified number of pages"""
    doc = fitz.open()
    
    for i in range(num_pages):
        page = doc.new_page(width=612, height=792)  # Standard US Letter
        
        # Add page number text
        page.insert_text(
            (50, 50), 
            f"This is page {i + 1}", 
            fontsize=16, 
            color=(0, 0, 0)
        )
        
        # Add some content to distinguish pages
        page.insert_text(
            (50, 100), 
            f"Content for page {i + 1}\nUnique identifier: PAGE_{i + 1:03d}", 
            fontsize=12, 
            color=(0.3, 0.3, 0.3)
        )
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc.save(temp_file.name)
    doc.close()
    
    return temp_file.name

def test_page_deletion():
    """Test page deletion functionality"""
    print("Creating test PDF with 5 pages...")
    test_pdf_path = create_test_pdf(5)
    
    try:
        # Test case 1: Delete first page (page 1 -> index 0)
        print("\n=== Test Case 1: Delete First Page ===")
        page_operations = [
            {"type": "delete", "pageIndex": 0}  # Delete first page (0-based)
        ]
        annotations = {}  # No annotations
        
        output_path = apply_pdf_modifications(test_pdf_path, annotations, page_operations, "test_session")
        
        if output_path and os.path.exists(output_path):
            # Verify result
            result_doc = fitz.open(output_path)
            print(f"Original pages: 5, Result pages: {result_doc.page_count}")
            
            # Check if the first page now contains what was originally page 2
            first_page = result_doc[0]
            text = first_page.get_text()
            print(f"First page text: {text[:100]}...")
            
            if "This is page 2" in text:
                print("✅ SUCCESS: First page correctly shows original page 2 content")
            else:
                print("❌ FAIL: First page does not show expected content")
            
            result_doc.close()
            os.unlink(output_path)
        else:
            print("❌ FAIL: Output file not created")
        
        # Test case 2: Delete middle page (page 3 -> index 2)
        print("\n=== Test Case 2: Delete Middle Page ===")
        page_operations = [
            {"type": "delete", "pageIndex": 2}  # Delete third page (0-based)
        ]
        
        output_path = apply_pdf_modifications(test_pdf_path, annotations, page_operations, "test_session")
        
        if output_path and os.path.exists(output_path):
            result_doc = fitz.open(output_path)
            print(f"Original pages: 5, Result pages: {result_doc.page_count}")
            
            if result_doc.page_count == 4:
                print("✅ SUCCESS: Correct number of pages after deletion")
                
                # Check page sequence
                pages_content = []
                for i in range(result_doc.page_count):
                    page = result_doc[i]
                    text = page.get_text()
                    if "This is page" in text:
                        page_num = text.split("This is page ")[1].split()[0]
                        pages_content.append(page_num)
                
                expected_sequence = ["1", "2", "4", "5"]  # Page 3 should be missing
                if pages_content == expected_sequence:
                    print("✅ SUCCESS: Page sequence is correct after deletion")
                else:
                    print(f"❌ FAIL: Expected {expected_sequence}, got {pages_content}")
            else:
                print(f"❌ FAIL: Expected 4 pages, got {result_doc.page_count}")
            
            result_doc.close()
            os.unlink(output_path)
        else:
            print("❌ FAIL: Output file not created")
        
        # Test case 3: Delete multiple pages
        print("\n=== Test Case 3: Delete Multiple Pages ===")
        page_operations = [
            {"type": "delete", "pageIndex": 0},  # Delete first page
            {"type": "delete", "pageIndex": 4}   # Delete last page
        ]
        
        output_path = apply_pdf_modifications(test_pdf_path, annotations, page_operations, "test_session")
        
        if output_path and os.path.exists(output_path):
            result_doc = fitz.open(output_path)
            print(f"Original pages: 5, Result pages: {result_doc.page_count}")
            
            if result_doc.page_count == 3:
                print("✅ SUCCESS: Correct number of pages after multiple deletions")
                
                # Check page sequence - should be pages 2, 3, 4 (original numbering)
                pages_content = []
                for i in range(result_doc.page_count):
                    page = result_doc[i]
                    text = page.get_text()
                    if "This is page" in text:
                        page_num = text.split("This is page ")[1].split()[0]
                        pages_content.append(page_num)
                
                expected_sequence = ["2", "3", "4"]
                if pages_content == expected_sequence:
                    print("✅ SUCCESS: Page sequence is correct after multiple deletions")
                else:
                    print(f"❌ FAIL: Expected {expected_sequence}, got {pages_content}")
            else:
                print(f"❌ FAIL: Expected 3 pages, got {result_doc.page_count}")
            
            result_doc.close()
            os.unlink(output_path)
        else:
            print("❌ FAIL: Output file not created")
        
        # Test case 4: Delete pages with annotations
        print("\n=== Test Case 4: Delete Pages with Annotations ===")
        page_operations = [
            {"type": "delete", "pageIndex": 1}  # Delete second page
        ]
        annotations = {
            "1": [{"type": "text", "text": "Annotation on page 1", "x": 100, "y": 200, "fontSize": 14, "color": "#FF0000"}],
            "2": [{"type": "text", "text": "Annotation on page 2 (will be deleted)", "x": 100, "y": 200, "fontSize": 14, "color": "#00FF00"}],
            "3": [{"type": "text", "text": "Annotation on page 3", "x": 100, "y": 200, "fontSize": 14, "color": "#0000FF"}]
        }
        
        output_path = apply_pdf_modifications(test_pdf_path, annotations, page_operations, "test_session")
        
        if output_path and os.path.exists(output_path):
            result_doc = fitz.open(output_path)
            print(f"Original pages: 5, Result pages: {result_doc.page_count}")
            
            if result_doc.page_count == 4:
                print("✅ SUCCESS: Correct number of pages after deletion with annotations")
                
                # Check that annotations were applied to the correct pages
                page1_text = result_doc[0].get_text()
                page2_text = result_doc[1].get_text()  # This should be original page 3
                
                if "Annotation on page 1" in page1_text:
                    print("✅ SUCCESS: Annotation on page 1 preserved")
                else:
                    print("❌ FAIL: Annotation on page 1 not found")
                
                if "Annotation on page 3" in page2_text:
                    print("✅ SUCCESS: Annotation on page 3 preserved and correctly positioned")
                else:
                    print("❌ FAIL: Annotation on page 3 not found or incorrectly positioned")
                
                if "Annotation on page 2 (will be deleted)" not in (page1_text + page2_text):
                    print("✅ SUCCESS: Annotation on deleted page 2 correctly removed")
                else:
                    print("❌ FAIL: Annotation on deleted page 2 still present")
            
            result_doc.close()
            os.unlink(output_path)
        else:
            print("❌ FAIL: Output file not created")
        
        print("\n=== All Tests Completed ===")
        
    finally:
        # Clean up test file
        if os.path.exists(test_pdf_path):
            os.unlink(test_pdf_path)

if __name__ == "__main__":
    test_page_deletion()