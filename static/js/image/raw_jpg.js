/**
 * RAW to JPG Converter - Professional JavaScript
 * Advanced file processing with drag/drop, preview, and batch support
 */

(function() {
    'use strict';

    // ==================== Application State ====================
    const App = {
        config: null,
        selectedFiles: [],
        conversionResults: [],
        isConverting: false,
        currentModal: null,
        presetSettings: {
            reset: { brightness: 0, contrast: 0, saturation: 0, sharpness: 0, temperature: 0 },
            vivid: { brightness: 0.3, contrast: 0.4, saturation: 0.6, sharpness: 0.2, temperature: 0 },
            natural: { brightness: 0.1, contrast: 0.2, saturation: 0.1, sharpness: 0.1, temperature: 0 },
            portrait: { brightness: 0.2, contrast: 0.3, saturation: 0.2, sharpness: -0.1, temperature: 200 }
        }
    };

    // ==================== Configuration & Initialization ====================
    function initializeApp() {
        // Load configuration from embedded JSON
        const configElement = document.getElementById('app-config');
        if (configElement) {
            try {
                App.config = JSON.parse(configElement.textContent);
            } catch (e) {
                console.error('Failed to parse configuration:', e);
                showErrorMessage('Configuration error. Please refresh the page.');
                return;
            }
        }

        // Early exit if RAW processing unavailable or quota exceeded
        if (App.config && (App.config.rawUnavailable || App.config.quotaExceeded)) {
            return;
        }

        initializeElements();
        bindEventListeners();
        initializeUI();
        initializeConversionDirection();
        console.log('RAW to JPG Converter initialized successfully');
    }

    function initializeElements() {
        // Cache frequently used elements
        App.elements = {
            uploadZone: document.getElementById('uploadZone'),
            fileInput: document.getElementById('fileInput'),
            fileList: document.getElementById('fileList'),
            fileItems: document.getElementById('fileItems'),
            clearFiles: document.getElementById('clearFiles'),
            addMoreFiles: document.getElementById('addMoreFiles'),
            
            optionsSection: document.getElementById('optionsSection'),
            actionSection: document.getElementById('actionSection'),
            resultsSection: document.getElementById('resultsSection'),
            
            outputFormat: document.getElementById('outputFormat'),
            quality: document.getElementById('quality'),
            qualityValue: document.querySelector('.quality-value'),
            
            preserveMetadata: document.getElementById('preserveMetadata'),
            autoWhiteBalance: document.getElementById('autoWhiteBalance'),
            autoBrightness: document.getElementById('autoBrightness'),
            
            advancedToggle: document.getElementById('advancedToggle'),
            advancedContent: document.getElementById('advancedContent'),
            
            // Advanced controls
            brightness: document.getElementById('brightness'),
            contrast: document.getElementById('contrast'),
            saturation: document.getElementById('saturation'),
            sharpness: document.getElementById('sharpness'),
            temperatureShift: document.getElementById('temperatureShift'),
            
            // Value displays
            brightnessValue: document.querySelector('.brightness-value'),
            contrastValue: document.querySelector('.contrast-value'),
            saturationValue: document.querySelector('.saturation-value'),
            sharpnessValue: document.querySelector('.sharpness-value'),
            temperatureValue: document.querySelector('.temperature-value'),
            
            // Action buttons
            analyzeBtn: document.getElementById('analyzeBtn'),
            previewBtn: document.getElementById('previewBtn'),
            convertBtn: document.getElementById('convertBtn'),
            
            // Progress and results
            progressContainer: document.getElementById('progressContainer'),
            progressFill: document.getElementById('progressFill'),
            progressText: document.getElementById('progressText'),
            progressDetails: document.getElementById('progressDetails'),
            
            successResults: document.getElementById('successResults'),
            errorResults: document.getElementById('errorResults'),
            successMessage: document.getElementById('successMessage'),
            errorMessage: document.getElementById('errorMessage'),
            conversionStats: document.getElementById('conversionStats'),
            downloadSection: document.getElementById('downloadSection'),
            
            convertMoreBtn: document.getElementById('convertMoreBtn'),
            retryBtn: document.getElementById('retryBtn'),
            
            // Modals
            analysisModal: document.getElementById('analysisModal'),
            analysisContent: document.getElementById('analysisContent'),
            analysisModalClose: document.getElementById('analysisModalClose'),
            
            previewModal: document.getElementById('previewModal'),
            previewContainer: document.getElementById('previewContainer'),
            previewModalClose: document.getElementById('previewModalClose')
        };
    }

    function bindEventListeners() {
        // Bidirectional file upload events
        const rawUploadZone = document.getElementById('rawToJpgUploadZone');
        const imageUploadZone = document.getElementById('jpgToRawUploadZone');
        const rawFileInput = document.getElementById('rawFileInput');
        const imageFileInput = document.getElementById('imageFileInput');
        
        // RAW upload zone click handler
        rawUploadZone?.addEventListener('click', (e) => {
            if (e.target === rawUploadZone || e.target.closest('.upload-content')) {
                rawFileInput?.click();
            }
        });
        
        // Image upload zone click handler
        imageUploadZone?.addEventListener('click', (e) => {
            if (e.target === imageUploadZone || e.target.closest('.upload-content')) {
                imageFileInput?.click();
            }
        });
        
        // Select files button handlers
        const selectRawFilesBtn = document.getElementById('selectRawFilesBtn');
        const selectImageFilesBtn = document.getElementById('selectImageFilesBtn');
        
        selectRawFilesBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            rawFileInput?.click();
        });
        
        selectImageFilesBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            imageFileInput?.click();
        });
        
        // File input change handlers
        rawFileInput?.addEventListener('change', handleFileSelection);
        imageFileInput?.addEventListener('change', handleFileSelection);
        
        // Other buttons
        App.elements.addMoreFiles?.addEventListener('click', () => {
            if (App.currentDirection === 'image_to_raw') {
                imageFileInput?.click();
            } else {
                rawFileInput?.click();
            }
        });
        App.elements.clearFiles?.addEventListener('click', clearAllFiles);

        // Drag and drop events for both upload zones
        const uploadZones = [rawUploadZone, imageUploadZone];
        uploadZones.forEach(zone => {
            if (zone) {
                ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                    zone.addEventListener(eventName, preventDefaults);
                });

                ['dragenter', 'dragover'].forEach(eventName => {
                    zone.addEventListener(eventName, (e) => zone.classList.add('drag-over'));
                });

                ['dragleave', 'drop'].forEach(eventName => {
                    zone.addEventListener(eventName, (e) => zone.classList.remove('drag-over'));
                });

                zone.addEventListener('drop', handleDrop);
            }
        });

        // Quality slider
        App.elements.quality?.addEventListener('input', updateQualityDisplay);

        // Advanced controls
        App.elements.advancedToggle?.addEventListener('click', toggleAdvancedOptions);
        
        // Slider updates
        App.elements.brightness?.addEventListener('input', updateBrightnessDisplay);
        App.elements.contrast?.addEventListener('input', updateContrastDisplay);
        App.elements.saturation?.addEventListener('input', updateSaturationDisplay);
        App.elements.sharpness?.addEventListener('input', updateSharpnessDisplay);
        App.elements.temperatureShift?.addEventListener('input', updateTemperatureDisplay);

        // Preset buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', () => applyPreset(btn.dataset.preset));
        });

        // Action buttons
        App.elements.analyzeBtn?.addEventListener('click', analyzeFile);
        App.elements.previewBtn?.addEventListener('click', generatePreview);
        App.elements.convertBtn?.addEventListener('click', startConversion);
        App.elements.convertMoreBtn?.addEventListener('click', resetForNewConversion);
        App.elements.retryBtn?.addEventListener('click', retryConversion);

        // Modal events
        App.elements.analysisModalClose?.addEventListener('click', closeAnalysisModal);
        App.elements.previewModalClose?.addEventListener('click', closePreviewModal);

        // Close modals on background click
        App.elements.analysisModal?.addEventListener('click', (e) => {
            if (e.target === App.elements.analysisModal) closeAnalysisModal();
        });
        App.elements.previewModal?.addEventListener('click', (e) => {
            if (e.target === App.elements.previewModal) closePreviewModal();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', handleKeyboardShortcuts);

        // Output format change
        App.elements.outputFormat?.addEventListener('change', handleFormatChange);
    }

    function initializeUI() {
        // Initialize quality display
        updateQualityDisplay();
        
        // Initialize advanced control displays
        updateBrightnessDisplay();
        updateContrastDisplay();
        updateSaturationDisplay();
        updateSharpnessDisplay();
        updateTemperatureDisplay();

        // Set initial format
        handleFormatChange();
    }

    // ==================== File Handling ====================
    function handleFileSelection(event) {
        const files = Array.from(event.target.files);
        addFiles(files);
        event.target.value = ''; // Reset input
    }

    function handleDrop(event) {
        const files = Array.from(event.dataTransfer.files);
        addFiles(files);
    }

    function addFiles(files) {
        // Use the bidirectional validation function
        addFilesWithValidation(files);
    }

    function isValidRAWFile(file) {
        const validExtensions = ['.cr2', '.cr3', '.nef', '.arw', '.dng', '.raf', '.rw2', '.orf', '.pef', '.srw', '.x3f', '.3fr', '.fff', '.mef', '.mos', '.raw'];
        const fileName = file.name.toLowerCase();
        return validExtensions.some(ext => fileName.endsWith(ext));
    }

    function generateFileId() {
        return Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    function removeFile(fileId) {
        App.selectedFiles = App.selectedFiles.filter(f => f.id !== fileId);
        updateUI();
        renderFileList();
    }

    function clearAllFiles() {
        App.selectedFiles = [];
        updateUI();
        renderFileList();
    }

    function renderFileList() {
        if (!App.elements.fileItems) return;

        if (App.selectedFiles.length === 0) {
            App.elements.fileList.style.display = 'none';
            return;
        }

        App.elements.fileList.style.display = 'block';
        
        const fileItemsHtml = App.selectedFiles.map(fileData => `
            <div class="file-item" data-file-id="${fileData.id}">
                <div class="file-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <polyline points="21,15 16,10 5,21"/>
                    </svg>
                </div>
                <div class="file-info">
                    <div class="file-name" title="${fileData.name}">${fileData.name}</div>
                    <div class="file-meta">
                        <span>${formatFileSize(fileData.size)}</span>
                        <span>•</span>
                        <span>${getFileFormat(fileData.name)}</span>
                    </div>
                </div>
                <button type="button" class="file-remove" onclick="window.rawConverter.removeFile('${fileData.id}')" title="Remove file">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
        `).join('');

        App.elements.fileItems.innerHTML = fileItemsHtml;
    }

    // ==================== UI Updates ====================
    function updateUI() {
        const hasFiles = App.selectedFiles.length > 0;
        const hasOneFile = App.selectedFiles.length === 1;
        const isRAWFile = hasOneFile && isValidRAWFile(App.selectedFiles[0].file);
        
        // Show/hide sections based on file selection
        if (App.elements.optionsSection) {
            App.elements.optionsSection.style.display = hasFiles ? 'block' : 'none';
        }
        if (App.elements.actionSection) {
            App.elements.actionSection.style.display = hasFiles ? 'block' : 'none';
        }

        // Update button states - Analyze and Preview work for both RAW and image files
        if (App.elements.analyzeBtn) {
            App.elements.analyzeBtn.disabled = !hasOneFile;
            App.elements.analyzeBtn.style.display = 'inline-flex';
        }
        if (App.elements.previewBtn) {
            App.elements.previewBtn.disabled = !hasOneFile;
            App.elements.previewBtn.style.display = 'inline-flex';
        }
        if (App.elements.convertBtn) {
            App.elements.convertBtn.disabled = !hasFiles || App.isConverting;
        }
    }

    function updateQualityDisplay() {
        if (App.elements.quality && App.elements.qualityValue) {
            const value = App.elements.quality.value;
            App.elements.qualityValue.textContent = `${value}%`;
        }
    }

    function updateBrightnessDisplay() {
        if (App.elements.brightness && App.elements.brightnessValue) {
            const value = parseFloat(App.elements.brightness.value);
            App.elements.brightnessValue.textContent = value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1);
        }
    }

    function updateContrastDisplay() {
        if (App.elements.contrast && App.elements.contrastValue) {
            const value = parseFloat(App.elements.contrast.value);
            App.elements.contrastValue.textContent = value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1);
        }
    }

    function updateSaturationDisplay() {
        if (App.elements.saturation && App.elements.saturationValue) {
            const value = parseFloat(App.elements.saturation.value);
            App.elements.saturationValue.textContent = value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1);
        }
    }

    function updateSharpnessDisplay() {
        if (App.elements.sharpness && App.elements.sharpnessValue) {
            const value = parseFloat(App.elements.sharpness.value);
            App.elements.sharpnessValue.textContent = value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1);
        }
    }

    function updateTemperatureDisplay() {
        if (App.elements.temperatureShift && App.elements.temperatureValue) {
            const value = parseInt(App.elements.temperatureShift.value);
            App.elements.temperatureValue.textContent = value > 0 ? `+${value}K` : `${value}K`;
        }
    }

    function toggleAdvancedOptions() {
        if (!App.elements.advancedContent || !App.elements.advancedToggle) return;

        const isExpanded = App.elements.advancedContent.style.display === 'block';
        
        if (isExpanded) {
            App.elements.advancedContent.style.display = 'none';
            App.elements.advancedToggle.classList.remove('expanded');
        } else {
            App.elements.advancedContent.style.display = 'block';
            App.elements.advancedToggle.classList.add('expanded');
        }
    }

    function applyPreset(presetName) {
        const preset = App.presetSettings[presetName];
        if (!preset) return;

        // Apply values to sliders
        if (App.elements.brightness) {
            App.elements.brightness.value = preset.brightness;
            updateBrightnessDisplay();
        }
        if (App.elements.contrast) {
            App.elements.contrast.value = preset.contrast;
            updateContrastDisplay();
        }
        if (App.elements.saturation) {
            App.elements.saturation.value = preset.saturation;
            updateSaturationDisplay();
        }
        if (App.elements.sharpness) {
            App.elements.sharpness.value = preset.sharpness;
            updateSharpnessDisplay();
        }
        if (App.elements.temperatureShift) {
            App.elements.temperatureShift.value = preset.temperature;
            updateTemperatureDisplay();
        }

        showSuccessMessage(`Applied ${presetName} preset`);
    }

    function handleFormatChange() {
        if (!App.elements.outputFormat) return;

        const format = App.elements.outputFormat.value;
        const qualitySection = App.elements.quality?.closest('.option-group');
        
        // Hide quality option for PNG (lossless)
        if (qualitySection) {
            qualitySection.style.display = format === 'PNG' ? 'none' : 'block';
        }
    }

    // ==================== File Analysis ====================
    async function analyzeFile() {
        if (App.selectedFiles.length !== 1) {
            showErrorMessage('Please select exactly one file for analysis.');
            return;
        }

        const fileData = App.selectedFiles[0];
        showLoadingState('Analyzing RAW file...');

        try {
            const formData = new FormData();
            formData.append('file', fileData.file);

            const response = await fetch(App.config.apiUrls.analyze, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                displayAnalysisResults(result);
            } else {
                throw new Error(result.error || 'Analysis failed');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            showErrorMessage(`Analysis failed: ${error.message}`);
        } finally {
            hideLoadingState();
        }
    }

    function displayAnalysisResults(result) {
        if (!App.elements.analysisContent) return;

        const analysisHtml = `
            <div class="analysis-results">
                <div class="analysis-section">
                    <h4>File Information</h4>
                    <div class="analysis-grid">
                        <div class="analysis-item">
                            <span class="label">Filename:</span>
                            <span class="value">${result.file_info.filename}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Size:</span>
                            <span class="value">${result.file_info.size_mb} MB</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Format:</span>
                            <span class="value">${result.file_info.format}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Camera Brand:</span>
                            <span class="value">${result.file_info.brand}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Dimensions:</span>
                            <span class="value">${result.file_info.dimensions}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Megapixels:</span>
                            <span class="value">${result.file_info.megapixels} MP</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Processing Time:</span>
                            <span class="value">${result.file_info.processing_estimate}</span>
                        </div>
                    </div>
                </div>

                <div class="analysis-section">
                    <h4>RAW Details</h4>
                    <div class="analysis-grid">
                        <div class="analysis-item">
                            <span class="label">Color Channels:</span>
                            <span class="value">${result.raw_details.color_channels}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Color Description:</span>
                            <span class="value">${result.raw_details.color_description}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">RAW Dimensions:</span>
                            <span class="value">${result.raw_details.raw_dimensions}</span>
                        </div>
                    </div>
                </div>

                <div class="analysis-section">
                    <h4>Processing Options</h4>
                    <div class="options-list">
                        <div class="option-category">
                            <h5>Recommended Formats:</h5>
                            <ul>
                                ${result.processing_options.recommended_formats.map(format => `<li>${format}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="option-category">
                            <h5>White Balance Options:</h5>
                            <ul>
                                ${result.processing_options.white_balance_options.map(option => `<li>${option}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>

                <div class="analysis-section">
                    <h4>Processing Tips</h4>
                    <ul class="tips-list">
                        ${result.tips.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;

        App.elements.analysisContent.innerHTML = analysisHtml;
        showAnalysisModal();
    }

    // ==================== Preview Generation ====================
    async function generatePreview() {
        if (App.selectedFiles.length !== 1) {
            showErrorMessage('Please select exactly one file for preview.');
            return;
        }

        const fileData = App.selectedFiles[0];
        showLoadingState('Generating preview...');

        try {
            const formData = new FormData();
            formData.append('file', fileData.file);

            const response = await fetch(App.config.apiUrls.preview, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                displayPreview(result.preview);
            } else {
                throw new Error(result.error || 'Preview generation failed');
            }
        } catch (error) {
            console.error('Preview error:', error);
            showErrorMessage(`Preview generation failed: ${error.message}`);
        } finally {
            hideLoadingState();
        }
    }

    function displayPreview(previewDataUrl) {
        if (!App.elements.previewContainer) return;

        App.elements.previewContainer.innerHTML = `
            <img src="${previewDataUrl}" alt="RAW Preview" style="max-width: 100%; height: auto;">
        `;

        showPreviewModal();
    }

    // ==================== File Conversion ====================
    async function startConversion() {
        if (App.selectedFiles.length === 0) {
            showErrorMessage('Please select files to convert.');
            return;
        }

        App.isConverting = true;
        updateUI();

        // Show progress section
        showResultsSection();
        showProgressContainer();

        try {
            let results;
            if (App.selectedFiles.length === 1) {
                results = await convertSingleFileWithDirection(App.selectedFiles[0]);
            } else {
                results = await convertMultipleFilesWithDirection(App.selectedFiles);
            }

            if (results.success) {
                displaySuccessResults(results);
            } else {
                throw new Error(results.error || 'Conversion failed');
            }
        } catch (error) {
            console.error('Conversion error:', error);
            displayErrorResults(error.message);
        } finally {
            App.isConverting = false;
            updateUI();
            hideProgressContainer();
        }
    }

    async function convertSingleFile(fileData) {
        const formData = createFormData([fileData]);
        
        updateProgress(10, 'Preparing file for conversion...');

        const response = await fetch(App.config.apiUrls.convert, {
            method: 'POST',
            body: formData
        });

        updateProgress(50, 'Processing RAW file...');

        const result = await response.json();
        
        updateProgress(100, 'Conversion complete!');

        return result;
    }

    async function convertMultipleFiles(filesData) {
        const formData = createBatchFormData(filesData);
        
        updateProgress(10, 'Preparing batch conversion...');

        const response = await fetch(App.config.apiUrls.batchConvert, {
            method: 'POST',
            body: formData
        });

        updateProgress(50, 'Processing files...');

        const result = await response.json();
        
        updateProgress(100, 'Batch conversion complete!');

        return result;
    }

    function createFormData(filesData) {
        const formData = new FormData();
        
        // Add files
        if (filesData.length === 1) {
            formData.append('file', filesData[0].file);
        }
        
        // Add conversion options
        formData.append('output_format', App.elements.outputFormat?.value || 'JPEG');
        formData.append('quality', App.elements.quality?.value || '95');
        formData.append('preserve_metadata', App.elements.preserveMetadata?.checked ? 'true' : 'false');
        formData.append('auto_white_balance', App.elements.autoWhiteBalance?.checked ? 'true' : 'false');
        formData.append('auto_brightness', App.elements.autoBrightness?.checked ? 'true' : 'false');
        
        // Add advanced options
        if (App.elements.brightness) formData.append('brightness', (parseFloat(App.elements.brightness.value) + 1).toString());
        if (App.elements.contrast) formData.append('contrast', (parseFloat(App.elements.contrast.value) + 1).toString());
        if (App.elements.saturation) formData.append('saturation', (parseFloat(App.elements.saturation.value) + 1).toString());
        if (App.elements.sharpness) formData.append('sharpness', (parseFloat(App.elements.sharpness.value) + 1).toString());
        if (App.elements.temperatureShift) formData.append('temperature_shift', App.elements.temperatureShift.value);

        return formData;
    }

    function createBatchFormData(filesData) {
        const formData = new FormData();
        
        // Add multiple files
        filesData.forEach(fileData => {
            formData.append('files[]', fileData.file);
        });
        
        // Add conversion options (same as single file)
        formData.append('output_format', App.elements.outputFormat?.value || 'JPEG');
        formData.append('quality', App.elements.quality?.value || '90');
        formData.append('preserve_metadata', App.elements.preserveMetadata?.checked ? 'true' : 'false');

        return formData;
    }

    // ==================== Progress Management ====================
    function updateProgress(percentage, message, details = '') {
        if (App.elements.progressFill) {
            App.elements.progressFill.style.width = `${percentage}%`;
        }
        if (App.elements.progressText) {
            App.elements.progressText.textContent = message;
        }
        if (App.elements.progressDetails && details) {
            App.elements.progressDetails.textContent = details;
        }
    }

    function showProgressContainer() {
        if (App.elements.progressContainer) {
            App.elements.progressContainer.style.display = 'block';
        }
        hideSuccessResults();
        hideErrorResults();
    }

    function hideProgressContainer() {
        if (App.elements.progressContainer) {
            App.elements.progressContainer.style.display = 'none';
        }
    }

    // ==================== Results Display ====================
    function showResultsSection() {
        if (App.elements.resultsSection) {
            App.elements.resultsSection.style.display = 'block';
        }
    }

    function displaySuccessResults(results) {
        hideProgressContainer();
        hideErrorResults();
        
        if (App.elements.successMessage) {
            App.elements.successMessage.textContent = results.message || 'Conversion completed successfully!';
        }

        // Display conversion statistics
        if (App.elements.conversionStats && results.stats) {
            const statsHtml = `
                <div class="stat-card">
                    <span class="stat-number">${results.stats.original_size || 'N/A'}</span>
                    <div class="stat-label">Original Size</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">${results.stats.converted_size || 'N/A'}</span>
                    <div class="stat-label">Converted Size</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">${results.stats.processing_time || 'N/A'}</span>
                    <div class="stat-label">Processing Time</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">${results.stats.output_format || 'N/A'}</span>
                    <div class="stat-label">Output Format</div>
                </div>
            `;
            App.elements.conversionStats.innerHTML = statsHtml;
        }

        // Display download links
        if (App.elements.downloadSection) {
            let downloadHtml = '';
            
            console.log('Results object:', results); // Debug log
            
            if (results.download) {
                // Single file download - works for both directions
                downloadHtml = `
                    <div class="download-item">
                        <div class="download-icon">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7,10 12,15 17,10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                        </div>
                        <div class="download-info">
                            <div class="download-name">${results.download.filename}</div>
                            <div class="download-meta">${formatFileSize(results.download.size)}</div>
                        </div>
                        <a href="${results.download.url}" download="${results.download.filename}" class="btn btn-primary">
                            Download
                        </a>
                    </div>
                `;
            } else if (results.results && results.results.converted) {
                // Batch download - works for both directions
                downloadHtml = results.results.converted.map(item => `
                    <div class="download-item">
                        <div class="download-icon">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                                <polyline points="7,10 12,15 17,10"/>
                                <line x1="12" y1="15" x2="12" y2="3"/>
                            </svg>
                        </div>
                        <div class="download-info">
                            <div class="download-name">${item.filename}</div>
                            <div class="download-meta">${item.output_format}</div>
                        </div>
                        <a href="${item.download_url}" download="${item.filename}" class="btn btn-primary">
                            Download
                        </a>
                    </div>
                `).join('');
            } else {
                // Fallback: Show a message if no download info found
                downloadHtml = `
                    <div class="download-item">
                        <div class="download-icon">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <line x1="12" y1="8" x2="12" y2="12"/>
                                <line x1="12" y1="16" x2="12.01" y2="16"/>
                            </svg>
                        </div>
                        <div class="download-info">
                            <div class="download-name">Download information not available</div>
                            <div class="download-meta">Please check server response</div>
                        </div>
                        <button class="btn btn-secondary" disabled>
                            Unavailable
                        </button>
                    </div>
                `;
                console.warn('No download information found in results:', results);
            }
            
            App.elements.downloadSection.innerHTML = downloadHtml;
        }

        showSuccessResults();
    }

    function displayErrorResults(errorMessage) {
        hideProgressContainer();
        hideSuccessResults();
        
        if (App.elements.errorMessage) {
            App.elements.errorMessage.textContent = errorMessage;
        }
        
        showErrorResults();
    }

    function showSuccessResults() {
        if (App.elements.successResults) {
            App.elements.successResults.style.display = 'block';
        }
    }

    function hideSuccessResults() {
        if (App.elements.successResults) {
            App.elements.successResults.style.display = 'none';
        }
    }

    function showErrorResults() {
        if (App.elements.errorResults) {
            App.elements.errorResults.style.display = 'block';
        }
    }

    function hideErrorResults() {
        if (App.elements.errorResults) {
            App.elements.errorResults.style.display = 'none';
        }
    }

    // ==================== Modal Management ====================
    function showAnalysisModal() {
        if (App.elements.analysisModal) {
            App.elements.analysisModal.style.display = 'flex';
            App.currentModal = 'analysis';
            document.body.style.overflow = 'hidden';
        }
    }

    function closeAnalysisModal() {
        if (App.elements.analysisModal) {
            App.elements.analysisModal.style.display = 'none';
            App.currentModal = null;
            document.body.style.overflow = '';
        }
    }

    function showPreviewModal() {
        if (App.elements.previewModal) {
            App.elements.previewModal.style.display = 'flex';
            App.currentModal = 'preview';
            document.body.style.overflow = 'hidden';
        }
    }

    function closePreviewModal() {
        if (App.elements.previewModal) {
            App.elements.previewModal.style.display = 'none';
            App.currentModal = null;
            document.body.style.overflow = '';
        }
    }

    // ==================== Reset and Retry ====================
    function resetForNewConversion() {
        // Clear results
        hideSuccessResults();
        hideErrorResults();
        if (App.elements.resultsSection) {
            App.elements.resultsSection.style.display = 'none';
        }
        
        // Clear selected files
        clearAllFiles();
        
        // Reset form values to defaults
        if (App.elements.outputFormat) App.elements.outputFormat.value = 'JPEG';
        if (App.elements.quality) App.elements.quality.value = '95';
        if (App.elements.preserveMetadata) App.elements.preserveMetadata.checked = true;
        if (App.elements.autoWhiteBalance) App.elements.autoWhiteBalance.checked = true;
        if (App.elements.autoBrightness) App.elements.autoBrightness.checked = true;
        
        // Reset advanced options
        applyPreset('reset');
        
        // Hide advanced section
        if (App.elements.advancedContent) {
            App.elements.advancedContent.style.display = 'none';
            App.elements.advancedToggle.classList.remove('expanded');
        }
        
        updateQualityDisplay();
        updateUI();
    }

    function retryConversion() {
        hideErrorResults();
        startConversion();
    }

    // ==================== Drag & Drop Helpers ====================
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        App.elements.uploadZone?.classList.add('drag-over');
    }

    function unhighlight(e) {
        App.elements.uploadZone?.classList.remove('drag-over');
    }

    // ==================== Keyboard Shortcuts ====================
    function handleKeyboardShortcuts(e) {
        // ESC key to close modals
        if (e.key === 'Escape' && App.currentModal) {
            if (App.currentModal === 'analysis') closeAnalysisModal();
            if (App.currentModal === 'preview') closePreviewModal();
            return;
        }

        // Ctrl/Cmd shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'u': // Upload files
                    e.preventDefault();
                    App.elements.fileInput?.click();
                    break;
                case 'Enter': // Convert
                    e.preventDefault();
                    if (!App.isConverting && App.selectedFiles.length > 0) {
                        startConversion();
                    }
                    break;
                case 'Backspace': // Clear files
                    e.preventDefault();
                    clearAllFiles();
                    break;
            }
        }
    }

    // ==================== Loading States ====================
    function showLoadingState(message) {
        // You can implement a global loading indicator here
        console.log('Loading:', message);
    }

    function hideLoadingState() {
        // Hide global loading indicator
        console.log('Loading complete');
    }

    // ==================== Utility Functions ====================
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    function getFileFormat(filename) {
        const extension = filename.split('.').pop().toUpperCase();
        return extension;
    }

    function showSuccessMessage(message) {
        // You can implement toast notifications here
        console.log('Success:', message);
    }

    function showErrorMessage(message) {
        // You can implement toast notifications here
        console.error('Error:', message);
        alert(message); // Temporary alert - replace with better notification system
    }

    // ==================== Conversion Direction Management ====================
    function updateConversionDirection(direction) {
        const rawZone = document.getElementById('rawToJpgUploadZone');
        const imageZone = document.getElementById('jpgToRawUploadZone');
        const rawOptions = document.querySelectorAll('.raw-to-jpg-option');
        const imageOptions = document.querySelectorAll('.jpg-to-raw-option');
        const convertBtn = document.getElementById('convertBtn');
        const description = document.getElementById('directionDescription');
        
        if (direction === 'raw_to_jpg') {
            // Show RAW upload zone and options
            if (rawZone) rawZone.style.display = 'block';
            if (imageZone) imageZone.style.display = 'none';
            rawOptions.forEach(el => el.style.display = 'block');
            imageOptions.forEach(el => el.style.display = 'none');
            
            // Update description
            if (description) {
                description.textContent = 'Convert RAW camera files to standard image formats with professional quality.';
            }
            
            // Update file validation
            App.currentDirection = 'raw_to_image';
            App.validateFile = isValidRAWFile;
            
        } else if (direction === 'jpg_to_raw') {
            // Show image upload zone and options
            if (rawZone) rawZone.style.display = 'none';
            if (imageZone) imageZone.style.display = 'block';
            rawOptions.forEach(el => el.style.display = 'none');
            imageOptions.forEach(el => el.style.display = 'block');
            
            // Update description
            if (description) {
                description.textContent = 'Convert standard image formats back to RAW format for advanced editing.';
            }
            
            // Update file validation
            App.currentDirection = 'image_to_raw';
            App.validateFile = isValidImageFile;
        }
        
        // Clear current files when switching direction
        clearAllFiles();
    }
    
    function isValidImageFile(file) {
        const validExtensions = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'];
        const fileName = file.name.toLowerCase();
        return validExtensions.some(ext => fileName.endsWith(ext));
    }
    
    function getConversionApiUrl() {
        if (App.currentDirection === 'image_to_raw') {
            return App.selectedFiles.length === 1 
                ? (App.config?.apiUrls?.pngRawConvert || '/raw-jpg/api/convert-png-to-raw')
                : (App.config?.apiUrls?.pngRawBatchConvert || '/raw-jpg/api/batch-convert-png-to-raw');
        } else {
            return App.selectedFiles.length === 1 
                ? (App.config?.apiUrls?.convert || '/raw-jpg/api/convert')
                : (App.config?.apiUrls?.batchConvert || '/raw-jpg/api/batch-convert');
        }
    }
    
    function initializeConversionDirection() {
        // Handle conversion direction toggle - fix selector to match HTML
        const directionToggles = document.querySelectorAll('input[name="conversionDirection"]');
        directionToggles.forEach(toggle => {
            toggle.addEventListener('change', function() {
                updateConversionDirection(this.value);
            });
        });
        
        // Initialize with the currently selected direction
        const selectedDirection = document.querySelector('input[name="conversionDirection"]:checked');
        if (selectedDirection) {
            updateConversionDirection(selectedDirection.value);
        } else {
            // Default to RAW to JPG conversion
            updateConversionDirection('raw_to_jpg');
        }
    }

    // ==================== Updated File Handling for Bidirectional ====================
    function addFilesWithValidation(files) {
        const validFiles = files.filter(file => {
            // Use the current direction's validation function
            const validationFn = App.validateFile || isValidRAWFile;
            
            if (!validationFn(file)) {
                const fileType = App.currentDirection === 'image_to_raw' ? 'image' : 'RAW';
                showErrorMessage(`Invalid file: ${file.name}. Please select ${fileType} files.`);
                return false;
            }
            
            if (file.size > App.config.maxFileSize * 1024 * 1024) {
                showErrorMessage(`File too large: ${file.name}. Maximum size is ${App.config.maxFileSize}MB.`);
                return false;
            }

            return true;
        });

        if (validFiles.length === 0) return;

        // Check batch limits
        const totalFiles = App.selectedFiles.length + validFiles.length;
        const maxFiles = App.config.isPremium ? 10 : (App.selectedFiles.length > 0 ? App.selectedFiles.length : 1);

        if (!App.config.isPremium && totalFiles > 1 && App.selectedFiles.length === 0) {
            showErrorMessage('Batch processing is only available for premium users. Please select one file at a time.');
            return;
        }

        if (totalFiles > maxFiles) {
            showErrorMessage(`Maximum ${maxFiles} files allowed. ${App.config.isPremium ? '' : 'Upgrade to premium for batch processing.'}`);
            return;
        }

        // Add files to selection
        validFiles.forEach(file => {
            const fileId = generateFileId();
            App.selectedFiles.push({
                id: fileId,
                file: file,
                name: file.name,
                size: file.size,
                type: file.type || (App.currentDirection === 'image_to_raw' ? 'image' : 'raw')
            });
        });

        updateUI();
        renderFileList();
    }
    
    // ==================== Updated Conversion Methods ====================
    async function convertSingleFileWithDirection(fileData) {
        const formData = createFormDataWithDirection([fileData]);
        const apiUrl = getConversionApiUrl();
        
        updateProgress(10, 'Preparing file for conversion...');

        const response = await fetch(apiUrl, {
            method: 'POST',
            body: formData
        });

        updateProgress(50, 'Processing file...');

        const result = await response.json();
        
        updateProgress(100, 'Conversion complete!');

        return result;
    }

    async function convertMultipleFilesWithDirection(filesData) {
        const formData = createBatchFormDataWithDirection(filesData);
        const apiUrl = getConversionApiUrl();
        
        updateProgress(10, 'Preparing batch conversion...');

        const response = await fetch(apiUrl, {
            method: 'POST',
            body: formData
        });

        updateProgress(50, 'Processing files...');

        const result = await response.json();
        
        updateProgress(100, 'Batch conversion complete!');

        return result;
    }
    
    function createFormDataWithDirection(filesData) {
        const formData = new FormData();
        
        // Add files
        if (filesData.length === 1) {
            formData.append('file', filesData[0].file);
        }
        
        if (App.currentDirection === 'image_to_raw') {
            // PNG/Image to RAW conversion options
            formData.append('output_format', document.getElementById('outputFormatJpgToRaw')?.value || 'DNG');
            formData.append('preserve_metadata', document.getElementById('preserveMetadataJpgToRaw')?.checked ? 'true' : 'false');
        } else {
            // RAW to Image conversion options (existing)
            formData.append('output_format', document.getElementById('outputFormatRawToJpg')?.value || 'JPEG');
            formData.append('quality', App.elements.quality?.value || '95');
            formData.append('preserve_metadata', document.getElementById('preserveMetadataRawToJpg')?.checked ? 'true' : 'false');
            formData.append('auto_white_balance', App.elements.autoWhiteBalance?.checked ? 'true' : 'false');
            formData.append('auto_brightness', App.elements.autoBrightness?.checked ? 'true' : 'false');
            
            // Add advanced options
            if (App.elements.brightness) formData.append('brightness', (parseFloat(App.elements.brightness.value) + 1).toString());
            if (App.elements.contrast) formData.append('contrast', (parseFloat(App.elements.contrast.value) + 1).toString());
            if (App.elements.saturation) formData.append('saturation', (parseFloat(App.elements.saturation.value) + 1).toString());
            if (App.elements.sharpness) formData.append('sharpness', (parseFloat(App.elements.sharpness.value) + 1).toString());
            if (App.elements.temperatureShift) formData.append('temperature_shift', App.elements.temperatureShift.value);
        }

        return formData;
    }
    
    function createBatchFormDataWithDirection(filesData) {
        const formData = new FormData();
        
        // Add multiple files
        filesData.forEach(fileData => {
            formData.append('files[]', fileData.file);
        });
        
        if (App.currentDirection === 'image_to_raw') {
            // PNG/Image to RAW batch conversion options
            formData.append('output_format', document.getElementById('outputFormatJpgToRaw')?.value || 'DNG');
            formData.append('preserve_metadata', document.getElementById('preserveMetadataJpgToRaw')?.checked ? 'true' : 'false');
        } else {
            // RAW to Image batch conversion options (existing)
            formData.append('output_format', document.getElementById('outputFormatRawToJpg')?.value || 'JPEG');
            formData.append('quality', App.elements.quality?.value || '90');
            formData.append('preserve_metadata', document.getElementById('preserveMetadataRawToJpg')?.checked ? 'true' : 'false');
        }

        return formData;
    }

    // ==================== Public API ====================
    window.rawConverter = {
        removeFile: removeFile,
        clearAllFiles: clearAllFiles,
        analyzeFile: analyzeFile,
        generatePreview: generatePreview,
        startConversion: startConversion,
        updateConversionDirection: updateConversionDirection
    };

    // ==================== Application Bootstrap ====================
    document.addEventListener('DOMContentLoaded', initializeApp);

    // Handle page unload
    window.addEventListener('beforeunload', function(e) {
        if (App.isConverting) {
            e.preventDefault();
            e.returnValue = 'Conversion is in progress. Are you sure you want to leave?';
        }
    });

    // ==================== Missing Functions - Fix Implementation ====================
    
    // Updated API analyze function to handle both RAW and image files
    async function analyzeFile() {
        if (App.selectedFiles.length !== 1) {
            showErrorMessage('Please select exactly one file for analysis.');
            return;
        }

        const fileData = App.selectedFiles[0];
        const isRAW = isValidRAWFile(fileData.file);
        const isImage = isValidImageFile(fileData.file);
        
        if (!isRAW && !isImage) {
            showErrorMessage('Analysis is only available for RAW and image files.');
            return;
        }
        
        const fileType = isRAW ? 'RAW' : 'image';
        showLoadingState(`Analyzing ${fileType} file...`);

        try {
            const formData = new FormData();
            formData.append('file', fileData.file);

            // Use different endpoints based on file type
            const endpoint = isRAW ? '/raw-jpg/api/analyze' : '/raw-jpg/api/analyze-image';
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                displayAnalysisResults(result.metadata || result, isRAW);
            } else {
                throw new Error(result.error || 'Analysis failed');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            showErrorMessage(`Analysis failed: ${error.message}`);
        } finally {
            hideLoadingState();
        }
    }

    // Updated displayAnalysisResults function to handle both RAW and image files
    function displayAnalysisResults(result, isRAW = true) {
        if (!App.elements.analysisContent) return;

        const metadata = result.metadata || result;
        
        let analysisHtml = `
            <div class="analysis-results">
                <div class="analysis-section">
                    <h4>File Information</h4>
                    <div class="analysis-grid">
                        <div class="analysis-item">
                            <span class="label">Filename:</span>
                            <span class="value">${metadata.filename || 'Unknown'}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Size:</span>
                            <span class="value">${formatFileSize(metadata.filesize || 0)}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Format:</span>
                            <span class="value">${metadata.format || 'Unknown'}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Dimensions:</span>
                            <span class="value">${metadata.dimensions?.width || 'N/A'} × ${metadata.dimensions?.height || 'N/A'}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Megapixels:</span>
                            <span class="value">${(((metadata.dimensions?.width || 0) * (metadata.dimensions?.height || 0)) / 1000000).toFixed(1)} MP</span>
                        </div>`;
        
        // Add camera/EXIF info if available
        if (metadata.brand || metadata.exif_data) {
            analysisHtml += `
                        <div class="analysis-item">
                            <span class="label">Camera/Software:</span>
                            <span class="value">${metadata.brand || metadata.exif_data?.Make || 'Unknown'}</span>
                        </div>`;
        }
        
        if (metadata.exif_data?.DateTime) {
            analysisHtml += `
                        <div class="analysis-item">
                            <span class="label">Date Taken:</span>
                            <span class="value">${metadata.exif_data.DateTime}</span>
                        </div>`;
        }
        
        analysisHtml += `
                    </div>
                </div>`;
        
        // Add RAW-specific details if it's a RAW file
        if (isRAW && metadata.raw_info) {
            analysisHtml += `
                <div class="analysis-section">
                    <h4>RAW Details</h4>
                    <div class="analysis-grid">
                        <div class="analysis-item">
                            <span class="label">Color Channels:</span>
                            <span class="value">${metadata.raw_info.num_colors || 'Unknown'}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Color Description:</span>
                            <span class="value">${metadata.raw_info.color_desc || 'Unknown'}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">RAW Type:</span>
                            <span class="value">${metadata.raw_info.raw_type || 'Unknown'}</span>
                        </div>
                        <div class="analysis-item">
                            <span class="label">Raw Dimensions:</span>
                            <span class="value">${metadata.dimensions?.raw_width || 'N/A'} × ${metadata.dimensions?.raw_height || 'N/A'}</span>
                        </div>
                    </div>
                </div>`;
        } else if (!isRAW && metadata.exif_data) {
            // Add EXIF details for regular image files
            analysisHtml += `
                <div class="analysis-section">
                    <h4>EXIF Data</h4>
                    <div class="analysis-grid">`;
            
            if (metadata.exif_data.Model) {
                analysisHtml += `
                        <div class="analysis-item">
                            <span class="label">Camera Model:</span>
                            <span class="value">${metadata.exif_data.Model}</span>
                        </div>`;
            }
            
            if (metadata.exif_data.FocalLength) {
                analysisHtml += `
                        <div class="analysis-item">
                            <span class="label">Focal Length:</span>
                            <span class="value">${metadata.exif_data.FocalLength}mm</span>
                        </div>`;
            }
            
            if (metadata.exif_data.FNumber) {
                analysisHtml += `
                        <div class="analysis-item">
                            <span class="label">Aperture:</span>
                            <span class="value">f/${metadata.exif_data.FNumber}</span>
                        </div>`;
            }
            
            if (metadata.exif_data.ExposureTime) {
                analysisHtml += `
                        <div class="analysis-item">
                            <span class="label">Shutter Speed:</span>
                            <span class="value">${metadata.exif_data.ExposureTime}s</span>
                        </div>`;
            }
            
            if (metadata.exif_data.ISOSpeedRatings) {
                analysisHtml += `
                        <div class="analysis-item">
                            <span class="label">ISO:</span>
                            <span class="value">${metadata.exif_data.ISOSpeedRatings}</span>
                        </div>`;
            }
            
            analysisHtml += `
                    </div>
                </div>`;
        }
        
        // Add appropriate processing tips based on file type
        const tips = isRAW ? [
            'Use Camera White Balance for natural colors',
            'Enable Auto Brightness for balanced exposure', 
            'Choose JPEG for smaller files or PNG for highest quality',
            'RAW files provide maximum editing flexibility'
        ] : [
            'Consider converting to DNG for better compatibility',
            'Preserve metadata to maintain original information',
            'RAW conversion allows for advanced post-processing',
            'Check image quality before converting to RAW format'
        ];
        
        analysisHtml += `
                <div class="analysis-section">
                    <h4>Processing Tips</h4>
                    <ul class="tips-list">
                        ${tips.map(tip => `<li>${tip}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;

        App.elements.analysisContent.innerHTML = analysisHtml;
        showAnalysisModal();
    }
    
    // Fix generatePreview function to handle both RAW and image files
    async function generatePreview() {
        if (App.selectedFiles.length !== 1) {
            showErrorMessage('Please select exactly one file for preview.');
            return;
        }

        const fileData = App.selectedFiles[0];
        const isRAW = isValidRAWFile(fileData.file);
        const isImage = isValidImageFile(fileData.file);
        
        if (!isRAW && !isImage) {
            showErrorMessage('Preview is only available for RAW and image files.');
            return;
        }
        
        const fileType = isRAW ? 'RAW' : 'image';
        showLoadingState(`Generating ${fileType} preview...`);

        try {
            const formData = new FormData();
            formData.append('file', fileData.file);

            // Use unified endpoint that handles both file types
            const response = await fetch('/raw-jpg/create-preview', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                if (result.file_type === 'raw' && result.preview_filename) {
                    // Handle RAW preview (file-based)
                    const previewResponse = await fetch(`/raw-jpg/preview/${result.preview_filename}`);
                    if (previewResponse.ok) {
                        const blob = await previewResponse.blob();
                        const previewUrl = URL.createObjectURL(blob);
                        displayPreview(previewUrl);
                    } else {
                        throw new Error('Failed to load RAW preview image');
                    }
                } else if (result.file_type === 'image' && result.preview) {
                    // Handle image preview (base64 data)
                    displayPreview(result.preview);
                } else {
                    // Fallback: try to handle either format
                    if (result.preview) {
                        displayPreview(result.preview);
                    } else if (result.preview_filename) {
                        const previewResponse = await fetch(`/raw-jpg/preview/${result.preview_filename}`);
                        if (previewResponse.ok) {
                            const blob = await previewResponse.blob();
                            const previewUrl = URL.createObjectURL(blob);
                            displayPreview(previewUrl);
                        } else {
                            throw new Error('Failed to load preview image');
                        }
                    } else {
                        throw new Error('No preview data received from server');
                    }
                }
            } else {
                throw new Error(result.error || 'Preview generation failed');
            }
        } catch (error) {
            console.error('Preview error:', error);
            showErrorMessage(`Preview generation failed: ${error.message}`);
        } finally {
            hideLoadingState();
        }
    }

    // Add missing utility functions
    function showLoadingState(message) {
        console.log('Loading:', message);
        if (App.elements.progressContainer) {
            App.elements.progressContainer.style.display = 'block';
            if (App.elements.progressText) {
                App.elements.progressText.textContent = message;
            }
        }
    }

    function hideLoadingState() {
        console.log('Loading complete');
        if (App.elements.progressContainer) {
            App.elements.progressContainer.style.display = 'none';
        }
    }
    
    function showAnalysisModal() {
        if (App.elements.analysisModal) {
            App.elements.analysisModal.style.display = 'flex';
            App.currentModal = 'analysis';
            document.body.style.overflow = 'hidden';
        }
    }

    function closeAnalysisModal() {
        if (App.elements.analysisModal) {
            App.elements.analysisModal.style.display = 'none';
            App.currentModal = null;
            document.body.style.overflow = '';
        }
    }

    function showPreviewModal() {
        if (App.elements.previewModal) {
            App.elements.previewModal.style.display = 'flex';
            App.currentModal = 'preview';
            document.body.style.overflow = 'hidden';
        }
    }

    function closePreviewModal() {
        if (App.elements.previewModal) {
            App.elements.previewModal.style.display = 'none';
            App.currentModal = null;
            document.body.style.overflow = '';
        }
    }
    
    function displayPreview(previewDataUrl) {
        if (!App.elements.previewContainer) return;

        App.elements.previewContainer.innerHTML = `
            <img src="${previewDataUrl}" alt="RAW Preview" style="max-width: 100%; height: auto; border-radius: 8px;">
        `;

        showPreviewModal();
    }
    
    function resetForNewConversion() {
        // Clear results
        hideSuccessResults();
        hideErrorResults();
        if (App.elements.resultsSection) {
            App.elements.resultsSection.style.display = 'none';
        }
        
        // Clear selected files
        clearAllFiles();
        
        // Reset form values to defaults
        if (App.elements.outputFormat) App.elements.outputFormat.value = 'JPEG';
        if (App.elements.quality) App.elements.quality.value = '95';
        if (document.getElementById('preserveMetadataRawToJpg')) {
            document.getElementById('preserveMetadataRawToJpg').checked = true;
        }
        if (App.elements.autoWhiteBalance) App.elements.autoWhiteBalance.checked = true;
        if (App.elements.autoBrightness) App.elements.autoBrightness.checked = true;
        
        updateQualityDisplay();
        updateUI();
    }
    
    function retryConversion() {
        hideErrorResults();
        startConversion();
    }

})();
