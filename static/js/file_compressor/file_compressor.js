// File Compressor JavaScript functionality
// Based on Image Converter with compression-specific enhancements

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the File Compressor
    initializeFileCompressor();
});

function initializeFileCompressor() {
    // File upload handling (supports multiple files)
    setupFileUpload('compressor-upload-area', 'compressor-files');
    
    // Form submission
    setupFormSubmission();
    
    // Compression mode selector
    setupCompressionModeSelector();
    
    // Quality settings
    setupQualitySettings();
    
    // Advanced options
    setupAdvancedOptions();
    
    // Modal controls
    setupModalControls();
    
    // Progress tracking
    setupProgressTracking();
    
    // Keyboard shortcuts
    setupKeyboardShortcuts();
    
    // File preview functionality
    setupFilePreview();
    
    // Compression comparison
    setupCompressionComparison();
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
                showNotification('Invalid file types. Please select supported file formats.', 'error');
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
    
    return isValidExtension;
}

function handleMultipleFileSelection(files, uploadArea) {
    // Check total file count (limit to 50 files for batch processing)
    if (files.length > 50) {
        showNotification('Too many files selected. Maximum 50 files allowed for batch processing.', 'error');
        return;
    }
    
    const maxSize = 1024 * 1024 * 1024; // 1GB per file
    const validFiles = [];
    const invalidFiles = [];
    
    files.forEach(file => {
        // Check file size
        if (file.size > maxSize) {
            invalidFiles.push(`${file.name} (exceeds 1GB limit)`);
            return;
        }
        
        // Validate file types
        if (!validateFileType(file)) {
            invalidFiles.push(`${file.name} (unsupported format)`);
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
    
    // Show file previews
    showFilePreviews(validFiles, uploadArea);
    
    // Enable compression estimation
    estimateCompressionSavings(validFiles);
}

function validateFileType(file) {
    // Supported file types for compression
    const supportedTypes = [
        // Images
        'image/jpeg', 'image/jpg', 'image/png', 'image/webp',
        // Documents
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        // Videos
        'video/mp4', 'video/avi', 'video/x-msvideo', 'video/x-matroska',
        // Archives
        'application/zip', 'application/x-rar-compressed'
    ];
    
    if (supportedTypes.includes(file.type)) {
        return true;
    }
    
    // Check file extension as fallback
    const supportedExtensions = [
        'pdf', 'jpg', 'jpeg', 'png', 'webp', 'mp4', 'avi', 'mkv', 
        'zip', 'rar', 'docx', 'pptx'
    ];
    const extension = file.name.toLowerCase().split('.').pop();
    
    return supportedExtensions.includes(extension);
}

function updateUploadAreaDisplay(uploadArea, files) {
    uploadArea.classList.add('files-selected');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    
    if (uploadText && uploadSubtext) {
        const fileCount = files.length;
        const totalSize = files.reduce((sum, file) => sum + file.size, 0);
        
        uploadText.textContent = `${fileCount} file${fileCount > 1 ? 's' : ''} selected`;
        uploadSubtext.innerHTML = `Total size: ${formatFileSize(totalSize)} • Click to change files<br>
                                  <small class="text-gray-400">Ready for compression</small>`;
    }
}

function showFilePreviews(files, uploadArea) {
    // Remove existing preview grid
    const existingGrid = uploadArea.querySelector('.file-preview-grid');
    if (existingGrid) {
        existingGrid.remove();
    }
    
    // Create preview grid
    const previewGrid = document.createElement('div');
    previewGrid.className = 'file-preview-grid';
    
    files.forEach((file, index) => {
        const previewItem = createFilePreviewItem(file, index);
        previewGrid.appendChild(previewItem);
    });
    
    uploadArea.appendChild(previewGrid);
}

function createFilePreviewItem(file, index) {
    const item = document.createElement('div');
    item.className = 'file-preview-item';
    item.dataset.fileIndex = index;
    
    const fileType = getFileTypeCategory(file);
    const icon = getFileTypeIcon(fileType);
    
    item.innerHTML = `
        <div class="file-preview-thumbnail">
            ${icon}
        </div>
        <div class="file-preview-info">
            <div class="file-preview-name">${truncateFileName(file.name, 20)}</div>
            <div class="file-preview-size">${formatFileSize(file.size)}</div>
            <div class="file-preview-type">${fileType}</div>
        </div>
        <button type="button" class="file-remove-btn" title="Remove file">×</button>
    `;
    
    // Add remove functionality
    const removeBtn = item.querySelector('.file-remove-btn');
    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        removeFileFromSelection(index);
    });
    
    // Add click to preview functionality
    item.addEventListener('click', () => {
        showFilePreview(file, index);
    });
    
    return item;
}

function getFileTypeCategory(file) {
    const extension = file.name.toLowerCase().split('.').pop();
    
    if (['jpg', 'jpeg', 'png', 'webp'].includes(extension)) {
        return 'IMAGE';
    } else if (['pdf'].includes(extension)) {
        return 'PDF';
    } else if (['docx', 'pptx'].includes(extension)) {
        return 'DOC';
    } else if (['mp4', 'avi', 'mkv'].includes(extension)) {
        return 'VIDEO';
    } else if (['zip', 'rar'].includes(extension)) {
        return 'ARCHIVE';
    }
    
    return 'FILE';
}

function getFileTypeIcon(type) {
    const icons = {
        'IMAGE': '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>',
        'PDF': '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>',
        'DOC': '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>',
        'VIDEO': '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>',
        'ARCHIVE': '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>',
        'FILE': '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>'
    };
    
    return icons[type] || icons['FILE'];
}

function removeFileFromSelection(index) {
    const fileInput = document.getElementById('compressor-files');
    const uploadArea = document.getElementById('compressor-upload-area');
    
    if (!fileInput || !uploadArea) return;
    
    // Create new file list without the removed file
    const dt = new DataTransfer();
    const currentFiles = Array.from(fileInput.files);
    
    currentFiles.forEach((file, i) => {
        if (i !== index) {
            dt.items.add(file);
        }
    });
    
    fileInput.files = dt.files;
    
    // Update display
    if (dt.files.length > 0) {
        handleMultipleFileSelection(Array.from(dt.files), uploadArea);
    } else {
        resetUploadArea(uploadArea);
    }
}

function resetUploadArea(uploadArea) {
    uploadArea.classList.remove('files-selected');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    const previewGrid = uploadArea.querySelector('.file-preview-grid');
    
    if (uploadText) {
        uploadText.textContent = 'Drop your files here or click to browse';
    }
    
    if (uploadSubtext) {
        uploadSubtext.innerHTML = 'PDFs, Images, Videos, Archives supported (Max 1GB each)<br><small class="text-gray-400">Batch processing available for multiple files</small>';
    }
    
    if (previewGrid) {
        previewGrid.remove();
    }
}

function setupCompressionModeSelector() {
    const qualityMode = document.getElementById('mode-quality');
    const targetMode = document.getElementById('mode-target');
    const qualitySettings = document.getElementById('quality-settings');
    const targetSettings = document.getElementById('target-settings');
    
    if (!qualityMode || !targetMode) return;
    
    function toggleCompressionMode() {
        if (qualityMode.checked) {
            qualitySettings.style.display = 'block';
            targetSettings.style.display = 'none';
        } else if (targetMode.checked) {
            qualitySettings.style.display = 'none';
            targetSettings.style.display = 'block';
        }
    }
    
    qualityMode.addEventListener('change', toggleCompressionMode);
    targetMode.addEventListener('change', toggleCompressionMode);
    
    // Initial setup
    toggleCompressionMode();
}

function setupQualitySettings() {
    const customQuality = document.getElementById('quality-custom');
    const customSlider = document.getElementById('custom-quality-slider');
    const qualitySlider = document.getElementById('quality-slider');
    const qualityValue = document.getElementById('quality-value');
    
    if (!customQuality || !customSlider || !qualitySlider || !qualityValue) return;
    
    // Toggle custom quality slider
    function toggleCustomSlider() {
        if (customQuality.checked) {
            customSlider.style.display = 'block';
        } else {
            customSlider.style.display = 'none';
        }
    }
    
    customQuality.addEventListener('change', toggleCustomSlider);
    
    // Update quality value display
    qualitySlider.addEventListener('input', () => {
        qualityValue.textContent = `${qualitySlider.value}%`;
    });
    
    // Initialize
    toggleCustomSlider();
    qualityValue.textContent = `${qualitySlider.value}%`;
}

function setupAdvancedOptions() {
    // Password protection checkbox and settings
    const passwordProtection = document.getElementById('password-protection');
    const passwordSettings = document.getElementById('password-settings');
    
    if (passwordProtection && passwordSettings) {
    passwordProtection.addEventListener('change', () => {
        if (passwordProtection.checked) {
            passwordSettings.style.display = 'block';
            // Add visual indication that protection is enabled
            const passwordInput = document.getElementById('compression-password');
            if (passwordInput) {
                passwordInput.placeholder = 'Enter password for file protection';
                passwordInput.classList.add('border-green-500', 'focus:ring-green-500');
            }
            showNotification('✅ Password protection enabled. Files will be secured with your password.', 'info');
        } else {
            passwordSettings.style.display = 'none';
            // Clear password field and visual indicators when disabled
            const passwordInput = document.getElementById('compression-password');
            if (passwordInput) {
                passwordInput.value = '';
                passwordInput.placeholder = 'Enter secure password';
                passwordInput.classList.remove('border-green-500', 'focus:ring-green-500');
            }
        }
    });
    }
    
    // AI optimization checkbox - add visual feedback
    const aiOptimization = document.getElementById('ai-optimization');
    if (aiOptimization) {
        aiOptimization.addEventListener('change', () => {
            console.log(`AI Optimization: ${aiOptimization.checked ? 'Enabled' : 'Disabled'}`);
            updateAdvancedOptionFeedback('ai-optimization', aiOptimization.checked);
        });
    }
    
    // Remove metadata checkbox
    const removeMetadata = document.getElementById('remove-metadata');
    if (removeMetadata) {
        removeMetadata.addEventListener('change', () => {
            console.log(`Remove Metadata: ${removeMetadata.checked ? 'Enabled' : 'Disabled'}`);
            updateAdvancedOptionFeedback('remove-metadata', removeMetadata.checked);
        });
    }
    
    // Lossless compression checkbox
    const losslessMode = document.getElementById('lossless-mode');
    if (losslessMode) {
        losslessMode.addEventListener('change', () => {
            console.log(`Lossless Mode: ${losslessMode.checked ? 'Enabled' : 'Disabled'}`);
            updateAdvancedOptionFeedback('lossless-mode', losslessMode.checked);
            
            // Show warning if lossless mode conflicts with target size
            if (losslessMode.checked) {
                const targetMode = document.getElementById('mode-target');
                if (targetMode && targetMode.checked) {
                    showNotification('Note: Lossless compression may not achieve exact target sizes.', 'warning');
                }
            }
        });
    }
    
    // Initialize checkbox states
    initializeAdvancedOptions();
}

function updateAdvancedOptionFeedback(optionId, isEnabled) {
    // Add visual feedback for checkbox state changes
    const checkbox = document.getElementById(optionId);
    const label = checkbox ? checkbox.closest('div').querySelector('label') : null;
    
    if (label) {
        if (isEnabled) {
            label.classList.add('text-purple-600', 'font-medium');
            label.classList.remove('text-gray-700', 'dark:text-gray-300');
        } else {
            label.classList.remove('text-purple-600', 'font-medium');
            label.classList.add('text-gray-700', 'dark:text-gray-300');
        }
    }
}

function initializeAdvancedOptions() {
    // Set initial states and visual feedback for all checkboxes
    const checkboxes = [
        'ai-optimization',
        'remove-metadata', 
        'lossless-mode',
        'password-protection'
    ];
    
    checkboxes.forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox) {
            updateAdvancedOptionFeedback(id, checkbox.checked);
        }
    });
}

function setupFormSubmission() {
    const form = document.getElementById('compressor-form');
    
    if (!form) return;
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const fileInput = document.getElementById('compressor-files');
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            showNotification('Please select files to compress.', 'error');
            return;
        }
        
        // Show processing modal
        showProcessingModal();
        
        // Submit the form using FormData
        const formData = new FormData(form);
        
        // Explicitly add advanced options to ensure they're included
        const advancedOptions = collectAdvancedOptions();
        Object.entries(advancedOptions).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                formData.set(key, value);
            }
        });
        
        console.log('Submitting compression with advanced options:', advancedOptions);
        
        fetch('/file-compressor/compress', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            hideProcessingModal();
            
            if (data.success) {
                // Check for password protection status and notify user
                if (data.processed_files) {
                    let passwordProtectedFiles = [];
                    data.processed_files.forEach(file => {
                        if (file.password_protected) {
                            passwordProtectedFiles.push(file);
                            console.log(`✅ Password protection applied to: ${file.original_filename}`);
                            console.log(`   Protection method: ${file.protection_method}`);
                            if (file.password_hint) {
                                console.log(`   Password hint: ${file.password_hint}`);
                            }
                        }
                    });
                    
                    // Show notification if files were password protected
                    if (passwordProtectedFiles.length > 0) {
                        const fileNames = passwordProtectedFiles.map(f => f.original_filename).join(', ');
                        showNotification(
                            `✅ Password protection applied to ${passwordProtectedFiles.length} file(s): ${fileNames}`, 
                            'success'
                        );
                    }
                }
                showCompressionResults(data);
            } else {
                showError(data.error || 'Compression failed');
            }
        })
        .catch(error => {
            hideProcessingModal();
            console.error('Compression error:', error);
            showError(`Compression failed: ${error.message}`);
        });
    });
}

function collectAdvancedOptions() {
    // Collect all advanced options checkbox states and other settings
    const options = {};
    
    // Collect checkbox states
    const aiOptimization = document.getElementById('ai-optimization');
    const removeMetadata = document.getElementById('remove-metadata');
    const losslessMode = document.getElementById('lossless-mode');
    const passwordProtection = document.getElementById('password-protection');
    
    // Set checkbox values (send true/false explicitly)
    options['ai_optimization'] = aiOptimization ? aiOptimization.checked : false;
    options['remove_metadata'] = removeMetadata ? removeMetadata.checked : false;
    options['lossless_mode'] = losslessMode ? losslessMode.checked : false;
    options['password_protection'] = passwordProtection ? passwordProtection.checked : false;
    
    // If password protection is enabled, include password
    if (passwordProtection && passwordProtection.checked) {
        const passwordInput = document.getElementById('compression-password');
        if (passwordInput && passwordInput.value.trim()) {
            options['password'] = passwordInput.value.trim();
        }
    }
    
    // Collect compression mode and settings
    const qualityMode = document.getElementById('mode-quality');
    const targetMode = document.getElementById('mode-target');
    
    if (qualityMode && qualityMode.checked) {
        options['compression_mode'] = 'quality_based';
        
        // Get quality setting
        const customQuality = document.getElementById('quality-custom');
        if (customQuality && customQuality.checked) {
            options['quality_level'] = 'custom';
            const qualitySlider = document.getElementById('quality-slider');
            if (qualitySlider) {
                options['custom_quality'] = parseInt(qualitySlider.value);
            }
        } else {
            // Get selected preset quality
            const qualityPresets = document.querySelectorAll('input[name="quality_level"]:checked');
            if (qualityPresets.length > 0) {
                options['quality_level'] = qualityPresets[0].value;
            }
        }
    } else if (targetMode && targetMode.checked) {
        options['compression_mode'] = 'target_size';
        
        const targetSizeInput = document.getElementById('target-size');
        const targetUnitSelect = document.getElementById('target-unit');
        
        if (targetSizeInput && targetSizeInput.value) {
            options['target_size'] = parseFloat(targetSizeInput.value);
            options['target_unit'] = targetUnitSelect ? targetUnitSelect.value : 'KB';
        }
    }
    
    return options;
}

function setupModalControls() {
    // Preview modal
    const previewModal = document.getElementById('preview-modal');
    const closePreview = document.getElementById('close-preview');
    const cancelCompression = document.getElementById('cancel-compression');
    const confirmCompression = document.getElementById('confirm-compression');
    
    if (closePreview) {
        closePreview.addEventListener('click', () => {
            hideModal(previewModal);
        });
    }
    
    if (cancelCompression) {
        cancelCompression.addEventListener('click', () => {
            hideModal(previewModal);
        });
    }
    
    // Success modal
    const successModal = document.getElementById('success-modal');
    const closeSuccess = document.getElementById('close-success');
    const downloadAgain = document.getElementById('download-again');
    
    if (closeSuccess) {
        closeSuccess.addEventListener('click', () => {
            hideModal(successModal);
        });
    }
    
    if (downloadAgain) {
        downloadAgain.addEventListener('click', () => {
            // Trigger download again
            triggerDownload();
        });
    }
    
    // Error modal
    const errorModal = document.getElementById('error-modal');
    const closeError = document.getElementById('close-error');
    
    if (closeError) {
        closeError.addEventListener('click', () => {
            hideModal(errorModal);
        });
    }
    
    // Close modals on outside click
    [previewModal, successModal, errorModal].forEach(modal => {
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    hideModal(modal);
                }
            });
        }
    });
}

function setupProgressTracking() {
    // Progress tracking will be handled during form submission
    // This function sets up any progress-related event listeners
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + Enter to submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            const submitButton = document.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.click();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const visibleModal = document.querySelector('.fixed:not(.hidden)');
            if (visibleModal) {
                hideModal(visibleModal);
            }
        }
    });
}

function setupFilePreview() {
    // File preview functionality for supported file types
    // This will be implemented when a user clicks on a file preview item
}

function setupCompressionComparison() {
    // Compression comparison functionality
    // This will show before/after previews for images
}

// Utility functions

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function truncateFileName(filename, maxLength) {
    if (filename.length <= maxLength) return filename;
    
    const extension = filename.split('.').pop();
    const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.'));
    const truncatedName = nameWithoutExt.substring(0, maxLength - extension.length - 4) + '...';
    
    return truncatedName + '.' + extension;
}

function estimateCompressionSavings(files) {
    // Estimate potential compression savings based on file types
    let estimatedSavings = 0;
    
    files.forEach(file => {
        const type = getFileTypeCategory(file);
        let savingsPercentage = 0;
        
        switch (type) {
            case 'IMAGE':
                savingsPercentage = 0.3; // 30% average for images
                break;
            case 'PDF':
                savingsPercentage = 0.4; // 40% average for PDFs
                break;
            case 'VIDEO':
                savingsPercentage = 0.15; // 15% average for videos
                break;
            case 'DOC':
                savingsPercentage = 0.2; // 20% average for documents
                break;
            default:
                savingsPercentage = 0.25; // 25% average for other files
        }
        
        estimatedSavings += file.size * savingsPercentage;
    });
    
    // Show estimation in UI
    showEstimatedSavings(estimatedSavings);
}

function showEstimatedSavings(savings) {
    // Create or update savings estimation display
    const uploadArea = document.getElementById('compressor-upload-area');
    let estimationDisplay = uploadArea.querySelector('.compression-estimation');
    
    if (!estimationDisplay) {
        estimationDisplay = document.createElement('div');
        estimationDisplay.className = 'compression-estimation mt-4 p-3 bg-purple-50 dark:bg-purple-900 rounded-lg border border-purple-200 dark:border-purple-700';
        uploadArea.appendChild(estimationDisplay);
    }
    
    estimationDisplay.innerHTML = `
        <div class="flex items-center text-purple-700 dark:text-purple-300">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
            <span class="font-medium">Estimated space savings: ${formatFileSize(savings)}</span>
        </div>
    `;
}

function showProcessingModal() {
    const modal = document.getElementById('processing-modal');
    if (modal) {
        modal.classList.remove('hidden');
        updateProgress(0, 'Initializing compression...');
        
        // Simulate progress updates
        simulateProgressUpdates();
    }
}

function hideProcessingModal() {
    const modal = document.getElementById('processing-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function simulateProgressUpdates() {
    const stages = [
        'Analyzing files...',
        'Optimizing compression settings...',
        'Processing files...',
        'Applying compression algorithms...',
        'Finalizing output...'
    ];
    
    let currentStage = 0;
    let progress = 0;
    
    const interval = setInterval(() => {
        progress += Math.random() * 20;
        if (progress > 95) {
            clearInterval(interval);
            return;
        }
        
        if (progress > (currentStage + 1) * 20 && currentStage < stages.length - 1) {
            currentStage++;
        }
        
        updateProgress(Math.min(progress, 95), stages[currentStage]);
    }, 1000);
}

function updateProgress(percentage, message) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const processingMessage = document.getElementById('processing-message');
    
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
    }
    
    if (progressText) {
        progressText.textContent = `${Math.round(percentage)}% complete`;
    }
    
    if (processingMessage) {
        processingMessage.textContent = message;
    }
}

function showCompressionResults(data) {
    const modal = document.getElementById('success-modal');
    const statsContainer = document.getElementById('compression-stats');
    
    if (modal && statsContainer) {
        // Populate compression statistics
        statsContainer.innerHTML = generateCompressionStatsHTML(data.stats);
        
        // Store download information
        window.compressionResults = data;
        
        showModal(modal);
        
        // Auto-trigger download using a more reliable method
        if (data.download_url) {
            setTimeout(() => {
                triggerReliableDownload(data.download_url);
            }, 1000);
        }
    }
}

function generateCompressionStatsHTML(stats) {
    return `
        <div class="compression-stats-grid">
            <div class="compression-stat-card">
                <div class="stat-value">${stats.files_processed || 0}</div>
                <div class="stat-label">Files Processed</div>
            </div>
            <div class="compression-stat-card">
                <div class="stat-value">${formatFileSize(stats.original_size || 0)}</div>
                <div class="stat-label">Original Size</div>
            </div>
            <div class="compression-stat-card">
                <div class="stat-value">${formatFileSize(stats.compressed_size || 0)}</div>
                <div class="stat-label">Compressed Size</div>
            </div>
            <div class="compression-stat-card">
                <div class="stat-value">${stats.compression_ratio || 0}%</div>
                <div class="stat-label">Compression Ratio</div>
                <div class="stat-improvement">Saved ${formatFileSize((stats.original_size || 0) - (stats.compressed_size || 0))}</div>
            </div>
        </div>
        <p class="text-gray-600 dark:text-gray-300 mt-4">
            Your files have been successfully compressed! The download will start automatically.
        </p>
    `;
}

function showError(message) {
    const modal = document.getElementById('error-modal');
    const errorMessage = document.getElementById('error-message');
    
    if (modal && errorMessage) {
        errorMessage.textContent = message;
        showModal(modal);
    }
}

function showModal(modal) {
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function hideModal(modal) {
    if (modal) {
        modal.classList.add('hidden');
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 ${getNotificationClasses(type)}`;
    notification.innerHTML = `
        <div class="flex items-center">
            ${getNotificationIcon(type)}
            <span class="ml-2">${message}</span>
            <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">×</button>
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

function getNotificationClasses(type) {
    const classes = {
        'success': 'bg-green-600 text-white',
        'error': 'bg-red-600 text-white',
        'warning': 'bg-yellow-600 text-white',
        'info': 'bg-blue-600 text-white'
    };
    
    return classes[type] || classes['info'];
}

function getNotificationIcon(type) {
    const icons = {
        'success': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
        'error': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>',
        'warning': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>',
        'info': '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
    };
    
    return icons[type] || icons['info'];
}

function triggerDownload() {
    if (window.compressionResults && window.compressionResults.download_url) {
        triggerReliableDownload(window.compressionResults.download_url);
    }
}

function triggerReliableDownload(downloadUrl) {
    // Use fetch to download the file while maintaining session context
    fetch(downloadUrl, {
        method: 'GET',
        credentials: 'same-origin', // Include cookies/session data
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Get filename from Content-Disposition header or URL
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'download';
        if (contentDisposition && contentDisposition.includes('filename=')) {
            filename = contentDisposition.split('filename=')[1].replace(/"/g, '');
        } else {
            // Extract filename from URL
            const urlParts = downloadUrl.split('/');
            if (urlParts.length > 0) {
                filename = `compressed_files_${urlParts[urlParts.length - 1]}.zip`;
            }
        }
        
        return response.blob().then(blob => ({ blob, filename }));
    })
    .then(({ blob, filename }) => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
        
        console.log('Download completed successfully');
    })
    .catch(error => {
        console.error('Download failed:', error);
        showError(`Download failed: ${error.message}`);
    });
}

function showFilePreview(file, index) {
    // Show file preview modal for supported file types
    const modal = document.getElementById('preview-modal');
    const previewContent = document.getElementById('preview-content');
    
    if (!modal || !previewContent) return;
    
    const fileType = getFileTypeCategory(file);
    let previewHTML = '';
    
    if (fileType === 'IMAGE' && file.size < 10 * 1024 * 1024) { // Only preview images under 10MB
        const objectURL = URL.createObjectURL(file);
        previewHTML = `
            <div class="compression-comparison">
                <div class="comparison-side">
                    <h4>
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                        </svg>
                        Original
                    </h4>
                    <div class="comparison-preview">
                        <img src="${objectURL}" alt="Original" />
                    </div>
                    <div class="comparison-details">
                        <div><span>Size:</span> <span>${formatFileSize(file.size)}</span></div>
                        <div><span>Type:</span> <span>${file.type}</span></div>
                    </div>
                </div>
                <div class="comparison-side">
                    <h4>
                        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path>
                        </svg>
                        After Compression
                    </h4>
                    <div class="comparison-preview">
                        <div class="flex items-center justify-center h-full text-gray-500">
                            <svg class="w-8 h-8 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                            Preview after compression
                        </div>
                    </div>
                    <div class="comparison-details">
                        <div><span>Estimated Size:</span> <span>${formatFileSize(file.size * 0.7)}</span></div>
                        <div><span>Quality:</span> <span>High</span></div>
                    </div>
                </div>
            </div>
        `;
    } else {
        previewHTML = `
            <div class="text-center p-8">
                <div class="text-6xl text-gray-400 mb-4">${getFileTypeIcon(fileType)}</div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">${file.name}</h3>
                <p class="text-gray-600 dark:text-gray-300 mb-4">
                    ${formatFileSize(file.size)} • ${fileType}
                </p>
                <div class="bg-gray-100 dark:bg-gray-700 rounded-lg p-4">
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                        This file will be compressed using advanced algorithms optimized for ${fileType.toLowerCase()} files.
                        Estimated compression: ${Math.round(Math.random() * 30 + 20)}%
                    </p>
                </div>
            </div>
        `;
    }
    
    previewContent.innerHTML = previewHTML;
    showModal(modal);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeFileCompressor);
} else {
    initializeFileCompressor();
}