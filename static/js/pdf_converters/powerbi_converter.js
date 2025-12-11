// PowerBI Converter JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
        });
    });
    
    // File upload handling
    setupFileUpload('basic-upload-area', 'basic-file');
    setupFileUpload('advanced-upload-area', 'advanced-file');
    
    // Advanced form handlers
    setupAdvancedOptions();
    
    // Form submission handlers
    setupFormSubmission();
    
    // Progress tracking
    initProgressTracking();
});

function setupFileUpload(areaId, inputId) {
    const uploadArea = document.getElementById(areaId);
    const fileInput = document.getElementById(inputId);
    
    if (!uploadArea || !fileInput) return;
    
    // Click to upload
    uploadArea.addEventListener('click', (e) => {
        // Prevent double triggering when clicking on label
        if (e.target.tagName.toLowerCase() === 'label' || e.target.closest('label')) {
            return;
        }
        fileInput.click();
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].name.toLowerCase().endsWith('.pbix')) {
            fileInput.files = files;
            updateUploadArea(uploadArea, files[0].name);
            validateFileSize(files[0]);
        } else {
            showNotification('Please select a PowerBI (.pbix) file', 'error');
        }
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            updateUploadArea(uploadArea, file.name);
            validateFileSize(file);
        }
    });
}

function updateUploadArea(uploadArea, filename) {
    uploadArea.classList.add('file-selected');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    
    uploadText.textContent = `Selected: ${filename}`;
    uploadSubtext.textContent = 'Click to change file';
}

function validateFileSize(file) {
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
        showNotification('File size exceeds 50MB limit. Please select a smaller file.', 'error');
        return false;
    }
    return true;
}

function setupAdvancedOptions() {
    // Export all checkbox handler
    const exportAllCheckbox = document.getElementById('export-all');
    const pageRangeInput = document.getElementById('page-range');
    
    if (exportAllCheckbox && pageRangeInput) {
        exportAllCheckbox.addEventListener('change', (e) => {
            pageRangeInput.disabled = e.target.checked;
            if (e.target.checked) {
                pageRangeInput.value = '';
            }
        });
    }
    
    // Watermark checkbox handler
    const watermarkCheckbox = document.getElementById('add-watermark');
    const watermarkText = document.getElementById('watermark-text');
    const watermarkOpacity = document.getElementById('watermark-opacity');
    
    if (watermarkCheckbox) {
        watermarkCheckbox.addEventListener('change', (e) => {
            const disabled = !e.target.checked;
            if (watermarkText) watermarkText.disabled = disabled;
            if (watermarkOpacity) watermarkOpacity.disabled = disabled;
            
            if (!e.target.checked) {
                if (watermarkText) watermarkText.value = '';
            }
        });
    }
    
    // Password checkbox handler
    const passwordCheckbox = document.getElementById('add-password');
    const passwordInput = document.getElementById('pdf-password');
    
    if (passwordCheckbox && passwordInput) {
        passwordCheckbox.addEventListener('change', (e) => {
            passwordInput.disabled = !e.target.checked;
            if (!e.target.checked) {
                passwordInput.value = '';
            }
        });
    }
}

function setupFormSubmission() {
    const basicForm = document.getElementById('basic-form');
    const advancedForm = document.getElementById('advanced-form');
    
    if (basicForm) {
        basicForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleFormSubmission(basicForm, 'basic');
        });
    }
    
    if (advancedForm) {
        advancedForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleFormSubmission(advancedForm, 'advanced');
        });
    }
}

async function handleFormSubmission(form, mode) {
    const fileInput = form.querySelector('input[type="file"]');
    
    if (!fileInput.files.length) {
        showNotification('Please select a PowerBI file', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    if (!validateFileSize(file)) {
        return;
    }
    
    // Show loading overlay
    showLoadingOverlay(true);
    updateProgressText('Uploading PowerBI file...');
    
    try {
        const formData = new FormData(form);
        
        const response = await fetch('/convert/powerbi-to-pdf/', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Check if response is a PDF file or error message
        const contentType = response.headers.get('Content-Type');
        
        if (contentType && contentType.includes('application/pdf')) {
            // Success - handle PDF download
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            // Create download link
            const a = document.createElement('a');
            a.href = url;
            a.download = file.name.replace('.pbix', '_converted.pdf');
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            updateProgressText('Conversion completed successfully!');
            showNotification('PowerBI file converted to PDF successfully!', 'success');
        } else {
            // Error response
            const result = await response.json();
            throw new Error(result.error || 'Conversion failed');
        }
        
    } catch (error) {
        console.error('Conversion error:', error);
        updateProgressText('Conversion failed');
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        // Hide loading overlay after a short delay
        setTimeout(() => {
            showLoadingOverlay(false);
        }, 2000);
    }
}

function initProgressTracking() {
    // This could be enhanced to show real-time progress
    // For now, it provides basic status updates
}

function updateProgressText(text) {
    const progressText = document.getElementById('progress-text');
    if (progressText) {
        progressText.textContent = text;
    }
}

function showLoadingOverlay(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 max-w-sm p-4 rounded-lg shadow-lg z-50 ${getNotificationClasses(type)}`;
    notification.innerHTML = `
        <div class="flex items-center">
            <div class="flex-shrink-0">
                ${getNotificationIcon(type)}
            </div>
            <div class="ml-3">
                <p class="text-sm font-medium">${message}</p>
            </div>
            <div class="ml-4 flex-shrink-0">
                <button class="inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2" onclick="this.parentElement.parentElement.parentElement.remove()">
                    <span class="sr-only">Dismiss</span>
                    <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                    </svg>
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

function getNotificationClasses(type) {
    switch (type) {
        case 'success':
            return 'bg-green-50 border border-green-200 text-green-800 dark:bg-green-800 dark:border-green-700 dark:text-green-100';
        case 'error':
            return 'bg-red-50 border border-red-200 text-red-800 dark:bg-red-800 dark:border-red-700 dark:text-red-100';
        case 'warning':
            return 'bg-yellow-50 border border-yellow-200 text-yellow-800 dark:bg-yellow-800 dark:border-yellow-700 dark:text-yellow-100';
        default:
            return 'bg-blue-50 border border-blue-200 text-blue-800 dark:bg-blue-800 dark:border-blue-700 dark:text-blue-100';
    }
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success':
            return '<svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path></svg>';
        case 'error':
            return '<svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path></svg>';
        case 'warning':
            return '<svg class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>';
        default:
            return '<svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path></svg>';
    }
}