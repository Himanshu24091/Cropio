/**
 * GIF ⇄ PNG Sequence Converter JavaScript
 * Complete rewrite with proper DOM handling and Bootstrap integration
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 GIF PNG Sequence Converter initializing...');
    
    // Initialize the converter
    window.GifPngConverter = new GifPngSequenceConverter();
});

class GifPngSequenceConverter {
    constructor() {
        this.currentMode = 'gif-to-png';
        this.uploadedFiles = [];
        this.isProcessing = false;
        this.currentConversionId = null;
        
        console.log('🔧 Initializing GIF PNG Sequence Converter');
        
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }
    
    init() {
        console.log('📋 Finding DOM elements...');
        this.findElements();
        this.bindEvents();
        this.setupDragAndDrop();
        this.initializeUI();
        console.log('✅ GIF PNG Converter initialized successfully');
    }
    
    findElements() {
        // Mode buttons
        this.gifToPngModeBtn = document.getElementById('gifToPngMode');
        this.pngToGifModeBtn = document.getElementById('pngToGifMode');
        
        // Upload zones
        this.gifUploadZone = document.getElementById('gifUploadZone');
        this.pngUploadZone = document.getElementById('pngUploadZone');
        this.gifDropzone = document.getElementById('gifDropzone');
        this.pngDropzone = document.getElementById('pngDropzone');
        
        // File inputs
        this.gifFileInput = document.getElementById('gifFileInput');
        this.pngFileInput = document.getElementById('pngFileInput');
        
        // UI elements
        this.uploadTitle = document.getElementById('uploadTitle');
        this.fileList = document.getElementById('fileList');
        this.conversionSettings = document.getElementById('conversionSettings');
        this.convertSection = document.getElementById('convertSection');
        this.convertBtn = document.getElementById('convertBtn');
        this.convertBtnText = document.getElementById('convertBtnText');
        
        // Progress elements
        this.progressSection = document.getElementById('progressSection');
        this.progressBar = document.getElementById('progressBar');
        this.progressText = document.getElementById('progressText');
        this.progressStatus = document.getElementById('progressStatus');
        
        // Settings elements
        this.gifSettings = document.getElementById('gifSettings');
        this.pngSettings = document.getElementById('pngSettings');
        this.frameDurationValue = document.getElementById('frameDurationValue');
        
        // Results elements
        this.noResults = document.getElementById('noResults');
        this.resultsContent = document.getElementById('resultsContent');
        this.conversionType = document.getElementById('conversionType');
        this.frameCount = document.getElementById('frameCount');
        this.totalSize = document.getElementById('totalSize');
        this.conversionStatus = document.getElementById('conversionStatus');
        
        // Download elements
        this.downloadBtn = document.getElementById('downloadBtn');
        this.downloadBtnText = document.getElementById('downloadBtnText');
        this.newConversionBtn = document.getElementById('newConversionBtn');
        
        // Error modal elements
        this.errorModal = document.getElementById('errorModal');
        this.errorMessage = document.getElementById('errorMessage');
        this.errorModalClose = document.getElementById('errorModalClose');
        this.errorModalCloseBtn = document.getElementById('errorModalCloseBtn');
        
        // Log which elements were found
        const elements = [
            'gifToPngModeBtn', 'pngToGifModeBtn', 'gifUploadZone', 'pngUploadZone',
            'gifFileInput', 'pngFileInput', 'convertBtn', 'downloadBtn', 'errorModal'
        ];
        elements.forEach(elem => {
            if (this[elem]) {
                console.log(`✅ Found element: ${elem}`);
            } else {
                console.warn(`❌ Missing element: ${elem}`);
            }
        });
    }
    
    bindEvents() {
        console.log('🔗 Binding events...');
        
        // Mode switching
        if (this.gifToPngModeBtn) {
            this.gifToPngModeBtn.addEventListener('click', () => {
                console.log('📝 Switching to GIF to PNG mode');
                this.switchMode('gif-to-png');
            });
        }
        
        if (this.pngToGifModeBtn) {
            this.pngToGifModeBtn.addEventListener('click', () => {
                console.log('📝 Switching to PNG to GIF mode');
                this.switchMode('png-to-gif');
            });
        }
        
        // File input events
        if (this.gifFileInput) {
            this.gifFileInput.addEventListener('change', (e) => {
                console.log('📁 GIF file selected:', e.target.files.length);
                this.handleFileSelect(e);
            });
        }
        
        if (this.pngFileInput) {
            this.pngFileInput.addEventListener('change', (e) => {
                console.log('📁 PNG files selected:', e.target.files.length);
                this.handleFileSelect(e);
            });
        }
        
        // Dropzone clicks
        if (this.gifDropzone) {
            this.gifDropzone.addEventListener('click', () => {
                console.log('🖱️ GIF dropzone clicked');
                if (this.gifFileInput) this.gifFileInput.click();
            });
        }
        
        if (this.pngDropzone) {
            this.pngDropzone.addEventListener('click', () => {
                console.log('🖱️ PNG dropzone clicked');
                if (this.pngFileInput) this.pngFileInput.click();
            });
        }
        
        // Convert button
        if (this.convertBtn) {
            this.convertBtn.addEventListener('click', () => {
                console.log('🔄 Convert button clicked');
                this.startConversion();
            });
        }
        
        // Frame duration slider
        const frameDuration = document.getElementById('frameDuration');
        if (frameDuration && this.frameDurationValue) {
            frameDuration.addEventListener('input', (e) => {
                this.frameDurationValue.textContent = e.target.value;
            });
        }
        
        // Download and new conversion buttons
        if (this.downloadBtn) {
            this.downloadBtn.addEventListener('click', () => {
                console.log('💾 Download button clicked');
                this.downloadResult();
            });
        }
        
        if (this.newConversionBtn) {
            this.newConversionBtn.addEventListener('click', () => {
                console.log('🆕 New conversion button clicked');
                this.resetConverter();
            });
        }
        
        // Modal close events
        if (this.errorModalClose) {
            this.errorModalClose.addEventListener('click', () => {
                this.hideModal();
            });
        }
        
        if (this.errorModalCloseBtn) {
            this.errorModalCloseBtn.addEventListener('click', () => {
                this.hideModal();
            });
        }
        
        console.log('✅ Events bound successfully');
    }
    
    setupDragAndDrop() {
        console.log('🎯 Setting up drag and drop...');
        
        // GIF dropzone
        if (this.gifDropzone) {
            this.setupDropzoneEvents(this.gifDropzone, (files) => {
                console.log('📂 GIF files dropped:', files.length);
                if (files.length > 1) {
                    this.showError('Please select only one GIF file');
                    return;
                }
                this.handleFiles(files);
            });
        }
        
        // PNG dropzone  
        if (this.pngDropzone) {
            this.setupDropzoneEvents(this.pngDropzone, (files) => {
                console.log('📂 PNG files dropped:', files.length);
                if (files.length > 500) {
                    this.showError('Please select no more than 500 files');
                    return;
                }
                this.handleFiles(files);
            });
        }
    }
    
    setupDropzoneEvents(element, callback) {
        const events = ['dragenter', 'dragover', 'dragleave', 'drop'];
        
        events.forEach(eventName => {
            element.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });
        
        element.addEventListener('dragover', () => {
            element.classList.add('dragover');
        });
        
        element.addEventListener('dragleave', () => {
            element.classList.remove('dragover');
        });
        
        element.addEventListener('drop', (e) => {
            element.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files);
            callback(files);
        });
    }
    
    initializeUI() {
        console.log('🎨 Initializing UI...');
        this.switchMode('gif-to-png');
    }
    
    switchMode(mode) {
        console.log(`🔄 Switching to mode: ${mode}`);
        this.currentMode = mode;
        
        // Update mode buttons
        if (this.gifToPngModeBtn && this.pngToGifModeBtn) {
            this.gifToPngModeBtn.classList.toggle('active', mode === 'gif-to-png');
            this.pngToGifModeBtn.classList.toggle('active', mode === 'png-to-gif');
        }
        
        // Update upload zones
        if (this.gifUploadZone && this.pngUploadZone) {
            this.gifUploadZone.classList.toggle('active', mode === 'gif-to-png');
            this.pngUploadZone.classList.toggle('active', mode === 'png-to-gif');
        }
        
        // Update settings visibility
        if (this.gifSettings && this.pngSettings) {
            this.gifSettings.style.display = mode === 'gif-to-png' ? 'block' : 'none';
            this.pngSettings.style.display = mode === 'png-to-gif' ? 'block' : 'none';
        }
        
        // Update text content
        if (this.uploadTitle) {
            this.uploadTitle.textContent = mode === 'gif-to-png' ? 'Upload GIF File' : 'Upload Image Files';
        }
        if (this.convertBtnText) {
            this.convertBtnText.textContent = mode === 'gif-to-png' ? 'Convert GIF to PNG' : 'Convert PNG to GIF';
        }
        if (this.downloadBtnText) {
            this.downloadBtnText.textContent = mode === 'gif-to-png' ? 'Download ZIP' : 'Download GIF';
        }
        
        // Reset upload state
        this.resetUpload();
    }
    
    handleFileSelect(event) {
        const files = Array.from(event.target.files);
        console.log(`📁 Files selected via input:`, files.length);
        this.handleFiles(files);
    }
    
    handleFiles(files) {
        console.log(`📋 Processing ${files.length} files for mode: ${this.currentMode}`);
        
        if (!this.validateFiles(files)) {
            return;
        }
        
        this.uploadedFiles = files;
        this.displayFileList();
        this.showConversionSettings();
        this.showConvertButton();
        
        console.log('✅ Files processed successfully');
    }
    
    validateFiles(files) {
        if (files.length === 0) {
            this.showError('No files selected');
            return false;
        }
        
        if (this.currentMode === 'gif-to-png') {
            if (files.length > 1) {
                this.showError('Please select only one GIF file');
                return false;
            }
            
            const file = files[0];
            if (!file.type.includes('gif') && !file.name.toLowerCase().endsWith('.gif')) {
                this.showError('Please select a valid GIF file');
                return false;
            }
            
            if (file.size > 50 * 1024 * 1024) {
                this.showError('GIF file must be smaller than 50MB');
                return false;
            }
        } else {
            if (files.length > 500) {
                this.showError('Please select no more than 500 files');
                return false;
            }
            
            for (const file of files) {
                if (!file.type.includes('image')) {
                    this.showError(`File "${file.name}" is not a valid image file`);
                    return false;
                }
                
                if (file.size > 50 * 1024 * 1024) {
                    this.showError(`File "${file.name}" is too large (max 50MB per file)`);
                    return false;
                }
            }
        }
        
        console.log('✅ File validation passed');
        return true;
    }
    
    displayFileList() {
        if (!this.fileList || this.uploadedFiles.length === 0) {
            if (this.fileList) this.fileList.style.display = 'none';
            return;
        }
        
        let html = '<h5><i class="fas fa-files me-2"></i>Selected Files</h5>';
        
        if (this.currentMode === 'gif-to-png') {
            const file = this.uploadedFiles[0];
            html += `
                <div class="file-item">
                    <div class="file-info">
                        <i class="fas fa-film me-2"></i>
                        <span class="file-name">${file.name}</span>
                        <span class="file-size">${this.formatFileSize(file.size)}</span>
                    </div>
                </div>
            `;
        } else {
            html += `<div class="file-count">${this.uploadedFiles.length} files selected</div>`;
            
            for (let i = 0; i < Math.min(this.uploadedFiles.length, 5); i++) {
                const file = this.uploadedFiles[i];
                html += `
                    <div class="file-item">
                        <div class="file-info">
                            <i class="fas fa-image me-2"></i>
                            <span class="file-name">${file.name}</span>
                            <span class="file-size">${this.formatFileSize(file.size)}</span>
                        </div>
                    </div>
                `;
            }
            
            if (this.uploadedFiles.length > 5) {
                html += `<div class="more-files">... and ${this.uploadedFiles.length - 5} more files</div>`;
            }
        }
        
        this.fileList.innerHTML = html;
        this.fileList.style.display = 'block';
    }
    
    showConversionSettings() {
        if (this.conversionSettings) {
            this.conversionSettings.style.display = 'block';
        }
    }
    
    showConvertButton() {
        if (this.convertSection) {
            this.convertSection.style.display = 'block';
        }
    }
    
    async startConversion() {
        if (this.isProcessing || this.uploadedFiles.length === 0) {
            console.warn('⚠️ Cannot start conversion - already processing or no files');
            return;
        }
        
        console.log('🚀 Starting conversion...');
        this.isProcessing = true;
        
        if (this.convertBtn) this.convertBtn.disabled = true;
        this.showProgress(10, 'Preparing conversion...');
        
        try {
            const formData = new FormData();
            
            if (this.currentMode === 'gif-to-png') {
                console.log('📤 Uploading GIF file for conversion');
                formData.append('gif_file', this.uploadedFiles[0]);
                
                // Add settings
                const preserveTiming = document.getElementById('preserveTiming');
                const optimizePng = document.getElementById('optimizePng');
                
                formData.append('preserve_timing', preserveTiming ? preserveTiming.checked : true);
                formData.append('optimize_png', optimizePng ? optimizePng.checked : true);
                
                await this.convertGifToPng(formData);
            } else {
                console.log('📤 Uploading PNG files for GIF creation');
                
                // Add all image files
                for (const file of this.uploadedFiles) {
                    formData.append('image_files', file);
                }
                
                // Add settings
                const frameDuration = document.getElementById('frameDuration');
                const loopCount = document.getElementById('loopCount');
                const quality = document.getElementById('quality');
                const optimizeGif = document.getElementById('optimizeGif');
                const enableDithering = document.getElementById('enableDithering');
                
                formData.append('frame_duration', frameDuration ? frameDuration.value : 100);
                formData.append('loop_count', loopCount ? loopCount.value : 0);
                formData.append('quality', quality ? quality.value : 'medium');
                formData.append('optimize', optimizeGif ? optimizeGif.checked : true);
                formData.append('dithering', enableDithering ? enableDithering.checked : false);
                
                await this.convertPngToGif(formData);
            }
        } catch (error) {
            console.error('❌ Conversion error:', error);
            this.showError('Conversion failed. Please try again.');
            this.resetProgress();
        }
    }
    
    async convertGifToPng(formData) {
        this.showProgress(50, 'Converting GIF to PNG frames...');
        
        try {
            const response = await fetch('/gif-png-sequence/convert/gif-to-png', {
                method: 'POST',
                body: formData
            });
            
            console.log('📨 Response status:', response.status);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            const result = await response.json();
            console.log('✅ GIF to PNG conversion result:', result);
            
            if (!result.success) {
                throw new Error(result.error || 'Conversion failed');
            }
            
            this.showProgress(100, 'Conversion completed!');
            this.showResults(result);
            
        } catch (error) {
            console.error('❌ GIF to PNG conversion error:', error);
            this.showError(error.message || 'Failed to convert GIF to PNG sequence');
            this.resetProgress();
        }
    }
    
    async convertPngToGif(formData) {
        this.showProgress(50, 'Creating GIF from image sequence...');
        
        try {
            const response = await fetch('/gif-png-sequence/convert/png-to-gif', {
                method: 'POST',
                body: formData
            });
            
            console.log('📨 Response status:', response.status);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            const result = await response.json();
            console.log('✅ PNG to GIF conversion result:', result);
            
            if (!result.success) {
                throw new Error(result.error || 'Conversion failed');
            }
            
            this.showProgress(100, 'Conversion completed!');
            this.showResults(result);
            
        } catch (error) {
            console.error('❌ PNG to GIF conversion error:', error);
            this.showError(error.message || 'Failed to convert PNG sequence to GIF');
            this.resetProgress();
        }
    }
    
    showResults(result) {
        console.log('📊 Showing conversion results:', result);
        
        // Hide progress and show results
        this.hideProgress();
        if (this.noResults) this.noResults.style.display = 'none';
        if (this.resultsContent) this.resultsContent.style.display = 'block';
        
        // Update conversion info
        if (this.conversionType) {
            this.conversionType.textContent = this.currentMode === 'gif-to-png' ? 'GIF → PNG' : 'PNG → GIF';
        }
        if (this.frameCount) {
            this.frameCount.textContent = result.frame_count || 'N/A';
        }
        if (this.totalSize) {
            this.totalSize.textContent = this.formatFileSize(result.file_size || 0);
        }
        if (this.conversionStatus) {
            this.conversionStatus.className = 'badge bg-success';
            this.conversionStatus.textContent = 'Complete';
        }
        
        // Store conversion ID for download
        this.currentConversionId = result.conversion_id;
        
        this.isProcessing = false;
        if (this.convertBtn) this.convertBtn.disabled = false;
        
        console.log('✅ Results displayed successfully');
    }
    
    downloadResult() {
        if (!this.currentConversionId) {
            console.warn('⚠️ No conversion ID available for download');
            return;
        }
        
        console.log('💾 Starting download for conversion:', this.currentConversionId);
        
        const resultType = this.currentMode === 'gif-to-png' ? 'zip' : 'gif';
        const downloadUrl = `/gif-png-sequence/download/${this.currentConversionId}/${resultType}`;
        
        console.log('🔗 Download URL:', downloadUrl);
        
        // Create download link
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = '';
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log('✅ Download initiated');
    }
    
    resetConverter() {
        console.log('🔄 Resetting converter state');
        
        this.uploadedFiles = [];
        this.currentConversionId = null;
        this.isProcessing = false;
        
        this.resetUpload();
        this.resetResults();
        this.resetProgress();
        
        console.log('✅ Converter reset complete');
    }
    
    resetUpload() {
        if (this.fileList) this.fileList.style.display = 'none';
        if (this.conversionSettings) this.conversionSettings.style.display = 'none';
        if (this.convertSection) this.convertSection.style.display = 'none';
        if (this.convertBtn) this.convertBtn.disabled = false;
        
        if (this.gifFileInput) this.gifFileInput.value = '';
        if (this.pngFileInput) this.pngFileInput.value = '';
    }
    
    resetResults() {
        if (this.resultsContent) this.resultsContent.style.display = 'none';
        if (this.noResults) this.noResults.style.display = 'block';
    }
    
    resetProgress() {
        this.hideProgress();
        this.isProcessing = false;
        if (this.convertBtn) this.convertBtn.disabled = false;
    }
    
    showProgress(percentage, status) {
        if (this.progressSection) this.progressSection.style.display = 'block';
        if (this.progressBar) this.progressBar.style.width = `${percentage}%`;
        if (this.progressText) this.progressText.textContent = `${percentage}%`;
        if (this.progressStatus) this.progressStatus.textContent = status;
        
        if (percentage === 100 && this.progressBar) {
            this.progressBar.classList.remove('progress-bar-animated');
        }
    }
    
    hideProgress() {
        if (this.progressSection) this.progressSection.style.display = 'none';
        if (this.progressBar) {
            this.progressBar.style.width = '0%';
            this.progressBar.classList.add('progress-bar-animated');
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showError(message) {
        console.error('❌ Error:', message);
        
        if (this.errorMessage && this.errorModal) {
            this.errorMessage.textContent = message;
            this.showModal();
        } else {
            alert(message);
        }
    }
    
    showModal() {
        if (this.errorModal) {
            this.errorModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }
    
    hideModal() {
        if (this.errorModal) {
            this.errorModal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }
}
