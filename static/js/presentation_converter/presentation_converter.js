// Presentation Converter JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the presentation converter
    initializePresentationConverter();
});

function initializePresentationConverter() {
    // File upload handling for PPTX to PDF
    setupFileUpload('drop-zone', 'file');
    
    // Form submission
    setupFormSubmission();
    
    // Page range selector
    setupPageRangeSelector();
    
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
    
    // Add click handler for the upload area
    uploadArea.addEventListener('click', () => {
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
                showNotification('Invalid file type. Please select a supported file.', 'error');
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
    
    // Update upload area appearance
    updateUploadAreaDisplay(uploadArea, file.name);
    
    // Show file info
    showFileInfo(file, uploadArea);
}

function updateUploadAreaDisplay(uploadArea, filename) {
    // Update file preview area instead of upload area
    const filePreview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    
    if (filePreview && fileName) {
        filePreview.classList.remove('hidden');
        fileName.innerHTML = `
            <div class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3 mt-2">
                <p class="font-medium text-green-800 dark:text-green-200">Selected: ${filename}</p>
                <p class="text-sm text-green-600 dark:text-green-400">Ready to convert • Click upload area to change file</p>
            </div>
        `;
    }
}

function showFileInfo(file, uploadArea) {
    // File info is now handled by updateUploadAreaDisplay function
    // This function can be used for additional file validation if needed
}

function clearFileSelection(button) {
    const fileInput = document.getElementById('file');
    const filePreview = document.getElementById('file-preview');
    
    // Clear file input
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Hide file preview
    if (filePreview) {
        filePreview.classList.add('hidden');
    }
}

function setupFormSubmission() {
    const form = document.getElementById('pptx-to-pdf-form');
    
    if (form) {
        form.addEventListener('submit', handleFormSubmission);
    }
}

function handleFormSubmission(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const conversionType = formData.get('conversion_type');
    
    // Validate form
    if (!validateForm(form)) {
        return;
    }
    
    // Show processing modal
    showProcessingModal(conversionType);
    
    // Start conversion
    startConversion(formData, conversionType);
}

function validateForm(form) {
    const fileInput = form.querySelector('#file');
    
    if (!fileInput || !fileInput.files.length) {
        showNotification('Please select a file to convert.', 'error');
        return false;
    }
    
    const file = fileInput.files[0];
    const maxSize = 50 * 1024 * 1024; // 50MB
    
    if (file.size > maxSize) {
        showNotification('File size exceeds 50MB limit.', 'error');
        return false;
    }
    
    return true;
}

function startConversion(formData, conversionType) {
    const xhr = new XMLHttpRequest();
    
    // Set up progress tracking
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            updateProgress(Math.round(percentComplete), 'Uploading...');
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
                handleDirectDownload(xhr, conversionType);
            }
        } else {
            handleConversionError(`Server error: ${xhr.status}`);
        }
    });
    
    xhr.addEventListener('error', () => {
        handleConversionError('Network error occurred');
    });
    
    // Send request
    xhr.open('POST', '/convert/presentation', true);
    xhr.responseType = 'blob';  // Expect binary response for file downloads
    xhr.send(formData);
}

function handleConversionSuccess(response) {
    hideProcessingModal();
    
    if (response.download_url) {
        // Start download
        const link = document.createElement('a');
        link.href = response.download_url;
        link.download = response.filename || 'converted_file';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Show success modal
        showSuccessModal(response.filename);
    }
}

function handleDirectDownload(xhr, conversionType) {
    hideProcessingModal();
    
    // Use the blob response directly
    const blob = xhr.response;
    const url = window.URL.createObjectURL(blob);
    
    // Extract filename from Content-Disposition header
    const disposition = xhr.getResponseHeader('Content-Disposition');
    let filename = 'converted_file';
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

function setupPageRangeSelector() {
    const pageRangeSelect = document.querySelector('select[name="page_range"]');
    const customRangeInput = document.getElementById('custom-range-input');
    
    if (pageRangeSelect && customRangeInput) {
        pageRangeSelect.addEventListener('change', (e) => {
            if (e.target.value === 'custom') {
                customRangeInput.classList.remove('hidden');
                const input = customRangeInput.querySelector('input');
                if (input) {
                    input.focus();
                }
            } else {
                customRangeInput.classList.add('hidden');
            }
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
                link.download = lastFilename || 'converted_file';
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
            if (e.target === modal) {
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
        
    });
}

// Modal functions
function showProcessingModal(conversionType) {
    const modal = document.getElementById('processing-modal');
    const message = document.getElementById('processing-message');
    
    if (modal) {
        modal.classList.remove('hidden');
        
        if (message) {
            message.textContent = 'Converting PowerPoint to PDF... Please wait.';
        }
        
        updateProgress(0, 'Preparing...');
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
            messageElement.textContent = errorMessage || 'An unexpected error occurred. Please try again.';
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
        progressBar.style.width = `${percent}%`;
    }
    
    if (progressText) {
        progressText.textContent = `${percent}% complete`;
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