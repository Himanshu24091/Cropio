// Simple PDF Editor - Testing Version
console.log('PDF Editor Simple Script Loaded');

// Global variables
let currentPdf = null;
let pdfLib = null;
let currentTool = 'select';
let annotations = [];
let currentColor = '#ff0000';
let currentWidth = 2;
let undoStack = [];
let redoStack = [];
let isDrawing = false;
let startX = 0;
let startY = 0;

// Function to load and render PDF
async function loadAndRenderPDF(file) {
    try {
        console.log('Starting PDF load process...');
        
        // Check if PDF.js is available
        if (typeof pdfjsLib === 'undefined') {
            console.error('PDF.js library not loaded!');
            alert('PDF.js library not loaded. Please refresh the page.');
            return;
        }
        
        console.log('PDF.js available, loading file...');
        
        // Convert file to array buffer
        const arrayBuffer = await file.arrayBuffer();
        console.log('File converted to array buffer, size:', arrayBuffer.byteLength);
        
        // Load PDF with PDF.js
        const loadingTask = pdfjsLib.getDocument({data: arrayBuffer});
        currentPdf = await loadingTask.promise;
        
        console.log('PDF loaded successfully, pages:', currentPdf.numPages);
        
        // Render all pages
        await renderAllPages();
        
        // Initialize editing tools
        initializeEditingTools();
        
    } catch (error) {
        console.error('Error loading PDF:', error);
        alert('Error loading PDF: ' + error.message);
    }
}

// Function to render all PDF pages
async function renderAllPages() {
    const viewerPanel = document.getElementById('pdf-viewer');
    viewerPanel.innerHTML = '';
    
    console.log('Rendering', currentPdf.numPages, 'pages...');
    
    for (let pageNum = 1; pageNum <= currentPdf.numPages; pageNum++) {
        await renderPage(pageNum, viewerPanel);
    }
}

// Function to render a single page
async function renderPage(pageNum, container) {
    try {
        const page = await currentPdf.getPage(pageNum);
        const viewport = page.getViewport({scale: 1.2});
        
        // Create page container
        const pageContainer = document.createElement('div');
        pageContainer.className = 'pdf-page-container mb-6 relative bg-white shadow-lg rounded-lg overflow-hidden';
        pageContainer.style.width = viewport.width + 'px';
        pageContainer.style.margin = '0 auto';
        
        // Create canvas for PDF content
        const canvas = document.createElement('canvas');
        canvas.className = 'pdf-page';
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        canvas.dataset.pageNum = pageNum;
        
        // Create overlay canvas for annotations
        const overlayCanvas = document.createElement('canvas');
        overlayCanvas.className = 'annotation-overlay absolute top-0 left-0';
        overlayCanvas.width = viewport.width;
        overlayCanvas.height = viewport.height;
        overlayCanvas.dataset.pageNum = pageNum;
        
        pageContainer.appendChild(canvas);
        pageContainer.appendChild(overlayCanvas);
        container.appendChild(pageContainer);
        
        // Render PDF content
        const context = canvas.getContext('2d');
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        console.log('Rendered page', pageNum);
        
        // Add mouse event listeners for drawing
        addDrawingListeners(overlayCanvas);
        
    } catch (error) {
        console.error('Error rendering page', pageNum, ':', error);
    }
}

// Function to initialize editing tools (after PDF is loaded)
function initializeEditingTools() {
    console.log('Initializing editing tools for PDF interaction...');
    // This function is called after PDF is loaded and can initialize PDF-specific tools
    // Toolbar buttons are already initialized in initializeToolbarButtons()
    console.log('PDF editing tools ready');
}

// Function to set current tool
function setTool(tool) {
    currentTool = tool;
    console.log('Tool changed to:', tool);
    
    // Update UI to show active tool
    document.querySelectorAll('[data-tool]').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeBtn = document.querySelector(`[data-tool="${tool}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // Update cursor style for PDF pages
    document.querySelectorAll('.pdf-page-container').forEach(container => {
        container.className = container.className.replace(/\s*select-tool\s*/, ' ');
        if (tool === 'select') {
            container.classList.add('select-tool');
        }
    });
}

// Function to update drawing color
function updateDrawingColor(color) {
    console.log('Drawing color changed to:', color);
    currentColor = color;
    // Update all canvas contexts
    document.querySelectorAll('.annotation-overlay').forEach(canvas => {
        const ctx = canvas.getContext('2d');
        ctx.strokeStyle = color;
    });
}

// Function to update drawing width
function updateDrawingWidth(width) {
    console.log('Drawing width changed to:', width);
    currentWidth = width;
    // Update all canvas contexts
    document.querySelectorAll('.annotation-overlay').forEach(canvas => {
        const ctx = canvas.getContext('2d');
        ctx.lineWidth = width;
    });
}

// Function to handle undo operation
function undo() {
    console.log('Undo action triggered');
    if (undoStack.length > 0) {
        const lastAction = undoStack.pop();
        redoStack.push(lastAction);
        restoreCanvas(lastAction);
    }
}

// Function to handle redo operation
function redo() {
    console.log('Redo action triggered');
    if (redoStack.length > 0) {
        const action = redoStack.pop();
        undoStack.push(action);
        restoreCanvas(action);
    }
}

// Function to restore canvas state
function restoreCanvas(data) {
    const overlays = document.querySelectorAll('.annotation-overlay');
    overlays.forEach((canvas) => {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.putImageData(data, 0, 0);
    });
}

// Function to add drawing listeners to canvas
function addDrawingListeners(canvas) {
    const ctx = canvas.getContext('2d');
    ctx.strokeStyle = currentColor;
    ctx.lineWidth = currentWidth;
    ctx.lineCap = 'round';
    
    canvas.addEventListener('mousedown', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        if (currentTool === 'text') {
            // Save state for undo
            undoStack.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
            redoStack = [];
            
            // Prompt for text input
            const text = prompt('Enter text to add:');
            if (text && text.trim()) {
                ctx.font = `${currentWidth * 8}px Arial`;
                ctx.fillStyle = currentColor;
                ctx.fillText(text, x, y);
            }
            return;
        }
        
        if (currentTool === 'eraser') {
            isDrawing = true;
            startX = x;
            startY = y;
            // Save state for undo
            undoStack.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
            redoStack = [];
            // Start erasing
            ctx.globalCompositeOperation = 'destination-out';
            ctx.beginPath();
            ctx.arc(x, y, currentWidth * 5, 0, 2 * Math.PI);
            ctx.fill();
            return;
        }
        
        if (currentTool === 'draw' || currentTool === 'highlight' || currentTool === 'rectangle' || currentTool === 'circle') {
            isDrawing = true;
            startX = x;
            startY = y;
            if (currentTool !== 'draw') {
                undoStack.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
                redoStack = [];
            }
        }
    });

    canvas.addEventListener('mousemove', (e) => {
        if (!isDrawing) return;
        const rect = canvas.getBoundingClientRect();
        const endX = e.clientX - rect.left;
        const endY = e.clientY - rect.top;
        
        if (currentTool === 'eraser') {
            // Continue erasing
            ctx.globalCompositeOperation = 'destination-out';
            ctx.beginPath();
            ctx.arc(endX, endY, currentWidth * 5, 0, 2 * Math.PI);
            ctx.fill();
            return;
        }
        
        // Reset composite operation for other tools
        ctx.globalCompositeOperation = 'source-over';
        ctx.lineWidth = (currentTool === 'highlight') ? currentWidth * 5 : currentWidth;
        ctx.strokeStyle = (currentTool === 'highlight') ? currentColor + '88' : currentColor;

        if (currentTool === 'draw') {
            ctx.beginPath();
            ctx.moveTo(startX, startY);
            ctx.lineTo(endX, endY);
            ctx.stroke();
            startX = endX;
            startY = endY;
        }
    });

    canvas.addEventListener('mouseup', (e) => {
        if (!isDrawing) return;
        isDrawing = false;
        const rect = canvas.getBoundingClientRect();
        const endX = e.clientX - rect.left;
        const endY = e.clientY - rect.top;

        if (currentTool === 'rectangle') {
            ctx.strokeRect(startX, startY, endX - startX, endY - startY);
        } else if (currentTool === 'circle') {
            ctx.beginPath();
            const radius = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
            ctx.arc(startX, startY, radius, 0, 2 * Math.PI);
            ctx.stroke();
        }
    });

    canvas.addEventListener('mouseout', () => {
        isDrawing = false;
    });
}

// Function to initialize the editor
function initializeSimpleEditor() {
    console.log('Initializing Simple PDF Editor...');
    
    // Initialize toolbar buttons immediately (even before PDF upload)
    initializeToolbarButtons();
    
    // Get the upload input element
    const uploadInput = document.getElementById('pdf-upload');
    const uploadPrompt = document.getElementById('upload-prompt');
    const viewerPanel = document.getElementById('pdf-viewer');
    const editorApp = document.getElementById('pdf-editor-app');
    
    console.log('Elements found:', {
        editorApp: !!editorApp,
        uploadInput: !!uploadInput,
        uploadPrompt: !!uploadPrompt,
        viewerPanel: !!viewerPanel
    });
    
    if (!uploadInput) {
        console.error('Upload input not found!');
        return;
    }
    
    if (!uploadPrompt) {
        console.error('Upload prompt not found!');
        return;
    }
    
    console.log('Adding event listeners...');
    
    // The upload prompt already has onclick in HTML, so we don't need to add another listener
    
    // Add change event to file input
    uploadInput.addEventListener('change', function(e) {
        console.log('File input changed');
        const file = e.target.files[0];
        
        if (!file) {
            console.log('No file selected');
            return;
        }
        
        console.log('File selected:', file.name, file.type, file.size);
        
        if (file.type !== 'application/pdf') {
            alert('Please select a PDF file');
            return;
        }
        
        // Load and render the PDF
        console.log('Loading PDF for rendering...');
        loadAndRenderPDF(file);
        
        // Hide upload prompt and show viewer
        uploadPrompt.classList.add('hidden');
        viewerPanel.classList.remove('hidden');
    });
    
    console.log('PDF Editor Simple initialized successfully');
}

// Function to initialize toolbar buttons (separate from PDF loading)
function initializeToolbarButtons() {
    // Initialize undo/redo handlers
    document.getElementById('undo-btn').addEventListener('click', undo);
    document.getElementById('redo-btn').addEventListener('click', redo);
    console.log('Initializing toolbar buttons...');
    
    // Get all toolbar buttons
    const toolButtons = document.querySelectorAll('[data-tool]');
    console.log('Found toolbar buttons:', toolButtons.length);
    
    // Add click listeners to all tool buttons
    toolButtons.forEach((button, index) => {
        const tool = button.getAttribute('data-tool');
        console.log(`Adding listener to button ${index}: ${tool}`);
        
        button.addEventListener('click', (e) => {
            console.log('Tool button clicked:', tool);
            e.preventDefault();
            e.stopPropagation();
            setTool(tool);
        });
    });
    
    // Initialize color picker
    const colorPicker = document.getElementById('color-picker');
    if (colorPicker) {
        console.log('Color picker found, adding listener');
        colorPicker.addEventListener('change', (e) => {
            console.log('Color changed to:', e.target.value);
            updateDrawingColor(e.target.value);
        });
    } else {
        console.log('Color picker not found');
    }
    
    // Initialize line width
    const lineWidthSlider = document.getElementById('line-width');
    const lineWidthValue = document.getElementById('line-width-value');
    if (lineWidthSlider && lineWidthValue) {
        console.log('Line width slider found, adding listener');
        lineWidthSlider.addEventListener('input', (e) => {
            const width = e.target.value;
            console.log('Line width changed to:', width);
            lineWidthValue.textContent = width;
            updateDrawingWidth(parseInt(width));
        });
    } else {
        console.log('Line width controls not found');
    }
    
    console.log('Toolbar buttons initialized');
}

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSimpleEditor);
} else {
    // DOM is already ready
    initializeSimpleEditor();
}
