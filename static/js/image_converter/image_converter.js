// Image Converter JavaScript functionality
// Based on Notebook Converter with image-specific enhancements

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the Image Converter
    initializeImageConverter();
});

function initializeImageConverter() {
    // File upload handling (supports multiple files)
    setupFileUpload('image-upload-area', 'image-files');
    
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
    
    // Image preview functionality
    setupImagePreview();
    
    // Processing options handlers
    setupProcessingOptions();
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
    
    // File input change handler (supports multiple files)
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleMultipleFileSelection(Array.from(e.target.files), uploadArea);
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
                // Simulate file input change
                const dt = new DataTransfer();
                validFiles.forEach(file => dt.items.add(file));
                fileInput.files = dt.files;
                
                handleMultipleFileSelection(validFiles, uploadArea);
            } else {
                showNotification('Invalid file types. Please select image files (JPG, PNG, BMP, TIFF, GIF, WEBP).', 'error');
            }
        }
    });
}

function validateFile(file, acceptedTypes) {
    if (!acceptedTypes) return true;
    
    // Check file extension
    const acceptedExtensions = acceptedTypes.split(',').map(type => type.trim());
    const fileName = file.name.toLowerCase();
    const fileExtension = '.' + fileName.split('.').pop();
    
    const isValidExtension = acceptedExtensions.some(ext => 
        ext === fileExtension || 
        file.type === ext ||
        (ext.includes('/') && file.type.includes(ext.split('/')[0]))
    );
    
    // Additional image type validation
    const imageTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff', 'image/gif', 'image/webp'];
    const isValidImageType = imageTypes.includes(file.type) || 
        fileName.match(/\.(jpe?g|png|bmp|tiff?|gif|webp)$/i);
    
    return isValidExtension && isValidImageType;
}

function handleMultipleFileSelection(files, uploadArea) {
    // Check total file count (limit to 10 files for batch processing)
    if (files.length > 10) {
        showNotification('Too many files selected. Maximum 10 images allowed for batch processing.', 'error');
        return;
    }
    
    const maxSize = 25 * 1024 * 1024; // 25MB per file
    const validFiles = [];
    const invalidFiles = [];
    
    files.forEach(file => {
        // Check file size
        if (file.size > maxSize) {
            invalidFiles.push(`${file.name} (exceeds 25MB limit)`);
            return;
        }
        
        // Validate image file types
        if (!validateImageFileType(file)) {
            invalidFiles.push(`${file.name} (invalid image format)`);
            return;
        }
        
        validFiles.push(file);
    });
    
    if (invalidFiles.length > 0) {
        showNotification(`Some files were rejected: ${invalidFiles.join(', ')}`, 'warning');
    }
    
    if (validFiles.length === 0) {
        return;
    }
    
    // Update upload area appearance
    updateUploadAreaDisplay(uploadArea, validFiles);
    
    // Show image previews
    showImagePreviews(validFiles, uploadArea);
}

function validateImageFileType(file) {
    // Check MIME type
    const validMimeTypes = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 
        'image/tiff', 'image/gif', 'image/webp'
    ];
    
    if (validMimeTypes.includes(file.type)) {
        return true;
    }
    
    // Check file extension as fallback
    const validExtensions = ['jpg', 'jpeg', 'png', 'bmp', 'tif', 'tiff', 'gif', 'webp'];
    const extension = file.name.toLowerCase().split('.').pop();
    
    return validExtensions.includes(extension);
}

function updateUploadAreaDisplay(uploadArea, files) {
    uploadArea.classList.add('files-selected');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    
    if (uploadText && uploadSubtext) {
        const fileCount = files.length;
        const totalSize = files.reduce((sum, file) => sum + file.size, 0);
        
        uploadText.textContent = `${fileCount} image${fileCount > 1 ? 's' : ''} selected`;
        uploadSubtext.textContent = `Total size: ${formatFileSize(totalSize)} • Click to change files`;
    }
}

function showImagePreviews(files, uploadArea) {
    // Remove any existing preview grid
    const existingGrid = uploadArea.querySelector('.image-preview-grid');
    if (existingGrid) {
        existingGrid.remove();
    }
    
    // Create preview grid
    const previewGrid = document.createElement('div');
    previewGrid.className = 'image-preview-grid';
    
    files.forEach((file, index) => {
        const previewItem = createImagePreviewItem(file, index);
        previewGrid.appendChild(previewItem);
    });
    
    uploadArea.appendChild(previewGrid);
}

function createImagePreviewItem(file, index) {
    const item = document.createElement('div');
    item.className = 'image-preview-item';
    item.dataset.fileIndex = index;
    
    // Create thumbnail
    const img = document.createElement('img');
    img.className = 'image-preview-thumbnail';
    img.alt = file.name;
    
    // Create file reader for thumbnail
    const reader = new FileReader();
    reader.onload = (e) => {
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
    
    // Create info section
    const info = document.createElement('div');
    info.className = 'image-preview-info';
    
    const name = document.createElement('div');
    name.className = 'image-preview-name';
    name.textContent = file.name;
    name.title = file.name; // Tooltip for long names
    
    const size = document.createElement('div');
    size.className = 'image-preview-size';
    size.textContent = `${formatFileSize(file.size)}`;
    
    // Create remove button
    const removeBtn = document.createElement('button');
    removeBtn.className = 'image-preview-remove';
    removeBtn.innerHTML = '×';
    removeBtn.title = 'Remove this image';
    removeBtn.onclick = (e) => {
        e.stopPropagation();
        removeImageFromSelection(index);
    };
    
    info.appendChild(name);
    info.appendChild(size);
    item.appendChild(img);
    item.appendChild(info);
    item.appendChild(removeBtn);
    
    return item;
}

function removeImageFromSelection(indexToRemove) {
    const fileInput = document.getElementById('image-files');
    const uploadArea = document.getElementById('image-upload-area');
    
    if (!fileInput.files) return;
    
    const files = Array.from(fileInput.files);
    files.splice(indexToRemove, 1);
    
    // Update file input
    const dt = new DataTransfer();
    files.forEach(file => dt.items.add(file));
    fileInput.files = dt.files;
    
    if (files.length === 0) {
        // Clear all selections
        clearAllFileSelection();
    } else {
        // Update display
        handleMultipleFileSelection(files, uploadArea);
    }
}

function clearAllFileSelection() {
    const uploadArea = document.getElementById('image-upload-area');
    const fileInput = document.getElementById('image-files');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    const previewGrid = uploadArea.querySelector('.image-preview-grid');
    
    // Clear file input
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Reset upload area
    uploadArea.classList.remove('files-selected');
    if (uploadText) {
        uploadText.textContent = 'Drop your images here or click to browse';
    }
    if (uploadSubtext) {
        uploadSubtext.textContent = 'JPG, PNG, BMP, TIFF, GIF, WEBP supported (Max 25MB each)';
    }
    
    // Remove preview grid
    if (previewGrid) {
        previewGrid.remove();
    }
}

function setupFormSubmission() {
    const form = document.getElementById('image-converter-form');
    
    if (form) {
        form.addEventListener('submit', handleFormSubmission);
    }
}

function handleFormSubmission(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    
    // Enhanced debug logging
    const selectedFormat = form.querySelector('input[name="output_format"]:checked');
    console.log('🔍 Image Converter Form submission debug:');
    console.log('  Selected format element:', selectedFormat);
    console.log('  Selected format value:', selectedFormat ? selectedFormat.value : 'NONE');
    console.log('  All radio buttons:');
    const allRadios = form.querySelectorAll('input[name="output_format"]');
    allRadios.forEach((radio, index) => {
        console.log(`    [${index}] ${radio.value}: ${radio.checked ? 'CHECKED' : 'unchecked'}`);
    });
    console.log('  Form data entries:');
    for (let [key, value] of formData.entries()) {
        if (value instanceof File) {
            console.log(`    ${key}: File(${value.name}, ${value.size} bytes)`);
        } else {
            console.log(`    ${key}: ${value}`);
        }
    }
    
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
        showNotification('Please select at least one image file to convert.', 'error');
        return false;
    }
    
    const files = Array.from(fileInput.files);
    const maxSize = 25 * 1024 * 1024; // 25MB per file
    
    // Validate each file
    for (const file of files) {
        if (file.size > maxSize) {
            showNotification(`File ${file.name} exceeds 25MB limit.`, 'error');
            return false;
        }
        
        if (!validateImageFileType(file)) {
            showNotification(`File ${file.name} is not a valid image format.`, 'error');
            return false;
        }
    }
    
    // Check if output format is selected
    const outputFormat = form.querySelector('input[name="output_format"]:checked');
    if (!outputFormat) {
        showNotification('Please select an output format.', 'error');
        return false;
    }
    
    // Debug: Log the selected format
    console.log('Validated output format:', outputFormat.value);
    
    // Additional validation: ensure the format value is valid
    const validFormats = ['jpg', 'png', 'webp', 'bmp', 'tiff', 'gif'];
    if (!validFormats.includes(outputFormat.value)) {
        showNotification('Invalid output format selected.', 'error');
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
            updateProgress(Math.round(percentComplete), 'Uploading images...');
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
            handleConversionError('Invalid request. Please check your files and try again.');
        } else if (xhr.status === 413) {
            handleConversionError('File size too large. Maximum size is 25MB per file.');
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
    xhr.open('POST', '/image-converter/convert', true);
    xhr.responseType = 'blob';  // Expect binary response for file downloads
    xhr.timeout = 300000; // 5 minute timeout
    xhr.send(formData);
    
    // Update progress to show processing
    setTimeout(() => {
        updateProgress(50, 'Converting images...');
    }, 1000);
}

function handleConversionSuccess(response) {
    hideProcessingModal();
    
    if (response.download_url) {
        // Start download
        const link = document.createElement('a');
        link.href = response.download_url;
        link.download = response.filename || 'converted_images';
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
    
    // Extract filename from Content-Disposition header with improved parsing
    const disposition = xhr.getResponseHeader('Content-Disposition');
    let filename = 'converted_image'; // Default without extension
    
    console.log('Content-Disposition header:', disposition);
    console.log('All headers:', xhr.getAllResponseHeaders());
    
    if (disposition) {
        // Try different patterns for filename extraction
        let filenameMatch = disposition.match(/filename="([^"]+)"/) || 
                           disposition.match(/filename=([^;\s]+)/) ||
                           disposition.match(/filename\*=UTF-8''([^;\s]+)/);
        
        if (filenameMatch) {
            filename = decodeURIComponent(filenameMatch[1]);
            console.log('Extracted filename from header:', filename);
        } else {
            console.log('No filename found in Content-Disposition header');
        }
    } else {
        console.log('No Content-Disposition header found');
    }
    
    // If no filename from server, create one based on selected format
    if (filename === 'converted_image' || filename === 'converted_images') {
        const selectedFormat = document.querySelector('input[name="output_format"]:checked');
        if (selectedFormat) {
            // Use the actual format extension
            filename = 'converted_image.' + selectedFormat.value;
            console.log('Generated filename:', filename);
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
    
    console.log('Download initiated for:', filename);
    
    // Show success modal
    showSuccessModal(filename);
}

function handleConversionError(error) {
    hideProcessingModal();
    showErrorModal(error);
}

function setupOutputFormatSelector() {
    const formatRadios = document.querySelectorAll('input[name="output_format"]');
    
    formatRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            // Update UI based on selected format
            updateFormatSelection(e.target.value);
        });
    });
}

function updateFormatSelection(format) {
    console.log(`Selected output format: ${format}`);
    
    // Format-specific information
    const formatInfo = {
        jpg: 'JPG format is best for photos with good compression.',
        png: 'PNG format supports transparency and lossless compression.',
        webp: 'WEBP format offers superior compression for modern web.',
        bmp: 'BMP format provides uncompressed bitmap images.',
        tiff: 'TIFF format is ideal for high-quality archival images.',
        gif: 'GIF format supports animation and limited colors.'
    };
    
    // You could show this info in a tooltip or info box
    if (formatInfo[format]) {
        console.log(formatInfo[format]);
    }
}

function setupImagePreview() {
    // Image preview functionality is handled in handleMultipleFileSelection
    console.log('Image preview system initialized');
}

function setupProcessingOptions() {
    const resizePercentage = document.getElementById('resize-percentage');
    const resizeWidth = document.getElementById('resize-width');
    const resizeHeight = document.getElementById('resize-height');
    const maintainAspect = document.getElementById('maintain-aspect');
    
    // Handle resize percentage changes
    if (resizePercentage) {
        resizePercentage.addEventListener('input', (e) => {
            if (e.target.value) {
                // Clear width/height when percentage is set
                if (resizeWidth) resizeWidth.value = '';
                if (resizeHeight) resizeHeight.value = '';
            }
        });
    }
    
    // Handle width/height changes
    if (resizeWidth || resizeHeight) {
        [resizeWidth, resizeHeight].forEach(input => {
            if (input) {
                input.addEventListener('input', (e) => {
                    if (e.target.value) {
                        // Clear percentage when width/height is set
                        if (resizePercentage) resizePercentage.value = '';
                    }
                });
            }
        });
    }
    
    // Handle aspect ratio maintenance
    if (maintainAspect && resizeWidth && resizeHeight) {
        const updateAspectRatio = (changedInput, otherInput) => {
            if (maintainAspect.checked && changedInput.value && !otherInput.value) {
                // Could implement aspect ratio calculation here
                console.log('Aspect ratio maintenance enabled');
            }
        };
        
        resizeWidth.addEventListener('input', () => updateAspectRatio(resizeWidth, resizeHeight));
        resizeHeight.addEventListener('input', () => updateAspectRatio(resizeHeight, resizeWidth));
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
                link.download = lastFilename || 'converted_images';
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
            const fileInput = document.getElementById('image-files');
            if (fileInput) {
                fileInput.click();
            }
        }
        
        // Delete key to clear selection
        if (e.key === 'Delete' && e.ctrlKey) {
            e.preventDefault();
            clearAllFileSelection();
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
            message.textContent = 'Converting images... Please wait.';
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
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.664-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"></path>' :
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
window.removeImageFromSelection = removeImageFromSelection;
window.clearAllFileSelection = clearAllFileSelection;