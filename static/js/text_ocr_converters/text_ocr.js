// Text & OCR Processor Specific JavaScript
document.addEventListener('DOMContentLoaded', function() {
    
    // Language selection enhancement
    const languageSelect = document.getElementById('language');
    const detectLanguageCheckbox = document.querySelector('input[name="detect_language"]');
    
    if (languageSelect && detectLanguageCheckbox) {
        // Enable/disable language selection based on auto-detect
        detectLanguageCheckbox.addEventListener('change', function() {
            if (this.checked) {
                languageSelect.value = 'auto';
                languageSelect.disabled = true;
            } else {
                languageSelect.disabled = false;
            }
        });
    }
    
    // File validation for OCR files
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Check file extension
                const fileName = file.name.toLowerCase();
                const validExtensions = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.docx', '.txt'];
                const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));
                
                if (!hasValidExtension) {
                    alert('Please select a valid file type: PDF, PNG, JPG, JPEG, TIFF, DOCX, or TXT');
                    this.value = '';
                    return;
                }
                
                // Check file size (max 50MB)
                const maxSize = 50 * 1024 * 1024; // 50MB in bytes
                if (file.size > maxSize) {
                    alert('File size exceeds 50MB limit. Please choose a smaller file.');
                    this.value = '';
                    return;
                }
                
                // Update file preview
                const fileNameElement = document.getElementById('file-name');
                if (fileNameElement) {
                    fileNameElement.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
                }
                
                console.log('Valid file selected for OCR processing');
            }
        });
    }
    
    // Enhanced form submission with processing modal
    const form = document.querySelector('form');
    const submitButton = form?.querySelector('button[type="submit"]');
    const processingModal = document.getElementById('processing-modal');
    
    if (form && submitButton && processingModal) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show processing modal
            processingModal.classList.remove('hidden');
            
            // Start progress animation
            let progress = 0;
            const progressBar = document.getElementById('progress-bar');
            const progressText = document.getElementById('progress-text');
            const statusText = document.getElementById('processing-status');
            
            // Simulate OCR processing stages
            const stages = [
                { progress: 0, status: 'Analyzing image...' },
                { progress: 25, status: 'Detecting text regions...' },
                { progress: 50, status: 'Extracting text...' },
                { progress: 75, status: 'Processing language...' },
                { progress: 90, status: 'Finalizing results...' }
            ];
            
            let stageIndex = 0;
            const progressInterval = setInterval(() => {
                if (stageIndex < stages.length) {
                    const stage = stages[stageIndex];
                    progress = stage.progress;
                    statusText.textContent = stage.status;
                    progressBar.style.width = progress + '%';
                    progressText.textContent = progress + '%';
                    stageIndex++;
                } else {
                    clearInterval(progressInterval);
                    // Submit the form after animation
                    setTimeout(() => {
                        form.submit();
                    }, 500);
                }
            }, 800);
            
            // Add a timeout to submit form if something goes wrong
            setTimeout(() => {
                if (processingModal && !processingModal.classList.contains('hidden')) {
                    clearInterval(progressInterval);
                    form.submit();
                }
            }, 10000); // 10 seconds timeout
        });
    }
    
    // Check if there's an OCR result and enhance display
    const ocrResult = document.querySelector('.result-success-box');
    if (ocrResult) {
        // Add fade-in animation
        ocrResult.style.opacity = '0';
        ocrResult.style.animation = 'fadeIn 0.5s ease-in forwards';
        
        // Highlight confidence score based on value
        const confidenceElement = document.querySelector('.stat-item:nth-child(2) strong');
        if (confidenceElement) {
            const confidenceText = confidenceElement.nextSibling.textContent;
            const confidenceValue = parseInt(confidenceText);
            
            if (confidenceValue >= 90) {
                confidenceElement.parentElement.style.color = 'rgb(22, 163, 74)';
            } else if (confidenceValue >= 70) {
                confidenceElement.parentElement.style.color = 'rgb(251, 146, 60)';
            } else {
                confidenceElement.parentElement.style.color = 'rgb(239, 68, 68)';
            }
        }
    }
    
    // OCR quality recommendations
    function getQualityRecommendations(file) {
        const recommendations = [];
        const fileName = file.name.toLowerCase();
        
        // Check if it's an image file
        if (['.png', '.jpg', '.jpeg', '.tiff'].some(ext => fileName.endsWith(ext))) {
            recommendations.push('For best results, ensure image is at least 300 DPI');
            recommendations.push('Text should be clear and well-lit');
        }
        
        // Check if it's a PDF
        if (fileName.endsWith('.pdf')) {
            recommendations.push('Scanned PDFs work best at high resolution');
            recommendations.push('Text-based PDFs will process faster');
        }
        
        return recommendations;
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            if (form && !submitButton.disabled) {
                form.submit();
            }
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            const fullTextModal = document.getElementById('full-text-modal');
            if (fullTextModal && !fullTextModal.classList.contains('hidden')) {
                closeFullView();
            }
        }
    });
    
    // Helper function to format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
});

// Function to copy extracted text
function copyText() {
    const textPreview = document.querySelector('#text-preview pre');
    if (textPreview) {
        // Get full text from the hidden full text modal
        const fullTextElement = document.querySelector('#full-text-modal pre');
        const textToCopy = fullTextElement ? fullTextElement.textContent : textPreview.textContent;
        
        navigator.clipboard.writeText(textToCopy).then(() => {
            // Show success feedback
            const copyBtn = event.target.closest('.preview-action-btn');
            const originalContent = copyBtn.innerHTML;
            copyBtn.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
                Copied!
            `;
            copyBtn.style.background = 'rgb(34, 197, 94)';
            copyBtn.style.color = 'white';
            
            setTimeout(() => {
                copyBtn.innerHTML = originalContent;
                copyBtn.style.background = '';
                copyBtn.style.color = '';
            }, 2000);
        }).catch(err => {
            alert('Failed to copy text. Please try again.');
        });
    }
}

// Function to toggle full text view
function toggleFullView() {
    const fullTextModal = document.getElementById('full-text-modal');
    if (fullTextModal) {
        fullTextModal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

// Function to close full text view
function closeFullView() {
    const fullTextModal = document.getElementById('full-text-modal');
    if (fullTextModal) {
        fullTextModal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

// Function to process another document (reset form)
function processAnother() {
    // Reset the form
    const form = document.querySelector('form');
    if (form) {
        form.reset();
    }
    
    // Hide result section
    const resultSection = document.querySelector('.result-success-box');
    if (resultSection) {
        resultSection.style.display = 'none';
    }
    
    // Reset file preview
    const filePreview = document.getElementById('file-preview');
    const fileName = document.getElementById('file-name');
    if (filePreview && fileName) {
        filePreview.style.display = 'none';
        fileName.textContent = '';
    }
    
    // Reset drop zone
    const dropZone = document.getElementById('drop-zone');
    if (dropZone) {
        dropZone.classList.remove('drag-over');
    }
    
    // Reset language settings
    const languageSelect = document.getElementById('language');
    const detectLanguageCheckbox = document.querySelector('input[name="detect_language"]');
    if (languageSelect && detectLanguageCheckbox) {
        detectLanguageCheckbox.checked = true;
        languageSelect.value = 'auto';
        languageSelect.disabled = true;
    }
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Focus on file input
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.focus();
    }
}

// CSS animation helper
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.7;
        }
    }
`;
document.head.appendChild(style);