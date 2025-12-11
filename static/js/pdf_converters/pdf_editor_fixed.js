// Fixed version of downloadPDFWithAnnotations function
// This should replace the existing function in pdf_editor.js

async function downloadPDFWithAnnotations() {
    if (!editorState.originalFile) {
        Utils.hideLoading();
        Utils.showError('Original file data not available');
        return;
    }
    
    try {
        Utils.showLoading('Embedding annotations into PDF...');
        
        // Load the original PDF with PDF-lib
        const originalBytes = await editorState.originalFile.arrayBuffer();
        const pdfDoc = await PDFLib.PDFDocument.load(originalBytes);
        
        // Apply page modifications first (deletions, rotations, duplications)
        await applyPageModifications(pdfDoc);
        
        // Get all pages from the modified PDF
        const pages = pdfDoc.getPages();
        
        // Process each page with annotations
        // IMPORTANT: editorState.annotations uses 1-based page numbers as keys
        for (const [pageNum, annotations] of editorState.annotations.entries()) {
            // Convert 1-based page number to 0-based index
            const pageIndex = pageNum - 1;
            
            // Skip if page doesn't exist (e.g., if it was deleted)
            if (pageIndex < 0 || pageIndex >= pages.length) {
                console.warn(`Skipping annotations for page ${pageNum} (index ${pageIndex}) - page not found`);
                continue;
            }
            
            const page = pages[pageIndex];
            const { width, height } = page.getSize();
            
            console.log(`Adding ${annotations.length} annotations to page ${pageNum} (index ${pageIndex})`);
            
            // Convert annotations to PDF coordinates and add them
            for (const annotation of annotations) {
                await addAnnotationToPDFPage(page, annotation, width, height);
            }
        }
        
        // Save the modified PDF
        const modifiedBytes = await pdfDoc.save();
        
        // Create download
        const blob = new Blob([modifiedBytes], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        // Add "_annotated" to filename
        const originalName = editorState.filename || 'document.pdf';
        const nameWithoutExt = originalName.replace(/\.pdf$/i, '');
        link.download = `${nameWithoutExt}_annotated.pdf`;
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up
        URL.revokeObjectURL(url);
        
        Utils.hideLoading();
        Utils.showSuccess('PDF with annotations downloaded successfully!');
        
        // Mark as clean
        editorState.isDirty = false;
        
    } catch (error) {
        Utils.hideLoading();
        Utils.showError(`Failed to embed annotations: ${error.message}`);
        console.error('Annotation embedding error:', error);
    }
}

// Also fix the applyPageModifications function to handle page operations correctly
async function applyPageModifications(pdfDoc) {
    try {
        // Get original page count before modifications
        const originalPageCount = pdfDoc.getPageCount();
        console.log(`Original PDF has ${originalPageCount} pages`);
        
        // If we have page operations stored, apply them
        if (editorState.pageOperations && editorState.pageOperations.length > 0) {
            console.log(`Applying ${editorState.pageOperations.length} page operations`);
            
            // Sort operations by timestamp to apply in correct order
            const sortedOps = [...editorState.pageOperations].sort((a, b) => a.timestamp - b.timestamp);
            
            // Keep track of page index mapping as we process operations
            let pageIndexMap = new Map();
            for (let i = 0; i < originalPageCount; i++) {
                pageIndexMap.set(i, i);
            }
            
            for (const operation of sortedOps) {
                console.log(`Applying operation: ${operation.type} on page ${operation.pageIndex + 1}`);
                
                switch (operation.type) {
                    case 'delete':
                        // Find the current index of the page to delete
                        const currentDeleteIndex = pageIndexMap.get(operation.pageIndex);
                        if (currentDeleteIndex !== undefined && currentDeleteIndex < pdfDoc.getPageCount()) {
                            pdfDoc.removePage(currentDeleteIndex);
                            console.log(`Deleted page at index ${currentDeleteIndex}`);
                            
                            // Update the mapping - all pages after the deleted one shift down
                            const newMap = new Map();
                            for (const [origIndex, currIndex] of pageIndexMap.entries()) {
                                if (currIndex > currentDeleteIndex) {
                                    newMap.set(origIndex, currIndex - 1);
                                } else if (currIndex < currentDeleteIndex) {
                                    newMap.set(origIndex, currIndex);
                                }
                                // Skip the deleted page
                            }
                            pageIndexMap = newMap;
                        }
                        break;
                        
                    case 'rotate':
                        const currentRotateIndex = pageIndexMap.get(operation.pageIndex);
                        if (currentRotateIndex !== undefined && currentRotateIndex < pdfDoc.getPageCount()) {
                            const page = pdfDoc.getPage(currentRotateIndex);
                            const currentRotation = page.getRotation().angle;
                            const newRotation = (currentRotation + (operation.angle || 90)) % 360;
                            page.setRotation(PDFLib.degrees(newRotation));
                            console.log(`Rotated page at index ${currentRotateIndex} to ${newRotation} degrees`);
                        }
                        break;
                        
                    case 'duplicate':
                        const currentDuplicateIndex = pageIndexMap.get(operation.sourceIndex);
                        if (currentDuplicateIndex !== undefined && currentDuplicateIndex < pdfDoc.getPageCount()) {
                            const [copiedPage] = await pdfDoc.copyPages(pdfDoc, [currentDuplicateIndex]);
                            const insertIndex = Math.min(operation.insertIndex || pdfDoc.getPageCount(), pdfDoc.getPageCount());
                            pdfDoc.insertPage(insertIndex, copiedPage);
                            console.log(`Duplicated page from index ${currentDuplicateIndex} to index ${insertIndex}`);
                            
                            // Update mapping - pages at or after insert index shift up
                            const newMap = new Map();
                            for (const [origIndex, currIndex] of pageIndexMap.entries()) {
                                if (currIndex >= insertIndex) {
                                    newMap.set(origIndex, currIndex + 1);
                                } else {
                                    newMap.set(origIndex, currIndex);
                                }
                            }
                            pageIndexMap = newMap;
                        }
                        break;
                }
            }
            
            console.log(`Final PDF has ${pdfDoc.getPageCount()} pages after modifications`);
        } else {
            console.log('No page operations to apply');
        }
        
    } catch (error) {
        console.error('Failed to apply page modifications:', error);
        throw error;
    }
}

// Additional helper function to debug annotation mapping
function debugAnnotationMapping() {
    console.log('=== Annotation Mapping Debug ===');
    console.log('Total pages in document:', document.querySelectorAll('.pdf-page-container').length);
    
    for (const [pageNum, annotations] of editorState.annotations.entries()) {
        console.log(`Page ${pageNum}: ${annotations.length} annotations`);
        annotations.forEach((ann, index) => {
            console.log(`  - Annotation ${index}: type=${ann.type}`);
        });
    }
    
    console.log('=== Page Operations ===');
    if (editorState.pageOperations) {
        editorState.pageOperations.forEach((op, index) => {
            console.log(`Operation ${index}: ${op.type} on page ${op.pageIndex + 1}`);
        });
    }
}

// Export the fix information
console.log(`
PDF Editor Fix Applied:
- Fixed page number to index conversion (1-based to 0-based)
- Added proper page mapping tracking during operations
- Added debug logging for troubleshooting
- Prevented annotations from being applied to wrong pages

To apply this fix:
1. Replace the downloadPDFWithAnnotations function in pdf_editor.js
2. Replace the applyPageModifications function in pdf_editor.js
3. Test with a multi-page PDF with annotations on different pages
`);
