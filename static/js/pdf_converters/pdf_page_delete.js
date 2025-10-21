// PDF Page Delete functionality
document.addEventListener('DOMContentLoaded', () => {
    const pageDeleteApp = document.getElementById('pdf-page-delete-app');
    if (!pageDeleteApp) return;

    // DOM Elements
    const elements = {
        uploadSection: pageDeleteApp.querySelector('#upload-section'),
        pagesSection: pageDeleteApp.querySelector('#pages-section'),
        batchOptionsSection: pageDeleteApp.querySelector('#batch-options-section'),
        fileInput: pageDeleteApp.querySelector('#pdf-file-input'),
        uploadZone: pageDeleteApp.querySelector('#upload-zone'),
        pagesGrid: pageDeleteApp.querySelector('#pages-grid'),
        selectionControls: pageDeleteApp.querySelector('#selection-controls'),
        operationToggle: pageDeleteApp.querySelector('#operation-toggle'),
        processBtn: pageDeleteApp.querySelector('#process-btn'),
        newUploadBtn: pageDeleteApp.querySelector('#new-upload-btn'),
        resultsSection: pageDeleteApp.querySelector('#results-section'),
        processingOverlay: pageDeleteApp.querySelector('#processing-overlay'),
        batchFileInput: pageDeleteApp.querySelector('#batch-file-input'),
        batchUploadZone: pageDeleteApp.querySelector('#batch-upload-zone'),
        batchProcessBtn: pageDeleteApp.querySelector('#batch-process-btn'),
        uploadModeToggle: pageDeleteApp.querySelector('#upload-mode-toggle'),
        singleUpload: pageDeleteApp.querySelector('#single-upload'),
        batchUpload: pageDeleteApp.querySelector('#batch-upload'),
        batchFileList: pageDeleteApp.querySelector('#batch-file-list')
    };

    // Application State
    let state = {
        currentFile: null,
        pages: [],
        selectedPages: new Set(),
        operationMode: 'delete', // 'delete' or 'keep'
        uploadMode: 'single', // 'single' or 'batch'
        isProcessing: false,
        batchFiles: []
    };

    // Initialize Event Listeners
    initializeEventListeners();

    function initializeEventListeners() {
        // Check if required elements exist before adding listeners
        if (!elements.uploadZone || !elements.fileInput) {
            console.error('Required upload elements not found');
            return;
        }

        // Single file upload - prevent event bubbling from label to upload zone
        elements.uploadZone.addEventListener('click', (e) => {
            // Only trigger if the click is not from the label or input
            if (!e.target.closest('label') && !e.target.closest('input')) {
                elements.fileInput.click();
            }
        });
        elements.uploadZone.addEventListener('dragover', handleDragOver);
        elements.uploadZone.addEventListener('dragleave', handleDragLeave);
        elements.uploadZone.addEventListener('drop', handleFileDrop);
        elements.fileInput.addEventListener('change', handleFileSelect);

        // Batch upload - prevent event bubbling from label to upload zone
        if (elements.batchUploadZone && elements.batchFileInput) {
            elements.batchUploadZone.addEventListener('click', (e) => {
                // Only trigger if the click is not from the label or input
                if (!e.target.closest('label') && !e.target.closest('input')) {
                    elements.batchFileInput.click();
                }
            });
            elements.batchUploadZone.addEventListener('dragover', handleBatchDragOver);
            elements.batchUploadZone.addEventListener('dragleave', handleBatchDragLeave);
            elements.batchUploadZone.addEventListener('drop', handleBatchFileDrop);
            elements.batchFileInput.addEventListener('change', handleBatchFileSelect);
        }

        // Upload mode toggle
        if (elements.uploadModeToggle) {
            elements.uploadModeToggle.addEventListener('click', handleUploadModeToggle);
        }
        
        // Operation mode toggle
        if (elements.operationToggle) {
            elements.operationToggle.addEventListener('click', handleOperationToggle);
        }

        // Process buttons
        if (elements.processBtn) {
            elements.processBtn.addEventListener('click', processSelectedPages);
        }
        if (elements.batchProcessBtn) {
            elements.batchProcessBtn.addEventListener('click', processBatchFiles);
        }
        if (elements.newUploadBtn) {
            elements.newUploadBtn.addEventListener('click', resetInterface);
        }

        // Selection controls
        setupSelectionControls();
    }

    function setupSelectionControls() {
        const selectAllBtn = elements.selectionControls.querySelector('#select-all-btn');
        const selectNoneBtn = elements.selectionControls.querySelector('#select-none-btn');
        const selectOddBtn = elements.selectionControls.querySelector('#select-odd-btn');
        const selectEvenBtn = elements.selectionControls.querySelector('#select-even-btn');
        const selectRangeBtn = elements.selectionControls.querySelector('#select-range-btn');

        selectAllBtn?.addEventListener('click', () => selectPages('all'));
        selectNoneBtn?.addEventListener('click', () => selectPages('none'));
        selectOddBtn?.addEventListener('click', () => selectPages('odd'));
        selectEvenBtn?.addEventListener('click', () => selectPages('even'));
        selectRangeBtn?.addEventListener('click', showRangeDialog);
    }

    // File Upload Handlers
    function handleDragOver(e) {
        e.preventDefault();
        elements.uploadZone.classList.add('dragover');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
    }

    function handleFileDrop(e) {
        e.preventDefault();
        elements.uploadZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            processFileUpload(files[0]);
        }
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            processFileUpload(files[0]);
        }
    }

    // Batch Upload Handlers
    function handleBatchDragOver(e) {
        e.preventDefault();
        elements.batchUploadZone.classList.add('dragover');
    }

    function handleBatchDragLeave(e) {
        e.preventDefault();
        elements.batchUploadZone.classList.remove('dragover');
    }

    function handleBatchFileDrop(e) {
        e.preventDefault();
        elements.batchUploadZone.classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files).filter(file => 
            file.type === 'application/pdf'
        );
        if (files.length > 0) {
            processBatchUpload(files);
        }
    }

    function handleBatchFileSelect(e) {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            processBatchUpload(files);
        }
    }

    // File Processing
    async function processFileUpload(file) {
        if (file.type !== 'application/pdf') {
            showNotification('Please upload a PDF file', 'error');
            return;
        }

        state.currentFile = file;
        showProcessingOverlay('Analyzing PDF...');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload-pdf-for-deletion', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to upload PDF');
            }

            const data = await response.json();
            displayPages(data);
            
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            hideProcessingOverlay();
        }
    }

    function displayPages(data) {
        state.pages = data.pages;
        state.selectedPages.clear();

        elements.uploadSection.classList.add('hidden');
        elements.pagesSection.classList.remove('hidden');

        renderPagesGrid();
        updateSelectionInfo();
    }

    function renderPagesGrid() {
        elements.pagesGrid.innerHTML = '';
        
        state.pages.forEach((page, index) => {
            const pageElement = createPageElement(page, index);
            elements.pagesGrid.appendChild(pageElement);
        });
    }

    function createPageElement(page, index) {
        const pageDiv = document.createElement('div');
        pageDiv.className = 'page-item';
        pageDiv.dataset.pageNumber = page.page_number;

        const isSelected = state.selectedPages.has(page.page_number);
        if (isSelected) {
            pageDiv.classList.add('selected');
            pageDiv.classList.add(state.operationMode === 'delete' ? 'to-delete' : 'to-keep');
        }

        pageDiv.innerHTML = `
            <div class="relative">
                <img src="${page.thumbnail_url}" alt="Page ${page.page_number}" class="page-thumbnail" loading="lazy">
                <input type="checkbox" class="page-checkbox" ${isSelected ? 'checked' : ''}>
                ${isSelected ? `<div class="page-status-badge ${state.operationMode === 'delete' ? 'status-delete' : 'status-keep'}">${state.operationMode === 'delete' ? 'DELETE' : 'KEEP'}</div>` : ''}
            </div>
            <div class="page-info">
                <div class="page-number">Page ${page.page_number}</div>
                <div class="page-size">${page.page_size}</div>
            </div>
        `;

        pageDiv.addEventListener('click', () => togglePageSelection(page.page_number));
        
        return pageDiv;
    }

    function togglePageSelection(pageNumber) {
        if (state.selectedPages.has(pageNumber)) {
            state.selectedPages.delete(pageNumber);
        } else {
            state.selectedPages.add(pageNumber);
        }
        
        updatePageDisplay(pageNumber);
        updateSelectionInfo();
        updateProcessButton();
    }

    function updatePageDisplay(pageNumber) {
        const pageElement = elements.pagesGrid.querySelector(`[data-page-number="${pageNumber}"]`);
        if (!pageElement) return;

        const isSelected = state.selectedPages.has(pageNumber);
        const checkbox = pageElement.querySelector('.page-checkbox');
        
        pageElement.classList.toggle('selected', isSelected);
        pageElement.classList.toggle('to-delete', isSelected && state.operationMode === 'delete');
        pageElement.classList.toggle('to-keep', isSelected && state.operationMode === 'keep');
        
        checkbox.checked = isSelected;

        // Update status badge
        const existingBadge = pageElement.querySelector('.page-status-badge');
        if (existingBadge) {
            existingBadge.remove();
        }

        if (isSelected) {
            const badge = document.createElement('div');
            badge.className = `page-status-badge ${state.operationMode === 'delete' ? 'status-delete' : 'status-keep'}`;
            badge.textContent = state.operationMode === 'delete' ? 'DELETE' : 'KEEP';
            pageElement.querySelector('.relative').appendChild(badge);
        }
    }

    function selectPages(type) {
        state.selectedPages.clear();

        switch (type) {
            case 'all':
                state.pages.forEach(page => state.selectedPages.add(page.page_number));
                break;
            case 'odd':
                state.pages.forEach((page, index) => {
                    if (page.page_number % 2 === 1) {
                        state.selectedPages.add(page.page_number);
                    }
                });
                break;
            case 'even':
                state.pages.forEach((page, index) => {
                    if (page.page_number % 2 === 0) {
                        state.selectedPages.add(page.page_number);
                    }
                });
                break;
            case 'none':
            default:
                // Already cleared
                break;
        }

        renderPagesGrid();
        updateSelectionInfo();
        updateProcessButton();
    }

    function showRangeDialog() {
        const range = prompt('Enter page range (e.g., "1,3,5-7,10"):');
        if (range) {
            selectPageRange(range);
        }
    }

    function selectPageRange(rangeString) {
        state.selectedPages.clear();
        const pages = parsePageRanges(rangeString, state.pages.length);
        pages.forEach(pageNum => state.selectedPages.add(pageNum));
        
        renderPagesGrid();
        updateSelectionInfo();
        updateProcessButton();
    }

    function parsePageRanges(rangeString, totalPages) {
        const pages = [];
        const parts = rangeString.replace(/\s/g, '').split(',');
        
        parts.forEach(part => {
            if (part.includes('-')) {
                const [start, end] = part.split('-').map(Number);
                for (let i = Math.max(1, start); i <= Math.min(totalPages, end); i++) {
                    pages.push(i);
                }
            } else {
                const pageNum = parseInt(part);
                if (pageNum >= 1 && pageNum <= totalPages) {
                    pages.push(pageNum);
                }
            }
        });
        
        return [...new Set(pages)]; // Remove duplicates
    }

    // Upload Mode Toggle Handler
    function handleUploadModeToggle(e) {
        if (e.target.dataset.uploadMode) {
            state.uploadMode = e.target.dataset.uploadMode;
            
            // Update toggle UI
            elements.uploadModeToggle.querySelectorAll('.toggle-option').forEach(option => {
                option.classList.toggle('active', option.dataset.uploadMode === state.uploadMode);
            });

            // Show/hide upload sections
            if (state.uploadMode === 'single') {
                elements.singleUpload.classList.remove('hidden');
                elements.batchUpload.classList.add('hidden');
                elements.batchOptionsSection.classList.add('hidden');
            } else {
                elements.singleUpload.classList.add('hidden');
                elements.batchUpload.classList.remove('hidden');
                // Don't show batch options until files are uploaded
                // elements.batchOptionsSection.classList.remove('hidden');
            }
        }
    }

    function handleOperationToggle(e) {
        if (e.target.dataset.mode) {
            state.operationMode = e.target.dataset.mode;
            
            // Update toggle UI
            elements.operationToggle.querySelectorAll('.toggle-option').forEach(option => {
                option.classList.toggle('active', option.dataset.mode === state.operationMode);
            });

            // Update page displays
            renderPagesGrid();
            updateSelectionInfo();
        }
    }

    function updateSelectionInfo() {
        const infoPanel = elements.selectionControls.querySelector('#selection-info');
        const selectedCount = state.selectedPages.size;
        const totalPages = state.pages.length;
        
        let message = '';
        if (selectedCount === 0) {
            message = `No pages selected. Total: ${totalPages} pages`;
        } else {
            const action = state.operationMode === 'delete' ? 'delete' : 'keep only';
            const remaining = state.operationMode === 'delete' 
                ? totalPages - selectedCount 
                : selectedCount;
            message = `Selected ${selectedCount} pages to ${action}. ${remaining} pages will remain.`;
        }
        
        if (infoPanel) {
            infoPanel.textContent = message;
        }
    }

    function updateProcessButton() {
        const hasSelection = state.selectedPages.size > 0;
        const wouldCreateEmptyPdf = state.operationMode === 'delete' 
            ? state.selectedPages.size === state.pages.length
            : state.selectedPages.size === 0;

        elements.processBtn.disabled = !hasSelection || wouldCreateEmptyPdf || state.isProcessing;
        elements.processBtn.classList.toggle('btn-disabled', elements.processBtn.disabled);

        // Update button text
        const buttonText = elements.processBtn.querySelector('#process-btn-text');
        if (buttonText) {
            buttonText.textContent = state.operationMode === 'delete' 
                ? `Delete ${state.selectedPages.size} Pages`
                : `Keep ${state.selectedPages.size} Pages`;
        }
    }

    async function processSelectedPages() {
        if (state.selectedPages.size === 0 || state.isProcessing) return;

        state.isProcessing = true;
        const actionText = state.operationMode === 'delete' ? 'Deleting' : 'Keeping';
        showProcessingOverlay(`${actionText} selected pages...`);

        try {
            const response = await fetch('/delete-pdf-pages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    filename: state.currentFile.name.replace(/[^a-zA-Z0-9.-]/g, '_'),
                    pages_to_delete: Array.from(state.selectedPages),
                    operation_type: state.operationMode
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to process pages');
            }

            // Download the processed PDF
            const blob = await response.blob();
            downloadBlob(blob, `${state.currentFile.name.split('.')[0]}_pages_${state.operationMode}d.pdf`);
            
            showNotification(`Successfully ${state.operationMode}d ${state.selectedPages.size} pages!`, 'success');
            
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            state.isProcessing = false;
            hideProcessingOverlay();
            updateProcessButton();
        }
    }

    // Batch Processing
    function processBatchUpload(files) {
        state.batchFiles = files;
        updateBatchFileList();
        
        // Show batch options section when files are uploaded
        if (files.length > 0) {
            elements.uploadSection.classList.add('hidden');
            elements.batchOptionsSection.classList.remove('hidden');
        }
    }

    function updateBatchFileList() {
        if (!elements.batchFileList) return;

        elements.batchFileList.innerHTML = '';
        state.batchFiles.forEach((file, index) => {
            const fileDiv = document.createElement('div');
            fileDiv.className = 'flex items-center justify-between p-3 bg-white dark:bg-slate-700 rounded border';
            fileDiv.innerHTML = `
                <span class="truncate">${file.name}</span>
                <button type="button" class="text-red-600 hover:text-red-800" onclick="removeBatchFile(${index})">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M6 2l2-2h4l2 2h4v2H2V2h4zM3 6h14v12a2 2 0 01-2 2H5a2 2 0 01-2-2V6z"/>
                    </svg>
                </button>
            `;
            elements.batchFileList.appendChild(fileDiv);
        });

        elements.batchProcessBtn.disabled = state.batchFiles.length === 0;
    }

    window.removeBatchFile = (index) => {
        state.batchFiles.splice(index, 1);
        updateBatchFileList();
    };

    async function processBatchFiles() {
        if (state.batchFiles.length === 0) return;

        const deletePattern = document.querySelector('input[name="delete-pattern"]:checked')?.value;
        const customPages = document.querySelector('#custom-pages-input')?.value;

        if (!deletePattern) {
            showNotification('Please select a deletion pattern', 'error');
            return;
        }

        showProcessingOverlay('Processing batch files...');

        const formData = new FormData();
        state.batchFiles.forEach(file => formData.append('files[]', file));
        formData.append('delete_pattern', deletePattern);
        if (customPages) {
            formData.append('custom_pages', customPages);
        }

        try {
            const response = await fetch('/batch-delete-pages', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Batch processing failed');
            }

            const data = await response.json();
            displayBatchResults(data.results);
            showNotification(`Processed ${data.processed_count} files successfully!`, 'success');

        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            hideProcessingOverlay();
        }
    }

    function displayBatchResults(results) {
        const resultsContainer = elements.resultsSection.querySelector('#batch-results');
        if (!resultsContainer) return;

        elements.resultsSection.classList.remove('hidden');
        resultsContainer.innerHTML = '';

        results.forEach(result => {
            const resultDiv = document.createElement('div');
            resultDiv.className = `result-card ${result.success ? 'result-success' : 'result-error'}`;
            
            resultDiv.innerHTML = `
                <div class="result-filename">${result.filename}</div>
                ${result.success ? `
                    <div class="result-stats">
                        Pages deleted: ${result.pages_deleted}<br>
                        Pages remaining: ${result.pages_remaining}
                    </div>
                    <a href="${result.download_url}" class="download-link">Download</a>
                ` : `
                    <div class="text-red-600 text-sm">${result.error}</div>
                `}
            `;
            
            resultsContainer.appendChild(resultDiv);
        });
    }

    // Utility Functions
    function downloadBlob(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    }

    function showProcessingOverlay(message) {
        if (!elements.processingOverlay) return;
        
        elements.processingOverlay.classList.remove('hidden');
        elements.processingOverlay.classList.add('show');
        const messageEl = elements.processingOverlay.querySelector('#processing-message');
        if (messageEl) messageEl.textContent = message;
    }

    function hideProcessingOverlay() {
        if (!elements.processingOverlay) return;
        
        elements.processingOverlay.classList.add('hidden');
        elements.processingOverlay.classList.remove('show');
    }

    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transition-all duration-300 transform ${
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'error' ? 'bg-red-500 text-white' :
            'bg-blue-500 text-white'
        }`;
        
        notification.innerHTML = `
            <div class="flex items-center">
                <span class="flex-1">${message}</span>
                <button type="button" class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M6 6L14 14M6 14L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    function resetInterface() {
        state.currentFile = null;
        state.pages = [];
        state.selectedPages.clear();
        state.batchFiles = [];
        
        elements.uploadSection.classList.remove('hidden');
        elements.pagesSection.classList.add('hidden');
        elements.batchOptionsSection.classList.add('hidden');
        elements.resultsSection.classList.add('hidden');
        
        elements.fileInput.value = '';
        elements.batchFileInput.value = '';
        updateBatchFileList();
    }
});
