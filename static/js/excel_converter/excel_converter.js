// Excel Converter JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the Excel Converter
    initializeExcelConverter();
});

function initializeExcelConverter() {
    // File upload handling
    setupFileUpload('excel-upload-area', 'excel-file');
    
    // Form submission
    setupFormSubmission();
    
    // Output format selector
    setupOutputFormatSelector();
    
    // Modal controls
    setupModalControls();
    
    // Progress tracking
    setupProgressTracking();
    
    // Keyboard shortcuts
    setupKeyboardShortcuts();
    
    // Sheet selection functionality
    setupSheetSelection();
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
    
    // File input change handler
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0], uploadArea);
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
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (validateFile(file, fileInput.accept)) {
                // Simulate file input change
                const dt = new DataTransfer();
                dt.items.add(file);
                fileInput.files = dt.files;
                
                handleFileSelection(file, uploadArea);
            } else {
                showNotification('Invalid file type. Please select an Excel file (.xls, .xlsx, or .xlsm).', 'error');
            }
        }
    });
}

function validateFile(file, acceptedTypes) {
    if (!acceptedTypes) return true;
    
    const acceptedExtensions = acceptedTypes.split(',').map(type => type.trim());
    const fileName = file.name.toLowerCase();
    const fileExtension = '.' + fileName.split('.').pop();
    
    return acceptedExtensions.some(ext => 
        ext === fileExtension || 
        file.type === ext ||
        (ext.includes('/') && file.type.includes(ext.split('/')[0]))
    );
}

function handleFileSelection(file, uploadArea) {
    // Check file size (50MB limit)
    const maxSize = 50 * 1024 * 1024; // 50MB in bytes
    if (file.size > maxSize) {
        showNotification('File size exceeds 50MB limit. Please select a smaller file.', 'error');
        return;
    }
    
    // Validate Excel file type
    const validExtensions = ['.xls', '.xlsx', '.xlsm'];
    const fileName = file.name.toLowerCase();
    const isValidExcel = validExtensions.some(ext => fileName.endsWith(ext));
    
    if (!isValidExcel) {
        showNotification('Please select a valid Excel file (.xls, .xlsx, or .xlsm).', 'error');
        return;
    }
    
    // Update upload area appearance
    updateUploadAreaDisplay(uploadArea, file.name);
    
    // Show file info
    showFileInfo(file, uploadArea);
    
    // Load sheet information (if possible via FileReader API)
    loadSheetInformation(file);
}

function updateUploadAreaDisplay(uploadArea, filename) {
    uploadArea.classList.add('file-selected');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    
    if (uploadText && uploadSubtext) {
        uploadText.textContent = `Selected: ${filename}`;
        uploadSubtext.textContent = 'Click to change file or drag another Excel file';
        
        // Add file size info if available
        const fileInput = uploadArea.querySelector('.file-input');
        if (fileInput && fileInput.files.length > 0) {
            const fileSize = formatFileSize(fileInput.files[0].size);
            uploadSubtext.textContent += ` • ${fileSize}`;
        }
    }
}

function showFileInfo(file, uploadArea) {
    // Remove any existing file info
    const existingInfo = uploadArea.querySelector('.file-info');
    if (existingInfo) {
        existingInfo.remove();
    }
    
    // Create file info element
    const fileInfo = document.createElement('div');
    fileInfo.className = 'file-info mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg';
    fileInfo.innerHTML = `
        <div class="flex items-center space-x-3">
            <svg class="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3M7 3h10a2 2 0 012 2v14a2 2 0 01-2 2H7a2 2 0 01-2-2V5a2 2 0 012-2z"></path>
            </svg>
            <div class="flex-1">
                <p class="font-semibold text-green-900 dark:text-green-100">${file.name}</p>
                <p class="text-sm text-green-600 dark:text-green-400">
                    ${formatFileSize(file.size)} • Excel Spreadsheet • ${formatDate(file.lastModified)}
                </p>
            </div>
            <button type="button" onclick="clearFileSelection(this)" class="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-200">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    uploadArea.appendChild(fileInfo);
}

function clearFileSelection(button) {
    const uploadArea = button.closest('.upload-area');
    const fileInput = uploadArea.querySelector('.file-input');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    const fileInfo = uploadArea.querySelector('.file-info');
    
    // Clear file input
    if (fileInput) {
        fileInput.value = '';
    }
    
    // Reset upload area
    uploadArea.classList.remove('file-selected');
    if (uploadText) {
        uploadText.textContent = 'Drop your Excel file here or click to browse';
    }
    if (uploadSubtext) {
        uploadSubtext.textContent = 'Excel files only (.xls, .xlsx, .xlsm) - Max 50MB';
    }
    
    // Remove file info
    if (fileInfo) {
        fileInfo.remove();
    }
    
    // Hide sheet selection
    hideSheetSelection();
}

function loadSheetInformation(file) {
    // Note: Full sheet information requires server-side processing
    // For now, we'll show a placeholder that will be populated after upload
    const sheetSelection = document.getElementById('sheet-selection');
    const sheetsContainer = document.getElementById('sheets-container');
    const totalSheetsSpan = document.getElementById('total-sheets');
    
    if (sheetSelection && sheetsContainer) {
        // Check current output format to set appropriate default
        const selectedFormat = document.querySelector('input[name="output_format"]:checked');
        const isCsvSelected = selectedFormat && selectedFormat.value === 'csv';
        
        // For CSV, default to "first sheet", for others default to "all sheets"
        const defaultAllChecked = isCsvSelected ? '' : 'checked';
        const defaultFirstChecked = isCsvSelected ? 'checked' : '';
        
        // Show default options (will be updated after server processes the file)
        sheetsContainer.innerHTML = `
            <div class="space-y-3">
                <div class="flex items-center space-x-2">
                    <input type="radio" name="selected_sheets" value="all" id="sheet-all" class="text-green-600 focus:ring-green-500" ${defaultAllChecked}>
                    <label for="sheet-all" class="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer">Convert all sheets</label>
                </div>
                <div class="flex items-center space-x-2">
                    <input type="radio" name="selected_sheets" value="first" id="sheet-first" class="text-green-600 focus:ring-green-500" ${defaultFirstChecked}>
                    <label for="sheet-first" class="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer">Convert first sheet only</label>
                </div>
                <div class="flex items-center space-x-2">
                    <input type="radio" name="selected_sheets" value="manual" id="sheet-manual" class="text-green-600 focus:ring-green-500">
                    <label for="sheet-manual" class="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer">Manual sheet selection</label>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    File analysis will show actual sheet count and enable precise selection
                </p>
            </div>
        `;
        
        // Set default total sheets (will be updated after analysis)
        if (totalSheetsSpan) {
            totalSheetsSpan.textContent = '?';
        }
        
        sheetSelection.classList.remove('hidden');
        
        // Set up manual selection listener
        setupManualSheetSelection();
        
        // Apply CSV restrictions if CSV is selected
        if (isCsvSelected) {
            updateCsvSheetUI();
        }
        
        // Try to analyze file for actual sheet information
        analyzeExcelFile(file);
    }
}

function hideSheetSelection() {
    const sheetSelection = document.getElementById('sheet-selection');
    if (sheetSelection) {
        sheetSelection.classList.add('hidden');
    }
}

function setupSheetSelection() {
    // Handle sheet selection changes
    document.addEventListener('change', function(e) {
        if (e.target.name === 'selected_sheets') {
            console.log('Sheet selection changed:', e.target.value);
            handleSheetSelectionChange(e.target.value);
            
            // Check if CSV format is selected and user tries to select multiple sheets
            const selectedFormat = document.querySelector('input[name="output_format"]:checked');
            if (selectedFormat && selectedFormat.value === 'csv') {
                validateCsvSheetSelection(e.target.value);
            }
        }
    });
}

function setupManualSheetSelection() {
    const manualRadio = document.getElementById('sheet-manual');
    const manualInput = document.getElementById('manual-sheet-input');
    const validateButton = document.getElementById('validate-sheets');
    const manualSheetsInput = document.getElementById('manual-sheets');
    
    if (manualRadio && manualInput && validateButton && manualSheetsInput) {
        // Show/hide manual input based on selection
        document.addEventListener('change', function(e) {
            if (e.target.name === 'selected_sheets') {
                if (e.target.value === 'manual') {
                    manualInput.classList.remove('hidden');
                } else {
                    manualInput.classList.add('hidden');
                    clearValidationMessage();
                }
            }
        });
        
        // Validate button click
        validateButton.addEventListener('click', function() {
            validateSheetSelection();
        });
        
        // Enter key in input
        manualSheetsInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                validateSheetSelection();
            }
        });
        
        // Real-time validation for CSV format
        manualSheetsInput.addEventListener('input', function(e) {
            const selectedFormat = document.querySelector('input[name="output_format"]:checked');
            if (selectedFormat && selectedFormat.value === 'csv') {
                const input = e.target.value.trim();
                if (input && (input.includes(',') || input.includes('-'))) {
                    showCsvSheetWarning('manual');
                    // Clear the invalid part, but don't clear the whole input immediately
                    // Let user see the warning first
                }
            }
        });
    }
}

function handleSheetSelectionChange(value) {
    const manualInput = document.getElementById('manual-sheet-input');
    
    if (manualInput) {
        if (value === 'manual') {
            manualInput.classList.remove('hidden');
        } else {
            manualInput.classList.add('hidden');
            clearValidationMessage();
        }
    }
}

function analyzeExcelFile(file) {
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/convert/excel/analyze', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateSheetInformation(data);
        } else {
            console.warn('File analysis failed:', data.error);
            // Keep placeholder values
        }
    })
    .catch(error => {
        console.warn('File analysis error:', error);
        // Keep placeholder values
    });
}

function updateSheetInformation(analysisData) {
    const totalSheetsSpan = document.getElementById('total-sheets');
    
    if (totalSheetsSpan && analysisData.file_info) {
        totalSheetsSpan.textContent = analysisData.file_info.sheet_count || '?';
    }
    
    // Store sheet information for validation
    if (analysisData.sheets) {
        window.excelSheetInfo = {
            totalSheets: analysisData.file_info.sheet_count,
            sheets: analysisData.sheets
        };
    }
}

function validateSheetSelection() {
    const manualSheetsInput = document.getElementById('manual-sheets');
    const validationMessage = document.getElementById('sheet-validation-message');
    
    if (!manualSheetsInput || !validationMessage) return;
    
    const input = manualSheetsInput.value.trim();
    if (!input) {
        showValidationMessage('Please enter sheet numbers or ranges', 'error');
        return;
    }
    
    const totalSheets = window.excelSheetInfo?.totalSheets || null;
    if (!totalSheets) {
        showValidationMessage('Sheet analysis not complete yet. Please wait.', 'error');
        return;
    }
    
    // Check if CSV format is selected
    const selectedFormat = document.querySelector('input[name="output_format"]:checked');
    const isCsvSelected = selectedFormat && selectedFormat.value === 'csv';
    
    try {
        const parsedSheets = parseSheetSelection(input, totalSheets);
        
        if (parsedSheets.length === 0) {
            showValidationMessage('No valid sheets selected', 'error');
            return;
        }
        
        // CSV format specific validation - only single sheet allowed
        if (isCsvSelected && parsedSheets.length > 1) {
            showValidationMessage('CSV format only supports single sheet conversion. Please enter only one sheet number (e.g., "1" or "3").', 'error');
            return;
        }
        
        // Success message
        if (isCsvSelected) {
            showValidationMessage(`Valid! Will convert sheet ${parsedSheets[0]} only (CSV format supports single sheet).`, 'success');
        } else {
            showValidationMessage(`Valid! Will convert ${parsedSheets.length} sheet(s): ${parsedSheets.join(', ')}`, 'success');
        }
    } catch (error) {
        showValidationMessage(error.message, 'error');
    }
}

function parseSheetSelection(input, totalSheets) {
    const parts = input.split(',').map(part => part.trim());
    const selectedSheets = new Set();
    
    for (const part of parts) {
        if (part.includes('-')) {
            // Range: "2-4"
            const [start, end] = part.split('-').map(num => parseInt(num.trim()));
            if (isNaN(start) || isNaN(end)) {
                throw new Error(`Invalid range: "${part}". Use format like "2-4"`);
            }
            if (start > end) {
                throw new Error(`Invalid range: "${part}". Start must be less than or equal to end`);
            }
            if (start < 1 || end > totalSheets) {
                throw new Error(`Range "${part}" is outside valid sheet range (1-${totalSheets})`);
            }
            for (let i = start; i <= end; i++) {
                selectedSheets.add(i);
            }
        } else {
            // Single number: "1", "3", "5"
            const num = parseInt(part);
            if (isNaN(num)) {
                throw new Error(`Invalid sheet number: "${part}"`);
            }
            if (num < 1 || num > totalSheets) {
                throw new Error(`Sheet number ${num} is outside valid range (1-${totalSheets})`);
            }
            selectedSheets.add(num);
        }
    }
    
    return Array.from(selectedSheets).sort((a, b) => a - b);
}

function showValidationMessage(message, type) {
    const validationMessage = document.getElementById('sheet-validation-message');
    if (!validationMessage) return;
    
    validationMessage.className = `mt-2 text-sm ${type === 'success' ? 'validation-success' : 'validation-error'}`;
    validationMessage.textContent = message;
    validationMessage.classList.remove('hidden');
}

function clearValidationMessage() {
    const validationMessage = document.getElementById('sheet-validation-message');
    if (validationMessage) {
        validationMessage.classList.add('hidden');
    }
}

function setupFormSubmission() {
    const form = document.getElementById('excel-converter-form');
    
    if (form) {
        form.addEventListener('submit', handleFormSubmission);
    }
}

function handleFormSubmission(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    
    // Enhanced debug logging
    const selectedFormat = form.querySelector('input[name="output_format"]:checked');
    console.log('🔍 Excel form submission debug:');
    console.log('  Selected format element:', selectedFormat);
    console.log('  Selected format value:', selectedFormat ? selectedFormat.value : 'NONE');
    console.log('  All radio buttons:');
    const allRadios = form.querySelectorAll('input[name="output_format"]');
    allRadios.forEach((radio, index) => {
        console.log(`    [${index}] ${radio.value}: ${radio.checked ? 'CHECKED' : 'unchecked'}`);
    });
    console.log('  Form data entries:');
    for (let [key, value] of formData.entries()) {
        console.log(`    ${key}: ${value}`);
    }
    
    // Validate form
    if (!validateForm(form)) {
        return;
    }
    
    // Show processing modal
    showProcessingModal();
    
    // Start conversion
    startConversion(formData);
}

function validateForm(form) {
    const fileInput = form.querySelector('.file-input');
    
    if (!fileInput || !fileInput.files.length) {
        showNotification('Please select an Excel file to convert.', 'error');
        return false;
    }
    
    const file = fileInput.files[0];
    const maxSize = 50 * 1024 * 1024; // 50MB
    
    if (file.size > maxSize) {
        showNotification('File size exceeds 50MB limit.', 'error');
        return false;
    }
    
    // Validate Excel file type
    const validExtensions = ['.xls', '.xlsx'];
    const fileName = file.name.toLowerCase();
    const isValidExcel = validExtensions.some(ext => fileName.endsWith(ext));
    
    if (!isValidExcel) {
        showNotification('Please select a valid Excel file (.xls or .xlsx).', 'error');
        return false;
    }
    
    // Check if output format is selected
    const outputFormat = form.querySelector('input[name="output_format"]:checked');
    if (!outputFormat) {
        showNotification('Please select an output format.', 'error');
        return false;
    }
    
    // Debug: Log the selected format
    console.log('Validated output format:', outputFormat.value);
    
    // Additional validation: ensure the format value is valid
    const validFormats = ['csv', 'tsv', 'json', 'html', 'txt', 'xml', 'ods', 'pdf'];
    if (!validFormats.includes(outputFormat.value)) {
        showNotification('Invalid output format selected.', 'error');
        return false;
    }
    
    // Additional CSV format validation
    if (outputFormat.value === 'csv') {
        const sheetSelection = form.querySelector('input[name="selected_sheets"]:checked');
        
        // Block 'all' sheets selection for CSV
        if (sheetSelection && sheetSelection.value === 'all') {
            showNotification('CSV format only supports single sheet conversion. Please select "Convert first sheet only".', 'error');
            return false;
        }
        
        // Handle manual sheet input for CSV (must be single sheet)
        if (sheetSelection && sheetSelection.value === 'manual') {
            const manualSheetsInput = document.getElementById('manual-sheets');
            if (manualSheetsInput && manualSheetsInput.value.trim()) {
                const input = manualSheetsInput.value.trim();
                
                // Check for multiple sheets patterns (commas or dashes)
                if (input.includes(',') || input.includes('-')) {
                    showNotification('CSV format doesn\'t support multiple sheet selection. Please enter only one sheet number (e.g., "1" or "3").', 'error');
                    return false;
                }
                
                // Validate it's a valid single number
                if (!/^\d+$/.test(input)) {
                    showNotification('Please enter a valid sheet number (e.g., "1" or "3").', 'error');
                    return false;
                }
                
                // Additional validation using parseSheetSelection if available
                try {
                    const totalSheets = window.excelSheetInfo?.totalSheets;
                    if (totalSheets) {
                        const parsedSheets = parseSheetSelection(input, totalSheets);
                        if (parsedSheets.length > 1) {
                            showNotification('CSV format only supports single sheet conversion. Please enter only one sheet number.', 'error');
                            return false;
                        }
                    }
                } catch (error) {
                    showNotification(`Invalid sheet selection: ${error.message}`, 'error');
                    return false;
                }
            } else {
                // Manual selected but no input provided
                showNotification('Please specify a sheet number for manual selection or choose "Convert first sheet only".', 'error');
                return false;
            }
        }
    }
    
    // Validate manual sheet selection if selected
    const sheetSelection = form.querySelector('input[name="selected_sheets"]:checked');
    if (sheetSelection && sheetSelection.value === 'manual') {
        const manualSheetsInput = document.getElementById('manual-sheets');
        if (!manualSheetsInput || !manualSheetsInput.value.trim()) {
            showNotification('Please specify sheet numbers for manual selection or choose a different option.', 'error');
            return false;
        }
        
        // Validate the manual selection format
        try {
            const totalSheets = window.excelSheetInfo?.totalSheets;
            if (totalSheets) {
                parseSheetSelection(manualSheetsInput.value.trim(), totalSheets);
            }
        } catch (error) {
            showNotification(`Invalid sheet selection: ${error.message}`, 'error');
            return false;
        }
    }
    
    return true;
}

function startConversion(formData) {
    const xhr = new XMLHttpRequest();
    
    // Set up progress tracking
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percentComplete = (e.loaded / e.total) * 100;
            updateProgress(Math.round(percentComplete), 'Uploading Excel file...');
        }
    });
    
    xhr.addEventListener('load', () => {
        console.log('XHR Response received:');
        console.log('  Status:', xhr.status);
        console.log('  Content-Type:', xhr.getResponseHeader('Content-Type'));
        console.log('  Response size:', xhr.response ? xhr.response.size : 'N/A');
        
        if (xhr.status === 200) {
            const contentType = xhr.getResponseHeader('Content-Type') || '';
            const responseSize = xhr.response ? xhr.response.size : 0;
            
            // Enhanced detection logic - only treat as JSON error if:
            // 1. Content-Type is application/json AND no Content-Disposition header
            // 2. OR very small response that looks like error JSON
            const disposition = xhr.getResponseHeader('Content-Disposition');
            const isErrorResponse = contentType.includes('application/json') && !disposition;
            const isPossibleErrorText = responseSize < 500 && contentType.includes('text') && !disposition;
            
            if (isErrorResponse || isPossibleErrorText) {
                // JSON response (likely an error case)
                const reader = new FileReader();
                reader.onload = function() {
                    try {
                        const response = JSON.parse(reader.result);
                        console.log('JSON Response parsed:', response);
                        if (response.success === false) {
                            handleConversionError(response.error || 'Conversion failed');
                        } else {
                            // Unexpected JSON success - treat as download
                            handleDirectDownload(xhr);
                        }
                    } catch (e) {
                        console.log('Failed to parse JSON, treating as binary download');
                        handleDirectDownload(xhr);
                    }
                };
                reader.readAsText(xhr.response);
            } else {
                // Binary response (successful file download)
                console.log('Treating as binary download');
                handleDirectDownload(xhr);
            }
        } else if (xhr.status === 400) {
            handleConversionError('Invalid request. Please check your file and try again.');
        } else if (xhr.status === 413) {
            handleConversionError('File size too large. Maximum size is 50MB.');
        } else if (xhr.status === 429) {
            handleConversionError('Too many requests. Please wait a moment and try again.');
        } else {
            handleConversionError(`Server error: ${xhr.status}. Please try again later.`);
        }
    });
    
    xhr.addEventListener('error', () => {
        handleConversionError('Network error occurred. Please check your connection and try again.');
    });
    
    xhr.addEventListener('timeout', () => {
        handleConversionError('Request timed out. Please try again with a smaller file.');
    });
    
    // Send request
    xhr.open('POST', '/convert/excel', true);
    xhr.responseType = 'blob';  // Expect binary response for file downloads
    xhr.timeout = 300000; // 5 minute timeout
    xhr.send(formData);
    
    // Update progress to show processing
    setTimeout(() => {
        updateProgress(50, 'Converting Excel file...');
    }, 1000);
}

function handleConversionSuccess(response) {
    hideProcessingModal();
    
    if (response.download_url) {
        // Start download
        const link = document.createElement('a');
        link.href = response.download_url;
        link.download = response.filename || 'converted_excel';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Show success modal
        showSuccessModal(response.filename);
    }
}

function handleDirectDownload(xhr) {
    console.log('Starting direct download handling...');
    
    try {
        hideProcessingModal();
        
        // Use the blob response directly
        const blob = xhr.response;
        console.log('Blob details:', {
            size: blob ? blob.size : 'N/A',
            type: blob ? blob.type : 'N/A'
        });
        
        if (!blob || blob.size === 0) {
            throw new Error('Empty response received from server');
        }
        
        // Check if the blob might actually be a JSON error response
        if (blob.size < 1000 && (blob.type.includes('application/json') || blob.type.includes('text'))) {
            // This might be an error response in JSON format
            const reader = new FileReader();
            reader.onload = function() {
                try {
                    const response = JSON.parse(reader.result);
                    if (response.success === false) {
                        handleConversionError(response.error || 'Conversion failed');
                        return;
                    }
                } catch (e) {
                    // If not JSON, continue with download
                }
                // Proceed with download
                proceedWithDownload(blob, xhr);
            };
            reader.readAsText(blob);
            return;
        }
        
        // Proceed with normal download
        proceedWithDownload(blob, xhr);
        
    } catch (error) {
        console.error('Download handling error:', error);
        handleConversionError('Failed to download converted file: ' + error.message);
    }
}

function proceedWithDownload(blob, xhr) {
    const url = window.URL.createObjectURL(blob);
    
    // Extract filename from Content-Disposition header
    const disposition = xhr.getResponseHeader('Content-Disposition');
    let filename = 'converted_excel'; // Default without extension
    
    console.log('Content-Disposition header:', disposition);
    
    if (disposition) {
        const filenameMatch = disposition.match(/filename="(.+)"/);
        if (filenameMatch) {
            filename = filenameMatch[1];
        }
    }
    
    // If no filename from server, try to determine based on selected format
    if (filename === 'converted_excel') {
        const selectedFormat = document.querySelector('input[name="output_format"]:checked');
        if (selectedFormat) {
            const extensionMap = {
                'csv': '.csv',
                'tsv': '.tsv',
                'json': '.json',
                'html': '.html',
                'txt': '.txt',
                'xml': '.xml',
                'ods': '.ods',
                'pdf': '.pdf'
            };
            filename += extensionMap[selectedFormat.value] || '';
        }
    }
    
    console.log('Final filename:', filename);
    
    // Start download
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up
    window.URL.revokeObjectURL(url);
    
    // Show success modal
    showSuccessModal(filename);
}

function handleConversionError(error) {
    hideProcessingModal();
    showErrorModal(error);
}

function setupOutputFormatSelector() {
    const formatRadios = document.querySelectorAll('input[name="output_format"]');
    const csvOptions = document.getElementById('csv-options');
    const tsvOptions = document.getElementById('tsv-options');
    const pdfOptions = document.getElementById('pdf-options');
    
    formatRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            // Update UI based on selected format
            updateFormatSelection(e.target.value);
            
            // CSV format: Handle sheet selection restrictions
            if (e.target.value === 'csv') {
                handleCsvFormatSelection();
                // Also ensure first sheet is selected by default if available
                ensureFirstSheetForCsv();
            } else {
                // Remove CSV restrictions when other formats are selected
                removeCsvSheetRestrictions();
            }
            
            // Hide all format-specific options first
            hideAllFormatOptions();
            
            // Show format-specific options
            const format = e.target.value;
            if (format === 'csv' && csvOptions) {
                csvOptions.classList.remove('hidden');
            } else if (format === 'tsv' && tsvOptions) {
                tsvOptions.classList.remove('hidden');
            } else if (format === 'pdf' && pdfOptions) {
                pdfOptions.classList.remove('hidden');
            }
        });
    });
    
    // Initialize format options display
    const checkedFormat = document.querySelector('input[name="output_format"]:checked');
    if (checkedFormat) {
        hideAllFormatOptions();
        const format = checkedFormat.value;
        if (format === 'csv' && csvOptions) {
            csvOptions.classList.remove('hidden');
            // Check if CSV is initially selected
            if (format === 'csv') {
                handleCsvFormatSelection();
            }
        }
    }
}

function hideAllFormatOptions() {
    const formatOptions = ['csv-options', 'tsv-options', 'pdf-options'];
    formatOptions.forEach(optionId => {
        const element = document.getElementById(optionId);
        if (element) {
            element.classList.add('hidden');
        }
    });
}

function updateFormatSelection(format) {
    // You can add specific UI updates based on the selected format here
    console.log(`Selected output format: ${format}`);
    
    // Example: Show format-specific information
    const formatInfo = {
        csv: 'CSV format is perfect for data analysis and spreadsheet applications.',
        tsv: 'TSV format uses tabs as delimiters, ideal for data that contains commas.',
        json: 'JSON format provides structured data for APIs and web applications.',
        html: 'HTML format creates web-ready tables with optional formatting.',
        txt: 'TXT format provides plain text representation of your data.',
        xml: 'XML format offers hierarchical data structure for system integration.',
        ods: 'ODS format creates OpenDocument spreadsheets compatible with LibreOffice.',
        pdf: 'PDF format creates professional documents for printing and sharing.'
    };
    
    // Show download info for PDF multi-sheet scenario
    if (format === 'pdf') {
        showPdfDownloadInfo();
    } else {
        hidePdfDownloadInfo();
    }
    
    // You could show this info in a tooltip or info box
    if (formatInfo[format]) {
        console.log(formatInfo[format]);
    }
}

function showPdfDownloadInfo() {
    const existingInfo = document.querySelector('.pdf-download-info');
    if (existingInfo) return; // Already shown
    
    const pdfOptions = document.getElementById('pdf-options');
    if (pdfOptions) {
        const info = document.createElement('div');
        info.className = 'pdf-download-info download-info';
        info.innerHTML = `
            <div class="flex items-center space-x-2">
                <svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span class="text-sm font-medium text-green-800 dark:text-green-200">
                    <strong>PDF Output:</strong> Each sheet becomes a separate PDF file. Multiple sheets will be packaged in a ZIP file.
                </span>
            </div>
        `;
        pdfOptions.appendChild(info);
    }
}

function hidePdfDownloadInfo() {
    const info = document.querySelector('.pdf-download-info');
    if (info) {
        info.remove();
    }
}

function setupModalControls() {
    // Close buttons
    const closeButtons = document.querySelectorAll('#close-success, #close-error');
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            hideAllModals();
        });
    });
    
    // Download again button
    const downloadAgainButton = document.getElementById('download-again');
    if (downloadAgainButton) {
        downloadAgainButton.addEventListener('click', () => {
            // Re-trigger last download if available
            const lastDownloadUrl = downloadAgainButton.dataset.downloadUrl;
            const lastFilename = downloadAgainButton.dataset.filename;
            
            if (lastDownloadUrl) {
                const link = document.createElement('a');
                link.href = lastDownloadUrl;
                link.download = lastFilename || 'converted_excel';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        });
    }
    
    // Close modals when clicking outside
    document.addEventListener('click', (e) => {
        const modals = document.querySelectorAll('.fixed.inset-0');
        modals.forEach(modal => {
            if (e.target === modal && !modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
            }
        });
    });
}

function setupProgressTracking() {
    // This will be called during conversion to show progress
    window.updateConversionProgress = (percent, message) => {
        updateProgress(percent, message);
    };
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Escape key to close modals
        if (e.key === 'Escape') {
            hideAllModals();
        }
        
        // Ctrl+U to focus file input
        if (e.ctrlKey && e.key === 'u') {
            e.preventDefault();
            const fileInput = document.getElementById('excel-file');
            if (fileInput) {
                fileInput.click();
            }
        }
    });
}

// Modal functions
function showProcessingModal() {
    const modal = document.getElementById('processing-modal');
    const message = document.getElementById('processing-message');
    
    if (modal) {
        modal.classList.remove('hidden');
        
        if (message) {
            message.textContent = 'Converting Excel file... Please wait.';
        }
        
        updateProgress(0, 'Preparing conversion...');
    }
}

function hideProcessingModal() {
    const modal = document.getElementById('processing-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function showSuccessModal(filename) {
    const modal = document.getElementById('success-modal');
    const downloadAgainButton = document.getElementById('download-again');
    
    if (modal) {
        modal.classList.remove('hidden');
        
        // Store download info for "Download Again" functionality
        if (downloadAgainButton && filename) {
            downloadAgainButton.dataset.filename = filename;
        }
    }
}

function showErrorModal(errorMessage) {
    const modal = document.getElementById('error-modal');
    const messageElement = document.getElementById('error-message');
    
    if (modal) {
        modal.classList.remove('hidden');
        
        if (messageElement) {
            messageElement.textContent = errorMessage || 'An unexpected error occurred during conversion. Please try again.';
        }
    }
}

function hideAllModals() {
    const modals = document.querySelectorAll('.fixed.inset-0');
    modals.forEach(modal => {
        modal.classList.add('hidden');
    });
}

function updateProgress(percent, message) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const processingMessage = document.getElementById('processing-message');
    
    if (progressBar) {
        progressBar.style.width = `${Math.max(0, Math.min(100, percent))}%`;
    }
    
    if (progressText) {
        progressText.textContent = `${Math.max(0, Math.min(100, percent))}% complete`;
    }
    
    if (processingMessage && message) {
        processingMessage.textContent = message;
    }
}

// CSV Format Specific Functions
function handleCsvFormatSelection() {
    console.log('CSV format selected - setting up sheet restrictions');
    
    // Force selection to "first sheet" only if "all" was previously selected
    // Allow manual selection but show UI restrictions
    const currentSheetSelection = document.querySelector('input[name="selected_sheets"]:checked');
    if (currentSheetSelection && currentSheetSelection.value === 'all') {
        // Show warning popup only for 'all' selection
        showCsvSheetWarning(currentSheetSelection.value);
        
        // Force select "first sheet"
        const firstSheetRadio = document.getElementById('sheet-first');
        if (firstSheetRadio) {
            firstSheetRadio.checked = true;
            handleSheetSelectionChange('first');
        }
    }
    
    // Add visual indicators and disable problematic options
    updateCsvSheetUI();
}

function validateCsvSheetSelection(selectedValue) {
    if (selectedValue === 'all') {
        // Only show warning for 'all' sheets, not for 'manual'
        showCsvSheetWarning(selectedValue);
        
        // Force select "first sheet"
        setTimeout(() => {
            const firstSheetRadio = document.getElementById('sheet-first');
            if (firstSheetRadio) {
                firstSheetRadio.checked = true;
                handleSheetSelectionChange('first');
            }
        }, 100);
        
        return false;
    }
    // Allow manual selection - validation will happen when user inputs values or clicks validate
    return true;
}

function showCsvSheetWarning(attemptedSelection) {
    const message = attemptedSelection === 'all' 
        ? 'CSV format only supports single sheet conversion. Please select "Convert first sheet only" or choose a different format like JSON for multiple sheets.'
        : 'CSV format only supports single sheet conversion. Please enter only one sheet number (e.g., "1" or "3") or select "Convert first sheet only". For multiple sheets, choose JSON format.';
    
    // Create and show warning modal
    const warningModal = createCsvWarningModal(message);
    document.body.appendChild(warningModal);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (warningModal.parentElement) {
            warningModal.remove();
        }
    }, 4000);
}

function createCsvWarningModal(message) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center csv-warning-modal';
    modal.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md mx-4 border-l-4 border-orange-500">
            <div class="flex items-center space-x-3 mb-4">
                <div class="w-10 h-10 bg-orange-100 dark:bg-orange-900 rounded-full flex items-center justify-center">
                    <svg class="w-6 h-6 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                    </svg>
                </div>
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">CSV Format Restriction</h3>
            </div>
            <p class="text-gray-600 dark:text-gray-300 mb-6">${message}</p>
            <div class="flex justify-end space-x-3">
                <button onclick="this.closest('.csv-warning-modal').remove()" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200">
                    Got it
                </button>
                <button onclick="switchToJsonFormat(); this.closest('.csv-warning-modal').remove();" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                    Switch to JSON
                </button>
            </div>
        </div>
    `;
    
    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    return modal;
}

function switchToJsonFormat() {
    const jsonRadio = document.getElementById('format-json');
    if (jsonRadio) {
        jsonRadio.checked = true;
        jsonRadio.dispatchEvent(new Event('change', { bubbles: true }));
        showNotification('Switched to JSON format which supports multiple sheets.', 'success');
    }
}

function ensureFirstSheetForCsv() {
    // If sheet selection is available and 'all' is currently selected,
    // switch to 'first sheet' for CSV format
    const currentSheetSelection = document.querySelector('input[name="selected_sheets"]:checked');
    if (currentSheetSelection && currentSheetSelection.value === 'all') {
        const firstSheetRadio = document.getElementById('sheet-first');
        if (firstSheetRadio) {
            firstSheetRadio.checked = true;
            handleSheetSelectionChange('first');
            console.log('Automatically switched to first sheet for CSV format');
        }
    }
}

function updateCsvSheetUI() {
    // Add visual indicators to show CSV restrictions
    const allSheetLabel = document.querySelector('label[for="sheet-all"]');
    const manualSheetLabel = document.querySelector('label[for="sheet-manual"]');
    const firstSheetLabel = document.querySelector('label[for="sheet-first"]');
    const manualSheetsInput = document.getElementById('manual-sheets');
    
    if (allSheetLabel) {
        allSheetLabel.classList.add('text-gray-400', 'dark:text-gray-500');
        if (!allSheetLabel.querySelector('.csv-restriction-note')) {
            const note = document.createElement('span');
            note.className = 'csv-restriction-note text-xs text-orange-500 ml-2';
            note.textContent = '(Not available for CSV)';
            allSheetLabel.appendChild(note);
        }
    }
    
    if (manualSheetLabel) {
        // Don't disable manual option, but change the text to indicate single sheet only
        if (!manualSheetLabel.querySelector('.csv-restriction-note')) {
            const note = document.createElement('span');
            note.className = 'csv-restriction-note text-xs text-orange-500 ml-2';
            note.textContent = '(Single sheet only for CSV)';
            manualSheetLabel.appendChild(note);
        }
    }
    
    if (firstSheetLabel) {
        firstSheetLabel.classList.remove('text-gray-400', 'dark:text-gray-500');
        firstSheetLabel.classList.add('text-green-600', 'dark:text-green-400', 'font-medium');
    }
    
    // Update placeholder text for manual input to show single sheet example
    if (manualSheetsInput) {
        manualSheetsInput.setAttribute('data-original-placeholder', manualSheetsInput.placeholder);
        manualSheetsInput.placeholder = 'e.g., 1 or 3 (single sheet only for CSV)';
    }
    
    // Disable only the "all sheets" radio button, keep manual available but restricted
    const allSheetRadio = document.getElementById('sheet-all');
    
    if (allSheetRadio) {
        allSheetRadio.disabled = true;
        allSheetRadio.classList.add('cursor-not-allowed');
    }
}

function removeCsvSheetRestrictions() {
    // Remove visual indicators and re-enable options
    const allSheetLabel = document.querySelector('label[for="sheet-all"]');
    const manualSheetLabel = document.querySelector('label[for="sheet-manual"]');
    const firstSheetLabel = document.querySelector('label[for="sheet-first"]');
    const manualSheetsInput = document.getElementById('manual-sheets');
    
    // Remove restriction notes
    document.querySelectorAll('.csv-restriction-note').forEach(note => note.remove());
    
    if (allSheetLabel) {
        allSheetLabel.classList.remove('text-gray-400', 'dark:text-gray-500');
        allSheetLabel.classList.add('text-gray-700', 'dark:text-gray-300');
    }
    
    if (manualSheetLabel) {
        manualSheetLabel.classList.remove('text-gray-400', 'dark:text-gray-500');
        manualSheetLabel.classList.add('text-gray-700', 'dark:text-gray-300');
    }
    
    if (firstSheetLabel) {
        firstSheetLabel.classList.remove('text-green-600', 'dark:text-green-400', 'font-medium');
        firstSheetLabel.classList.add('text-gray-700', 'dark:text-gray-300');
    }
    
    // Restore original placeholder text
    if (manualSheetsInput) {
        const originalPlaceholder = manualSheetsInput.getAttribute('data-original-placeholder');
        if (originalPlaceholder) {
            manualSheetsInput.placeholder = originalPlaceholder;
        } else {
            manualSheetsInput.placeholder = 'e.g., 1,3,5 or 2-4 or 1,4-6';
        }
    }
    
    // Re-enable radio buttons
    const allSheetRadio = document.getElementById('sheet-all');
    const manualSheetRadio = document.getElementById('sheet-manual');
    
    if (allSheetRadio) {
        allSheetRadio.disabled = false;
        allSheetRadio.classList.remove('cursor-not-allowed');
    }
    
    if (manualSheetRadio) {
        manualSheetRadio.disabled = false;
        manualSheetRadio.classList.remove('cursor-not-allowed');
    }
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(timestamp) {
    return new Date(timestamp).toLocaleDateString();
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 ${
        type === 'error' ? 'bg-red-500 text-white' : 
        type === 'success' ? 'bg-green-500 text-white' : 
        'bg-green-500 text-white'
    }`;
    notification.innerHTML = `
        <div class="flex items-center space-x-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${type === 'error' ? 
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>' :
                    type === 'success' ?
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>' :
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>'
                }
            </svg>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 hover:text-gray-200">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
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

// Global functions to make them accessible from HTML
window.clearFileSelection = clearFileSelection;
window.switchToJsonFormat = switchToJsonFormat;
