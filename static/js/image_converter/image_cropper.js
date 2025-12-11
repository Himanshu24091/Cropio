// Image Cropper JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the Image Cropper
    initializeImageCropper();
});

let currentCropper = null;
let selectedFiles = [];
let currentImageIndex = 0;

function initializeImageCropper() {
    // File upload handling
    setupFileUpload('image-upload-area', 'image-files');
    
    // Form submission
    setupFormSubmission();
    
    // Crop mode selector
    setupCropModeSelector();
    
    // Modal controls
    setupModalControls();
    
    // Progress tracking
    setupProgressTracking();
    
    // Keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Aspect ratio handlers
    setupAspectRatioHandlers();
    
    // Interactive crop feature handlers
    setupInteractiveCropFeatureHandlers();
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
        const validFiles = files.filter(file => validateImageFile(file));
        
        if (validFiles.length > 0) {
            // Update file input
            const dt = new DataTransfer();
            validFiles.forEach(file => dt.items.add(file));
            fileInput.files = dt.files;
            
            handleMultipleFileSelection(validFiles, uploadArea);
        } else {
            showNotification('Please select valid image files (JPG, PNG, BMP, TIFF, WEBP, GIF).', 'error');
        }
    });
}

function validateImageFile(file) {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp', 'image/gif'];
    const maxSize = 25 * 1024 * 1024; // 25MB
    
    if (!validTypes.includes(file.type)) {
        showNotification(`${file.name} is not a valid image format.`, 'error');
        return false;
    }
    
    if (file.size > maxSize) {
        showNotification(`${file.name} exceeds the 25MB size limit.`, 'error');
        return false;
    }
    
    return true;
}

function handleMultipleFileSelection(files, uploadArea) {
    // Limit to 10 files
    if (files.length > 10) {
        showNotification('Maximum 10 images allowed. First 10 images will be selected.', 'warning');
        files = files.slice(0, 10);
    }
    
    selectedFiles = files;
    updateUploadAreaDisplay(uploadArea, files);
    createImagePreviewGrid(files, uploadArea);
    
    // Initialize inline cropper if Free Crop is selected
    const cropMode = document.querySelector('input[name="crop_mode"]:checked')?.value;
    if (cropMode === 'free' && files.length > 0) {
        initializeInlineCropper(files[0]); // Show first image in inline cropper
    }
}

function updateUploadAreaDisplay(uploadArea, files) {
    uploadArea.classList.add('file-selected');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    
    if (uploadText && uploadSubtext) {
        uploadText.textContent = `Selected: ${files.length} image${files.length > 1 ? 's' : ''}`;
        
        const totalSize = files.reduce((sum, file) => sum + file.size, 0);
        const totalSizeFormatted = formatFileSize(totalSize);
        
        uploadSubtext.textContent = `Total size: ${totalSizeFormatted} • Click to change files or drag more images`;
    }
}

function createImagePreviewGrid(files, uploadArea) {
    // Remove existing preview grid
    const existingGrid = uploadArea.querySelector('.image-preview-grid');
    if (existingGrid) {
        existingGrid.remove();
    }
    
    // Create new preview grid
    const previewGrid = document.createElement('div');
    previewGrid.className = 'image-preview-grid';
    
    files.forEach((file, index) => {
        const previewItem = document.createElement('div');
        previewItem.className = 'image-preview-item';
        
        // Create thumbnail
        const reader = new FileReader();
        reader.onload = function(e) {
            previewItem.innerHTML = `
                <img src="${e.target.result}" alt="${file.name}" class="image-preview-thumb" data-index="${index}">
                <div class="image-preview-name">${file.name}</div>
                <button class="image-preview-remove" onclick="removeImageFromSelection(${index})" title="Remove image">×</button>
            `;
            
            // Add click handler to show crop preview
            const thumb = previewItem.querySelector('.image-preview-thumb');
            thumb.addEventListener('click', () => showCropPreview(index));
        };
        reader.readAsDataURL(file);
        
        previewGrid.appendChild(previewItem);
    });
    
    uploadArea.appendChild(previewGrid);
}

function removeImageFromSelection(index) {
    selectedFiles.splice(index, 1);
    
    // Update file input
    const fileInput = document.getElementById('image-files');
    const dt = new DataTransfer();
    selectedFiles.forEach(file => dt.items.add(file));
    fileInput.files = dt.files;
    
    const uploadArea = document.getElementById('image-upload-area');
    
    if (selectedFiles.length === 0) {
        clearFileSelection();
    } else {
        updateUploadAreaDisplay(uploadArea, selectedFiles);
        createImagePreviewGrid(selectedFiles, uploadArea);
    }
}

function clearFileSelection() {
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
    uploadArea.classList.remove('file-selected');
    if (uploadText) {
        uploadText.textContent = 'Drop your images here or click to browse';
    }
    if (uploadSubtext) {
        uploadSubtext.textContent = 'Image files only (JPG, PNG, BMP, TIFF, WEBP, GIF) • Max 25MB per file • Up to 10 images';
    }
    
    // Remove preview grid
    if (previewGrid) {
        previewGrid.remove();
    }
    
    selectedFiles = [];
    currentImageIndex = 0;
    
    // Clear inline cropper
    clearInlineCropper();
}

function showCropPreview(imageIndex) {
    if (!selectedFiles[imageIndex]) return;
    
    currentImageIndex = imageIndex;
    const file = selectedFiles[imageIndex];
    
    // Show preview modal
    const modal = document.getElementById('preview-modal');
    const cropperContainer = document.getElementById('cropper-container');
    
    modal.classList.remove('hidden');
    
    // Clear previous cropper
    if (currentCropper) {
        currentCropper.destroy();
        currentCropper = null;
    }
    
    cropperContainer.innerHTML = '';
    
    // Create image element
    const img = document.createElement('img');
    img.style.maxWidth = '100%';
    img.style.maxHeight = '60vh';
    
    // Load image
    const reader = new FileReader();
    reader.onload = function(e) {
        img.src = e.target.result;
        cropperContainer.appendChild(img);
        
        // Initialize cropper
        setTimeout(() => {
            initializeCropper(img);
        }, 100);
    };
    reader.readAsDataURL(file);
}

function initializeCropper(img) {
    const cropMode = document.querySelector('input[name="crop_mode"]:checked').value;
    const showGrid = document.getElementById('show-grid')?.checked ?? true;
    let aspectRatio = NaN; // Free crop by default
    
    if (cropMode === 'aspect') {
        const selectedRatio = document.querySelector('input[name="aspect_ratio"]:checked');
        if (selectedRatio) {
            const ratio = selectedRatio.value;
            if (ratio === '1:1') aspectRatio = 1;
            else if (ratio === '4:3') aspectRatio = 4/3;
            else if (ratio === '16:9') aspectRatio = 16/9;
            else if (ratio === '3:2') aspectRatio = 3/2;
        }
    }
    
    // Get custom dimensions if provided
    const customWidth = document.getElementById('custom-width').value;
    const customHeight = document.getElementById('custom-height').value;
    
    if (customWidth && customHeight) {
        aspectRatio = parseFloat(customWidth) / parseFloat(customHeight);
    }
    
    currentCropper = new Cropper(img, {
        aspectRatio: aspectRatio,
        viewMode: 1,
        dragMode: 'move',
        autoCropArea: 0.8,
        restore: false,
        guides: showGrid,
        center: true,
        highlight: false,
        cropBoxMovable: true,
        cropBoxResizable: true,
        toggleDragModeOnDblclick: false,
        responsive: true,
        checkCrossOrigin: false,
        minContainerWidth: 300,
        minContainerHeight: 200,
        ready: function() {
            // Initialize enhanced cropping features
            initializeEnhancedCropping(this.cropper);
            
            // Center crop if enabled
            const centerCrop = document.getElementById('center-crop').checked;
            if (centerCrop) {
                const containerData = this.cropper.getContainerData();
                const imageData = this.cropper.getImageData();
                const centerX = imageData.width / 2;
                const centerY = imageData.height / 2;
                const cropSize = Math.min(imageData.width, imageData.height) * 0.8;
                
                this.cropper.setCropBoxData({
                    left: centerX - cropSize/2,
                    top: centerY - cropSize/2,
                    width: cropSize,
                    height: aspectRatio ? cropSize / aspectRatio : cropSize
                });
            }
        },
        cropend: function() {
            updateCropInfo(this.cropper);
        },
        cropmove: function() {
            updateCropInfo(this.cropper);
        }
    });
}

function setupCropModeSelector() {
    const cropModeRadios = document.querySelectorAll('input[name="crop_mode"]');
    const aspectOptions = document.getElementById('aspect-options');
    const shapeOptions = document.getElementById('shape-options');
    const interactiveFeatures = document.querySelector('.crop-mode-enhanced');
    
    // Initialize visibility based on selected mode
    const initialMode = document.querySelector('input[name="crop_mode"]:checked')?.value || 'free';
    if (interactiveFeatures) {
        interactiveFeatures.style.display = (initialMode === 'free') ? 'block' : 'none';
    }
    
    cropModeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            const mode = e.target.value;
            
            // Show/hide mode-specific options
            if (mode === 'aspect') {
                if (aspectOptions) aspectOptions.style.display = 'block';
                if (shapeOptions) shapeOptions.style.display = 'none';
            } else if (mode === 'shape') {
                if (aspectOptions) aspectOptions.style.display = 'none';
                if (shapeOptions) shapeOptions.style.display = 'block';
            } else {
                if (aspectOptions) aspectOptions.style.display = 'none';
                if (shapeOptions) shapeOptions.style.display = 'none';
            }
            
            // Show Interactive features only for Free Crop
            if (interactiveFeatures) {
                if (mode === 'free') {
                    interactiveFeatures.style.display = 'block';
                    showNotification('Interactive crop features enabled - Use drag-and-drop cropping with advanced controls', 'info');
                } else {
                    interactiveFeatures.style.display = 'none';
                    if (mode === 'aspect') {
                        showNotification('Fixed aspect ratio mode - Select an aspect ratio below', 'info');
                    } else if (mode === 'shape') {
                        showNotification('Shape crop mode - Select a shape below', 'info');
                    }
                }
            }
            
            // Initialize or clear inline cropper based on mode
            if (mode === 'free' && selectedFiles.length > 0) {
                initializeInlineCropper(selectedFiles[0]);
            } else {
                clearInlineCropper();
            }
            
            // Update cropper if active
            if (currentCropper) {
                updateCropperMode();
            }
        });
    });
    
    // No need to dispatch change here; we've initialized visibility above.
}

function setupAspectRatioHandlers() {
    const aspectRadios = document.querySelectorAll('input[name="aspect_ratio"]');
    
    aspectRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (currentCropper) {
                updateCropperMode();
            }
        });
    });
}

function updateCropperMode() {
    if (!currentCropper) return;
    
    const cropMode = document.querySelector('input[name="crop_mode"]:checked').value;
    let aspectRatio = NaN;
    
    if (cropMode === 'aspect') {
        const selectedRatio = document.querySelector('input[name="aspect_ratio"]:checked');
        if (selectedRatio) {
            const ratio = selectedRatio.value;
            if (ratio === '1:1') aspectRatio = 1;
            else if (ratio === '4:3') aspectRatio = 4/3;
            else if (ratio === '16:9') aspectRatio = 16/9;
            else if (ratio === '3:2') aspectRatio = 3/2;
        }
    }
    
    currentCropper.setAspectRatio(aspectRatio);
}

function setupFormSubmission() {
    const form = document.getElementById('image-cropper-form');
    const fileInput = document.getElementById('image-files');
    
    if (form) {
        // Prevent default browser validation
        form.noValidate = true;
        form.addEventListener('submit', handleFormSubmission);
        
        // Custom file input validation to prevent focus errors
        if (fileInput) {
            // Remove required attribute to prevent browser validation
            fileInput.removeAttribute('required');
            
            fileInput.addEventListener('invalid', (e) => {
                e.preventDefault();
                showNotification('Please select at least one image file.', 'error');
            });
            
            // Ensure file input doesn't trigger validation focus issues
            // Keep it accessible but hidden properly
            fileInput.style.position = 'absolute';
            fileInput.style.left = '-1px';
            fileInput.style.top = '-1px';
            fileInput.style.width = '1px';
            fileInput.style.height = '1px';
            fileInput.style.opacity = '0';
            fileInput.style.overflow = 'hidden';
            fileInput.style.clip = 'rect(0, 0, 0, 0)';
            fileInput.style.whiteSpace = 'nowrap';
            fileInput.setAttribute('aria-hidden', 'true');
            fileInput.tabIndex = -1;
        }
    }
}

function handleFormSubmission(e) {
    e.preventDefault();
    
    const form = e.target;
    
    // Validate form
    if (!validateForm(form)) {
        return;
    }
    
    // Show processing modal
    showProcessingModal();
    
    // Prepare form data
    const formData = new FormData(form);
    
    // Add cropping metadata if available
    if (currentCropper) {
        const cropData = currentCropper.getData();
        formData.append('crop_data', JSON.stringify(cropData));
    } else if (window.appliedCropData) {
        // Use applied crop data from inline cropper if available
        formData.append('crop_data', JSON.stringify(window.appliedCropData));
    }
    
    // Start cropping
    startCropping(formData);
}

function validateForm(form) {
    if (selectedFiles.length === 0) {
        showNotification('Please select at least one image to crop.', 'error');
        return false;
    }
    
    // Validate crop mode and options
    const cropMode = form.querySelector('input[name="crop_mode"]:checked');
    if (!cropMode) {
        showNotification('Please select a crop mode.', 'error');
        return false;
    }
    
    if (cropMode.value === 'aspect') {
        const aspectRatio = form.querySelector('input[name="aspect_ratio"]:checked');
        if (!aspectRatio) {
            showNotification('Please select an aspect ratio for fixed aspect cropping.', 'error');
            return false;
        }
    }
    
    if (cropMode.value === 'shape') {
        const cropShape = form.querySelector('input[name="crop_shape"]:checked');
        if (!cropShape) {
            showNotification('Please select a shape for shape cropping.', 'error');
            return false;
        }
    }
    
    return true;
}

function startCropping(formData) {
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
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        handleCroppingSuccess(response);
                    } else {
                        handleCroppingError(response.error || 'Cropping failed');
                    }
                } catch (e) {
                    handleCroppingError('Invalid response format');
                }
            } else {
                // Binary response (successful file download)
                handleDirectDownload(xhr);
            }
        } else if (xhr.status === 400) {
            handleCroppingError('Invalid request. Please check your images and settings.');
        } else if (xhr.status === 413) {
            handleCroppingError('File size too large. Please reduce image sizes.');
        } else if (xhr.status === 429) {
            handleCroppingError('Too many requests. Please wait a moment and try again.');
        } else {
            handleCroppingError(`Server error: ${xhr.status}. Please try again later.`);
        }
    });
    
    xhr.addEventListener('error', () => {
        handleCroppingError('Network error occurred. Please check your connection and try again.');
    });
    
    xhr.addEventListener('timeout', () => {
        handleCroppingError('Request timed out. Please try again with smaller images.');
    });
    
    // Send request
    xhr.open('POST', '/crop/images', true);
    xhr.responseType = 'blob';  // Expect binary response for file downloads
    xhr.timeout = 300000; // 5 minute timeout
    xhr.send(formData);
    
    // Update progress to show processing
    setTimeout(() => {
        updateProgress(50, 'Cropping images...');
    }, 1000);
}

function handleCroppingSuccess(response) {
    hideProcessingModal();
    
    if (response.download_url) {
        // Start download
        const link = document.createElement('a');
        link.href = response.download_url;
        link.download = response.filename || 'cropped_images';
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
    let filename = 'cropped_image';
    if (disposition) {
        const filenameMatch = disposition.match(/filename="(.+)"/);
        if (filenameMatch) {
            filename = filenameMatch[1];
        }
    }
    
    // If no filename from server, create based on original file and format
    if (filename === 'cropped_image' && selectedFiles.length > 0) {
        const outputFormat = document.getElementById('output-format').value;
        const baseName = selectedFiles[0].name.split('.')[0];
        filename = `${baseName}_cropped.${outputFormat}`;
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

function handleCroppingError(error) {
    hideProcessingModal();
    showErrorModal(error);
}

function setupModalControls() {
    // Close buttons
    const closeButtons = document.querySelectorAll('#close-success, #close-error, #close-preview');
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            hideAllModals();
        });
    });
    
    // Reset crop button
    const resetButton = document.getElementById('reset-crop');
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            if (currentCropper) {
                currentCropper.reset();
            }
        });
    }
    
    // Apply crop button
    const applyCropButton = document.getElementById('apply-crop');
    if (applyCropButton) {
        applyCropButton.addEventListener('click', () => {
            if (currentCropper) {
                // Get crop data and store it
                const cropData = currentCropper.getData();
                console.log('Crop data:', cropData);
                
                // Close preview modal
                document.getElementById('preview-modal').classList.add('hidden');
                
                showNotification('Crop settings applied. Submit form to process images.', 'success');
            }
        });
    }
    
    // Close modals when clicking outside
    document.addEventListener('click', (e) => {
        const modals = document.querySelectorAll('.fixed.inset-0');
        modals.forEach(modal => {
            if (e.target === modal && !modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
                
                // Destroy cropper when closing preview modal
                if (modal.id === 'preview-modal' && currentCropper) {
                    currentCropper.destroy();
                    currentCropper = null;
                }
            }
        });
    });
}

function setupProgressTracking() {
    // This will be called during cropping to show progress
    window.updateCroppingProgress = (percent, message) => {
        updateProgress(percent, message);
    };
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Escape key to close modals
        if (e.key === 'Escape') {
            hideAllModals();
            
            // Destroy cropper when closing preview modal
            if (currentCropper) {
                currentCropper.destroy();
                currentCropper = null;
            }
        }
        
        // Ctrl+U to focus file input
        if (e.ctrlKey && e.key === 'u') {
            e.preventDefault();
            const fileInput = document.getElementById('image-files');
            if (fileInput) {
                fileInput.click();
            }
        }
        
        // Arrow keys for cropper navigation
        if (currentCropper && !document.getElementById('preview-modal').classList.contains('hidden')) {
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight' || e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                e.preventDefault();
                const cropBoxData = currentCropper.getCropBoxData();
                const step = e.shiftKey ? 10 : 1;
                
                switch (e.key) {
                    case 'ArrowLeft':
                        cropBoxData.left -= step;
                        break;
                    case 'ArrowRight':
                        cropBoxData.left += step;
                        break;
                    case 'ArrowUp':
                        cropBoxData.top -= step;
                        break;
                    case 'ArrowDown':
                        cropBoxData.top += step;
                        break;
                }
                
                currentCropper.setCropBoxData(cropBoxData);
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
            message.textContent = 'Cropping images... Please wait.';
        }
        
        updateProgress(0, 'Preparing to crop images...');
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
    
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function showErrorModal(errorMessage) {
    const modal = document.getElementById('error-modal');
    const messageElement = document.getElementById('error-message');
    
    if (modal) {
        modal.classList.remove('hidden');
        
        if (messageElement) {
            messageElement.textContent = errorMessage || 'An unexpected error occurred during cropping. Please try again.';
        }
    }
}

function hideAllModals() {
    const modals = document.querySelectorAll('.fixed.inset-0');
    modals.forEach(modal => {
        modal.classList.add('hidden');
    });
    
    // Destroy cropper when hiding preview modal
    if (currentCropper) {
        currentCropper.destroy();
        currentCropper = null;
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

// Enhanced cropping functions for interactive grid overlay
function initializeEnhancedCropping(cropper) {
    createGridOverlay(cropper);
    setupCropInfoDisplay();
    setupGridToggle();
    setupRuleOfThirdsHelpers(cropper);
}

function createGridOverlay(cropper) {
    const container = cropper.getContainerData();
    const cropperContainer = document.querySelector('.cropper-container');
    
    // Create 3x3 grid overlay
    const gridOverlay = document.createElement('div');
    gridOverlay.className = 'crop-grid-overlay';
    gridOverlay.innerHTML = `
        <div class="grid-line grid-line-v-1"></div>
        <div class="grid-line grid-line-v-2"></div>
        <div class="grid-line grid-line-h-1"></div>
        <div class="grid-line grid-line-h-2"></div>
    `;
    
    if (cropperContainer && !cropperContainer.querySelector('.crop-grid-overlay')) {
        cropperContainer.appendChild(gridOverlay);
    }
    
    // Update grid position when crop box changes
    updateGridOverlay(cropper);
}

function updateGridOverlay(cropper) {
    const cropBoxData = cropper.getCropBoxData();
    const gridOverlay = document.querySelector('.crop-grid-overlay');
    
    if (!gridOverlay || !cropBoxData) return;
    
    const { left, top, width, height } = cropBoxData;
    
    // Position the overlay
    gridOverlay.style.left = `${left}px`;
    gridOverlay.style.top = `${top}px`;
    gridOverlay.style.width = `${width}px`;
    gridOverlay.style.height = `${height}px`;
    
    // Position grid lines (rule of thirds)
    const vLine1 = gridOverlay.querySelector('.grid-line-v-1');
    const vLine2 = gridOverlay.querySelector('.grid-line-v-2');
    const hLine1 = gridOverlay.querySelector('.grid-line-h-1');
    const hLine2 = gridOverlay.querySelector('.grid-line-h-2');
    
    if (vLine1) vLine1.style.left = '33.33%';
    if (vLine2) vLine2.style.left = '66.67%';
    if (hLine1) hLine1.style.top = '33.33%';
    if (hLine2) hLine2.style.top = '66.67%';
    
    // Show/hide grid based on setting
    const showGrid = document.getElementById('show-grid')?.checked ?? true;
    gridOverlay.style.opacity = showGrid ? '1' : '0';
}

function setupCropInfoDisplay() {
    const cropperContainer = document.querySelector('.cropper-container');
    
    if (!cropperContainer || cropperContainer.querySelector('.crop-info-display')) {
        return;
    }
    
    // Create crop info display
    const cropInfoDisplay = document.createElement('div');
    cropInfoDisplay.className = 'crop-info-display';
    cropInfoDisplay.innerHTML = `
        <div class="crop-info-item">
            <span class="crop-info-label">Size:</span>
            <span class="crop-info-value" id="crop-size">0 × 0</span>
        </div>
        <div class="crop-info-item">
            <span class="crop-info-label">Position:</span>
            <span class="crop-info-value" id="crop-position">0, 0</span>
        </div>
        <div class="crop-info-item">
            <span class="crop-info-label">Ratio:</span>
            <span class="crop-info-value" id="crop-ratio">1:1</span>
        </div>
    `;
    
    cropperContainer.appendChild(cropInfoDisplay);
}

function updateCropInfo(cropper) {
    const cropData = cropper.getData();
    const cropBoxData = cropper.getCropBoxData();
    
    // Update size display
    const sizeElement = document.getElementById('crop-size');
    if (sizeElement) {
        sizeElement.textContent = `${Math.round(cropData.width)} × ${Math.round(cropData.height)}`;
    }
    
    // Update position display
    const positionElement = document.getElementById('crop-position');
    if (positionElement) {
        positionElement.textContent = `${Math.round(cropData.x)}, ${Math.round(cropData.y)}`;
    }
    
    // Update ratio display
    const ratioElement = document.getElementById('crop-ratio');
    if (ratioElement && cropData.width && cropData.height) {
        const ratio = cropData.width / cropData.height;
        const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);
        const w = Math.round(cropData.width);
        const h = Math.round(cropData.height);
        const divisor = gcd(w, h);
        ratioElement.textContent = `${w / divisor}:${h / divisor}`;
    }
    
    // Update grid overlay
    updateGridOverlay(cropper);
}

function setupGridToggle() {
    const gridToggle = document.getElementById('show-grid');
    if (gridToggle) {
        gridToggle.addEventListener('change', (e) => {
            const gridOverlay = document.querySelector('.crop-grid-overlay');
            if (gridOverlay) {
                gridOverlay.style.opacity = e.target.checked ? '1' : '0';
            }
            
            // Update cropper guides
            if (currentCropper) {
                currentCropper.setGuides(e.target.checked);
            }
        });
    }
}

function setupRuleOfThirdsHelpers(cropper) {
    // Add rule of thirds snap points
    const containerElement = cropper.getContainerData();
    
    // Create snap points for rule of thirds
    const snapPoints = [
        { x: 0.333, y: 0.333 },
        { x: 0.333, y: 0.667 },
        { x: 0.667, y: 0.333 },
        { x: 0.667, y: 0.667 }
    ];
    
    // Listen for crop box movements to provide visual feedback
    const cropperContainer = document.querySelector('.cropper-container');
    if (cropperContainer) {
        cropperContainer.addEventListener('mousemove', (e) => {
            if (document.getElementById('snap-to-grid')?.checked) {
                highlightNearestSnapPoint(e, cropper, snapPoints);
            }
        });
    }
}

function highlightNearestSnapPoint(event, cropper, snapPoints) {
    const cropBoxData = cropper.getCropBoxData();
    const imageData = cropper.getImageData();
    
    if (!cropBoxData || !imageData) return;
    
    const threshold = 20; // pixels
    const rect = cropper.getContainerData();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    
    // Find nearest snap point
    let nearestPoint = null;
    let minDistance = threshold;
    
    snapPoints.forEach(point => {
        const snapX = imageData.left + (imageData.width * point.x);
        const snapY = imageData.top + (imageData.height * point.y);
        
        const distance = Math.sqrt(
            Math.pow(mouseX - snapX, 2) + Math.pow(mouseY - snapY, 2)
        );
        
        if (distance < minDistance) {
            minDistance = distance;
            nearestPoint = { x: snapX, y: snapY };
        }
    });
    
    // Highlight nearest snap point
    highlightSnapPoint(nearestPoint);
}

function highlightSnapPoint(point) {
    // Remove existing highlights
    const existingHighlights = document.querySelectorAll('.snap-point-highlight');
    existingHighlights.forEach(el => el.remove());
    
    if (!point) return;
    
    // Create highlight element
    const highlight = document.createElement('div');
    highlight.className = 'snap-point-highlight';
    highlight.style.left = `${point.x - 5}px`;
    highlight.style.top = `${point.y - 5}px`;
    
    const cropperContainer = document.querySelector('.cropper-container');
    if (cropperContainer) {
        cropperContainer.appendChild(highlight);
        
        // Auto-remove after short delay
        setTimeout(() => {
            if (highlight.parentElement) {
                highlight.remove();
            }
        }, 1000);
    }
}

// Enhanced crop mode functions
function applyCropMode(mode) {
    if (!currentCropper) return;
    
    switch (mode) {
        case 'rule-of-thirds':
            applyRuleOfThirdsCrop();
            break;
        case 'center':
            applyCenterCrop();
            break;
        case 'golden-ratio':
            applyGoldenRatioCrop();
            break;
    }
}

function applyRuleOfThirdsCrop() {
    if (!currentCropper) return;
    
    const imageData = currentCropper.getImageData();
    const cropWidth = imageData.width * 0.8;
    const cropHeight = imageData.height * 0.8;
    
    // Position according to rule of thirds
    const left = imageData.left + (imageData.width * 0.1);
    const top = imageData.top + (imageData.height * 0.1);
    
    currentCropper.setCropBoxData({
        left: left,
        top: top,
        width: cropWidth,
        height: cropHeight
    });
}

function applyCenterCrop() {
    if (!currentCropper) return;
    
    const imageData = currentCropper.getImageData();
    const size = Math.min(imageData.width, imageData.height) * 0.8;
    
    currentCropper.setCropBoxData({
        left: imageData.left + (imageData.width - size) / 2,
        top: imageData.top + (imageData.height - size) / 2,
        width: size,
        height: size
    });
}

function applyGoldenRatioCrop() {
    if (!currentCropper) return;
    
    const imageData = currentCropper.getImageData();
    const goldenRatio = 1.618;
    
    let cropWidth = imageData.width * 0.8;
    let cropHeight = cropWidth / goldenRatio;
    
    // Adjust if height exceeds image bounds
    if (cropHeight > imageData.height * 0.9) {
        cropHeight = imageData.height * 0.8;
        cropWidth = cropHeight * goldenRatio;
    }
    
    currentCropper.setCropBoxData({
        left: imageData.left + (imageData.width - cropWidth) / 2,
        top: imageData.top + (imageData.height - cropHeight) / 2,
        width: cropWidth,
        height: cropHeight
    });
}

// ================================== //
// INLINE CROPPER FUNCTIONALITY      //
// ================================== //

let inlineCropper = null;
let currentInlineFile = null;

function initializeInlineCropper(file) {
    if (!file) return;
    
    currentInlineFile = file;
    const container = document.getElementById('inline-cropper-container');
    const placeholder = document.getElementById('no-image-placeholder');
    const actionButtons = document.getElementById('crop-action-buttons');
    
    if (!container || !placeholder) return;
    
    // Clear existing cropper
    if (inlineCropper) {
        inlineCropper.destroy();
        inlineCropper = null;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Create image element
    const img = document.createElement('img');
    img.style.maxWidth = '100%';
    img.style.maxHeight = '400px';
    
    // Load image
    const reader = new FileReader();
    reader.onload = function(e) {
        img.src = e.target.result;
        container.appendChild(img);
        container.classList.add('has-image');
        
        // Show action buttons
        if (actionButtons) {
            actionButtons.style.display = 'flex';
        }
        
        // Initialize cropper after image loads
        img.onload = function() {
            setTimeout(() => {
                initializeInlineCropperInstance(img);
            }, 100);
        };
    };
    reader.readAsDataURL(file);
}

function initializeInlineCropperInstance(img) {
    const showGrid = document.getElementById('show-grid')?.checked ?? true;
    
    inlineCropper = new Cropper(img, {
        aspectRatio: NaN, // Free crop
        viewMode: 1,
        dragMode: 'move',
        autoCropArea: 0.8,
        restore: false,
        guides: showGrid,
        center: true,
        highlight: false,
        cropBoxMovable: true,
        cropBoxResizable: true,
        toggleDragModeOnDblclick: false,
        responsive: true,
        checkCrossOrigin: false,
        minContainerWidth: 200,
        minContainerHeight: 150,
        ready: function() {
            // Initialize enhanced features for inline cropper
            initializeInlineEnhancedCropping(this.cropper);
            
            // Set initial crop info
            updateInlineCropInfo(this.cropper);
        },
        cropend: function() {
            updateInlineCropInfo(this.cropper);
        },
        cropmove: function() {
            updateInlineCropInfo(this.cropper);
        }
    });
    
    // Set up action button handlers
    setupInlineCropperButtons();
    
    // Set up interactive crop feature handlers
    setupInteractiveCropFeatureHandlers();
}

function initializeInlineEnhancedCropping(cropper) {
    // Create grid overlay for inline cropper
    createInlineGridOverlay(cropper);
    
    // Create info panel
    createInlineCropInfoPanel(cropper);
}

function createInlineGridOverlay(cropper) {
    const containerElement = cropper.getContainerData();
    const cropperContainer = document.querySelector('#inline-cropper-container .cropper-container');
    
    if (!cropperContainer || cropperContainer.querySelector('.crop-grid-overlay')) {
        return;
    }
    
    // Create 3x3 grid overlay
    const gridOverlay = document.createElement('div');
    gridOverlay.className = 'crop-grid-overlay inline-grid-overlay';
    gridOverlay.innerHTML = `
        <div class="grid-line grid-line-v-1"></div>
        <div class="grid-line grid-line-v-2"></div>
        <div class="grid-line grid-line-h-1"></div>
        <div class="grid-line grid-line-h-2"></div>
    `;
    
    cropperContainer.appendChild(gridOverlay);
    
    // Update grid position
    updateInlineGridOverlay(cropper);
}

function updateInlineGridOverlay(cropper) {
    const cropBoxData = cropper.getCropBoxData();
    const gridOverlay = document.querySelector('#inline-cropper-container .crop-grid-overlay');
    
    if (!gridOverlay || !cropBoxData) return;
    
    const { left, top, width, height } = cropBoxData;
    
    // Position the overlay
    gridOverlay.style.left = `${left}px`;
    gridOverlay.style.top = `${top}px`;
    gridOverlay.style.width = `${width}px`;
    gridOverlay.style.height = `${height}px`;
    
    // Position grid lines
    const vLine1 = gridOverlay.querySelector('.grid-line-v-1');
    const vLine2 = gridOverlay.querySelector('.grid-line-v-2');
    const hLine1 = gridOverlay.querySelector('.grid-line-h-1');
    const hLine2 = gridOverlay.querySelector('.grid-line-h-2');
    
    if (vLine1) vLine1.style.left = '33.33%';
    if (vLine2) vLine2.style.left = '66.67%';
    if (hLine1) hLine1.style.top = '33.33%';
    if (hLine2) hLine2.style.top = '66.67%';
    
    // Show/hide grid based on setting
    const showGrid = document.getElementById('show-grid')?.checked ?? true;
    gridOverlay.style.opacity = showGrid ? '1' : '0';
}

function createInlineCropInfoPanel(cropper) {
    const container = document.getElementById('inline-cropper-container');
    
    if (!container || container.querySelector('.crop-info-panel')) {
        return;
    }
    
    // Create info panel
    const infoPanel = document.createElement('div');
    infoPanel.className = 'crop-info-panel inline-crop-info-panel';
    infoPanel.innerHTML = `
        <div class="info-row">
            <span class="info-label">Size:</span>
            <span class="info-value" id="inline-crop-size">0 × 0</span>
        </div>
        <div class="info-row">
            <span class="info-label">Position:</span>
            <span class="info-value" id="inline-crop-position">0, 0</span>
        </div>
        <div class="info-row">
            <span class="info-label">Ratio:</span>
            <span class="info-value" id="inline-crop-ratio">1:1</span>
        </div>
    `;
    
    container.appendChild(infoPanel);
}

function updateInlineCropInfo(cropper) {
    const cropData = cropper.getData();
    
    // Update size display
    const sizeElement = document.getElementById('inline-crop-size');
    if (sizeElement) {
        sizeElement.textContent = `${Math.round(cropData.width)} × ${Math.round(cropData.height)}`;
    }
    
    // Update position display
    const positionElement = document.getElementById('inline-crop-position');
    if (positionElement) {
        positionElement.textContent = `${Math.round(cropData.x)}, ${Math.round(cropData.y)}`;
    }
    
    // Update ratio display
    const ratioElement = document.getElementById('inline-crop-ratio');
    if (ratioElement && cropData.width && cropData.height) {
        const ratio = cropData.width / cropData.height;
        const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);
        const w = Math.round(cropData.width);
        const h = Math.round(cropData.height);
        const divisor = gcd(w, h);
        ratioElement.textContent = `${w / divisor}:${h / divisor}`;
    }
    
    // Update grid overlay
    updateInlineGridOverlay(cropper);
}

function setupInlineCropperButtons() {
    const resetButton = document.getElementById('reset-inline-crop');
    const applyButton = document.getElementById('apply-inline-crop');
    
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            if (inlineCropper) {
                inlineCropper.reset();
                showNotification('Crop area reset successfully', 'success');
            }
        });
    }
    
    if (applyButton) {
        applyButton.addEventListener('click', () => {
            if (inlineCropper) {
                const cropData = inlineCropper.getData();
                showNotification(`Crop applied: ${Math.round(cropData.width)}×${Math.round(cropData.height)} at (${Math.round(cropData.x)}, ${Math.round(cropData.y)})`, 'success');
                // Store crop data for form submission
                storeCropDataForSubmission(cropData);
            }
        });
    }
}

function storeCropDataForSubmission(cropData) {
    // Store the crop data so it can be used when form is submitted
    window.appliedCropData = cropData;
}

function setupInteractiveCropFeatureHandlers() {
    // Grid toggle handler
    const showGridCheckbox = document.getElementById('show-grid');
    if (showGridCheckbox) {
        showGridCheckbox.addEventListener('change', (e) => {
            if (inlineCropper) {
                inlineCropper.setGuides(e.target.checked);
                const gridOverlay = document.querySelector('#inline-cropper-container .crop-grid-overlay');
                if (gridOverlay) {
                    gridOverlay.style.opacity = e.target.checked ? '1' : '0';
                }
            }
        });
    }
    
    // Snap to grid handler (placeholder - could be enhanced)
    const snapToGridCheckbox = document.getElementById('snap-to-grid');
    if (snapToGridCheckbox) {
        snapToGridCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                showNotification('Snap to grid enabled - drag crop box near grid lines', 'info');
            } else {
                showNotification('Snap to grid disabled', 'info');
            }
        });
    }
    
    // Live preview handler - toggles real-time crop updates
    const livePreviewCheckbox = document.getElementById('live-preview');
    if (livePreviewCheckbox) {
        livePreviewCheckbox.addEventListener('change', (e) => {
            if (inlineCropper) {
                if (e.target.checked) {
                    // Enable continuous crop updates
                    inlineCropper.crop();
                    showNotification('Live preview enabled - crop updates in real-time', 'info');
                } else {
                    showNotification('Live preview disabled', 'info');
                }
            }
        });
    }
    
    // Show crop info handler - toggles crop information panel visibility
    const showCropInfoCheckbox = document.getElementById('show-crop-info');
    if (showCropInfoCheckbox) {
        showCropInfoCheckbox.addEventListener('change', (e) => {
            const infoPanel = document.querySelector('#inline-cropper-container .crop-info-panel');
            if (infoPanel) {
                infoPanel.style.display = e.target.checked ? 'block' : 'none';
            }
        });
    }
}

function clearInlineCropper() {
    const container = document.getElementById('inline-cropper-container');
    const placeholder = document.getElementById('no-image-placeholder');
    const actionButtons = document.getElementById('crop-action-buttons');
    
    if (inlineCropper) {
        inlineCropper.destroy();
        inlineCropper = null;
    }
    
    if (container) {
        container.innerHTML = `
            <div class="no-image-placeholder" id="no-image-placeholder">
                <svg class="w-16 h-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 002 2z"></path>
                </svg>
                <p class="text-gray-500 dark:text-gray-400 text-center">
                    Upload an image to see the interactive crop preview
                </p>
            </div>
        `;
        container.classList.remove('has-image');
    }
    
    if (actionButtons) {
        actionButtons.style.display = 'none';
    }
    
    currentInlineFile = null;
}

// Update crop mode functions to work with inline cropper
function applyInlineCropMode(mode) {
    if (!inlineCropper) return;
    
    switch (mode) {
        case 'rule-of-thirds':
            applyInlineRuleOfThirdsCrop();
            break;
        case 'center':
            applyInlineCenterCrop();
            break;
        case 'golden-ratio':
            applyInlineGoldenRatioCrop();
            break;
    }
}

function applyInlineRuleOfThirdsCrop() {
    if (!inlineCropper) return;
    
    const imageData = inlineCropper.getImageData();
    const cropWidth = imageData.width * 0.8;
    const cropHeight = imageData.height * 0.8;
    
    const left = imageData.left + (imageData.width * 0.1);
    const top = imageData.top + (imageData.height * 0.1);
    
    inlineCropper.setCropBoxData({
        left: left,
        top: top,
        width: cropWidth,
        height: cropHeight
    });
}

function applyInlineCenterCrop() {
    if (!inlineCropper) return;
    
    const imageData = inlineCropper.getImageData();
    const size = Math.min(imageData.width, imageData.height) * 0.8;
    
    inlineCropper.setCropBoxData({
        left: imageData.left + (imageData.width - size) / 2,
        top: imageData.top + (imageData.height - size) / 2,
        width: size,
        height: size
    });
}

function applyInlineGoldenRatioCrop() {
    if (!inlineCropper) return;
    
    const imageData = inlineCropper.getImageData();
    const goldenRatio = 1.618;
    
    let cropWidth = imageData.width * 0.8;
    let cropHeight = cropWidth / goldenRatio;
    
    if (cropHeight > imageData.height * 0.9) {
        cropHeight = imageData.height * 0.8;
        cropWidth = cropHeight * goldenRatio;
    }
    
    inlineCropper.setCropBoxData({
        left: imageData.left + (imageData.width - cropWidth) / 2,
        top: imageData.top + (imageData.height - cropHeight) / 2,
        width: cropWidth,
        height: cropHeight
    });
}

// Global functions to make them accessible from HTML
window.clearFileSelection = clearFileSelection;
window.removeImageFromSelection = removeImageFromSelection;
window.showCropPreview = showCropPreview;
window.applyCropMode = applyInlineCropMode; // Use inline version for quick crop buttons
window.initializeEnhancedCropping = initializeEnhancedCropping;
window.updateCropInfo = updateCropInfo;
window.initializeInlineCropper = initializeInlineCropper;
window.clearInlineCropper = clearInlineCropper;
