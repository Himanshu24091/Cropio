/**
 * YAML ⇄ JSON Converter JavaScript
 * Handles file upload, conversion, validation, and UI interactions
 */

class YamlJsonConverter {
    constructor() {
        this.inputEditor = null;
        this.outputEditor = null;
        this.currentMode = 'yaml-to-json';
        this.currentFile = null;
        this.validationTimeout = null;
        
        this.init();
    }

    init() {
        this.setupCodeMirrorEditors();
        this.setupEventListeners();
        this.setupModeToggle();
        this.setupFileUpload();
        this.updateUI();
    }

    setupCodeMirrorEditors() {
        // Input editor
        this.inputEditor = CodeMirror.fromTextArea(document.getElementById('input-content'), {
            lineNumbers: true,
            mode: 'yaml',
            theme: 'default',
            lineWrapping: true,
            matchBrackets: true,
            autoCloseBrackets: true,
            foldGutter: true,
            gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
            extraKeys: {
                "Ctrl-Space": "autocomplete",
                "F11": function(cm) {
                    cm.setOption("fullScreen", !cm.getOption("fullScreen"));
                },
                "Esc": function(cm) {
                    if (cm.getOption("fullScreen")) cm.setOption("fullScreen", false);
                }
            }
        });

        // Output editor (read-only)
        this.outputEditor = CodeMirror.fromTextArea(document.getElementById('output-content'), {
            lineNumbers: true,
            mode: 'javascript', // JSON mode
            theme: 'default',
            lineWrapping: true,
            readOnly: true,
            matchBrackets: true,
            foldGutter: true,
            gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"]
        });

        // Setup change handlers
        this.inputEditor.on('change', () => {
            this.updateInputStats();
            this.scheduleValidation();
        });

        this.outputEditor.on('change', () => {
            this.updateOutputStats();
        });

        // Initial stats update
        this.updateInputStats();
        this.updateOutputStats();
    }

    setupEventListeners() {
        // Action buttons
        document.getElementById('convert-btn').addEventListener('click', () => this.convert());
        document.getElementById('validate-btn').addEventListener('click', () => this.validateInput());
        document.getElementById('format-btn').addEventListener('click', () => this.formatInput());
        document.getElementById('sample-btn').addEventListener('click', () => this.loadSample());
        document.getElementById('clear-btn').addEventListener('click', () => this.clearAll());

        // Panel controls
        document.getElementById('input-download-btn').addEventListener('click', () => this.downloadInput());
        document.getElementById('input-copy-btn').addEventListener('click', () => this.copyInput());
        document.getElementById('input-fullscreen-btn').addEventListener('click', () => this.openFullscreen('input'));
        document.getElementById('output-download-btn').addEventListener('click', () => this.downloadOutput());
        document.getElementById('output-copy-btn').addEventListener('click', () => this.copyOutput());
        document.getElementById('output-fullscreen-btn').addEventListener('click', () => this.openFullscreen('output'));

        // Error and success displays
        document.getElementById('error-close').addEventListener('click', () => this.hideError());
        document.getElementById('success-close').addEventListener('click', () => this.hideSuccess());

        // Fullscreen modal
        document.getElementById('fullscreen-close').addEventListener('click', () => this.closeFullscreen());
        document.getElementById('fullscreen-save').addEventListener('click', () => this.saveFullscreen());
        document.getElementById('fullscreen-copy').addEventListener('click', () => this.copyFullscreen());

        // Click outside modal to close
        document.getElementById('fullscreen-modal').addEventListener('click', (e) => {
            if (e.target.id === 'fullscreen-modal') {
                this.closeFullscreen();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'Enter':
                        e.preventDefault();
                        this.convert();
                        break;
                    case 'k':
                        e.preventDefault();
                        this.clearAll();
                        break;
                    case 's':
                        e.preventDefault();
                        this.downloadOutput();
                        break;
                }
            }
            
            if (e.key === 'Escape') {
                this.hideError();
                this.hideSuccess();
                this.closeFullscreen();
            }
        });
    }

    setupModeToggle() {
        const modeRadios = document.querySelectorAll('input[name="conversion-mode"]');
        modeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                this.currentMode = radio.value;
                this.updateUI();
                this.clearOutput();
                this.updateEditorModes();
            });
        });
    }

    setupFileUpload() {
        const fileInput = document.getElementById('file-upload');
        const uploadInfo = document.getElementById('upload-info');
        const removeBtn = document.getElementById('remove-file');

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileUpload(file);
            }
        });

        removeBtn.addEventListener('click', () => {
            this.removeFile();
        });

        // Drag and drop support
        const dropZone = document.querySelector('.upload-label');
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'var(--primary-color, #2563eb)';
            dropZone.style.background = 'var(--primary-light, #eff6ff)';
        });

        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'var(--border-color, #e2e8f0)';
            dropZone.style.background = 'white';
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'var(--border-color, #e2e8f0)';
            dropZone.style.background = 'white';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });
    }

    async handleFileUpload(file) {
        try {
            this.showLoading('Uploading file...');
            
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/yaml-json/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentFile = {
                    name: result.filename,
                    size: result.file_size,
                    type: result.content_type
                };
                
                // Set content and mode
                this.inputEditor.setValue(result.content);
                
                if (result.suggested_mode !== this.currentMode) {
                    document.querySelector(`input[value="${result.suggested_mode}"]`).checked = true;
                    this.currentMode = result.suggested_mode;
                    this.updateUI();
                    this.updateEditorModes();
                }
                
                // Show file info
                this.showFileInfo();
                
                // Update validation
                this.updateValidation('input', result.validation);
                
                this.showSuccess(`File "${result.filename}" uploaded successfully!`, result.stats);
            } else {
                this.showError('Upload failed', result.error);
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showError('Upload failed', 'Failed to upload file. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    showFileInfo() {
        if (!this.currentFile) return;
        
        const uploadInfo = document.getElementById('upload-info');
        const filenameSpan = uploadInfo.querySelector('.filename');
        const filesizeSpan = uploadInfo.querySelector('.filesize');
        
        filenameSpan.textContent = this.currentFile.name;
        filesizeSpan.textContent = this.formatFileSize(this.currentFile.size);
        
        uploadInfo.style.display = 'flex';
    }

    removeFile() {
        this.currentFile = null;
        document.getElementById('file-upload').value = '';
        document.getElementById('upload-info').style.display = 'none';
        this.inputEditor.setValue('');
        this.clearOutput();
    }

    async convert() {
        const content = this.inputEditor.getValue().trim();
        
        if (!content) {
            this.showError('No content', 'Please provide content to convert');
            return;
        }

        try {
            this.showLoading('Converting...');
            
            const options = this.getConversionOptions();
            
            const response = await fetch('/api/yaml-json/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    mode: this.currentMode,
                    options: options
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.outputEditor.setValue(result.output || '');
                this.updateValidation('output', { valid: true, errors: [] });
                this.showSuccess('Conversion successful!', result.stats);
            } else {
                this.showError('Conversion failed', result.error, result.details);
                this.clearOutput();
            }
        } catch (error) {
            console.error('Conversion error:', error);
            this.showError('Conversion failed', 'Failed to convert content. Please try again.');
            this.clearOutput();
        } finally {
            this.hideLoading();
        }
    }

    async validateInput() {
        const content = this.inputEditor.getValue().trim();
        
        if (!content) {
            this.updateValidation('input', { valid: false, errors: ['No content to validate'] });
            return;
        }

        try {
            const contentType = this.currentMode.startsWith('yaml') ? 'yaml' : 'json';
            
            const response = await fetch('/api/yaml-json/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    type: contentType
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.updateValidation('input', result.validation);
                
                if (result.validation.valid) {
                    this.showSuccess('Validation successful!', {
                        'Content': 'Valid ' + contentType.toUpperCase()
                    });
                } else {
                    this.showError('Validation failed', result.validation.errors.join('; '));
                }
            } else {
                this.updateValidation('input', { valid: false, errors: [result.error] });
                this.showError('Validation failed', result.error);
            }
        } catch (error) {
            console.error('Validation error:', error);
            this.showError('Validation failed', 'Failed to validate content. Please try again.');
        }
    }

    async formatInput() {
        const content = this.inputEditor.getValue().trim();
        
        if (!content) {
            this.showError('No content', 'Please provide content to format');
            return;
        }

        try {
            this.showLoading('Formatting...');
            
            const contentType = this.currentMode.startsWith('yaml') ? 'yaml' : 'json';
            const options = this.getConversionOptions();
            
            const response = await fetch('/api/yaml-json/format', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    type: contentType,
                    options: options
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.inputEditor.setValue(result.output || content);
                this.showSuccess('Formatting successful!');
            } else {
                this.showError('Formatting failed', result.error);
            }
        } catch (error) {
            console.error('Formatting error:', error);
            this.showError('Formatting failed', 'Failed to format content. Please try again.');
        } finally {
            this.hideLoading();
        }
    }

    async loadSample() {
        try {
            const contentType = this.currentMode.startsWith('yaml') ? 'yaml' : 'json';
            
            const response = await fetch(`/api/yaml-json/sample/${contentType}`);
            const result = await response.json();
            
            if (result.success) {
                this.inputEditor.setValue(result.content);
                this.clearOutput();
                this.showSuccess(`Sample ${contentType.toUpperCase()} loaded!`);
            } else {
                this.showError('Load sample failed', result.error);
            }
        } catch (error) {
            console.error('Sample load error:', error);
            this.showError('Load sample failed', 'Failed to load sample content.');
        }
    }

    clearAll() {
        this.inputEditor.setValue('');
        this.outputEditor.setValue('');
        this.removeFile();
        this.hideError();
        this.hideSuccess();
        this.updateValidation('input', { valid: null, errors: [] });
        this.updateValidation('output', { valid: null, errors: [] });
    }

    clearOutput() {
        this.outputEditor.setValue('');
        this.updateValidation('output', { valid: null, errors: [] });
    }

    getConversionOptions() {
        return {
            pretty: document.getElementById('pretty-format').checked,
            sort_keys: document.getElementById('sort-keys').checked,
            flow_style: document.getElementById('flow-style').checked,
            indent: parseInt(document.getElementById('indent-size').value)
        };
    }

    updateUI() {
        // Update panel titles
        if (this.currentMode === 'yaml-to-json') {
            document.getElementById('input-title').textContent = 'Input (YAML)';
            document.getElementById('output-title').textContent = 'Output (JSON)';
            this.inputEditor.setOption('mode', 'yaml');
            this.outputEditor.setOption('mode', 'javascript');
        } else {
            document.getElementById('input-title').textContent = 'Input (JSON)';
            document.getElementById('output-title').textContent = 'Output (YAML)';
            this.inputEditor.setOption('mode', 'javascript');
            this.outputEditor.setOption('mode', 'yaml');
        }

        // Show/hide YAML-specific options
        const yamlOnlyOptions = document.querySelectorAll('.yaml-only');
        yamlOnlyOptions.forEach(option => {
            if (this.currentMode === 'json-to-yaml') {
                option.classList.add('enabled');
            } else {
                option.classList.remove('enabled');
            }
        });

        // Update placeholders
        const inputPlaceholder = this.currentMode === 'yaml-to-json' 
            ? 'Paste your YAML content here or upload a file...'
            : 'Paste your JSON content here or upload a file...';
        
        this.inputEditor.setOption('placeholder', inputPlaceholder);
    }

    updateEditorModes() {
        if (this.currentMode === 'yaml-to-json') {
            this.inputEditor.setOption('mode', 'yaml');
            this.outputEditor.setOption('mode', 'javascript');
        } else {
            this.inputEditor.setOption('mode', 'javascript');
            this.outputEditor.setOption('mode', 'yaml');
        }
    }

    updateInputStats() {
        const content = this.inputEditor.getValue();
        const stats = this.calculateStats(content);
        document.getElementById('input-stats').textContent = 
            `Lines: ${stats.lines} | Words: ${stats.words} | Characters: ${stats.characters}`;
    }

    updateOutputStats() {
        const content = this.outputEditor.getValue();
        const stats = this.calculateStats(content);
        document.getElementById('output-stats').textContent = 
            `Lines: ${stats.lines} | Words: ${stats.words} | Characters: ${stats.characters}`;
    }

    calculateStats(content) {
        const lines = content ? content.split('\n').length : 0;
        const words = content.trim() ? content.trim().split(/\s+/).length : 0;
        const characters = content.length;
        
        return { lines, words, characters };
    }

    scheduleValidation() {
        if (this.validationTimeout) {
            clearTimeout(this.validationTimeout);
        }
        
        this.validationTimeout = setTimeout(() => {
            this.validateInputSilent();
        }, 1000);
    }

    async validateInputSilent() {
        const content = this.inputEditor.getValue().trim();
        
        if (!content) {
            this.updateValidation('input', { valid: null, errors: [] });
            return;
        }

        try {
            const contentType = this.currentMode.startsWith('yaml') ? 'yaml' : 'json';
            
            const response = await fetch('/api/yaml-json/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    type: contentType
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.updateValidation('input', result.validation);
            }
        } catch (error) {
            console.warn('Silent validation error:', error);
        }
    }

    updateValidation(panel, validation) {
        const validationElement = document.getElementById(`${panel}-validation`);
        const indicator = validationElement.querySelector('.validation-indicator');
        const icon = indicator.querySelector('i');
        const text = indicator.querySelector('span');

        if (validation.valid === true) {
            indicator.dataset.status = 'valid';
            icon.className = 'fas fa-check-circle';
            text.textContent = 'Valid';
        } else if (validation.valid === false) {
            indicator.dataset.status = 'invalid';
            icon.className = 'fas fa-exclamation-circle';
            text.textContent = validation.errors?.length ? validation.errors[0] : 'Invalid';
        } else {
            indicator.dataset.status = 'unknown';
            icon.className = 'fas fa-question-circle';
            text.textContent = 'Not validated';
        }
    }

    async downloadInput() {
        const content = this.inputEditor.getValue().trim();
        if (!content) {
            this.showError('No content', 'No input content to download');
            return;
        }

        const filename = this.currentFile?.name?.replace(/\.[^/.]+$/, '') || 'input';
        const fileType = this.currentMode.startsWith('yaml') ? 'yaml' : 'json';
        
        this.downloadContent(content, filename, fileType);
    }

    async downloadOutput() {
        const content = this.outputEditor.getValue().trim();
        if (!content) {
            this.showError('No content', 'No output content to download');
            return;
        }

        const filename = this.currentFile?.name?.replace(/\.[^/.]+$/, '') || 'converted';
        const fileType = this.currentMode.endsWith('yaml') ? 'yaml' : 'json';
        
        this.downloadContent(content, filename, fileType);
    }

    async downloadContent(content, filename, fileType) {
        try {
            const response = await fetch('/api/yaml-json/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content: content,
                    filename: filename,
                    type: fileType
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${filename}.${fileType}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showSuccess('Download started!');
            } else {
                const result = await response.json();
                this.showError('Download failed', result.error || 'Failed to download file');
            }
        } catch (error) {
            console.error('Download error:', error);
            this.showError('Download failed', 'Failed to download file. Please try again.');
        }
    }

    copyInput() {
        const content = this.inputEditor.getValue();
        this.copyToClipboard(content, 'Input copied to clipboard!');
    }

    copyOutput() {
        const content = this.outputEditor.getValue();
        this.copyToClipboard(content, 'Output copied to clipboard!');
    }

    copyToClipboard(text, successMessage) {
        if (!text.trim()) {
            this.showError('No content', 'No content to copy');
            return;
        }

        navigator.clipboard.writeText(text).then(() => {
            this.showSuccess(successMessage);
        }).catch(err => {
            console.error('Copy error:', err);
            this.showError('Copy failed', 'Failed to copy to clipboard');
        });
    }

    openFullscreen(panel) {
        const modal = document.getElementById('fullscreen-modal');
        const title = document.getElementById('fullscreen-title');
        const textarea = document.getElementById('fullscreen-textarea');
        
        const editor = panel === 'input' ? this.inputEditor : this.outputEditor;
        const content = editor.getValue();
        const panelTitle = panel === 'input' ? 'Input Content' : 'Output Content';
        
        title.textContent = panelTitle;
        textarea.value = content;
        textarea.dataset.panel = panel;
        
        modal.style.display = 'flex';
        textarea.focus();
    }

    closeFullscreen() {
        document.getElementById('fullscreen-modal').style.display = 'none';
    }

    saveFullscreen() {
        const textarea = document.getElementById('fullscreen-textarea');
        const panel = textarea.dataset.panel;
        const content = textarea.value;
        
        if (panel === 'input') {
            this.inputEditor.setValue(content);
        } else {
            // Output is typically read-only, but we can allow manual edits in fullscreen
            this.outputEditor.setValue(content);
        }
        
        this.closeFullscreen();
        this.showSuccess('Content updated!');
    }

    copyFullscreen() {
        const textarea = document.getElementById('fullscreen-textarea');
        this.copyToClipboard(textarea.value, 'Content copied to clipboard!');
    }

    showLoading(message = 'Loading...') {
        const loadingElement = document.getElementById('loading-indicator');
        const loadingText = loadingElement.querySelector('.loading-text');
        loadingText.textContent = message;
        loadingElement.style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading-indicator').style.display = 'none';
    }

    showError(title, message, details = null) {
        const errorElement = document.getElementById('error-display');
        const messageElement = document.getElementById('error-message');
        const detailsElement = document.getElementById('error-details');
        
        messageElement.textContent = `${title}: ${message}`;
        
        if (details) {
            const detailsContent = detailsElement.querySelector('.error-details-content');
            detailsContent.textContent = details;
            detailsElement.style.display = 'block';
        } else {
            detailsElement.style.display = 'none';
        }
        
        errorElement.style.display = 'block';
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            this.hideError();
        }, 10000);
    }

    hideError() {
        document.getElementById('error-display').style.display = 'none';
    }

    showSuccess(message, stats = null) {
        const successElement = document.getElementById('success-display');
        const messageElement = document.getElementById('success-message');
        const statsElement = document.getElementById('success-stats');
        
        messageElement.textContent = message;
        
        if (stats && typeof stats === 'object') {
            const statsText = Object.entries(stats)
                .map(([key, value]) => `${key}: ${value}`)
                .join(' | ');
            statsElement.textContent = statsText;
            statsElement.style.display = 'block';
        } else {
            statsElement.style.display = 'none';
        }
        
        successElement.style.display = 'block';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideSuccess();
        }, 5000);
    }

    hideSuccess() {
        document.getElementById('success-display').style.display = 'none';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return (bytes / Math.pow(k, i)).toFixed(1) + ' ' + sizes[i];
    }
}

// Initialize converter when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.yamlJsonConverter = new YamlJsonConverter();
});

// Export for potential external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = YamlJsonConverter;
}
