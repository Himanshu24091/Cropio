// PDF to PowerPoint Converter JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the PDF to PowerPoint converter
    initializePdfToPptxConverter();
});

function initializePdfToPptxConverter() {
    // File upload handling
    setupFileUpload('pdf-upload-area', 'pdf-file');
    
    // Form submission
    setupFormSubmission();
    
    // Conversion mode selector
    setupConversionModeSelector();
    
    // Modal controls
    setupModalControls();
    
    // Progress tracking
    setupProgressTracking();
    
    // Keyboard shortcuts
    setupKeyboardShortcuts();
}

function setupFileUpload(areaId, inputId) {
    const uploadArea = document.getElementById(areaId);
    const fileInput = document.getElementById(inputId);
    
    if (!uploadArea || !fileInput) {
        console.warn(`Upload area ${areaId} or file input ${inputId} not found`);
        return;
    }
    
    // Click to upload
    uploadArea.addEventListener('click', (e) => {
        // Prevent double triggering when clicking on label
        if (e.target.tagName.toLowerCase() === 'label' || e.target.closest('label')) {
            return;
        }
        fileInput.click();
    });
    
    // Drag and drop functionality
    setupDragAndDrop(uploadArea, fileInput);
    
    // File input change handler
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0], uploadArea);
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
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (validateFile(file, fileInput.accept)) {
                // Simulate file input change
                const dt = new DataTransfer();
                dt.items.add(file);
                fileInput.files = dt.files;
                
                handleFileSelection(file, uploadArea);
            } else {
                showNotification('Invalid file type. Please select a PDF file.', 'error');
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

function handleFileSelection(file, uploadArea) {
    // Check file size (50MB limit)
    const maxSize = 50 * 1024 * 1024; // 50MB in bytes
    if (file.size > maxSize) {
        showNotification('File size exceeds 50MB limit. Please select a smaller file.', 'error');
        return;
    }
    
    // Validate PDF file type
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        showNotification('Please select a valid PDF file.', 'error');
        return;
    }
    
    // Update upload area appearance
    updateUploadAreaDisplay(uploadArea, file.name);
    
    // Show file info
    showFileInfo(file, uploadArea);
}

function updateUploadAreaDisplay(uploadArea, filename) {
    uploadArea.classList.add('file-selected');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    
    if (uploadText && uploadSubtext) {
        uploadText.textContent = `Selected: ${filename}`;
        uploadSubtext.textContent = 'Click to change file or drag another PDF';
        
        // Add file size info if available
        const fileInput = uploadArea.querySelector('.file-input');
        if (fileInput && fileInput.files.length > 0) {
            const fileSize = formatFileSize(fileInput.files[0].size);
            uploadSubtext.textContent += ` • ${fileSize}`;
        }
    }
}

function showFileInfo(file, uploadArea) {
    // Remove any existing file info
    const existingInfo = uploadArea.querySelector('.file-info');
    if (existingInfo) {
        existingInfo.remove();
    }
    
    // Create file info element
    const fileInfo = document.createElement('div');
    fileInfo.className = 'file-info mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg';
    fileInfo.innerHTML = `
        <div class="flex items-center space-x-3">
            <svg class="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
            </svg>
            <div class="flex-1">
                <p class="font-semibold text-green-900 dark:text-green-100">${file.name}</p>
                <p class="text-sm text-green-600 dark:text-green-400">
                    ${formatFileSize(file.size)} • ${file.type || 'PDF Document'} • ${formatDate(file.lastModified)}
                </p>
            </div>
            <button type="button" onclick="clearFileSelection(this)" class="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-200">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    uploadArea.appendChild(fileInfo);
}

function clearFileSelection(button) {
    const uploadArea = button.closest('.upload-area');
    const fileInput = uploadArea.querySelector('.file-input');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    const fileInfo = uploadArea.querySelector('.file-info');
    
    // Clear file input
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Reset upload area
    uploadArea.classList.remove('file-selected');
    if (uploadText) {
        uploadText.textContent = 'Drop your PDF file here or click to browse';
    }
    if (uploadSubtext) {
        uploadSubtext.textContent = 'PDF files only (Max 50MB)';
    }
    
    // Remove file info
    if (fileInfo) {
        fileInfo.remove();
    }
}

function setupFormSubmission() {
    const form = document.getElementById('pdf-to-pptx-form');
    
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
    const fileInput = form.querySelector('.file-input');
    
    if (!fileInput || !fileInput.files.length) {
        showNotification('Please select a PDF file to convert.', 'error');
        return false;
    }
    
    const file = fileInput.files[0];
    const maxSize = 50 * 1024 * 1024; // 50MB
    
    if (file.size > maxSize) {
        showNotification('File size exceeds 50MB limit.', 'error');
        return false;
    }
    
    // Validate PDF file type
    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        showNotification('Please select a valid PDF file.', 'error');
        return false;
    }
    
    return true;
}

function startConversion(formData) {
    const xhr = new XMLHttpRequest();
    
    // Set up progress tracking
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            updateProgress(Math.round(percentComplete), 'Uploading PDF...');
        }
    });
    
    xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
            const contentType = xhr.getResponseHeader('Content-Type');
            
            if (contentType && contentType.includes('application/json')) {
                // JSON response (error case)
                const reader = new FileReader();
                reader.onload = function() {
                    try {
                        const response = JSON.parse(reader.result);
                        if (response.success) {
                            handleConversionSuccess(response);
                        } else {
                            handleConversionError(response.error || 'Conversion failed');
                        }
                    } catch (e) {
                        handleConversionError('Invalid response format');
                    }
                };
                reader.readAsText(xhr.response);
            } else {
                // Binary response (successful file download)
                handleDirectDownload(xhr);
            }
        } else if (xhr.status === 400) {
            handleConversionError('Invalid request. Please check your file and try again.');
        } else if (xhr.status === 413) {
            handleConversionError('File size too large. Maximum size is 50MB.');
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
        handleConversionError('Request timed out. Please try again with a smaller file.');
    });
    
    // Send request
    xhr.open('POST', '/convert/pdf-to-pptx', true);
    xhr.responseType = 'blob';  // Expect binary response for file downloads
    xhr.timeout = 300000; // 5 minute timeout
    xhr.send(formData);
    
    // Update progress to show processing
    setTimeout(() => {
        updateProgress(50, 'Converting PDF to PowerPoint...');
    }, 1000);
}

function handleConversionSuccess(response) {
    hideProcessingModal();
    
    if (response.download_url) {
        // Start download
        const link = document.createElement('a');
        link.href = response.download_url;
        link.download = response.filename || 'converted_presentation.pptx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Show success modal
        showSuccessModal(response.filename);
    }
}

function handleDirectDownload(xhr) {
    hideProcessingModal();
    
    // Use the blob response directly
    const blob = xhr.response;
    const url = window.URL.createObjectURL(blob);
    
    // Extract filename from Content-Disposition header
    const disposition = xhr.getResponseHeader('Content-Disposition');
    let filename = 'converted_presentation.pptx';
    if (disposition) {
        const filenameMatch = disposition.match(/filename="(.+)"/);
        if (filenameMatch) {
            filename = filenameMatch[1];
        }
    }
    
    // Start download
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up
    window.URL.revokeObjectURL(url);
    
    // Show success modal
    showSuccessModal(filename);
}

function handleConversionError(error) {
    hideProcessingModal();
    showErrorModal(error);
}

function setupConversionModeSelector() {
    const basicMode = document.getElementById('basic-mode');
    const accurateMode = document.getElementById('accurate-mode');
    const accurateSettings = document.getElementById('accurate-settings');
    
    if (basicMode && accurateMode && accurateSettings) {
        [basicMode, accurateMode].forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.value === 'accurate' && e.target.checked) {
                    accurateSettings.classList.remove('hidden');
                } else {
                    accurateSettings.classList.add('hidden');
                }
            });
        });
    }
}

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
            // Re-trigger last download if available
            const lastDownloadUrl = downloadAgainButton.dataset.downloadUrl;
            const lastFilename = downloadAgainButton.dataset.filename;
            
            if (lastDownloadUrl) {
                const link = document.createElement('a');
                link.href = lastDownloadUrl;
                link.download = lastFilename || 'converted_presentation.pptx';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
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
    // This will be called during conversion to show progress
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
            const fileInput = document.getElementById('pdf-file');
            if (fileInput) {
                fileInput.click();
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
            message.textContent = 'Converting PDF to PowerPoint... Please wait.';
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

function showSuccessModal(filename) {
    const modal = document.getElementById('success-modal');
    const downloadAgainButton = document.getElementById('download-again');
    
    if (modal) {
        modal.classList.remove('hidden');
        
        // Store download info for "Download Again" functionality
        if (downloadAgainButton && filename) {
            downloadAgainButton.dataset.filename = filename;
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
        'bg-blue-500 text-white'
    }`;
    notification.innerHTML = `
        <div class="flex items-center space-x-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${type === 'error' ? 
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>' :
                    type === 'success' ?
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>' :
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

// Global function to make it accessible from HTML
window.clearFileSelection = clearFileSelection;