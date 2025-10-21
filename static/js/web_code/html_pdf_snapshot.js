/**
 * HTML PDF Snapshot Converter JavaScript
 * Handles user interactions, form validation, and conversion process
 */

class HTMLPDFSnapshotConverter {
    constructor() {
        this.currentMode = 'url';
        this.isConverting = false;
        this.backendInfo = null;
        this.validationCache = new Map();
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initializeDragAndDrop();
        this.updateUI();
        console.log('HTML PDF Snapshot Converter initialized');
    }
    
    bindEvents() {
        // Conversion type selection
        document.querySelectorAll('.type-option').forEach(option => {
            option.addEventListener('click', (e) => {
                this.switchConversionType(e.currentTarget.dataset.type);
            });
        });
        
        // URL input and preview
        const urlInput = document.getElementById('urlInput');
        if (urlInput) {
            urlInput.addEventListener('input', () => this.validateUrl());
            urlInput.addEventListener('blur', () => this.validateUrl());
        }
        
        const previewBtn = document.getElementById('previewBtn');
        if (previewBtn) {
            previewBtn.addEventListener('click', () => this.previewUrl());
        }
        
        // File input
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }
        
        // Content input
        const contentInput = document.getElementById('contentInput');
        if (contentInput) {
            contentInput.addEventListener('input', () => this.updateContentStats());
            contentInput.addEventListener('paste', () => {
                setTimeout(() => this.updateContentStats(), 100);
            });
        }
        
        // Content validation and formatting
        const validateBtn = document.getElementById('validate-content');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => this.validateContent());
        }
        
        const formatBtn = document.getElementById('format-content');
        if (formatBtn) {
            formatBtn.addEventListener('click', () => this.formatContent());
        }
        
        // Settings
        const scaleSlider = document.getElementById('scaleFactor');
        if (scaleSlider) {
            scaleSlider.addEventListener('input', (e) => this.updateScaleValue(e));
        }
        
        const waitForLoad = document.getElementById('waitForLoad');
        if (waitForLoad) {
            waitForLoad.addEventListener('change', (e) => this.toggleWaitTime(e));
        }
        
        // Advanced settings toggle
        const advancedToggle = document.getElementById('advancedToggle');
        if (advancedToggle) {
            advancedToggle.addEventListener('click', () => this.toggleAdvancedSettings());
        }
        
        // Convert button
        const convertBtn = document.getElementById('convertBtn');
        if (convertBtn) {
            convertBtn.addEventListener('click', () => this.startConversion());
        }
        
        // Result actions
        const convertAnotherBtn = document.getElementById('convert-another');
        if (convertAnotherBtn) {
            convertAnotherBtn.addEventListener('click', () => this.resetForm());
        }
        
        const retryBtn = document.getElementById('retry-conversion');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => this.retryConversion());
        }
    }
    
    initializeDragAndDrop() {
        const uploadZone = document.getElementById('uploadZone');
        if (!uploadZone) return;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.add('dragover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, () => {
                uploadZone.classList.remove('dragover');
            }, false);
        });
        
        uploadZone.addEventListener('drop', (e) => this.handleDrop(e), false);
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    handleDrop(e) {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const fileInput = document.getElementById('fileInput');
            if (fileInput) {
                fileInput.files = files;
                this.handleFileSelect({ target: { files } });
            }
        }
    }
    
    switchConversionType(type) {
        // Update current mode
        this.currentMode = type;
        
        // Update UI
        document.querySelectorAll('.type-option').forEach(option => {
            option.classList.remove('active');
        });
        document.querySelector(`[data-type="${type}"]`).classList.add('active');
        
        // Show/hide input sections
        document.querySelectorAll('.input-section').forEach(section => {
            section.style.display = 'none';
            section.classList.remove('active');
        });
        
        const activeSection = document.getElementById(`${type}-section`);
        if (activeSection) {
            activeSection.style.display = 'block';
            activeSection.classList.add('active');
        }
        
        // Reset results
        this.hideResults();
        
        // Update convert button
        this.updateConvertButton();
    }
    
    validateUrl() {
        const urlInput = document.getElementById('urlInput');
        const validation = document.getElementById('url-validation');
        
        if (!urlInput || !validation) return;
        
        const url = urlInput.value.trim();
        
        if (!url) {
            validation.textContent = '';
            validation.className = 'validation-message';
            return false;
        }
        
        try {
            const urlObj = new URL(url);
            
            if (!['http:', 'https:'].includes(urlObj.protocol)) {
                validation.textContent = 'Only HTTP and HTTPS URLs are supported';
                validation.className = 'validation-message invalid';
                return false;
            }
            
            // Check for localhost/private IPs
            const hostname = urlObj.hostname.toLowerCase();
            if (['localhost', '127.0.0.1', '0.0.0.0'].includes(hostname)) {
                validation.textContent = 'Local URLs are not allowed for security reasons';
                validation.className = 'validation-message invalid';
                return false;
            }
            
            validation.textContent = 'Valid URL';
            validation.className = 'validation-message valid';
            return true;
            
        } catch (error) {
            validation.textContent = 'Invalid URL format';
            validation.className = 'validation-message invalid';
            return false;
        }
    }
    
    async previewUrl() {
        const urlInput = document.getElementById('urlInput');
        const previewContainer = document.getElementById('url-preview');
        
        if (!urlInput || !previewContainer) return;
        
        const url = urlInput.value.trim();
        
        if (!url || !this.validateUrl()) {
            this.showNotification('Please enter a valid URL first', 'error');
            return;
        }
        
        try {
            // Show loading state
            previewContainer.innerHTML = `
                <div class="preview-content">
                    <div class="preview-icon">
                        <i class="fas fa-spinner fa-spin"></i>
                    </div>
                    <div class="preview-details">
                        <h4>Loading preview...</h4>
                        <p>Fetching page information...</p>
                    </div>
                </div>
            `;
            previewContainer.style.display = 'block';
            
            const response = await fetch('/html-pdf-snapshot/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const preview = data.preview;
                
                previewContainer.innerHTML = `
                    <div class="preview-content">
                        <div class="preview-icon">
                            ${preview.favicon ? 
                                `<img src="${preview.favicon}" alt="Favicon" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                                 <i class="fas fa-globe default-icon" style="display: none;"></i>` :
                                `<i class="fas fa-globe default-icon"></i>`
                            }
                        </div>
                        <div class="preview-details">
                            <h4>${preview.title || 'Untitled'}</h4>
                            <p>${preview.description || 'No description available'}</p>
                            <small>Size: ${this.formatBytes(preview.content_length || 0)} | Status: ${preview.status_code || 'Unknown'}</small>
                        </div>
                    </div>
                `;
            } else {
                throw new Error(data.error || 'Preview failed');
            }
            
        } catch (error) {
            console.error('Preview error:', error);
            previewContainer.innerHTML = `
                <div class="preview-content">
                    <div class="preview-icon">
                        <i class="fas fa-exclamation-triangle" style="color: #ef4444;"></i>
                    </div>
                    <div class="preview-details">
                        <h4>Preview Failed</h4>
                        <p>${error.message}</p>
                    </div>
                </div>
            `;
            previewContainer.style.display = 'block';
        }
    }
    
    handleFileSelect(e) {
        const files = e.target.files;
        const fileList = document.getElementById('fileList');
        
        if (!files.length || !fileList) return;
        
        fileList.innerHTML = '';
        
        Array.from(files).forEach((file, index) => {
            const fileItem = this.createFileItem(file, index);
            fileList.appendChild(fileItem);
        });
        
        fileList.style.display = 'block';
        this.updateConvertButton();
    }
    
    createFileItem(file, index) {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `
            <div class="file-info">
                <div class="file-icon">
                    <i class="fas fa-file-code"></i>
                </div>
                <div class="file-details">
                    <h4>${file.name}</h4>
                    <p>${this.formatBytes(file.size)} | ${file.type || 'HTML file'}</p>
                </div>
            </div>
            <div class="file-actions">
                <button type="button" class="btn btn-secondary remove-file" data-index="${index}">
                    <i class="fas fa-times"></i> Remove
                </button>
            </div>
        `;
        
        // Bind remove event
        const removeBtn = item.querySelector('.remove-file');
        removeBtn.addEventListener('click', () => this.removeFile(index));
        
        return item;
    }
    
    removeFile(index) {
        const fileInput = document.getElementById('fileInput');
        const fileList = document.getElementById('fileList');
        
        if (!fileInput || !fileList) return;
        
        // Create new FileList without the removed file
        const dt = new DataTransfer();
        const files = Array.from(fileInput.files);
        
        files.forEach((file, i) => {
            if (i !== index) {
                dt.items.add(file);
            }
        });
        
        fileInput.files = dt.files;
        
        // Update file list display
        if (fileInput.files.length === 0) {
            fileList.style.display = 'none';
        } else {
            this.handleFileSelect({ target: fileInput });
        }
        
        this.updateConvertButton();
    }
    
    updateContentStats() {
        const contentInput = document.getElementById('contentInput');
        const charCount = document.getElementById('char-count');
        const wordCount = document.getElementById('word-count');
        const estimatedPages = document.getElementById('estimated-pages');
        
        if (!contentInput) return;
        
        const content = contentInput.value;
        const chars = content.length;
        const words = content.trim() ? content.trim().split(/\s+/).length : 0;
        const pages = Math.max(1, Math.ceil(chars / 3000)); // Rough estimate
        
        if (charCount) charCount.textContent = chars.toLocaleString();
        if (wordCount) wordCount.textContent = words.toLocaleString();
        if (estimatedPages) estimatedPages.textContent = `~${pages}`;
        
        this.updateConvertButton();
    }
    
    async validateContent() {
        const contentInput = document.getElementById('contentInput');
        const validationContainer = document.getElementById('content-validation');
        
        if (!contentInput || !validationContainer) return;
        
        const content = contentInput.value.trim();
        
        if (!content) {
            validationContainer.style.display = 'none';
            return;
        }
        
        try {
            validationContainer.innerHTML = `
                <div class="validation-item">
                    <i class="fas fa-spinner fa-spin"></i>
                    <span>Validating HTML content...</span>
                </div>
            `;
            validationContainer.style.display = 'block';
            
            const response = await fetch('/html-pdf-snapshot/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content, type: 'html' })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const validation = data.validation;
                let validationHtml = '';
                
                if (validation.valid) {
                    validationHtml += `
                        <div class="validation-item">
                            <i class="fas fa-check-circle" style="color: #10b981;"></i>
                            <span>HTML content is valid</span>
                        </div>
                    `;
                }
                
                if (validation.warnings && validation.warnings.length > 0) {
                    validation.warnings.forEach(warning => {
                        validationHtml += `
                            <div class="validation-item">
                                <i class="fas fa-exclamation-triangle" style="color: #f59e0b;"></i>
                                <span>${warning}</span>
                            </div>
                        `;
                    });
                }
                
                if (validation.errors && validation.errors.length > 0) {
                    validation.errors.forEach(error => {
                        validationHtml += `
                            <div class="validation-item">
                                <i class="fas fa-times-circle" style="color: #ef4444;"></i>
                                <span>${error}</span>
                            </div>
                        `;
                    });
                }
                
                validationContainer.innerHTML = validationHtml;
                validationContainer.className = `validation-results ${validation.valid ? 'valid' : 'invalid'}`;
                
            } else {
                throw new Error(data.error || 'Validation failed');
            }
            
        } catch (error) {
            console.error('Validation error:', error);
            validationContainer.innerHTML = `
                <div class="validation-item">
                    <i class="fas fa-times-circle" style="color: #ef4444;"></i>
                    <span>Validation failed: ${error.message}</span>
                </div>
            `;
            validationContainer.className = 'validation-results invalid';
        }
    }
    
    formatContent() {
        const contentInput = document.getElementById('contentInput');
        if (!contentInput) return;
        
        const content = contentInput.value;
        if (!content.trim()) return;
        
        try {
            // Basic HTML formatting
            let formatted = content
                .replace(/></g, '>\n<')
                .replace(/^\s+|\s+$/gm, '')
                .split('\n')
                .map(line => line.trim())
                .filter(line => line.length > 0)
                .join('\n');
            
            // Basic indentation
            let indentLevel = 0;
            const lines = formatted.split('\n');
            const formattedLines = [];
            
            lines.forEach(line => {
                if (line.startsWith('</')) {
                    indentLevel = Math.max(0, indentLevel - 1);
                }
                
                formattedLines.push('  '.repeat(indentLevel) + line);
                
                if (line.startsWith('<') && !line.startsWith('</') && !line.endsWith('/>')) {
                    indentLevel++;
                }
            });
            
            contentInput.value = formattedLines.join('\n');
            this.updateContentStats();
            this.showNotification('Content formatted successfully', 'success');
            
        } catch (error) {
            console.error('Format error:', error);
            this.showNotification('Failed to format content', 'error');
        }
    }
    
    updateScaleValue(e) {
        const scaleValue = document.getElementById('scale-value');
        if (scaleValue) {
            scaleValue.textContent = `${parseFloat(e.target.value).toFixed(1)}x`;
        }
    }
    
    toggleWaitTime(e) {
        const waitTimeGroup = document.getElementById('wait-time-group');
        if (waitTimeGroup) {
            waitTimeGroup.style.display = e.target.checked ? 'block' : 'none';
        }
    }
    
    toggleAdvancedSettings() {
        const toggle = document.getElementById('advancedToggle');
        const content = document.getElementById('advancedContent');
        
        if (!toggle || !content) return;
        
        const isExpanded = content.style.display === 'block';
        
        content.style.display = isExpanded ? 'none' : 'block';
        toggle.classList.toggle('expanded', !isExpanded);
    }
    
    updateConvertButton() {
        const convertBtn = document.getElementById('convertBtn');
        if (!convertBtn) return;
        
        const canConvert = this.canConvert();
        convertBtn.disabled = !canConvert || this.isConverting;
        
        if (!canConvert) {
            convertBtn.querySelector('span').textContent = 'Enter Input First';
        } else if (this.isConverting) {
            convertBtn.querySelector('span').textContent = 'Converting...';
        } else {
            convertBtn.querySelector('span').textContent = 'Convert to PDF';
        }
    }
    
    canConvert() {
        switch (this.currentMode) {
            case 'url':
                const urlInput = document.getElementById('urlInput');
                return urlInput && urlInput.value.trim() && this.validateUrl();
                
            case 'file':
                const fileInput = document.getElementById('fileInput');
                return fileInput && fileInput.files && fileInput.files.length > 0;
                
            case 'content':
                const contentInput = document.getElementById('contentInput');
                return contentInput && contentInput.value.trim();
                
            default:
                return false;
        }
    }
    
    async startConversion() {
        if (this.isConverting || !this.canConvert()) return;
        
        this.isConverting = true;
        this.showProgress();
        this.updateConvertButton();
        
        try {
            const formData = this.buildFormData();
            
            this.updateProgress(20, 'Preparing conversion...');
            
            const response = await fetch('/html-pdf-snapshot/convert', {
                method: 'POST',
                body: formData
            });
            
            this.updateProgress(60, 'Generating PDF...');
            
            if (response.ok) {
                this.updateProgress(90, 'Finalizing...');
                
                // Handle JSON response
                const data = await response.json();
                
                if (data.success) {
                    this.updateProgress(100, 'Complete!');
                    
                    setTimeout(() => {
                        this.showSuccess({
                            filename: data.converted_info.filename,
                            size: data.stats.converted_size,
                            processing_time: data.stats.processing_time,
                            backend: data.stats.backend,
                            download_url: data.download_url
                        });
                    }, 500);
                } else {
                    throw new Error(data.error || 'Conversion failed');
                }
                
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Conversion failed');
            }
            
        } catch (error) {
            console.error('Conversion error:', error);
            this.showError(error.message || 'An unexpected error occurred');
        } finally {
            this.isConverting = false;
            this.hideProgress();
            this.updateConvertButton();
        }
    }
    
    buildFormData() {
        const formData = new FormData();
        
        // Add conversion mode
        formData.append('conversion_mode', this.currentMode);
        
        // Add input data based on mode
        switch (this.currentMode) {
            case 'url':
                const url = document.getElementById('urlInput').value.trim();
                formData.append('url', url);
                break;
                
            case 'file':
                const fileInput = document.getElementById('fileInput');
                if (fileInput.files.length > 0) {
                    formData.append('file', fileInput.files[0]);
                }
                break;
                
            case 'content':
                const content = document.getElementById('contentInput').value;
                formData.append('content', content);
                break;
        }
        
        // Add settings
        this.addSettingsToFormData(formData);
        
        return formData;
    }
    
    addSettingsToFormData(formData) {
        // Page settings
        const pageSize = document.getElementById('pageSize');
        if (pageSize) formData.append('page_size', pageSize.value);
        
        const orientation = document.getElementById('orientation');
        if (orientation) formData.append('orientation', orientation.value);
        
        // Margins
        const marginTop = document.getElementById('marginTop');
        if (marginTop) formData.append('margin_top', marginTop.value);
        
        const marginBottom = document.getElementById('marginBottom');
        if (marginBottom) formData.append('margin_bottom', marginBottom.value);
        
        const marginLeft = document.getElementById('marginLeft');
        if (marginLeft) formData.append('margin_left', marginLeft.value);
        
        const marginRight = document.getElementById('marginRight');
        if (marginRight) formData.append('margin_right', marginRight.value);
        
        // Viewport
        const viewportWidth = document.getElementById('viewportWidth');
        if (viewportWidth) formData.append('viewport_width', viewportWidth.value);
        
        const viewportHeight = document.getElementById('viewportHeight');
        if (viewportHeight) formData.append('viewport_height', viewportHeight.value);
        
        // Rendering options
        const fullPage = document.getElementById('fullPage');
        if (fullPage) formData.append('full_page', fullPage.checked);
        
        const backgroundGraphics = document.getElementById('backgroundGraphics');
        if (backgroundGraphics) formData.append('background_graphics', backgroundGraphics.checked);
        
        const waitForLoad = document.getElementById('waitForLoad');
        if (waitForLoad) formData.append('wait_for_load', waitForLoad.checked);
        
        const waitTime = document.getElementById('waitTime');
        if (waitTime) formData.append('wait_time', waitTime.value);
        
        const scaleFactor = document.getElementById('scaleFactor');
        if (scaleFactor) formData.append('scale_factor', scaleFactor.value);
        
        // Advanced settings
        const customCss = document.getElementById('customCss');
        if (customCss && customCss.value.trim()) {
            formData.append('custom_css', customCss.value);
        }
        
        const headerHtml = document.getElementById('headerHtml');
        if (headerHtml && headerHtml.value.trim()) {
            formData.append('header_html', headerHtml.value);
        }
        
        const footerHtml = document.getElementById('footerHtml');
        if (footerHtml && footerHtml.value.trim()) {
            formData.append('footer_html', footerHtml.value);
        }
    }
    
    showProgress() {
        const progress = document.getElementById('conversionProgress');
        const progressText = document.getElementById('progressText');
        
        if (progress) {
            progress.style.display = 'block';
            this.updateProgress(0, 'Starting conversion...');
        }
    }
    
    hideProgress() {
        const progress = document.getElementById('conversionProgress');
        if (progress) {
            progress.style.display = 'none';
        }
    }
    
    updateProgress(percent, text) {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (progressBar) {
            progressBar.style.width = `${percent}%`;
        }
        
        if (progressText) {
            progressText.textContent = text;
        }
    }
    
    showSuccess(stats) {
        const resultsSection = document.getElementById('resultsSection');
        const successResult = document.getElementById('success-result');
        const errorResult = document.getElementById('error-result');
        
        if (!resultsSection) {
            // Create results section if it doesn't exist
            this.createResultsSection(stats);
            return;
        }
        
        if (successResult) {
            // Hide error result
            if (errorResult) errorResult.style.display = 'none';
            
            // Update success stats
            const resultSize = document.getElementById('result-size');
            const resultTime = document.getElementById('result-time');
            const resultBackend = document.getElementById('result-backend');
            
            if (resultSize) resultSize.textContent = stats.size;
            if (resultTime) resultTime.textContent = stats.processing_time;
            if (resultBackend) resultBackend.textContent = stats.backend;
            
            // Update download links if available
            if (stats.download_url) {
                const viewBtn = document.getElementById('view-pdf-btn');
                const downloadBtn = document.getElementById('download-pdf-btn');
                
                if (viewBtn) viewBtn.href = stats.download_url;
                if (downloadBtn) downloadBtn.href = stats.download_url + '?download=true';
            }
            
            // Show success result
            successResult.style.display = 'block';
            resultsSection.style.display = 'block';
        } else {
            // Create inline success message
            this.createInlineSuccessMessage(stats);
        }
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    showError(errorMessage) {
        const resultsSection = document.getElementById('resultsSection');
        const successResult = document.getElementById('success-result');
        const errorResult = document.getElementById('error-result');
        const errorText = document.getElementById('error-text');
        
        if (!resultsSection || !errorResult) return;
        
        // Hide success result
        if (successResult) successResult.style.display = 'none';
        
        // Update error message
        if (errorText) errorText.textContent = errorMessage;
        
        // Show error result
        errorResult.style.display = 'block';
        resultsSection.style.display = 'block';
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    hideResults() {
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'none';
        }
    }
    
    downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
    
    getFilenameFromResponse(response) {
        const contentDisposition = response.headers.get('Content-Disposition');
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch) {
                return filenameMatch[1].replace(/['"]/g, '');
            }
        }
        return null;
    }
    
    generateFilename() {
        const timestamp = new Date().toISOString().slice(0, 19).replace(/[:\-T]/g, '');
        
        switch (this.currentMode) {
            case 'url':
                const urlInput = document.getElementById('urlInput');
                if (urlInput) {
                    try {
                        const url = new URL(urlInput.value);
                        const domain = url.hostname.replace('www.', '');
                        return `pdf_snapshot_${domain}_${timestamp}.pdf`;
                    } catch {
                        return `pdf_snapshot_webpage_${timestamp}.pdf`;
                    }
                }
                break;
                
            case 'file':
                const fileInput = document.getElementById('fileInput');
                if (fileInput && fileInput.files.length > 0) {
                    const filename = fileInput.files[0].name.replace(/\.[^/.]+$/, '');
                    return `pdf_snapshot_${filename}_${timestamp}.pdf`;
                }
                break;
                
            case 'content':
                return `pdf_snapshot_content_${timestamp}.pdf`;
        }
        
        return `pdf_snapshot_${timestamp}.pdf`;
    }
    
    resetForm() {
        // Reset inputs
        const urlInput = document.getElementById('urlInput');
        if (urlInput) urlInput.value = '';
        
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.value = '';
        
        const contentInput = document.getElementById('contentInput');
        if (contentInput) contentInput.value = '';
        
        // Reset validation and preview
        const urlValidation = document.getElementById('url-validation');
        if (urlValidation) {
            urlValidation.textContent = '';
            urlValidation.className = 'validation-message';
        }
        
        const urlPreview = document.getElementById('url-preview');
        if (urlPreview) urlPreview.style.display = 'none';
        
        const fileList = document.getElementById('fileList');
        if (fileList) fileList.style.display = 'none';
        
        const contentValidation = document.getElementById('content-validation');
        if (contentValidation) contentValidation.style.display = 'none';
        
        // Reset stats
        this.updateContentStats();
        
        // Hide results
        this.hideResults();
        
        // Update UI
        this.updateConvertButton();
        
        this.showNotification('Form reset', 'info');
    }
    
    retryConversion() {
        this.hideResults();
        this.startConversion();
    }
    
    updateUI() {
        // Initialize with URL mode
        this.switchConversionType('url');
        
        // Initialize content stats
        this.updateContentStats();
        
        // Initialize scale value
        const scaleSlider = document.getElementById('scaleFactor');
        if (scaleSlider) {
            this.updateScaleValue({ target: scaleSlider });
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 3000);
        
        // Allow manual close
        notification.addEventListener('click', () => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        });
    }
    
    formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    createResultsSection(stats) {
        // Find the converter card to append results after it
        const converterCard = document.querySelector('.converter-card');
        if (!converterCard) return;
        
        // Create results section
        const resultsSection = document.createElement('div');
        resultsSection.id = 'resultsSection';
        resultsSection.className = 'results-section';
        resultsSection.innerHTML = this.createInlineSuccessMessage(stats, false);
        
        // Insert after converter card
        converterCard.parentNode.insertBefore(resultsSection, converterCard.nextSibling);
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    createInlineSuccessMessage(stats, standalone = true) {
        const content = `
            <div class="result-success">
                <div class="result-header">
                    <i class="fas fa-check-circle"></i>
                    <h3>Conversion Successful!</h3>
                </div>
                <div class="result-content">
                    <div class="result-file-info">
                        <div class="file-details">
                            <h4><i class="fas fa-file-pdf"></i> ${stats.filename}</h4>
                            <p>Size: ${stats.size} | Processing: ${stats.processing_time} | Backend: ${stats.backend}</p>
                        </div>
                    </div>
                    <div class="result-actions">
                        <a href="${stats.download_url}" class="btn btn-primary" target="_blank" id="view-pdf-btn">
                            <i class="fas fa-eye"></i> View PDF
                        </a>
                        <a href="${stats.download_url}?download=true" class="btn btn-secondary" download id="download-pdf-btn">
                            <i class="fas fa-download"></i> Download PDF
                        </a>
                        <button class="btn btn-secondary" onclick="htmlPdfConverter.resetForm()">
                            <i class="fas fa-plus"></i> Convert Another
                        </button>
                    </div>
                    <div class="result-tips">
                        <small class="text-muted">
                            <i class="fas fa-info-circle"></i> 
                            If PDF doesn't display in browser, try downloading it or opening in a different PDF viewer.
                        </small>
                    </div>
                </div>
            </div>
        `;
        
        if (standalone) {
            // Find the converter card to append results after it
            const converterCard = document.querySelector('.converter-card');
            if (converterCard) {
                const resultsDiv = document.createElement('div');
                resultsDiv.className = 'results-section';
                resultsDiv.innerHTML = content;
                converterCard.parentNode.insertBefore(resultsDiv, converterCard.nextSibling);
                resultsDiv.scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            return content;
        }
    }
}

// Additional notification styles (inject into head)
const notificationStyles = `
<style>
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    border-radius: 0.5rem;
    padding: 1rem 1.5rem;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    border: 1px solid #e5e7eb;
    z-index: 1000;
    cursor: pointer;
    animation: slideInRight 0.3s ease;
    max-width: 300px;
}

.notification-success {
    border-left: 4px solid #10b981;
}

.notification-error {
    border-left: 4px solid #ef4444;
}

.notification-info {
    border-left: 4px solid #3b82f6;
}

.notification-content {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.notification-success i {
    color: #10b981;
}

.notification-error i {
    color: #ef4444;
}

.notification-info i {
    color: #3b82f6;
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
</style>
`;

// Inject notification styles
document.head.insertAdjacentHTML('beforeend', notificationStyles);

// Initialize converter when DOM is ready
let htmlPdfConverter;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        htmlPdfConverter = new HTMLPDFSnapshotConverter();
    });
} else {
    htmlPdfConverter = new HTMLPDFSnapshotConverter();
}

// Export for global access
window.HTMLPDFSnapshotConverter = HTMLPDFSnapshotConverter;
