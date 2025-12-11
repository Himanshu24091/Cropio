// HEIC ⇄ JPG Converter JavaScript
// Professional image conversion with preview and batch support

class HEICConverter {
    constructor() {
        this.files = [];
        this.currentConversionType = 'heic_to_jpg';
        this.isProcessing = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.setupDragAndDrop();
    }
    
    initializeElements() {
        this.fileInput = document.getElementById('fileInput');
        this.uploadZone = document.getElementById('uploadZone');
        this.fileList = document.getElementById('fileList');
        this.progressBar = document.getElementById('progressBar');
        this.progressText = document.getElementById('progressText');
        this.conversionProgress = document.getElementById('conversionProgress');
        this.previewSection = document.getElementById('previewSection');
        this.previewBefore = document.getElementById('previewBefore');
        this.previewAfter = document.getElementById('previewAfter');
        this.previewInfoBefore = document.getElementById('previewInfoBefore');
        this.previewInfoAfter = document.getElementById('previewInfoAfter');
        
        // Settings elements
        this.outputFormat = document.getElementById('outputFormat');
        this.quality = document.getElementById('quality');
        this.preserveMetadata = document.getElementById('preserveMetadata');
        this.enableLossless = document.getElementById('enableLossless');
        this.heicOptions = document.getElementById('heicOptions');
        
        // Conversion type selector
        this.typeOptions = document.querySelectorAll('.type-option');
    }
    
    setupEventListeners() {
        // File input change
        this.fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });
        
        // Conversion type selection
        this.typeOptions.forEach(option => {
            option.addEventListener('click', () => {
                this.setConversionType(option.dataset.type);
            });
        });
        
        // Settings changes
        this.outputFormat.addEventListener('change', () => this.updateUIForSettings());
        this.quality.addEventListener('change', () => this.updateQualityDisplay());
        
        // Upload zone click
        this.uploadZone.addEventListener('click', (e) => {
            if (e.target === this.uploadZone || e.target.classList.contains('upload-text') || e.target.classList.contains('upload-hint')) {
                this.fileInput.click();
            }
        });
    }
    
    setupDragAndDrop() {
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
        this.uploadZone.classList.add('drag-over');
    }
    
    unhighlight() {
        this.uploadZone.classList.remove('drag-over');
    }
    
    setConversionType(type) {
        this.currentConversionType = type;
        
        // Update UI
        this.typeOptions.forEach(option => {
            option.classList.toggle('active', option.dataset.type === type);
        });
        
        // Update file input accept attribute
        if (type === 'heic_to_jpg') {
            this.fileInput.accept = '.heic,.heif';
            this.uploadZone.querySelector('.upload-text').textContent = 'Drop your HEIC files here';
            this.heicOptions.style.display = 'none';
        } else {
            this.fileInput.accept = '.jpg,.jpeg';
            this.uploadZone.querySelector('.upload-text').textContent = 'Drop your JPG files here';
            this.heicOptions.style.display = 'block';
        }
        
        // Clear existing files when switching conversion type
        this.clearFiles();
    }
    
    updateUIForSettings() {
        // Update settings based on current selections
        const format = this.outputFormat.value;
        
        // Adjust quality options for different formats
        if (format === 'png') {
            this.quality.style.display = 'none';
            this.quality.parentElement.style.display = 'none';
        } else {
            this.quality.style.display = 'block';
            this.quality.parentElement.style.display = 'block';
        }
    }
    
    updateQualityDisplay() {
        // Update quality display if there's a slider
        const qualityValue = document.querySelector('.quality-value');
        if (qualityValue) {
            qualityValue.textContent = `${this.quality.value}%`;
        }
    }
    
    async handleFiles(fileList) {
        const validFiles = Array.from(fileList).filter(file => this.validateFile(file));
        
        if (validFiles.length === 0) {
            this.showError('No valid files selected. Please choose HEIC or JPG files.');
            return;
        }
        
        // Add files to our collection
        validFiles.forEach(file => {
            const fileId = this.generateFileId();
            this.files.push({
                id: fileId,
                file: file,
                status: 'pending',
                progress: 0
            });
        });
        
        this.renderFileList();
        this.showPreview(validFiles[0]); // Show preview for first file
    }
    
    validateFile(file) {
        const allowedTypes = {
            'heic_to_jpg': ['image/heic', 'image/heif', 'application/octet-stream'],
            'jpg_to_heic': ['image/jpeg', 'image/jpg']
        };
        
        const allowedExtensions = {
            'heic_to_jpg': ['.heic', '.heif'],
            'jpg_to_heic': ['.jpg', '.jpeg']
        };
        
        // Check file extension
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        const validExtensions = allowedExtensions[this.currentConversionType];
        
        if (!validExtensions.includes(ext)) {
            this.showError(`Invalid file type. Expected: ${validExtensions.join(', ')}`);
            return false;
        }
        
        // Check file size (50MB for premium, 5MB for free)
        const maxSize = 50 * 1024 * 1024; // Assume premium for now
        if (file.size > maxSize) {
            this.showError(`File "${file.name}" is too large. Maximum size: ${maxSize / (1024*1024)}MB`);
            return false;
        }
        
        return true;
    }
    
    generateFileId() {
        return Math.random().toString(36).substr(2, 9);
    }
    
    renderFileList() {
        if (this.files.length === 0) {
            this.fileList.style.display = 'none';
            return;
        }
        
        this.fileList.style.display = 'block';
        this.fileList.innerHTML = this.files.map(fileItem => `
            <div class="file-item" data-file-id="${fileItem.id}">
                <div class="file-info">
                    <div class="file-icon">
                        <i class="fas ${this.getFileIcon(fileItem.file)}"></i>
                    </div>
                    <div class="file-details">
                        <h4>${fileItem.file.name}</h4>
                        <p>${this.formatFileSize(fileItem.file.size)} • ${this.getFileFormat(fileItem.file)}</p>
                    </div>
                </div>
                <div class="file-actions">
                    <span class="status status-${fileItem.status}">
                        ${this.getStatusText(fileItem.status)}
                    </span>
                    ${fileItem.status === 'pending' ? `
                        <button class="btn btn-primary btn-sm" onclick="heicConverter.convertSingle('${fileItem.id}')">
                            <i class="fas fa-exchange-alt"></i> Convert
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="heicConverter.removeFile('${fileItem.id}')">
                            <i class="fas fa-times"></i>
                        </button>
                    ` : ''}
                    ${fileItem.status === 'completed' ? `
                        <button class="btn download-btn btn-sm" onclick="heicConverter.downloadFile('${fileItem.id}')">
                            <i class="fas fa-download"></i> Download
                        </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
        
        // Add batch convert button if multiple files
        if (this.files.length > 1 && this.files.some(f => f.status === 'pending')) {
            const batchButton = document.createElement('div');
            batchButton.className = 'batch-actions';
            batchButton.innerHTML = `
                <button class="btn btn-primary" onclick="heicConverter.convertAll()">
                    <i class="fas fa-layer-group"></i> Convert All (${this.files.filter(f => f.status === 'pending').length} files)
                </button>
                <button class="btn btn-secondary" onclick="heicConverter.clearAll()">
                    <i class="fas fa-trash"></i> Clear All
                </button>
            `;
            this.fileList.appendChild(batchButton);
        }
    }
    
    getFileIcon(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        switch (ext) {
            case 'heic':
            case 'heif':
                return 'fa-mobile-alt';
            case 'jpg':
            case 'jpeg':
                return 'fa-image';
            default:
                return 'fa-file-image';
        }
    }
    
    getFileFormat(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        return ext.toUpperCase();
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    getStatusText(status) {
        const statusMap = {
            'pending': 'Ready',
            'processing': 'Converting...',
            'completed': 'Done',
            'failed': 'Failed'
        };
        return statusMap[status] || status;
    }
    
    async showPreview(file) {
        if (!file) return;
        
        this.previewSection.style.display = 'block';
        
        // Check if it's a HEIC file
        const fileExt = file.name.toLowerCase().split('.').pop();
        
        if (['heic', 'heif'].includes(fileExt)) {
            // For HEIC files, use server-side preview generation since browsers can't display HEIC natively
            try {
                this.showOriginalPreviewLoading();
                
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch('/heic-jpg/api/heic-preview', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                this.hideOriginalPreviewLoading();
                
                if (result.success && result.preview) {
                    this.previewBefore.src = result.preview;
                    this.previewBefore.style.display = 'block';
                } else {
                    this.showOriginalPreviewError('Unable to generate HEIC preview');
                }
            } catch (error) {
                console.error('Failed to generate HEIC preview:', error);
                this.hideOriginalPreviewLoading();
                this.showOriginalPreviewError('Preview generation failed');
            }
        } else {
            // For JPG and other web-compatible formats, use direct FileReader
            const reader = new FileReader();
            reader.onload = (e) => {
                this.previewBefore.src = e.target.result;
                this.previewBefore.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
        
        // Get file info
        try {
            const fileInfo = await this.getFileInfo(file);
            this.previewInfoBefore.innerHTML = this.formatFileInfo(fileInfo, file);
        } catch (error) {
            console.error('Failed to get file info:', error);
        }
    }
    
    async getFileInfo(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/heic-info', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            if (result.success) {
                return result.info;
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            return {
                error: error.message,
                dimensions: 'Unknown',
                format: this.getFileFormat(file),
                size: file.size
            };
        }
    }
    
    formatFileInfo(info, file) {
        if (info.error) {
            return `
                <strong>Format:</strong> ${this.getFileFormat(file)}<br>
                <strong>Size:</strong> ${this.formatFileSize(file.size)}<br>
                <strong>Info:</strong> ${info.error}
            `;
        }
        
        return `
            <strong>Format:</strong> ${info.format || this.getFileFormat(file)}<br>
            <strong>Dimensions:</strong> ${info.dimensions || 'Unknown'}<br>
            <strong>Size:</strong> ${this.formatFileSize(file.size)}<br>
            ${info.color_mode ? `<strong>Color:</strong> ${info.color_mode}<br>` : ''}
            ${info.has_transparency ? `<strong>Transparency:</strong> Yes<br>` : ''}
        `;
    }
    
    async convertSingle(fileId) {
        const fileItem = this.files.find(f => f.id === fileId);
        if (!fileItem || this.isProcessing) return;
        
        this.isProcessing = true;
        fileItem.status = 'processing';
        this.renderFileList();
        
        try {
            const result = await this.performConversion(fileItem.file);
            
            if (result.success) {
                fileItem.status = 'completed';
                fileItem.downloadUrl = result.download_url;
                fileItem.stats = result.stats;
                fileItem.convertedInfo = result.converted_info;
                
                this.showSuccess(result.message);
                await this.updatePreviewAfter(result);
            } else {
                fileItem.status = 'failed';
                fileItem.error = result.error;
                this.showError(result.error);
            }
        } catch (error) {
            fileItem.status = 'failed';
            fileItem.error = error.message;
            this.showError(`Conversion failed: ${error.message}`);
        } finally {
            this.isProcessing = false;
            this.renderFileList();
            this.hideProgress();
        }
    }
    
    async convertAll() {
        if (this.isProcessing) return;
        
        const pendingFiles = this.files.filter(f => f.status === 'pending');
        if (pendingFiles.length === 0) return;
        
        this.isProcessing = true;
        this.showProgress('Converting files...', 0);
        
        try {
            // Process files one by one
            for (let i = 0; i < pendingFiles.length; i++) {
                const fileItem = pendingFiles[i];
                const progress = ((i + 1) / pendingFiles.length) * 100;
                
                this.showProgress(`Converting ${fileItem.file.name}...`, progress);
                fileItem.status = 'processing';
                this.renderFileList();
                
                try {
                    const result = await this.performConversion(fileItem.file);
                    
                    if (result.success) {
                        fileItem.status = 'completed';
                        fileItem.downloadUrl = result.download_url;
                        fileItem.stats = result.stats;
                    } else {
                        fileItem.status = 'failed';
                        fileItem.error = result.error;
                    }
                } catch (error) {
                    fileItem.status = 'failed';
                    fileItem.error = error.message;
                }
            }
            
            const successCount = pendingFiles.filter(f => f.status === 'completed').length;
            this.showSuccess(`Batch conversion completed: ${successCount}/${pendingFiles.length} files processed successfully`);
            
        } catch (error) {
            this.showError(`Batch conversion failed: ${error.message}`);
        } finally {
            this.isProcessing = false;
            this.renderFileList();
            this.hideProgress();
        }
    }
    
    async performConversion(file) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('conversion_type', this.currentConversionType);
        formData.append('quality', this.quality.value);
        formData.append('output_format', this.outputFormat.value);
        formData.append('preserve_metadata', this.preserveMetadata.checked);
        
        const response = await fetch('/api/heic-convert', {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    }
    
    async updatePreviewAfter(result) {
        try {
            // Show loading state first
            this.showPreviewLoading();
            
            // Show converted image details immediately
            if (result.stats && result.converted_info) {
                this.previewInfoAfter.innerHTML = `
                    <strong>Format:</strong> ${result.stats.output_format}<br>
                    <strong>Size:</strong> ${result.stats.converted_size}<br>
                    <strong>Processing Time:</strong> ${result.stats.processing_time}<br>
                    <strong>Compression:</strong> ${result.stats.compression_ratio}<br>
                    <strong>File:</strong> ${result.converted_info.filename}<br>
                `;
            }
            
            // Fetch and display converted image preview
            if (result.download_url) {
                const filename = result.download_url.split('/').pop();
                
                try {
                    const previewResponse = await fetch(`/api/preview-converted/${filename}`);
                    const previewResult = await previewResponse.json();
                    
                    // Remove loading state
                    this.hidePreviewLoading();
                    
                    if (previewResult.success && previewResult.preview) {
                        this.previewAfter.src = previewResult.preview;
                        this.previewAfter.style.display = 'block';
                        
                        // Add format info to the preview
                        const formatBadge = document.createElement('div');
                        formatBadge.className = 'format-badge';
                        formatBadge.textContent = previewResult.format || result.stats.output_format;
                        
                        // Remove existing format badge if any
                        const existingBadge = this.previewAfter.parentNode.querySelector('.format-badge');
                        if (existingBadge) {
                            existingBadge.remove();
                        }
                        
                        this.previewAfter.parentNode.appendChild(formatBadge);
                    } else {
                        // If preview fails, show a placeholder
                        this.showPreviewPlaceholder(result.stats.output_format);
                    }
                } catch (error) {
                    console.error('Failed to fetch converted image preview:', error);
                    this.hidePreviewLoading();
                    this.showPreviewPlaceholder(result.stats.output_format);
                }
            }
        } catch (error) {
            console.error('Error updating preview after conversion:', error);
            this.hidePreviewLoading();
        }
    }
    
    showPreviewLoading() {
        // Hide existing preview
        this.previewAfter.style.display = 'none';
        
        // Remove existing placeholder or loading
        const existingElements = this.previewAfter.parentNode.querySelectorAll('.preview-placeholder, .preview-loading');
        existingElements.forEach(el => el.remove());
        
        // Show loading state
        const loading = document.createElement('div');
        loading.className = 'preview-loading';
        loading.innerHTML = `
            <div>
                <i class="fas fa-spinner"></i>
                <p style="margin-top: 1rem; color: #6b7280;">Generating preview...</p>
            </div>
        `;
        
        this.previewAfter.parentNode.appendChild(loading);
    }
    
    hidePreviewLoading() {
        const loading = this.previewAfter.parentNode.querySelector('.preview-loading');
        if (loading) {
            loading.remove();
        }
    }
    
    showPreviewPlaceholder(format) {
        // Hide the image and show a placeholder for formats that can't be previewed
        this.previewAfter.style.display = 'none';
        
        // Remove existing placeholder
        const existingPlaceholder = this.previewAfter.parentNode.querySelector('.preview-placeholder');
        if (existingPlaceholder) {
            existingPlaceholder.remove();
        }
        
        // Create placeholder
        const placeholder = document.createElement('div');
        placeholder.className = 'preview-placeholder';
        placeholder.innerHTML = `
            <div class="placeholder-content">
                <i class="fas fa-mobile-alt" style="font-size: 3rem; color: #3b82f6; margin-bottom: 1rem;"></i>
                <h4>${format} File Created</h4>
                <p>Preview not available for ${format} format.<br>Download to view the converted image.</p>
            </div>
        `;
        
        this.previewAfter.parentNode.appendChild(placeholder);
    }
    
    showOriginalPreviewLoading() {
        // Hide existing preview
        this.previewBefore.style.display = 'none';
        
        // Remove existing placeholder or loading
        const existingElements = this.previewBefore.parentNode.querySelectorAll('.preview-placeholder, .preview-loading');
        existingElements.forEach(el => el.remove());
        
        // Show loading state
        const loading = document.createElement('div');
        loading.className = 'preview-loading';
        loading.innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #3b82f6; margin-bottom: 1rem;"></i>
                <p style="margin: 0; color: #6b7280;">Generating HEIC preview...</p>
            </div>
        `;
        
        this.previewBefore.parentNode.appendChild(loading);
    }
    
    hideOriginalPreviewLoading() {
        const loading = this.previewBefore.parentNode.querySelector('.preview-loading');
        if (loading) {
            loading.remove();
        }
    }
    
    showOriginalPreviewError(errorMessage) {
        // Hide existing preview
        this.previewBefore.style.display = 'none';
        
        // Remove existing placeholder or loading
        const existingElements = this.previewBefore.parentNode.querySelectorAll('.preview-placeholder, .preview-loading');
        existingElements.forEach(el => el.remove());
        
        // Show error state
        const errorDiv = document.createElement('div');
        errorDiv.className = 'preview-placeholder';
        errorDiv.innerHTML = `
            <div style="text-align: center; padding: 2rem;">
                <i class="fas fa-exclamation-triangle" style="font-size: 2rem; color: #ef4444; margin-bottom: 1rem;"></i>
                <h4>Preview Error</h4>
                <p style="margin: 0; color: #6b7280;">${errorMessage}</p>
            </div>
        `;
        
        this.previewBefore.parentNode.appendChild(errorDiv);
    }
    
    downloadFile(fileId) {
        const fileItem = this.files.find(f => f.id === fileId);
        if (!fileItem || !fileItem.downloadUrl) return;
        
        // Create download link
        const link = document.createElement('a');
        link.href = fileItem.downloadUrl;
        link.download = fileItem.file.name.replace(/\.[^/.]+$/, '') + this.getOutputExtension();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    getOutputExtension() {
        const format = this.outputFormat.value;
        if (this.currentConversionType === 'heic_to_jpg') {
            return format === 'png' ? '.png' : '.jpg';
        } else {
            return '.heic'; // or .jpg if HEIC conversion fails
        }
    }
    
    removeFile(fileId) {
        this.files = this.files.filter(f => f.id !== fileId);
        this.renderFileList();
        
        if (this.files.length === 0) {
            this.clearFiles();
        }
    }
    
    clearFiles() {
        this.files = [];
        this.fileList.style.display = 'none';
        this.previewSection.style.display = 'none';
        this.fileInput.value = '';
    }
    
    clearAll() {
        this.clearFiles();
    }
    
    showProgress(text, percentage) {
        this.conversionProgress.style.display = 'block';
        this.progressText.textContent = text;
        this.progressBar.style.width = `${percentage}%`;
    }
    
    hideProgress() {
        this.conversionProgress.style.display = 'none';
        this.progressText.textContent = '';
    }
    
    showError(message) {
        // Create and show error toast
        const toast = document.createElement('div');
        toast.className = 'toast toast-error';
        toast.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
    
    showSuccess(message) {
        // Create and show success toast
        const toast = document.createElement('div');
        toast.className = 'toast toast-success';
        toast.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
}

// Toast Styles (inline for simplicity)
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
        gap: 0.5rem;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        animation: slideIn 0.3s ease;
    }
    
    .toast-error {
        background: linear-gradient(135deg, #ef4444, #dc2626);
    }
    
    .toast-success {
        background: linear-gradient(135deg, #10b981, #059669);
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
`;

// Add toast styles to document
const styleSheet = document.createElement('style');
styleSheet.textContent = toastStyles;
document.head.appendChild(styleSheet);

// Drag over styles
const dragStyles = `
    .upload-zone.drag-over {
        border-color: #3b82f6;
        background: linear-gradient(135deg, #dbeafe, #bfdbfe);
        transform: scale(1.02);
    }
`;

const dragStyleSheet = document.createElement('style');
dragStyleSheet.textContent = dragStyles;
document.head.appendChild(dragStyleSheet);

// Initialize converter when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.heicConverter = new HEICConverter();
});

// Additional utility functions for HEIC conversion
function validateHEICSupport() {
    // Check if browser supports HEIC
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // This is a simple check - actual support would need server validation
    return typeof ctx.createImageData === 'function';
}

function showHEICInfo() {
    // Show HEIC format information modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>About HEIC Format</h3>
                <button class="modal-close" onclick="this.closest('.modal').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <p><strong>HEIC (High Efficiency Image Container)</strong> is Apple's modern image format:</p>
                <ul>
                    <li>50% better compression than JPEG</li>
                    <li>Higher image quality at smaller file sizes</li>
                    <li>Support for transparency and multiple images</li>
                    <li>Better color depth and dynamic range</li>
                    <li>Used by iPhone and iPad cameras since iOS 11</li>
                </ul>
                <p><strong>Compatibility Note:</strong> While HEIC provides superior quality and compression, 
                it may not be supported by all devices and software. Converting to JPG ensures universal compatibility 
                across all platforms and applications.</p>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
}
