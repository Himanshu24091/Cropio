// GIF ⇄ MP4 Converter JavaScript
// Professional video conversion with advanced features

class GifMp4Converter {
    constructor() {
        this.files = [];
        this.currentConversionType = 'gif_to_mp4';
        this.isProcessing = false;
        this.currentConversionId = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.updateUIForConversionType();
    }
    
    initializeElements() {
        // Main elements
        this.fileInput = document.getElementById('fileInput');
        this.uploadZone = document.getElementById('uploadZone');
        this.uploadText = document.getElementById('uploadText');
        this.formatBadge = document.getElementById('formatBadge');
        
        // Conversion type
        this.typeOptions = document.querySelectorAll('.type-option');
        
        // File management
        this.fileList = document.getElementById('fileList');
        
        // Settings
        this.conversionSettings = document.getElementById('conversionSettings');
        this.gifToMp4Settings = document.getElementById('gifToMp4Settings');
        this.mp4ToGifSettings = document.getElementById('mp4ToGifSettings');
        
        // GIF to MP4 settings
        this.quality = document.getElementById('quality');
        this.fps = document.getElementById('fps');
        this.scale = document.getElementById('scale');
        this.optimize = document.getElementById('optimize');
        
        // MP4 to GIF settings
        this.gifFps = document.getElementById('gifFps');
        this.gifFpsValue = document.getElementById('gifFpsValue');
        this.gifScale = document.getElementById('gifScale');
        this.startTime = document.getElementById('startTime');
        this.duration = document.getElementById('duration');
        this.paletteQuality = document.getElementById('paletteQuality');
        this.loopCount = document.getElementById('loopCount');
        
        // Conversion
        this.convertBtn = document.getElementById('convertBtn');
        this.convertBtnText = document.getElementById('convertBtnText');
        
        // Progress
        this.conversionProgress = document.getElementById('conversionProgress');
        this.progressBar = document.getElementById('progressBar');
        this.progressText = document.getElementById('progressText');
        
        // Results
        this.resultsSection = document.getElementById('resultsSection');
        this.conversionType = document.getElementById('conversionType');
        this.inputSize = document.getElementById('inputSize');
        this.outputSize = document.getElementById('outputSize');
        this.compressionRatio = document.getElementById('compressionRatio');
        
        // Download
        this.downloadBtn = document.getElementById('downloadBtn');
        this.downloadBtnText = document.getElementById('downloadBtnText');
        this.newConversionBtn = document.getElementById('newConversionBtn');
    }
    
    setupEventListeners() {
        // Conversion type selection
        this.typeOptions.forEach(option => {
            option.addEventListener('click', () => {
                this.setConversionType(option.dataset.type);
            });
        });
        
        // File input
        if (this.fileInput) {
            this.fileInput.addEventListener('change', (e) => {
                this.handleFiles(e.target.files);
            });
        }
        
        // Upload zone click
        if (this.uploadZone) {
            this.uploadZone.addEventListener('click', (e) => {
                if (e.target === this.uploadZone || 
                    e.target.classList.contains('upload-icon') ||
                    e.target.classList.contains('upload-text') ||
                    e.target.classList.contains('upload-hint')) {
                    this.fileInput.click();
                }
            });
        }
        
        // GIF FPS slider
        if (this.gifFps && this.gifFpsValue) {
            this.gifFps.addEventListener('input', (e) => {
                this.gifFpsValue.textContent = e.target.value;
            });
        }
        
        // Convert button
        if (this.convertBtn) {
            this.convertBtn.addEventListener('click', () => {
                this.startConversion();
            });
        }
        
        // Download button
        if (this.downloadBtn) {
            this.downloadBtn.addEventListener('click', () => {
                this.downloadResult();
            });
        }
        
        // New conversion button
        if (this.newConversionBtn) {
            this.newConversionBtn.addEventListener('click', () => {
                this.resetConverter();
            });
        }
    }
    
    setupDragAndDrop() {
        if (!this.uploadZone) return;
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.uploadZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });
        
        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            this.uploadZone.addEventListener(eventName, () => this.highlight(), false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            this.uploadZone.addEventListener(eventName, () => this.unhighlight(), false);
        });
        
        // Handle dropped files
        this.uploadZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            this.handleFiles(files);
        }, false);
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    highlight() {
        this.uploadZone.classList.add('dragover');
    }
    
    unhighlight() {
        this.uploadZone.classList.remove('dragover');
    }
    
    setConversionType(type) {
        this.currentConversionType = type;
        
        // Update UI
        this.typeOptions.forEach(option => {
            option.classList.toggle('active', option.dataset.type === type);
        });
        
        this.updateUIForConversionType();
        this.clearFiles();
    }
    
    updateUIForConversionType() {
        if (this.currentConversionType === 'gif_to_mp4') {
            // Update upload zone
            if (this.uploadText) {
                this.uploadText.textContent = 'Drop your GIF files here';
            }
            if (this.formatBadge) {
                this.formatBadge.textContent = 'Format: GIF';
            }
            if (this.fileInput) {
                this.fileInput.accept = '.gif';
            }
            
            // Update settings visibility
            if (this.gifToMp4Settings) {
                this.gifToMp4Settings.style.display = 'block';
            }
            if (this.mp4ToGifSettings) {
                this.mp4ToGifSettings.style.display = 'none';
            }
            
            // Update button text
            if (this.convertBtnText) {
                this.convertBtnText.textContent = 'Convert GIF to MP4';
            }
            if (this.downloadBtnText) {
                this.downloadBtnText.textContent = 'Download MP4';
            }
            
        } else { // mp4_to_gif
            // Update upload zone
            if (this.uploadText) {
                this.uploadText.textContent = 'Drop your MP4 files here';
            }
            if (this.formatBadge) {
                this.formatBadge.textContent = 'Format: MP4, MOV, AVI, MKV, WEBM';
            }
            if (this.fileInput) {
                this.fileInput.accept = '.mp4,.mov,.avi,.mkv,.webm';
            }
            
            // Update settings visibility
            if (this.gifToMp4Settings) {
                this.gifToMp4Settings.style.display = 'none';
            }
            if (this.mp4ToGifSettings) {
                this.mp4ToGifSettings.style.display = 'block';
            }
            
            // Update button text
            if (this.convertBtnText) {
                this.convertBtnText.textContent = 'Convert MP4 to GIF';
            }
            if (this.downloadBtnText) {
                this.downloadBtnText.textContent = 'Download GIF';
            }
        }
    }
    
    handleFiles(fileList) {
        const validFiles = Array.from(fileList).filter(file => this.validateFile(file));
        
        if (validFiles.length === 0) {
            this.showError('No valid files selected. Please choose the correct file format.');
            return;
        }
        
        if (validFiles.length > 1) {
            this.showError('Please select only one file at a time.');
            return;
        }
        
        this.files = validFiles.map(file => ({
            id: this.generateFileId(),
            file: file,
            status: 'ready'
        }));
        
        this.displayFiles();
        this.showSettings();
        this.showConvertButton();
    }
    
    validateFile(file) {
        const allowedExtensions = {
            'gif_to_mp4': ['.gif'],
            'mp4_to_gif': ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        };
        
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        const validExtensions = allowedExtensions[this.currentConversionType];
        
        if (!validExtensions.includes(ext)) {
            return false;
        }
        
        // Check file size (100MB max)
        const maxSize = 100 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showError(`File "${file.name}" is too large. Maximum size: 100MB`);
            return false;
        }
        
        return true;
    }
    
    generateFileId() {
        return Math.random().toString(36).substr(2, 9);
    }
    
    displayFiles() {
        if (!this.fileList || this.files.length === 0) return;
        
        const file = this.files[0];
        const fileExtension = file.file.name.split('.').pop().toUpperCase();
        const fileSize = this.formatFileSize(file.file.size);
        
        this.fileList.innerHTML = `
            <div class="file-item">
                <div class="file-info">
                    <div class="file-icon">
                        <i class="fas ${this.getFileIcon(file.file)}"></i>
                    </div>
                    <div class="file-details">
                        <h4>${file.file.name}</h4>
                        <p>${fileSize} • ${fileExtension} format</p>
                    </div>
                </div>
                <div class="file-actions">
                    <button class="btn btn-outline-danger btn-sm" onclick="gifMp4Converter.removeFile('${file.id}')">
                        <i class="fas fa-times"></i> Remove
                    </button>
                </div>
            </div>
        `;
        
        this.fileList.style.display = 'block';
    }
    
    getFileIcon(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        switch (ext) {
            case 'gif':
                return 'fa-film';
            case 'mp4':
            case 'mov':
            case 'avi':
            case 'mkv':
            case 'webm':
                return 'fa-video';
            default:
                return 'fa-file';
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showSettings() {
        if (this.conversionSettings) {
            this.conversionSettings.style.display = 'block';
        }
    }
    
    showConvertButton() {
        if (this.convertBtn) {
            this.convertBtn.style.display = 'inline-block';
        }
    }
    
    removeFile(fileId) {
        this.files = this.files.filter(f => f.id !== fileId);
        if (this.files.length === 0) {
            this.clearFiles();
        } else {
            this.displayFiles();
        }
    }
    
    clearFiles() {
        this.files = [];
        if (this.fileList) {
            this.fileList.style.display = 'none';
        }
        if (this.conversionSettings) {
            this.conversionSettings.style.display = 'none';
        }
        if (this.convertBtn) {
            this.convertBtn.style.display = 'none';
        }
        if (this.fileInput) {
            this.fileInput.value = '';
        }
        this.hideResults();
    }
    
    async startConversion() {
        if (this.isProcessing || this.files.length === 0) return;
        
        this.isProcessing = true;
        this.convertBtn.disabled = true;
        this.showProgress(10, 'Preparing conversion...');
        
        try {
            const formData = new FormData();
            
            // Add file
            formData.append('files', this.files[0].file);
            formData.append('conversion_mode', this.currentConversionType);
            
            // Add settings based on conversion type
            if (this.currentConversionType === 'gif_to_mp4') {
                formData.append('quality', this.quality?.value || 'high');
                formData.append('fps', this.fps?.value || '');
                formData.append('scale', this.scale?.value || '');
                formData.append('optimize', this.optimize?.checked || true);
            } else {
                formData.append('fps', this.gifFps?.value || '15');
                formData.append('scale', this.gifScale?.value || '-1:480');
                formData.append('start_time', this.startTime?.value || '');
                formData.append('duration', this.duration?.value || '');
                formData.append('palette_quality', this.paletteQuality?.value || 'high');
                formData.append('loop_count', this.loopCount?.value || '0');
            }
            
            this.showProgress(30, 'Uploading file...');
            
            const response = await fetch('/gif-mp4/convert', {
                method: 'POST',
                body: formData
            });
            
            this.showProgress(70, 'Processing conversion...');
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `HTTP ${response.status}`);
            }
            
            if (!result.success) {
                throw new Error(result.error || 'Conversion failed');
            }
            
            this.showProgress(100, 'Conversion completed!');
            this.currentConversionId = result.conversion_id;
            this.showResults(result);
            
        } catch (error) {
            console.error('Conversion error:', error);
            this.showError(error.message || 'Conversion failed. Please try again.');
        } finally {
            this.isProcessing = false;
            this.convertBtn.disabled = false;
            this.hideProgress();
        }
    }
    
    showProgress(percentage, message) {
        if (this.conversionProgress) {
            this.conversionProgress.style.display = 'block';
        }
        if (this.progressBar) {
            this.progressBar.style.width = `${percentage}%`;
        }
        if (this.progressText) {
            this.progressText.textContent = message;
        }
    }
    
    hideProgress() {
        if (this.conversionProgress) {
            this.conversionProgress.style.display = 'none';
        }
        if (this.progressText) {
            this.progressText.textContent = '';
        }
    }
    
    showResults(result) {
        // Update conversion info
        if (this.conversionType) {
            this.conversionType.textContent = result.conversion_type;
        }
        if (this.inputSize) {
            this.inputSize.textContent = this.formatFileSize(result.input_size);
        }
        if (this.outputSize) {
            this.outputSize.textContent = this.formatFileSize(result.output_size);
        }
        if (this.compressionRatio) {
            if (result.compression_ratio) {
                this.compressionRatio.textContent = result.compression_ratio;
            } else if (result.size_ratio) {
                this.compressionRatio.textContent = result.size_ratio;
            } else {
                this.compressionRatio.textContent = 'N/A';
            }
        }
        
        // Show results section
        if (this.resultsSection) {
            this.resultsSection.style.display = 'block';
            this.resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
        
        this.showSuccess(result.message);
    }
    
    hideResults() {
        if (this.resultsSection) {
            this.resultsSection.style.display = 'none';
        }
        this.currentConversionId = null;
    }
    
    downloadResult() {
        if (!this.currentConversionId) {
            this.showError('No conversion available for download');
            return;
        }
        
        const downloadUrl = `/gif-mp4/download/${this.currentConversionId}`;
        
        // Create download link
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = '';
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    resetConverter() {
        this.clearFiles();
        this.hideResults();
        this.currentConversionId = null;
        
        // Scroll back to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    showSuccess(message) {
        this.showToast(message, 'success');
    }
    
    showError(message) {
        this.showToast(message, 'error');
    }
    
    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add to page
        document.body.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }
}

// Toast CSS (injected)
const toastStyles = `
    .toast {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        color: white;
        font-weight: 500;
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        min-width: 350px;
        max-width: 500px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        animation: slideIn 0.3s ease;
        font-size: 0.9rem;
    }
    
    .toast-success {
        background: linear-gradient(135deg, #10b981, #059669);
    }
    
    .toast-error {
        background: linear-gradient(135deg, #ef4444, #dc2626);
    }
    
    .toast i {
        font-size: 1.25rem;
        flex-shrink: 0;
    }
    
    .toast span {
        flex: 1;
        line-height: 1.4;
    }
    
    .toast-close {
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        padding: 0.25rem;
        opacity: 0.7;
        transition: opacity 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 0.25rem;
    }
    
    .toast-close:hover {
        opacity: 1;
        background: rgba(255, 255, 255, 0.1);
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @media (max-width: 640px) {
        .toast {
            right: 10px;
            left: 10px;
            min-width: auto;
            max-width: none;
        }
    }
`;

// Inject toast styles
const styleSheet = document.createElement('style');
styleSheet.textContent = toastStyles;
document.head.appendChild(styleSheet);

// Initialize converter when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.gifMp4Converter = new GifMp4Converter();
});
