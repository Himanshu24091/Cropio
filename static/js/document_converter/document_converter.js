// Document Converter JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the Document Converter
    initializeDocumentConverter();
});

function initializeDocumentConverter() {
    // File upload handling
    setupFileUpload('document-upload-area', 'document-files');
    
    // Form submission
    setupFormSubmission();
    
    // Output format selector
    setupOutputFormatSelector();
    
    // Modal controls
    setupModalControls();
    
    // Progress tracking
    setupProgressTracking();
    
    // Keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Advanced options handlers
    setupAdvancedOptionsHandlers();
}

let selectedFiles = [];
let currentBatch = null;

function setupFileUpload(areaId, inputId) {
    const uploadArea = document.getElementById(areaId);
    const fileInput = document.getElementById(inputId);
    
    if (!uploadArea || !fileInput) {
        console.warn(`Upload area ${areaId} or file input ${inputId} not found`);
        return;
    }
    
    // Click to upload
    uploadArea.addEventListener('click', (e) => {
        // Prevent double triggering when clicking on label or existing files
        if (e.target.tagName.toLowerCase() === 'label' || 
            e.target.closest('label') || 
            e.target.closest('.file-preview-item')) {
            return;
        }
        fileInput.click();
    });
    
    // Drag and drop functionality
    setupDragAndDrop(uploadArea, fileInput);
    
    // File input change handler
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(Array.from(e.target.files), uploadArea);
        }
    });
}

function setupDragAndDrop(uploadArea, fileInput) {
    let dragCounter = 0;
    
    uploadArea.addEventListener('dragenter', (e) => {
        e.preventDefault();
        dragCounter++;
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dragCounter--;
        if (dragCounter === 0) {
            uploadArea.classList.remove('dragover');
        }
    });
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dragCounter = 0;
        uploadArea.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            const validFiles = files.filter(file => validateFile(file, fileInput.accept));
            if (validFiles.length > 0) {
                handleFileSelection(validFiles, uploadArea);
            } else {
                showNotification('Invalid file types. Please select supported document formats.', 'error');
            }
        }
    });
}

function validateFile(file, acceptedTypes) {
    if (!acceptedTypes) return true;
    
    const acceptedExtensions = acceptedTypes.split(',').map(type => type.trim());
    const fileName = file.name.toLowerCase();
    const fileExtension = '.' + fileName.split('.').pop();
    
    return acceptedExtensions.some(ext => 
        ext === fileExtension || 
        file.type === ext ||
        (ext.includes('/') && file.type.includes(ext.split('/')[0]))
    );
}

function handleFileSelection(files, uploadArea) {
    const maxFiles = 10;
    const maxSize = 50 * 1024 * 1024; // 50MB in bytes
    
    // Filter out files that are too large
    const validFiles = files.filter(file => {
        if (file.size > maxSize) {
            showNotification(`File ${file.name} exceeds 50MB limit and will be skipped.`, 'warning');
            return false;
        }
        return true;
    });
    
    // Check total file count
    if (selectedFiles.length + validFiles.length > maxFiles) {
        showNotification(`Maximum ${maxFiles} files allowed. Some files will be skipped.`, 'warning');
        const remainingSlots = maxFiles - selectedFiles.length;
        validFiles.splice(remainingSlots);
    }
    
    // Add new files to selection
    validFiles.forEach(file => {
        // Check for duplicates
        const isDuplicate = selectedFiles.some(existing => 
            existing.name === file.name && existing.size === file.size
        );
        
        if (!isDuplicate) {
            selectedFiles.push(file);
        }
    });
    
    // Update display
    updateUploadAreaDisplay(uploadArea);
    updateFileInputFiles();
    
    // Show file preview
    showFilePreview(uploadArea);
    
    // Auto-detect and suggest output format
    autoDetectOutputFormat();
    
    // Merge option temporarily disabled
    // validateMergeOption();
}

function updateUploadAreaDisplay(uploadArea) {
    uploadArea.classList.add('file-selected');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    
    if (uploadText && uploadSubtext) {
        if (selectedFiles.length === 1) {
            uploadText.textContent = `Selected: ${selectedFiles[0].name}`;
        } else {
            uploadText.textContent = `Selected: ${selectedFiles.length} files`;
        }
        
        const totalSize = selectedFiles.reduce((sum, file) => sum + file.size, 0);
        uploadSubtext.textContent = `${formatFileSize(totalSize)} total • Click to add more files or drag to replace`;
    }
}

function updateFileInputFiles() {
    const fileInput = document.getElementById('document-files');
    if (fileInput && selectedFiles.length > 0) {
        const dt = new DataTransfer();
        selectedFiles.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
    }
}

function showFilePreview(uploadArea) {
    // Remove existing preview
    const existingPreview = uploadArea.querySelector('.file-preview-list');
    if (existingPreview) {
        existingPreview.remove();
    }
    
    if (selectedFiles.length === 0) return;
    
    // Create file preview list
    const previewList = document.createElement('div');
    previewList.className = 'file-preview-list';
    
    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-preview-item';
        
        const fileType = getFileType(file.name);
        const fileIcon = getFileIcon(fileType);
        
        fileItem.innerHTML = `
            <div class="file-icon ${getFileTypeClass(fileType)}">
                ${fileIcon}
            </div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-details">
                    ${formatFileSize(file.size)} • ${fileType.toUpperCase()} • ${formatDate(file.lastModified)}
                    <span class="doc-type-indicator doc-type-${fileType}">${fileType}</span>
                </div>
            </div>
            <button type="button" onclick="removeFile(${index})" class="file-remove" title="Remove file">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;
        
        previewList.appendChild(fileItem);
    });
    
    uploadArea.appendChild(previewList);
    
    // Update batch indicator
    updateBatchIndicator(uploadArea);
}

function removeFile(index) {
    if (index >= 0 && index < selectedFiles.length) {
        selectedFiles.splice(index, 1);
        
        const uploadArea = document.getElementById('document-upload-area');
        
        if (selectedFiles.length === 0) {
            clearFileSelection();
        } else {
            updateUploadAreaDisplay(uploadArea);
            updateFileInputFiles();
            showFilePreview(uploadArea);
        }
    }
}

function clearFileSelection() {
    selectedFiles = [];
    const uploadArea = document.getElementById('document-upload-area');
    const fileInput = document.getElementById('document-files');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    const filePreview = uploadArea.querySelector('.file-preview-list');
    
    // Clear file input
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Reset upload area
    uploadArea.classList.remove('file-selected');
    if (uploadText) {
        uploadText.textContent = 'Drop your documents here or click to browse';
    }
    if (uploadSubtext) {
        uploadSubtext.textContent = 'DOCX, DOC, RTF, ODT, TXT, MD, HTML, EPUB, PDF • Max 50MB per file • Up to 10 files';
    }
    
    // Remove file preview
    if (filePreview) {
        filePreview.remove();
    }
    
    // Remove batch indicator
    const batchIndicator = uploadArea.querySelector('.batch-indicator');
    if (batchIndicator) {
        batchIndicator.remove();
    }
}

function updateBatchIndicator(uploadArea) {
    // Remove existing indicator
    const existingIndicator = uploadArea.querySelector('.batch-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    // Add batch indicator for multiple files
    if (selectedFiles.length > 1) {
        const batchIndicator = document.createElement('div');
        batchIndicator.className = 'batch-indicator';
        batchIndicator.textContent = `${selectedFiles.length} files`;
        uploadArea.appendChild(batchIndicator);
    }
}

function autoDetectOutputFormat() {
    if (selectedFiles.length === 0) return;
    
    // Analyze input formats to suggest optimal output format
    const inputFormats = selectedFiles.map(file => getFileType(file.name));
    const formatCounts = {};
    
    inputFormats.forEach(format => {
        formatCounts[format] = (formatCounts[format] || 0) + 1;
    });
    
    // Smart format suggestion logic
    let suggestedFormat = 'docx'; // Default
    
    if (inputFormats.includes('pdf')) {
        suggestedFormat = 'docx'; // Convert PDFs to editable format
    } else if (inputFormats.includes('md') || inputFormats.includes('html')) {
        suggestedFormat = 'pdf'; // Convert web formats to document
    } else if (inputFormats.includes('txt')) {
        suggestedFormat = 'docx'; // Enhance plain text
    }
    
    // Auto-select suggested format
    const formatRadio = document.getElementById(`format-${suggestedFormat}`);
    if (formatRadio) {
        formatRadio.checked = true;
        showFormatSpecificOptions(suggestedFormat);
        showNotification(`Auto-selected ${suggestedFormat.toUpperCase()} format based on your files`, 'info');
    }
}

function getFileType(filename) {
    const extension = filename.toLowerCase().split('.').pop();
    const typeMap = {
        'pdf': 'pdf',
        'docx': 'docx',
        'doc': 'docx',
        'rtf': 'rtf',
        'odt': 'odt',
        'txt': 'txt',
        'md': 'markdown',
        'html': 'html',
        'htm': 'html',
        'epub': 'epub'
    };
    return typeMap[extension] || 'unknown';
}

function getFileIcon(fileType) {
    const iconMap = {
        'pdf': `<svg class="w-full h-full text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                </svg>`,
        'docx': `<svg class="w-full h-full text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>`,
        'html': `<svg class="w-full h-full text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path>
                </svg>`,
        'markdown': `<svg class="w-full h-full text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                    </svg>`,
        'rtf': `<svg class="w-full h-full text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>`
    };
    
    return iconMap[fileType] || `<svg class="w-full h-full text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                                </svg>`;
}

function getFileTypeClass(fileType) {
    return `file-type-${fileType}`;
}

function setupFormSubmission() {
    const form = document.getElementById('document-converter-form');
    
    if (form) {
        form.addEventListener('submit', handleFormSubmission);
    }
}

function handleFormSubmission(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    
    // Validate form
    if (!validateForm(form)) {
        return;
    }
    
    // Show processing modal
    showProcessingModal();
    
    // Start conversion
    startConversion(formData);
}

function validateForm(form) {
    if (selectedFiles.length === 0) {
        showNotification('Please select at least one document to convert.', 'error');
        return false;
    }
    
    // Check output format is selected
    const outputFormat = form.querySelector('input[name="output_format"]:checked');
    if (!outputFormat) {
        showNotification('Please select an output format.', 'error');
        return false;
    }
    
    // Validate format-specific requirements
    if (outputFormat.value === 'pdf') {
        const pdfPassword = form.querySelector('#pdf-password').value;
        if (pdfPassword && pdfPassword.length < 4) {
            showNotification('PDF password must be at least 4 characters long.', 'error');
            return false;
        }
    }
    
    // Merge option temporarily disabled
    /*
    const mergeFiles = form.querySelector('#merge-files').checked;
    if (mergeFiles && selectedFiles.length < 2) {
        showNotification('File merging requires at least 2 files. Please select multiple files or disable the merge option.', 'error');
        return false;  // Prevent form submission
    }
    */
    
    return true;
}

function startConversion(formData) {
    const xhr = new XMLHttpRequest();
    
    // Set up progress tracking
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            updateProgress(Math.round(percentComplete), 'Uploading documents...');
        }
    });
    
    xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
            const contentType = xhr.getResponseHeader('Content-Type');
            
            if (contentType && contentType.includes('application/json')) {
                // JSON response (error case or success with download URL)
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        handleConversionSuccess(response);
                    } else {
                        handleConversionError(response.error || 'Conversion failed');
                    }
                } catch (e) {
                    handleConversionError('Invalid response format');
                }
            } else {
                // Binary response (successful file download)
                handleDirectDownload(xhr);
            }
        } else if (xhr.status === 400) {
            handleConversionError('Invalid request. Please check your files and settings.');
        } else if (xhr.status === 413) {
            handleConversionError('File size too large. Please reduce document sizes.');
        } else if (xhr.status === 429) {
            handleConversionError('Too many requests. Please wait a moment and try again.');
        } else {
            handleConversionError(`Server error: ${xhr.status}. Please try again later.`);
        }
    });
    
    xhr.addEventListener('error', () => {
        handleConversionError('Network error occurred. Please check your connection and try again.');
    });
    
    xhr.addEventListener('timeout', () => {
        handleConversionError('Request timed out. Please try again with smaller files.');
    });
    
    // Send request
    xhr.open('POST', '/convert/documents', true);
    xhr.responseType = 'blob';  // Expect binary response for file downloads
    xhr.timeout = 300000; // 5 minute timeout
    xhr.send(formData);
    
    // Update progress to show processing
    setTimeout(() => {
        updateProgress(30, 'Processing documents...');
    }, 1000);
    
    setTimeout(() => {
        updateProgress(60, 'Converting formats...');
    }, 3000);
}

function handleConversionSuccess(response) {
    hideProcessingModal();
    
    if (response.download_url) {
        // Start download
        const link = document.createElement('a');
        link.href = response.download_url;
        link.download = response.filename || 'converted_documents';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Show success modal
        showSuccessModal(response.filename, response.download_url);
    }
}

function handleDirectDownload(xhr) {
    hideProcessingModal();
    
    // Use the blob response directly
    const blob = xhr.response;
    const url = window.URL.createObjectURL(blob);
    
    // Extract filename from Content-Disposition header
    const disposition = xhr.getResponseHeader('Content-Disposition');
    let filename = 'converted_documents'; // Default
    if (disposition) {
        const filenameMatch = disposition.match(/filename="(.+)"/);
        if (filenameMatch) {
            filename = filenameMatch[1];
        }
    }
    
    // If no filename from server, create based on selection
    if (filename === 'converted_documents') {
        const selectedFormat = document.querySelector('input[name="output_format"]:checked');
        // Merge option temporarily disabled
        const mergeFiles = false; // document.querySelector('#merge-files').checked;
        
        if (selectedFiles.length === 1 && !mergeFiles) {
            const baseName = selectedFiles[0].name.split('.')[0];
            const extensionMap = {
                'pdf': '.pdf',
                'docx': '.docx',
                'html': '.html',
                'markdown': '.md',
                'rtf': '.rtf',
                'odt': '.odt',
                'txt': '.txt'
            };
            filename = baseName + (extensionMap[selectedFormat.value] || '');
        } else {
            filename = selectedFiles.length > 1 ? 'converted_documents.zip' : filename;
        }
    }
    
    // Start download
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Show success modal with URL (don't revoke yet)
    showSuccessModal(filename, url);
}

function handleConversionError(error) {
    hideProcessingModal();
    showErrorModal(error);
}

function setupOutputFormatSelector() {
    const formatRadios = document.querySelectorAll('input[name="output_format"]');
    
    formatRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            showFormatSpecificOptions(e.target.value);
        });
    });
    
    // Initialize with default selection
    const checkedFormat = document.querySelector('input[name="output_format"]:checked');
    if (checkedFormat) {
        showFormatSpecificOptions(checkedFormat.value);
    }
}

function showFormatSpecificOptions(format) {
    const pdfOptions = document.getElementById('pdf-options');
    const textOptions = document.getElementById('text-options');
    
    // Hide all options first
    if (pdfOptions) pdfOptions.style.display = 'none';
    if (textOptions) textOptions.style.display = 'none';
    
    // Show relevant options
    if (format === 'pdf' && pdfOptions) {
        pdfOptions.style.display = 'block';
    } else if (['txt', 'markdown'].includes(format) && textOptions) {
        textOptions.style.display = 'block';
    }
}

function setupAdvancedOptionsHandlers() {
    // Merge files handler - temporarily disabled
    /*
    const mergeFilesCheckbox = document.getElementById('merge-files');
    if (mergeFilesCheckbox) {
        mergeFilesCheckbox.addEventListener('change', (e) => {
            if (e.target.checked && selectedFiles.length < 2) {
                showNotification('Select at least 2 files to enable merging', 'warning');
                e.target.checked = false;
            }
            
            // Add/remove merge indicator
            toggleMergeIndicator(e.target.checked);
        });
    }
    */
    
    // OCR scan handler
    const ocrScanCheckbox = document.getElementById('ocr-scan');
    if (ocrScanCheckbox) {
        ocrScanCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                const hasPDF = selectedFiles.some(file => getFileType(file.name) === 'pdf');
                if (!hasPDF) {
                    showNotification('OCR is only useful for PDF files', 'info');
                }
                showNotification('OCR enabled - will extract text from scanned PDFs', 'info');
            }
        });
    }
    
    // Format preservation handler
    const preserveFormattingCheckbox = document.getElementById('preserve-formatting');
    if (preserveFormattingCheckbox) {
        preserveFormattingCheckbox.addEventListener('change', (e) => {
            if (!e.target.checked) {
                showNotification('Formatting preservation disabled - output may lose styling', 'warning');
            }
        });
    }
}

// Merge-related functions - temporarily disabled
/*
function validateMergeOption() {
    const mergeFilesCheckbox = document.getElementById('merge-files');
    if (!mergeFilesCheckbox) return;
    
    if (mergeFilesCheckbox.checked && selectedFiles.length < 2) {
        mergeFilesCheckbox.checked = false;
        showNotification('Merge option disabled - requires at least 2 files', 'warning');
    }
    
    // Update merge indicator
    toggleMergeIndicator(mergeFilesCheckbox.checked);
}

function toggleMergeIndicator(enabled) {
    const uploadArea = document.getElementById('document-upload-area');
    let mergeIndicator = uploadArea.querySelector('.merge-indicator');
    
    if (enabled && selectedFiles.length > 1) {
        if (!mergeIndicator) {
            mergeIndicator = document.createElement('div');
            mergeIndicator.className = 'merge-indicator';
            mergeIndicator.textContent = 'MERGE';
            uploadArea.appendChild(mergeIndicator);
        }
    } else {
        if (mergeIndicator) {
            mergeIndicator.remove();
        }
    }
}
*/

function setupModalControls() {
    // Close buttons
    const closeButtons = document.querySelectorAll('#close-success, #close-error');
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            hideAllModals();
        });
    });
    
    // Download again button
    const downloadAgainButton = document.getElementById('download-again');
    if (downloadAgainButton) {
        downloadAgainButton.addEventListener('click', () => {
            const lastDownloadUrl = downloadAgainButton.dataset.downloadUrl;
            const lastFilename = downloadAgainButton.dataset.filename;
            
            if (lastDownloadUrl) {
                try {
                    const link = document.createElement('a');
                    link.href = lastDownloadUrl;
                    link.download = lastFilename || 'converted_documents';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                } catch (error) {
                    console.error('Download failed:', error);
                    showNotification('Download link expired. Please convert the documents again.', 'error');
                }
            } else {
                showNotification('No download available. Please convert the documents again.', 'warning');
            }
        });
    }
    
    // Close modals when clicking outside
    document.addEventListener('click', (e) => {
        const modals = document.querySelectorAll('.fixed.inset-0');
        modals.forEach(modal => {
            if (e.target === modal && !modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
            }
        });
    });
}

function setupProgressTracking() {
    window.updateConversionProgress = (percent, message) => {
        updateProgress(percent, message);
    };
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Escape key to close modals
        if (e.key === 'Escape') {
            hideAllModals();
        }
        
        // Ctrl+U to focus file input
        if (e.ctrlKey && e.key === 'u') {
            e.preventDefault();
            const fileInput = document.getElementById('document-files');
            if (fileInput) {
                fileInput.click();
            }
        }
        
        // Delete key to clear selected files
        if (e.key === 'Delete' && selectedFiles.length > 0) {
            if (!e.target.matches('input, textarea, select')) {
                e.preventDefault();
                clearFileSelection();
                showNotification('All files cleared', 'info');
            }
        }
    });
}

// Modal functions
function showProcessingModal() {
    const modal = document.getElementById('processing-modal');
    const message = document.getElementById('processing-message');
    
    if (modal) {
        modal.classList.remove('hidden');
        
        if (message) {
            if (selectedFiles.length === 1) {
                message.textContent = 'Converting your document... Please wait.';
            } else {
                message.textContent = `Converting ${selectedFiles.length} documents... Please wait.`;
            }
        }
        
        updateProgress(0, 'Preparing conversion...');
    }
}

function hideProcessingModal() {
    const modal = document.getElementById('processing-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function showSuccessModal(filename, downloadUrl = null) {
    const modal = document.getElementById('success-modal');
    const downloadAgainButton = document.getElementById('download-again');
    
    if (modal) {
        modal.classList.remove('hidden');
        
        // Store download info for "Download Again" functionality
        if (downloadAgainButton && filename) {
            downloadAgainButton.dataset.filename = filename;
            if (downloadUrl) {
                downloadAgainButton.dataset.downloadUrl = downloadUrl;
            }
        }
    }
}

function showErrorModal(errorMessage) {
    const modal = document.getElementById('error-modal');
    const messageElement = document.getElementById('error-message');
    
    if (modal) {
        modal.classList.remove('hidden');
        
        if (messageElement) {
            messageElement.textContent = errorMessage || 'An unexpected error occurred during conversion. Please try again.';
        }
    }
}

function hideAllModals() {
    const modals = document.querySelectorAll('.fixed.inset-0');
    modals.forEach(modal => {
        modal.classList.add('hidden');
    });
    
    // Clean up blob URL when success modal is closed
    const downloadAgainButton = document.getElementById('download-again');
    if (downloadAgainButton && downloadAgainButton.dataset.downloadUrl) {
        const url = downloadAgainButton.dataset.downloadUrl;
        if (url.startsWith('blob:')) {
            window.URL.revokeObjectURL(url);
            delete downloadAgainButton.dataset.downloadUrl;
        }
    }
}

function updateProgress(percent, message) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const processingMessage = document.getElementById('processing-message');
    
    if (progressBar) {
        progressBar.style.width = `${Math.max(0, Math.min(100, percent))}%`;
    }
    
    if (progressText) {
        progressText.textContent = `${Math.max(0, Math.min(100, percent))}% complete`;
    }
    
    if (processingMessage && message) {
        processingMessage.textContent = message;
    }
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(timestamp) {
    return new Date(timestamp).toLocaleDateString();
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 ${
        type === 'error' ? 'bg-red-500 text-white' : 
        type === 'success' ? 'bg-green-500 text-white' : 
        type === 'warning' ? 'bg-yellow-500 text-white' :
        'bg-blue-500 text-white'
    }`;
    notification.innerHTML = `
        <div class="flex items-center space-x-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${type === 'error' ? 
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>' :
                    type === 'success' ?
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>' :
                    type === 'warning' ?
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>' :
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
                }
            </svg>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 hover:text-gray-200">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Global functions to make them accessible from HTML
window.removeFile = removeFile;
window.clearFileSelection = clearFileSelection;