// Text OCR Converter JavaScript Handler

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('text-ocr-form');
    const uploadArea = document.getElementById('text-ocr-upload-area');
    const fileInput = document.getElementById('text-ocr-file');
    const processingModal = document.getElementById('processing-modal');
    const successModal = document.getElementById('success-modal');
    const errorModal = document.getElementById('error-modal');
    const errorMessage = document.getElementById('error-message');
    const closeSuccessBtn = document.getElementById('close-success');
    const closeErrorBtn = document.getElementById('close-error');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    // File upload handling
    setupFileUpload();

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        await submitForm();
    });

    // Modal close buttons
    closeSuccessBtn.addEventListener('click', function() {
        successModal.classList.add('hidden');
        form.reset();
    });

    closeErrorBtn.addEventListener('click', function() {
        errorModal.classList.add('hidden');
    });

    function setupFileUpload() {
        // Drag and drop
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', function() {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelected(files[0]);
            }
        });

        // File input change
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                handleFileSelected(file);
            }
        });
    }

    function handleFileSelected(file) {
        if (validateFile(file)) {
            displaySelectedFile(file);
        } else {
            fileInput.value = '';
            clearSelectedFileDisplay();
        }
    }

    function displaySelectedFile(file) {
        // Create or update file info display
        let fileInfoDiv = document.getElementById('file-info-display');
        
        if (!fileInfoDiv) {
            fileInfoDiv = document.createElement('div');
            fileInfoDiv.id = 'file-info-display';
            uploadArea.parentElement.insertBefore(fileInfoDiv, uploadArea.nextSibling);
        }

        // Format file size
        const fileSize = file.size;
        let fileSizeStr = '';
        if (fileSize < 1024) {
            fileSizeStr = fileSize + ' B';
        } else if (fileSize < 1024 * 1024) {
            fileSizeStr = (fileSize / 1024).toFixed(2) + ' KB';
        } else {
            fileSizeStr = (fileSize / (1024 * 1024)).toFixed(2) + ' MB';
        }

        fileInfoDiv.innerHTML = `
            <div class="bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-700 rounded-lg p-4 mb-6">
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0 flex items-center justify-center h-8 w-8 rounded-md bg-green-500">
                        <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-green-800 dark:text-green-200">File Selected</p>
                        <p class="text-sm text-green-700 dark:text-green-300 truncate">📄 ${file.name}</p>
                        <p class="text-xs text-green-600 dark:text-green-400 mt-1">Size: ${fileSizeStr}</p>
                    </div>
                    <button type="button" onclick="clearFileSelection()" class="flex-shrink-0 text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300">
                        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        uploadArea.classList.add('selected');
    }

    function clearSelectedFileDisplay() {
        const fileInfoDiv = document.getElementById('file-info-display');
        if (fileInfoDiv) {
            fileInfoDiv.remove();
        }
        uploadArea.classList.remove('selected');
    }

    function validateFile(file) {
        const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'image/png', 'image/jpeg', 'image/jpg'];
        const maxSize = 50 * 1024 * 1024; // 50MB
        const imageTypes = ['image/png', 'image/jpeg', 'image/jpg'];

        if (!allowedTypes.includes(file.type)) {
            showError('Invalid file type. Please upload PDF, DOCX, TXT, PNG, JPG, or JPEG files only.');
            fileInput.value = '';
            return false;
        }

        if (file.size > maxSize) {
            showError('File size exceeds 50MB limit. Please choose a smaller file.');
            fileInput.value = '';
            return false;
        }

        // Warn about image files if Tesseract might not be available
        if (imageTypes.includes(file.type)) {
            console.warn('Note: Image files require Tesseract OCR. If not installed, please use PDF, DOCX, or TXT files instead.');
        }

        return true;
    }

    async function submitForm() {
        const file = fileInput.files[0];
        
        if (!file) {
            showError('Please select a file to process.');
            return;
        }

        if (!validateFile(file)) {
            return;
        }

        const formData = new FormData(form);
        
        // Show processing modal
        processingModal.classList.remove('hidden');
        updateProgress(0, 'Preparing file...');

        try {
            // Simulate progress
            simulateProgress();

            const response = await fetch(form.action || '/convert/text-ocr/', {
                method: 'POST',
                body: formData
            });

            clearProgressSimulation();

            if (!response.ok) {
                let errorData = {};
                const contentType = response.headers.get('content-type');
                
                try {
                    if (contentType && contentType.includes('application/json')) {
                        errorData = await response.json();
                    } else {
                        errorData = { error: await response.text() };
                    }
                } catch (e) {
                    errorData = { error: `HTTP error! status: ${response.status}` };
                }
                
                throw new Error(JSON.stringify(errorData));
            }

            // Check if response is a file download or JSON
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                
                if (data.success) {
                    updateProgress(100, 'Complete!');
                    processingModal.classList.add('hidden');
                    successModal.classList.remove('hidden');
                    
                    // Download file if provided
                    if (data.download_url) {
                        setTimeout(() => {
                            window.location.href = data.download_url;
                        }, 500);
                    }
                } else {
                    throw new Error(data.message || 'Conversion failed');
                }
            } else {
                // File download response
                updateProgress(100, 'Complete!');
                
                // Extract filename from Content-Disposition header
                const disposition = response.headers.get('content-disposition');
                let filename = 'extracted_text.txt';
                
                if (disposition && disposition.includes('filename')) {
                    const filenameMatch = disposition.match(/filename[^;=\n]*=(?:(['"]).*?\1|[^;\n]*)/);
                    if (filenameMatch && filenameMatch[0]) {
                        filename = filenameMatch[0].split('=')[1].replace(/['"]/g, '');
                    }
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);

                processingModal.classList.add('hidden');
                successModal.classList.remove('hidden');
            }

        } catch (error) {
            console.error('Error:', error);
            clearProgressSimulation();
            processingModal.classList.add('hidden');
            
            let errorMsg = error.message || 'An error occurred during processing. Please try again.';
            
            // Parse JSON error response if available
            try {
                const errorData = JSON.parse(error.message);
                if (errorData.error) {
                    errorMsg = errorData.error;
                }
            } catch (e) {
                // Not JSON, use the message as is
            }
            
            errorMessage.textContent = errorMsg;
            errorModal.classList.remove('hidden');
        }
    }

    let progressInterval;
    let currentProgress = 0;

    function simulateProgress() {
        currentProgress = 10;
        progressInterval = setInterval(() => {
            if (currentProgress < 90) {
                currentProgress += Math.random() * 30;
                if (currentProgress > 90) currentProgress = 90;
                updateProgress(currentProgress, 'Processing file...');
            }
        }, 500);
    }

    function clearProgressSimulation() {
        if (progressInterval) {
            clearInterval(progressInterval);
        }
    }

    function updateProgress(percent, message) {
        progressBar.style.width = percent + '%';
        progressText.textContent = Math.round(percent) + '% complete - ' + message;
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorModal.classList.remove('hidden');
    }

    // Global function to clear file selection
    window.clearFileSelection = function() {
        fileInput.value = '';
        clearSelectedFileDisplay();
    };

    // Add dragover visual feedback
    const style = document.createElement('style');
    style.textContent = `
        .upload-area.dragover {
            background-color: rgba(59, 130, 246, 0.1);
            border-color: rgb(59, 130, 246);
        }

        .upload-area.selected {
            background-color: rgba(34, 197, 94, 0.05);
            border-color: rgb(34, 197, 94);
        }

        .spinner {
            border: 4px solid rgba(0, 0, 0, 0.1);
            border-top: 4px solid rgb(59, 130, 246);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .dark .spinner {
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-top: 4px solid rgb(59, 130, 246);
        }

        .upload-label {
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 3rem 2rem;
        }

        .upload-text {
            font-weight: 600;
            color: rgb(55, 65, 81);
            margin-top: 0.5rem;
        }

        .dark .upload-text {
            color: rgb(243, 244, 246);
        }

        .upload-subtext {
            font-size: 0.875rem;
            color: rgb(107, 114, 128);
            margin-top: 0.25rem;
        }

        .dark .upload-subtext {
            color: rgb(209, 213, 219);
        }

        #text-ocr-file {
            display: none;
        }

        #file-info-display {
            animation: slideDown 0.3s ease-out;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);
});
