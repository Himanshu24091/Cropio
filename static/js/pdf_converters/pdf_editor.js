/**
 * PDF Editor Pro - Advanced JavaScript Engine
 * Professional-grade PDF editing with comprehensive features
 */

'use strict';

// Global Configuration
const PDF_EDITOR_CONFIG = {
    MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
    SUPPORTED_FORMATS: ['application/pdf'],
    MAX_ZOOM: 3.0,
    MIN_ZOOM: 0.25,
    DEFAULT_ZOOM: 1.0,
    CANVAS_SCALE: 1.5, // Optimized for coordinate accuracy
    AUTOSAVE_INTERVAL: 30000, // 30 seconds
    SESSION_TIMEOUT: 3600000, // 1 hour
    
    TOOLS: {
        SELECT: 'select',
        PEN: 'pen',
        HIGHLIGHTER: 'highlighter',
        ERASER: 'eraser',
        TEXT: 'text',
        RECTANGLE: 'rectangle',
        CIRCLE: 'circle',
        ARROW: 'arrow',
        LINE: 'line',
        STAR: 'star',
        STAMP: 'stamp',
        SIGNATURE: 'signature',
        PAN: 'pan'
    },
    
    COLORS: {
        DEFAULT_STROKE: '#ff0000',
        DEFAULT_HIGHLIGHT: '#ffff00',
        DEFAULT_TEXT: '#000000'
    }
};

// Global State Management
class PDFEditorState {
    constructor() {
        this.reset();
    }
    
    reset() {
        this.fileId = null;
        this.filename = null;
        this.originalFile = null;
        this.pdfDocument = null;
        this.metadata = null;
        this.currentTool = PDF_EDITOR_CONFIG.TOOLS.SELECT;
        this.currentColor = PDF_EDITOR_CONFIG.COLORS.DEFAULT_STROKE;
        this.currentStrokeWidth = 3;
        this.zoom = PDF_EDITOR_CONFIG.DEFAULT_ZOOM;
        this.annotations = new Map(); // pageNum -> annotations array
        this.pageOperations = []; // Track page modifications
        this.undoStack = [];
        this.redoStack = [];
        this.isDrawing = false;
        this.currentPath = null;
        this.textInputPosition = null;
        this.sessionId = null;
        this.isDirty = false; // Has unsaved changes
        
        // Advanced features
        this.layers = [{ id: 'default', name: 'Default Layer', visible: true, annotations: [] }];
        this.currentLayer = 'default';
        this.panX = 0;
        this.panY = 0;
        this.isPanning = false;
        this.lastPanX = 0;
        this.lastPanY = 0;
        this.stampPosition = null;
        this.signaturePosition = null;
        this.fillOpacity = 0.3;
        this.isRendering = false; // Prevent multiple render operations
    }
    
    addAnnotation(pageNum, annotation) {
        if (!this.annotations.has(pageNum)) {
            this.annotations.set(pageNum, []);
        }
        this.annotations.get(pageNum).push(annotation);
        this.isDirty = true;
        this.saveState();
    }
    
    saveState() {
        const state = {
            annotations: Array.from(this.annotations.entries()),
            tool: this.currentTool,
            color: this.currentColor,
            strokeWidth: this.currentStrokeWidth,
            timestamp: Date.now()
        };
        
        this.undoStack.push(JSON.stringify(state));
        if (this.undoStack.length > 50) {
            this.undoStack.shift();
        }
        this.redoStack = []; // Clear redo stack on new action
    }
    
    undo() {
        if (this.undoStack.length < 2) return false;
        
        const currentState = this.undoStack.pop();
        this.redoStack.push(currentState);
        
        const previousState = JSON.parse(this.undoStack[this.undoStack.length - 1]);
        this.restoreState(previousState);
        return true;
    }
    
    redo() {
        if (this.redoStack.length === 0) return false;
        
        const nextState = JSON.parse(this.redoStack.pop());
        this.undoStack.push(JSON.stringify(nextState));
        this.restoreState(nextState);
        return true;
    }
    
    restoreState(state) {
        this.annotations = new Map(state.annotations);
        this.currentTool = state.tool;
        this.currentColor = state.color;
        this.currentStrokeWidth = state.strokeWidth;
        
        // Update UI
        this.updateToolUI();
        this.rerenderAnnotations();
    }
    
    updateToolUI() {
        // Update tool buttons
        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tool === this.currentTool);
        });
        
        // Update color picker
        const colorPicker = document.getElementById('color-picker');
        if (colorPicker) colorPicker.value = this.currentColor;
        
        // Update stroke width
        const strokeWidth = document.getElementById('stroke-width');
        const strokeWidthValue = document.getElementById('stroke-width-value');
        if (strokeWidth) strokeWidth.value = this.currentStrokeWidth;
        if (strokeWidthValue) strokeWidthValue.textContent = this.currentStrokeWidth;
    }
    
    rerenderAnnotations() {
        // Re-render all annotations
        document.querySelectorAll('.annotation-overlay').forEach(canvas => {
            const pageNum = parseInt(canvas.dataset.pageNum);
            this.renderPageAnnotations(canvas, pageNum);
        });
    }
    
    renderPageAnnotations(canvas, pageNum) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const annotations = this.annotations.get(pageNum) || [];
        annotations.forEach(annotation => {
            this.renderAnnotation(ctx, annotation);
        });
    }
    
    renderAnnotation(ctx, annotation) {
        ctx.save();
        
        switch (annotation.type) {
            case 'pen':
                this.renderPenStroke(ctx, annotation);
                break;
            case 'highlighter':
                this.renderHighlight(ctx, annotation);
                break;
            case 'text':
                this.renderText(ctx, annotation);
                break;
            case 'rectangle':
                this.renderRectangle(ctx, annotation);
                break;
            case 'circle':
                this.renderCircle(ctx, annotation);
                break;
            case 'arrow':
                this.renderArrow(ctx, annotation);
                break;
            case 'line':
                this.renderLine(ctx, annotation);
                break;
            case 'star':
                this.renderStar(ctx, annotation);
                break;
            case 'stamp':
                this.renderStamp(ctx, annotation);
                break;
            case 'signature':
                this.renderSignature(ctx, annotation);
                break;
        }
        
        ctx.restore();
    }
    
    renderPenStroke(ctx, annotation) {
        if (!annotation.path || annotation.path.length < 2) return;
        
        ctx.strokeStyle = annotation.color || this.currentColor;
        ctx.lineWidth = annotation.strokeWidth || this.currentStrokeWidth;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        ctx.beginPath();
        ctx.moveTo(annotation.path[0].x, annotation.path[0].y);
        
        for (let i = 1; i < annotation.path.length; i++) {
            ctx.lineTo(annotation.path[i].x, annotation.path[i].y);
        }
        
        ctx.stroke();
    }
    
    renderHighlight(ctx, annotation) {
        if (!annotation.path || annotation.path.length < 2) return;
        
        ctx.strokeStyle = annotation.color || PDF_EDITOR_CONFIG.COLORS.DEFAULT_HIGHLIGHT;
        ctx.lineWidth = annotation.strokeWidth || 20;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.globalAlpha = 0.3;
        
        ctx.beginPath();
        ctx.moveTo(annotation.path[0].x, annotation.path[0].y);
        
        for (let i = 1; i < annotation.path.length; i++) {
            ctx.lineTo(annotation.path[i].x, annotation.path[i].y);
        }
        
        ctx.stroke();
        ctx.globalAlpha = 1.0;
    }
    
    renderText(ctx, annotation) {
        ctx.fillStyle = annotation.color || PDF_EDITOR_CONFIG.COLORS.DEFAULT_TEXT;
        ctx.font = `${annotation.fontSize || 16}px Arial`;
        ctx.fillText(annotation.text, annotation.x, annotation.y);
    }
    
    renderRectangle(ctx, annotation) {
        ctx.strokeStyle = annotation.color || this.currentColor;
        ctx.lineWidth = annotation.strokeWidth || this.currentStrokeWidth;
        ctx.strokeRect(annotation.x, annotation.y, annotation.width, annotation.height);
    }
    
    renderCircle(ctx, annotation) {
        ctx.strokeStyle = annotation.color || this.currentColor;
        ctx.lineWidth = annotation.strokeWidth || this.currentStrokeWidth;
        ctx.beginPath();
        ctx.arc(annotation.centerX, annotation.centerY, annotation.radius, 0, 2 * Math.PI);
        ctx.stroke();
    }
    
    renderArrow(ctx, annotation) {
        ctx.strokeStyle = annotation.color || this.currentColor;
        ctx.lineWidth = annotation.strokeWidth || this.currentStrokeWidth;
        
        // Draw line
        ctx.beginPath();
        ctx.moveTo(annotation.startX, annotation.startY);
        ctx.lineTo(annotation.endX, annotation.endY);
        ctx.stroke();
        
        // Draw arrowhead
        const angle = Math.atan2(annotation.endY - annotation.startY, annotation.endX - annotation.startX);
        const headLength = 15;
        
        ctx.beginPath();
        ctx.moveTo(annotation.endX, annotation.endY);
        ctx.lineTo(
            annotation.endX - headLength * Math.cos(angle - Math.PI / 6),
            annotation.endY - headLength * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
            annotation.endX - headLength * Math.cos(angle + Math.PI / 6),
            annotation.endY - headLength * Math.sin(angle + Math.PI / 6)
        );
        ctx.lineTo(annotation.endX, annotation.endY);
        ctx.stroke();
    }
    
    renderLine(ctx, annotation) {
        ctx.strokeStyle = annotation.color || this.currentColor;
        ctx.lineWidth = annotation.strokeWidth || this.currentStrokeWidth;
        
        ctx.beginPath();
        ctx.moveTo(annotation.startX, annotation.startY);
        ctx.lineTo(annotation.endX, annotation.endY);
        ctx.stroke();
    }
    
    renderStar(ctx, annotation) {
        ctx.strokeStyle = annotation.color || this.currentColor;
        ctx.lineWidth = annotation.strokeWidth || this.currentStrokeWidth;
        
        if (annotation.fillOpacity && annotation.fillOpacity > 0) {
            ctx.fillStyle = annotation.color || this.currentColor;
            ctx.globalAlpha = annotation.fillOpacity;
        }
        
        const centerX = annotation.centerX;
        const centerY = annotation.centerY;
        const outerRadius = annotation.outerRadius;
        const innerRadius = outerRadius * 0.4;
        const points = 5;
        
        ctx.beginPath();
        for (let i = 0; i < points * 2; i++) {
            const angle = (i * Math.PI) / points;
            const radius = i % 2 === 0 ? outerRadius : innerRadius;
            const x = centerX + radius * Math.cos(angle - Math.PI / 2);
            const y = centerY + radius * Math.sin(angle - Math.PI / 2);
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.closePath();
        
        if (annotation.fillOpacity && annotation.fillOpacity > 0) {
            ctx.fill();
            ctx.globalAlpha = 1.0;
        }
        ctx.stroke();
    }
    
    renderStamp(ctx, annotation) {
        if (!annotation.text) return;
        
        const x = annotation.x;
        const y = annotation.y;
        const padding = 8;
        
        ctx.strokeStyle = annotation.color || this.currentColor;
        ctx.fillStyle = annotation.color || this.currentColor;
        ctx.lineWidth = 2;
        ctx.font = `bold ${annotation.fontSize || 14}px Arial`;
        
        const textMetrics = ctx.measureText(annotation.text);
        const textWidth = textMetrics.width;
        const textHeight = annotation.fontSize || 14;
        
        // Draw stamp border with dashed line
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(x - padding, y - padding, textWidth + padding * 2, textHeight + padding * 2);
        ctx.setLineDash([]);
        
        // Draw text
        ctx.fillText(annotation.text, x, y + textHeight - 2);
    }
    
    renderSignature(ctx, annotation) {
        if (!annotation.signatureData) return;
        
        const x = annotation.x;
        const y = annotation.y;
        const width = annotation.width || 150;
        const height = annotation.height || 50;
        
        if (annotation.isDrawn && annotation.signatureData) {
            // Render drawn signature from image data
            const img = new Image();
            img.onload = () => {
                ctx.drawImage(img, x, y, width, height);
            };
            img.src = annotation.signatureData;
        } else if (annotation.signatureData && annotation.signatureData.text) {
            // Render typed signature
            ctx.fillStyle = '#000';
            ctx.font = `italic 24px ${annotation.signatureData.font || 'cursive'}`;
            ctx.fillText(annotation.signatureData.text, x, y + height - 10);
        }
    }
    
    // Layer Management Methods
    addLayer(name) {
        const layerId = this.generateUUID();
        const layer = {
            id: layerId,
            name: name,
            visible: true,
            annotations: []
        };
        this.layers.push(layer);
        return layer;
    }
    
    selectLayer(layerId) {
        this.currentLayer = layerId;
    }
    
    toggleLayerVisibility(layerId) {
        const layer = this.layers.find(l => l.id === layerId);
        if (layer) {
            layer.visible = !layer.visible;
            this.rerenderAnnotations();
        }
    }
    
    removeLayer(layerId) {
        if (layerId === 'default') return false; // Cannot remove default layer
        
        const index = this.layers.findIndex(l => l.id === layerId);
        if (index > -1) {
            this.layers.splice(index, 1);
            if (this.currentLayer === layerId) {
                this.currentLayer = 'default';
            }
            this.rerenderAnnotations();
            return true;
        }
        return false;
    }
    
    getVisibleAnnotations(pageNum) {
        const visibleLayers = this.layers.filter(l => l.visible);
        const allAnnotations = this.annotations.get(pageNum) || [];
        
        return allAnnotations.filter(annotation => {
            const layer = this.layers.find(l => l.id === annotation.layerId);
            return layer && layer.visible;
        });
    }
    
    // Zoom and Pan Methods
    zoomIn() {
        this.zoom = Math.min(this.zoom * 1.2, PDF_EDITOR_CONFIG.MAX_ZOOM);
        this.updateZoomUI();
        return this.zoom;
    }
    
    zoomOut() {
        this.zoom = Math.max(this.zoom / 1.2, PDF_EDITOR_CONFIG.MIN_ZOOM);
        this.updateZoomUI();
        return this.zoom;
    }
    
    resetZoom() {
        this.zoom = PDF_EDITOR_CONFIG.DEFAULT_ZOOM;
        this.panX = 0;
        this.panY = 0;
        this.updateZoomUI();
        this.updatePanUI();
        return this.zoom;
    }
    
    async fitWidth() {
        if (!this.pdfDocument) return this.zoom;
        
        const container = document.getElementById('pdf-container');
        if (!container) return this.zoom;
        
        try {
            // Get the first page to calculate natural width
            const page = await this.pdfDocument.getPage(1);
            const viewport = page.getViewport({scale: 1.0}); // Get natural size
            
            const containerWidth = container.clientWidth - 48; // Account for padding
            const pageNaturalWidth = viewport.width / PDF_EDITOR_CONFIG.CANVAS_SCALE;
            
            if (pageNaturalWidth > 0) {
                // Calculate zoom to fit width
                this.zoom = containerWidth / pageNaturalWidth;
                this.zoom = Math.max(this.zoom, PDF_EDITOR_CONFIG.MIN_ZOOM);
                this.zoom = Math.min(this.zoom, PDF_EDITOR_CONFIG.MAX_ZOOM);
                
                // Reset pan
                this.panX = 0;
                this.panY = 0;
                
                this.updateZoomUI();
                this.updatePanUI();
            }
        } catch (error) {
            console.error('Error in fitWidth:', error);
        }
        
        return this.zoom;
    }
    
    updateZoomUI() {
        const zoomDisplay = document.getElementById('zoom-level');
        if (zoomDisplay) {
            zoomDisplay.textContent = `${Math.round(this.zoom * 100)}%`;
        }
    }
    
    updatePanUI() {
        document.querySelectorAll('.pdf-page-container').forEach(container => {
            // Apply zoom scale while maintaining proper centering
            const scale = this.zoom;
            container.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${scale})`;
        });
    }
    
    // Utility Methods
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
}

// Global state instance
const editorState = new PDFEditorState();

// Utility Functions
const Utils = {
    /**
     * Debounce function calls
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * Show loading overlay with message
     */
    showLoading(message = 'Processing...') {
        const overlay = document.getElementById('loading-overlay');
        const messageEl = document.getElementById('loading-message');
        
        if (overlay) {
            if (messageEl) messageEl.textContent = message;
            overlay.classList.remove('hidden');
            overlay.classList.add('modal-enter');
        }
    },
    
    /**
     * Hide loading overlay
     */
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('modal-exit');
            setTimeout(() => {
                overlay.classList.add('hidden');
                overlay.classList.remove('modal-enter', 'modal-exit');
            }, 200);
        }
    },
    
    /**
     * Show error modal
     */
    showError(message) {
        const modal = document.getElementById('error-modal');
        const messageEl = document.getElementById('error-message');
        
        if (modal && messageEl) {
            messageEl.textContent = message;
            modal.classList.remove('hidden');
            modal.classList.add('modal-enter');
        }
        
        console.error('PDF Editor Error:', message);
    },
    
    /**
     * Show success modal
     */
    showSuccess(message) {
        const modal = document.getElementById('success-modal');
        const messageEl = document.getElementById('success-message');
        
        if (modal && messageEl) {
            messageEl.textContent = message;
            modal.classList.remove('hidden');
            modal.classList.add('modal-enter');
        }
    },
    
    /**
     * Hide modal
     */
    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('modal-exit');
            setTimeout(() => {
                modal.classList.add('hidden');
                modal.classList.remove('modal-enter', 'modal-exit');
            }, 200);
        }
    },
    
    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    /**
     * Get relative coordinates from mouse event with proper scaling
     */
    getRelativeCoords(event, element) {
        const rect = element.getBoundingClientRect();
        const scaleX = element.width / rect.width;
        const scaleY = element.height / rect.height;
        
        return {
            x: (event.clientX - rect.left) * scaleX,
            y: (event.clientY - rect.top) * scaleY
        };
    },
    
    /**
     * Generate UUID for unique identifiers
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    },
    
    /**
     * Validate color hex code
     */
    isValidHexColor(color) {
        return /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(color);
    }
};

// API Communication
class PDFEditorAPI {
    static async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/pdf-editor/upload', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `Upload failed with status ${response.status}`);
        }
        
        return await response.json();
    }
    
    static async processAnnotations(fileId, annotations, pageOperations = []) {
        const annotationsObj = {};
        
        // Convert Map to Object and ensure proper data format
        if (annotations instanceof Map) {
            annotations.forEach((pageAnnotations, pageNum) => {
                if (pageAnnotations && pageAnnotations.length > 0) {
                    annotationsObj[pageNum] = pageAnnotations;
                }
            });
        } else {
            // If it's already an object, use it directly
            Object.assign(annotationsObj, annotations);
        }
        
        console.log('Sending annotations and page operations to backend:', {
            fileId,
            annotationsCount: Object.keys(annotationsObj).length,
            totalAnnotations: Object.values(annotationsObj).reduce((total, arr) => total + (arr ? arr.length : 0), 0),
            pageOperationsCount: pageOperations.length,
            pageOperations: pageOperations
        });
        
        const response = await fetch('/pdf-editor/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                file_id: fileId,
                annotations: annotationsObj,
                page_operations: pageOperations,
                operation: 'annotate'
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `Processing failed with status ${response.status}`);
        }
        
        return await response.json();
    }
    
    static async extractText(fileId, pageNum = null) {
        const response = await fetch('/pdf-editor/extract-text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                file_id: fileId,
                page_num: pageNum
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Text extraction failed');
        }
        
        return await response.json();
    }
    
    static async getPDFInfo(fileId) {
        const response = await fetch('/pdf-editor/info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                file_id: fileId
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to get PDF info');
        }
        
        return await response.json();
    }
}

// PDF Renderer
class PDFRenderer {
    constructor() {
        this.pages = new Map(); // pageNum -> canvas element
        this.thumbnails = new Map(); // pageNum -> thumbnail element
    }
    
    async loadPDF(file) {
        try {
            console.log('Configuring PDF.js...');
            
            // Configure PDF.js worker - use local worker file to match library version
            if (typeof pdfjsLib !== 'undefined') {
                // Use the local worker file that matches the PDF.js library version (3.4.120)
                pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/libs/pdf.worker.min.js';
                console.log('PDF.js worker configured with local worker file');
            } else {
                throw new Error('PDF.js library not loaded');
            }
            
            console.log('Converting file to array buffer...');
            const arrayBuffer = await file.arrayBuffer();
            console.log('Array buffer size:', arrayBuffer.byteLength);
            
            console.log('Loading PDF document...');
            const loadingTask = pdfjsLib.getDocument({data: arrayBuffer});
            const pdf = await loadingTask.promise;
            
            console.log('PDF loaded successfully:', pdf.numPages, 'pages');
            
            editorState.pdfDocument = pdf;
            return pdf;
        } catch (error) {
            console.error('Error loading PDF:', error);
            throw new Error(`Failed to load PDF file: ${error.message}`);
        }
    }
    
    async renderAllPages() {
        if (!editorState.pdfDocument) {
            throw new Error('No PDF document loaded');
        }
        
        const container = document.getElementById('pdf-container');
        const thumbnailContainer = document.getElementById('page-thumbnails');
        
        if (!container) {
            throw new Error('PDF container not found');
        }
        
        // Clear existing content
        container.innerHTML = '';
        if (thumbnailContainer) thumbnailContainer.innerHTML = '';
        
        const numPages = editorState.pdfDocument.numPages;
        
        for (let pageNum = 1; pageNum <= numPages; pageNum++) {
            await this.renderPage(pageNum);
        }
        
        // Show PDF viewer and hide upload area
        document.getElementById('upload-area').classList.add('hidden');
        document.getElementById('pdf-viewer').classList.remove('hidden');
        document.getElementById('sidebar').classList.remove('hidden');
        document.getElementById('toolbar').classList.remove('hidden');
        document.getElementById('tool-properties').classList.remove('hidden');
        document.getElementById('download-btn').classList.remove('hidden');
        
        // Show layer panel
        const layerPanel = document.getElementById('layer-panel');
        if (layerPanel) {
            layerPanel.classList.remove('hidden');
            updateLayersUI();
        }
    }
    
    async renderPage(pageNum) {
        const page = await editorState.pdfDocument.getPage(pageNum);
        const viewport = page.getViewport({scale: editorState.zoom * PDF_EDITOR_CONFIG.CANVAS_SCALE});
        
        // Check if page already exists
        let pageContainer = document.querySelector(`[data-page-num="${pageNum}"]`);
        
        if (pageContainer) {
            // Update existing page dimensions and re-render
            const canvas = pageContainer.querySelector('.pdf-page');
            const annotationCanvas = pageContainer.querySelector('.annotation-overlay');
            
            if (canvas && annotationCanvas) {
                await this.updateExistingPage(canvas, annotationCanvas, viewport, page, pageNum);
                return;
            }
        }
        
        // Create new page container only if it doesn't exist
        pageContainer = document.createElement('div');
        pageContainer.className = 'pdf-page-container';
        pageContainer.dataset.pageNum = pageNum;
        
        // Create main canvas for PDF content
        const canvas = document.createElement('canvas');
        canvas.className = 'pdf-page';
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        canvas.style.width = `${viewport.width / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        canvas.style.height = `${viewport.height / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        
        // Create annotation overlay canvas
        const annotationCanvas = document.createElement('canvas');
        annotationCanvas.className = 'annotation-overlay';
        annotationCanvas.width = viewport.width;
        annotationCanvas.height = viewport.height;
        annotationCanvas.style.width = `${viewport.width / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        annotationCanvas.style.height = `${viewport.height / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        annotationCanvas.dataset.pageNum = pageNum;
        
        pageContainer.appendChild(canvas);
        pageContainer.appendChild(annotationCanvas);
        
        // Add page number label
        const pageLabel = document.createElement('div');
        pageLabel.className = 'absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm';
        pageLabel.textContent = `Page ${pageNum}`;
        pageContainer.appendChild(pageLabel);
        
        document.getElementById('pdf-container').appendChild(pageContainer);
        
        // Render PDF content
        const context = canvas.getContext('2d');
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        
        // Set up annotation canvas - no additional scaling needed
        const annotationCtx = annotationCanvas.getContext('2d');
        // Remove extra scaling to fix coordinate mismatch
        
        // Add event listeners for drawing
        this.setupCanvasListeners(annotationCanvas, pageNum);
        
        // Store references
        this.pages.set(pageNum, annotationCanvas);
        
        // Create thumbnail
        await this.createThumbnail(page, pageNum, viewport);
        
        console.log(`Rendered page ${pageNum}`);
    }
    
    async createThumbnail(page, pageNum, fullViewport) {
        const thumbnailContainer = document.getElementById('page-thumbnails');
        if (!thumbnailContainer) return;
        
        const thumbnailScale = 0.15;
        const thumbnailViewport = page.getViewport({scale: thumbnailScale});
        
        const thumbnailCanvas = document.createElement('canvas');
        thumbnailCanvas.width = thumbnailViewport.width;
        thumbnailCanvas.height = thumbnailViewport.height;
        
        const thumbnailContext = thumbnailCanvas.getContext('2d');
        await page.render({
            canvasContext: thumbnailContext,
            viewport: thumbnailViewport
        }).promise;
        
        // Create thumbnail element
        const thumbnailEl = document.createElement('div');
        thumbnailEl.className = 'page-thumbnail';
        thumbnailEl.dataset.pageNum = pageNum;
        
        thumbnailEl.innerHTML = `
            <div class="thumbnail-image-container">
                <img src="${thumbnailCanvas.toDataURL()}" alt="Page ${pageNum}">
                <div class="page-actions">
                    <button class="page-action-btn duplicate-page-btn" data-page="${pageNum}" title="Duplicate Page">
                        <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
                        </svg>
                    </button>
                    <button class="page-action-btn rotate-page-btn" data-page="${pageNum}" title="Rotate Page">
                        <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                    </button>
                    <button class="page-action-btn delete-page-btn" data-page="${pageNum}" title="Delete Page">
                        <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="page-info">
                <div class="page-number">${pageNum}</div>
                <div class="page-size">${Math.round(fullViewport.width / PDF_EDITOR_CONFIG.CANVAS_SCALE)}×${Math.round(fullViewport.height / PDF_EDITOR_CONFIG.CANVAS_SCALE)}</div>
            </div>
        `;
        
        // Add click handler to scroll to page (only on image area)
        const imageContainer = thumbnailEl.querySelector('.thumbnail-image-container img');
        imageContainer.addEventListener('click', () => {
            const pageContainer = document.querySelector(`[data-page-num="${pageNum}"]`);
            if (pageContainer) {
                pageContainer.scrollIntoView({behavior: 'smooth', block: 'center'});
                
                // Update active thumbnail
                document.querySelectorAll('.page-thumbnail').forEach(t => t.classList.remove('active'));
                thumbnailEl.classList.add('active');
            }
        });
        
        // Add page action event listeners
        this.setupPageActions(thumbnailEl, pageNum);
        
        thumbnailContainer.appendChild(thumbnailEl);
        this.thumbnails.set(pageNum, thumbnailEl);
    }
    
    setupCanvasListeners(canvas, pageNum) {
        let isDrawing = false;
        let startPos = null;
        let currentPath = null;
        
        // Mouse/Touch event handlers
        canvas.addEventListener('mousedown', (e) => this.handleStart(e, canvas, pageNum));
        canvas.addEventListener('mousemove', (e) => this.handleMove(e, canvas, pageNum));
        canvas.addEventListener('mouseup', (e) => this.handleEnd(e, canvas, pageNum));
        canvas.addEventListener('mouseout', () => this.handleEnd(null, canvas, pageNum));
        
        // Touch support
        canvas.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousedown', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            canvas.dispatchEvent(mouseEvent);
        });
        
        canvas.addEventListener('touchmove', (e) => {
            e.preventDefault();
            const touch = e.touches[0];
            const mouseEvent = new MouseEvent('mousemove', {
                clientX: touch.clientX,
                clientY: touch.clientY
            });
            canvas.dispatchEvent(mouseEvent);
        });
        
        canvas.addEventListener('touchend', (e) => {
            e.preventDefault();
            const mouseEvent = new MouseEvent('mouseup', {});
            canvas.dispatchEvent(mouseEvent);
        });
    }
    
    handleStart(event, canvas, pageNum) {
        if (editorState.currentTool === PDF_EDITOR_CONFIG.TOOLS.SELECT) return;
        
        // Handle pan tool
        if (editorState.currentTool === PDF_EDITOR_CONFIG.TOOLS.PAN) {
            editorState.isPanning = true;
            editorState.lastPanX = event.clientX;
            editorState.lastPanY = event.clientY;
            return;
        }
        
        const coords = Utils.getRelativeCoords(event, canvas);
        editorState.isDrawing = true;
        editorState.currentPath = [coords];
        
        if (editorState.currentTool === PDF_EDITOR_CONFIG.TOOLS.TEXT) {
            this.handleTextTool(coords, pageNum);
            return;
        }
        
        // For stamp and signature tools
        if (editorState.currentTool === PDF_EDITOR_CONFIG.TOOLS.STAMP || editorState.currentTool === PDF_EDITOR_CONFIG.TOOLS.SIGNATURE) {
            editorState.startPos = coords;
            return;
        }
        
        // For shape tools, store start position
        if ([PDF_EDITOR_CONFIG.TOOLS.RECTANGLE, PDF_EDITOR_CONFIG.TOOLS.CIRCLE, PDF_EDITOR_CONFIG.TOOLS.ARROW, PDF_EDITOR_CONFIG.TOOLS.LINE, PDF_EDITOR_CONFIG.TOOLS.STAR].includes(editorState.currentTool)) {
            editorState.startPos = coords;
        }
    }
    
    handleMove(event, canvas, pageNum) {
        // Handle pan tool
        if (editorState.isPanning && editorState.currentTool === PDF_EDITOR_CONFIG.TOOLS.PAN) {
            const deltaX = event.clientX - editorState.lastPanX;
            const deltaY = event.clientY - editorState.lastPanY;
            
            editorState.panX += deltaX;
            editorState.panY += deltaY;
            
            editorState.updatePanUI();
            
            editorState.lastPanX = event.clientX;
            editorState.lastPanY = event.clientY;
            return;
        }
        
        if (!editorState.isDrawing || editorState.currentTool === PDF_EDITOR_CONFIG.TOOLS.SELECT) return;
        
        const coords = Utils.getRelativeCoords(event, canvas);
        const ctx = canvas.getContext('2d');
        
        if (editorState.currentTool === PDF_EDITOR_CONFIG.TOOLS.PEN || editorState.currentTool === PDF_EDITOR_CONFIG.TOOLS.HIGHLIGHTER) {
            editorState.currentPath.push(coords);
            
            // Draw in real-time with correct coordinates
            ctx.globalCompositeOperation = 'source-over';
            if (editorState.currentTool === PDF_EDITOR_CONFIG.TOOLS.HIGHLIGHTER) {
                ctx.globalAlpha = 0.3;
                ctx.strokeStyle = editorState.currentColor;
                ctx.lineWidth = editorState.currentStrokeWidth * 3;
            } else {
                ctx.globalAlpha = 1.0;
                ctx.strokeStyle = editorState.currentColor;
                ctx.lineWidth = editorState.currentStrokeWidth;
            }
            
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            
            if (editorState.currentPath.length > 1) {
                const prev = editorState.currentPath[editorState.currentPath.length - 2];
                ctx.beginPath();
                ctx.moveTo(prev.x, prev.y);
                ctx.lineTo(coords.x, coords.y);
                ctx.stroke();
            }
            
            ctx.globalAlpha = 1.0;
        }
        
        // For eraser - fixed coordinates
        if (editorState.currentTool === PDF_EDITOR_CONFIG.TOOLS.ERASER) {
            ctx.globalCompositeOperation = 'destination-out';
            ctx.beginPath();
            ctx.arc(
                coords.x, 
                coords.y, 
                editorState.currentStrokeWidth * 5, 
                0, 2 * Math.PI
            );
            ctx.fill();
            ctx.globalCompositeOperation = 'source-over';
        }
    }
    
    handleEnd(event, canvas, pageNum) {
        // Handle pan tool
        if (editorState.isPanning) {
            editorState.isPanning = false;
            return;
        }
        
        if (!editorState.isDrawing) return;
        
        editorState.isDrawing = false;
        
        if (!event) return; // Mouse out event
        
        const coords = Utils.getRelativeCoords(event, canvas);
        
        // Create annotation based on tool
        let annotation = null;
        
        switch (editorState.currentTool) {
            case PDF_EDITOR_CONFIG.TOOLS.PEN:
                annotation = {
                    type: 'pen',
                    path: editorState.currentPath,
                    color: editorState.currentColor,
                    strokeWidth: editorState.currentStrokeWidth,
                    timestamp: Date.now()
                };
                break;
                
            case PDF_EDITOR_CONFIG.TOOLS.HIGHLIGHTER:
                annotation = {
                    type: 'highlighter',
                    path: editorState.currentPath,
                    color: editorState.currentColor,
                    strokeWidth: editorState.currentStrokeWidth * 3,
                    timestamp: Date.now()
                };
                break;
                
            case PDF_EDITOR_CONFIG.TOOLS.RECTANGLE:
                if (editorState.startPos) {
                    annotation = {
                        type: 'rectangle',
                        x: Math.min(editorState.startPos.x, coords.x),
                        y: Math.min(editorState.startPos.y, coords.y),
                        width: Math.abs(coords.x - editorState.startPos.x),
                        height: Math.abs(coords.y - editorState.startPos.y),
                        color: editorState.currentColor,
                        strokeWidth: editorState.currentStrokeWidth,
                        timestamp: Date.now()
                    };
                    
                    // Draw rectangle
                    const ctx = canvas.getContext('2d');
                    ctx.strokeStyle = editorState.currentColor;
                    ctx.lineWidth = editorState.currentStrokeWidth;
                    ctx.strokeRect(annotation.x, annotation.y, annotation.width, annotation.height);
                }
                break;
                
            case PDF_EDITOR_CONFIG.TOOLS.CIRCLE:
                if (editorState.startPos) {
                    const radius = Math.sqrt(
                        Math.pow(coords.x - editorState.startPos.x, 2) + 
                        Math.pow(coords.y - editorState.startPos.y, 2)
                    );
                    
                    annotation = {
                        type: 'circle',
                        centerX: editorState.startPos.x,
                        centerY: editorState.startPos.y,
                        radius: radius,
                        color: editorState.currentColor,
                        strokeWidth: editorState.currentStrokeWidth,
                        timestamp: Date.now()
                    };
                    
                    // Draw circle
                    const ctx = canvas.getContext('2d');
                    ctx.strokeStyle = editorState.currentColor;
                    ctx.lineWidth = editorState.currentStrokeWidth;
                    ctx.beginPath();
                    ctx.arc(annotation.centerX, annotation.centerY, radius, 0, 2 * Math.PI);
                    ctx.stroke();
                }
                break;
                
            case PDF_EDITOR_CONFIG.TOOLS.ARROW:
                if (editorState.startPos) {
                    annotation = {
                        type: 'arrow',
                        startX: editorState.startPos.x,
                        startY: editorState.startPos.y,
                        endX: coords.x,
                        endY: coords.y,
                        color: editorState.currentColor,
                        strokeWidth: editorState.currentStrokeWidth,
                        timestamp: Date.now()
                    };
                    
                    // Draw arrow
                    editorState.renderArrow(canvas.getContext('2d'), annotation);
                }
                break;
                
            case PDF_EDITOR_CONFIG.TOOLS.LINE:
                if (editorState.startPos) {
                    annotation = {
                        type: 'line',
                        startX: editorState.startPos.x,
                        startY: editorState.startPos.y,
                        endX: coords.x,
                        endY: coords.y,
                        color: editorState.currentColor,
                        strokeWidth: editorState.currentStrokeWidth,
                        timestamp: Date.now()
                    };
                    
                    // Draw line
                    editorState.renderLine(canvas.getContext('2d'), annotation);
                }
                break;
                
            case PDF_EDITOR_CONFIG.TOOLS.STAR:
                if (editorState.startPos) {
                    const outerRadius = Math.sqrt(
                        Math.pow(coords.x - editorState.startPos.x, 2) + 
                        Math.pow(coords.y - editorState.startPos.y, 2)
                    );
                    
                    annotation = {
                        type: 'star',
                        centerX: editorState.startPos.x,
                        centerY: editorState.startPos.y,
                        outerRadius: outerRadius,
                        color: editorState.currentColor,
                        strokeWidth: editorState.currentStrokeWidth,
                        fillOpacity: editorState.fillOpacity,
                        timestamp: Date.now()
                    };
                    
                    // Draw star
                    editorState.renderStar(canvas.getContext('2d'), annotation);
                }
                break;
                
            case PDF_EDITOR_CONFIG.TOOLS.STAMP:
                editorState.stampPosition = {
                    x: coords.x,
                    y: coords.y,
                    pageNum: pageNum
                };
                
                // Show stamp modal
                const stampModal = document.getElementById('stamp-modal');
                if (stampModal) {
                    stampModal.classList.remove('hidden');
                    stampModal.classList.add('modal-enter');
                }
                break;
                
            case PDF_EDITOR_CONFIG.TOOLS.SIGNATURE:
                editorState.signaturePosition = {
                    x: coords.x,
                    y: coords.y,
                    pageNum: pageNum
                };
                
                // Show signature modal
                const signatureModal = document.getElementById('signature-modal');
                if (signatureModal) {
                    signatureModal.classList.remove('hidden');
                    signatureModal.classList.add('modal-enter');
                    switchSignatureTab('draw');
                }
                break;
        }
        
        if (annotation) {
            editorState.addAnnotation(pageNum, annotation);
        }
        
        editorState.currentPath = null;
        editorState.startPos = null;
    }
    
    handleTextTool(coords, pageNum) {
        editorState.textInputPosition = {
            x: coords.x,
            y: coords.y,
            pageNum: pageNum
        };
        
        // Show text input modal
        const modal = document.getElementById('text-input-modal');
        const textInput = document.getElementById('text-input');
        
        if (modal && textInput) {
            textInput.value = '';
            modal.classList.remove('hidden');
            modal.classList.add('modal-enter');
            textInput.focus();
        }
    }
    
    addTextAnnotation(text) {
        if (!editorState.textInputPosition || !text.trim()) return;
        
        const annotation = {
            type: 'text',
            text: text.trim(),
            x: editorState.textInputPosition.x,
            y: editorState.textInputPosition.y,
            fontSize: editorState.currentStrokeWidth * 4 + 12,
            color: editorState.currentColor,
            timestamp: Date.now()
        };
        
        // Add to annotations
        editorState.addAnnotation(editorState.textInputPosition.pageNum, annotation);
        
        // Render on canvas
        const canvas = this.pages.get(editorState.textInputPosition.pageNum);
        if (canvas) {
            editorState.renderText(canvas.getContext('2d'), annotation);
        }
        
        editorState.textInputPosition = null;
    }
    
    async updateExistingPage(canvas, annotationCanvas, viewport, page, pageNum) {
        // Clear the canvas first
        const context = canvas.getContext('2d');
        const annotationContext = annotationCanvas.getContext('2d');
        
        // Update canvas dimensions
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        canvas.style.width = `${viewport.width / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        canvas.style.height = `${viewport.height / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        
        annotationCanvas.width = viewport.width;
        annotationCanvas.height = viewport.height;
        annotationCanvas.style.width = `${viewport.width / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        annotationCanvas.style.height = `${viewport.height / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        
        // Re-render PDF content
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        
        await page.render(renderContext).promise;
        
        // Re-render annotations
        editorState.renderPageAnnotations(annotationCanvas, pageNum);
    }
    
    async rerenderAllPages() {
        if (!editorState.pdfDocument || editorState.isRendering) return;
        
        editorState.isRendering = true;
        const numPages = editorState.pdfDocument.numPages;
        
        // Update all existing pages without creating new ones
        for (let pageNum = 1; pageNum <= numPages; pageNum++) {
            const pageContainer = document.querySelector(`[data-page-num="${pageNum}"]`);
            if (pageContainer) {
                const canvas = pageContainer.querySelector('.pdf-page');
                const annotationCanvas = pageContainer.querySelector('.annotation-overlay');
                
                if (canvas && annotationCanvas) {
                    const page = await editorState.pdfDocument.getPage(pageNum);
                    const viewport = page.getViewport({scale: editorState.zoom * PDF_EDITOR_CONFIG.CANVAS_SCALE});
                    await this.updateExistingPage(canvas, annotationCanvas, viewport, page, pageNum);
                }
            }
        }
        
        // Update UI transforms
        editorState.updatePanUI();
        editorState.updateZoomUI();
        
        editorState.isRendering = false;
    }
    
    setupPageActions(thumbnailEl, pageNum) {
        // Duplicate page button
        const duplicateBtn = thumbnailEl.querySelector('.duplicate-page-btn');
        duplicateBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.duplicatePage(pageNum);
        });
        
        // Rotate page button
        const rotateBtn = thumbnailEl.querySelector('.rotate-page-btn');
        rotateBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.rotatePage(pageNum);
        });
        
        // Delete page button
        const deleteBtn = thumbnailEl.querySelector('.delete-page-btn');
        deleteBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.deletePage(pageNum);
        });
    }
    
    async duplicatePage(pageNum) {
        if (!editorState.pdfDocument || editorState.isRendering) return;
        
        try {
            Utils.showLoading('Duplicating page...');
            
            // Get the page to duplicate
            const sourcePage = await editorState.pdfDocument.getPage(pageNum);
            const viewport = sourcePage.getViewport({scale: editorState.zoom * PDF_EDITOR_CONFIG.CANVAS_SCALE});
            
            // Get total current pages and assign next integer
            const currentPages = document.querySelectorAll('.pdf-page-container').length;
            const newPageNum = currentPages + 1;
            
            console.log(`Duplicating page ${pageNum} as new page ${newPageNum}`);
            
            // Create the duplicate page
            await this.createDuplicatePage(sourcePage, newPageNum, pageNum);
            
            // Track the operation
            editorState.pageOperations.push({
                type: 'duplicate',
                sourceIndex: pageNum - 1, // Convert to 0-based
                insertIndex: newPageNum - 1, // Convert to 0-based
                timestamp: Date.now()
            });
            editorState.isDirty = true;
            
            Utils.hideLoading();
            Utils.showSuccess(`Page ${pageNum} duplicated successfully as page ${newPageNum}!`);
            
        } catch (error) {
            console.error('Error duplicating page:', error);
            Utils.hideLoading();
            Utils.showError('Failed to duplicate page');
        }
    }
    
    async createDuplicatePage(sourcePage, newPageNum, originalPageNum) {
        const viewport = sourcePage.getViewport({scale: editorState.zoom * PDF_EDITOR_CONFIG.CANVAS_SCALE});
        
        // Create page container for duplicate
        const pageContainer = document.createElement('div');
        pageContainer.className = 'pdf-page-container';
        pageContainer.dataset.pageNum = newPageNum.toString();
        
        // Create canvases
        const canvas = document.createElement('canvas');
        canvas.className = 'pdf-page';
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        canvas.style.width = `${viewport.width / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        canvas.style.height = `${viewport.height / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        
        const annotationCanvas = document.createElement('canvas');
        annotationCanvas.className = 'annotation-overlay';
        annotationCanvas.width = viewport.width;
        annotationCanvas.height = viewport.height;
        annotationCanvas.style.width = `${viewport.width / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        annotationCanvas.style.height = `${viewport.height / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        annotationCanvas.dataset.pageNum = newPageNum.toString();
        
        pageContainer.appendChild(canvas);
        pageContainer.appendChild(annotationCanvas);
        
        // Add page label
        const pageLabel = document.createElement('div');
        pageLabel.className = 'absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm';
        pageLabel.textContent = `Page ${newPageNum}`;
        pageContainer.appendChild(pageLabel);
        
        // Always append to end of container (simpler and more reliable)
        const pdfContainer = document.getElementById('pdf-container');
        if (pdfContainer) {
            pdfContainer.appendChild(pageContainer);
            console.log('Appended new page container to PDF container');
        } else {
            console.error('PDF container not found!');
            throw new Error('PDF container not found');
        }
        
        // Render the page content
        const context = canvas.getContext('2d');
        await sourcePage.render({ canvasContext: context, viewport: viewport }).promise;
        
        // Copy annotations from original page
        const originalAnnotations = editorState.annotations.get(originalPageNum) || [];
        const duplicateAnnotations = originalAnnotations.map(annotation => ({
            ...annotation,
            id: editorState.generateUUID(),
            timestamp: Date.now()
        }));
        
        editorState.annotations.set(newPageNum, duplicateAnnotations);
        editorState.renderPageAnnotations(annotationCanvas, newPageNum);
        
        // Set up event listeners
        this.setupCanvasListeners(annotationCanvas, newPageNum);
        this.pages.set(newPageNum, annotationCanvas);
        
        // Create new thumbnail
        await this.createThumbnail(sourcePage, newPageNum, viewport);
        
        console.log(`Duplicate page ${newPageNum} created successfully`);
    }
    
    async rotatePage(pageNum) {
        if (!editorState.pdfDocument || editorState.isRendering) return;
        
        try {
            Utils.showLoading('Rotating page...');
            
            // Find the page container in the main editor area
            const pageContainer = document.querySelector(`[data-page-num="${pageNum}"]`);
            
            if (!pageContainer) {
                throw new Error(`Page container not found for page ${pageNum}`);
            }
            
            // Get current rotation or default to 0
            const currentRotation = parseInt(pageContainer.dataset.rotation || '0');
            const newRotation = (currentRotation + 90) % 360;
            
            // Store new rotation
            pageContainer.dataset.rotation = newRotation.toString();
            
            // Find canvas elements
            const canvas = pageContainer.querySelector('.pdf-page');
            const annotationCanvas = pageContainer.querySelector('.annotation-overlay');
            
            if (canvas && annotationCanvas) {
                const rotateTransform = `rotate(${newRotation}deg)`;
                canvas.style.transform = rotateTransform;
                annotationCanvas.style.transform = rotateTransform;
                
                // Add transform origin for better rotation
                canvas.style.transformOrigin = 'center center';
                annotationCanvas.style.transformOrigin = 'center center';
            }
            
            // Update thumbnail rotation
            const thumbnailImg = document.querySelector(`.page-thumbnail[data-page-num="${pageNum}"] img`);
            
            if (thumbnailImg) {
                const rotateTransform = `rotate(${newRotation}deg)`;
                thumbnailImg.style.transform = rotateTransform;
                thumbnailImg.style.transformOrigin = 'center center';
            }
            
            // Track the operation
            editorState.pageOperations.push({
                type: 'rotate',
                pageIndex: pageNum - 1, // Convert to 0-based
                angle: 90, // Always rotate by 90 degrees
                timestamp: Date.now()
            });
            editorState.isDirty = true;
            
            Utils.hideLoading();
            Utils.showSuccess(`Page ${pageNum} rotated to ${newRotation}° successfully!`);
            
        } catch (error) {
            console.error('Error rotating page:', error);
            Utils.hideLoading();
            Utils.showError(`Failed to rotate page: ${error.message}`);
        }
    }
    
    async deletePage(pageNum) {
        if (!editorState.pdfDocument || editorState.isRendering) return;
        
        const totalPages = document.querySelectorAll('.pdf-page-container').length;
        if (totalPages <= 1) {
            Utils.showError('Cannot delete the last remaining page');
            return;
        }
        
        const confirmDelete = confirm(`Are you sure you want to delete page ${pageNum}? This action cannot be undone.`);
        if (!confirmDelete) return;
        
        try {
            Utils.showLoading('Deleting page...');
            
            console.log('=== DELETING PAGE', pageNum, '===');
            console.log('Total pages before:', document.querySelectorAll('.pdf-page-container').length);
            
            // Debug: Show all existing page containers
            const allContainers = document.querySelectorAll('.pdf-page-container');
            console.log('All page containers:');
            allContainers.forEach((container, index) => {
                console.log(`  Container ${index}: data-page-num="${container.dataset.pageNum}"`);
            });
            
            // FIXED: Find page container specifically in main editor area
            const pdfContainer = document.getElementById('pdf-container');
            let pageContainer = null;
            
            if (pdfContainer) {
                // Look for page container specifically in main editor area
                pageContainer = pdfContainer.querySelector(`.pdf-page-container[data-page-num="${pageNum}"]`);
                console.log('Found main page container:', !!pageContainer);
            }
            
            if (!pageContainer) {
                // Fallback: search by class and filter by page number
                const containers = document.querySelectorAll('#pdf-container .pdf-page-container');
                for (let container of containers) {
                    if (container.dataset.pageNum === pageNum.toString()) {
                        pageContainer = container;
                        console.log('Found by fallback search:', !!pageContainer);
                        break;
                    }
                }
            }
            
            if (pageContainer) {
                console.log('Removing main page container from DOM...');
                pageContainer.remove();
                console.log('Main page container removed successfully');
            } else {
                console.warn(`Could not find main page container for page ${pageNum}`);
            }
            
            // Remove from pages map
            const removedFromPages = this.pages.delete(pageNum);
            console.log('Removed from pages map:', removedFromPages);
            
            // Remove annotations
            const removedAnnotations = editorState.annotations.delete(pageNum);
            console.log('Removed annotations:', removedAnnotations);
            
            // Remove thumbnail from sidebar specifically
            const thumbnailContainer = document.getElementById('page-thumbnails');
            let thumbnail = null;
            
            if (thumbnailContainer) {
                thumbnail = thumbnailContainer.querySelector(`.page-thumbnail[data-page-num="${pageNum}"]`);
                console.log('Found thumbnail in sidebar:', !!thumbnail);
                
                if (thumbnail) {
                    thumbnail.remove();
                    console.log('Thumbnail removed from sidebar');
                }
            }
            
            // Also remove from thumbnails map
            const removedFromThumbnails = this.thumbnails.delete(pageNum);
            console.log('Removed from thumbnails map:', removedFromThumbnails);
            
            // Update page numbers for both main pages and thumbnails
            console.log('Updating page numbers...');
            this.updatePageNumbers();
            
            // Force refresh of the main editor display
            console.log('Refreshing main editor display...');
            this.refreshMainDisplay();
            
            // Track the operation
            editorState.pageOperations.push({
                type: 'delete',
                pageIndex: pageNum - 1, // Convert to 0-based
                timestamp: Date.now()
            });
            editorState.isDirty = true;
            
            console.log('Total pages after:', document.querySelectorAll('.pdf-page-container').length);
            console.log('=== DELETE COMPLETE ===');
            
            Utils.hideLoading();
            Utils.showSuccess(`Page ${pageNum} deleted successfully!`);
            
        } catch (error) {
            console.error('Error deleting page:', error);
            Utils.hideLoading();
            Utils.showError(`Failed to delete page: ${error.message}`);
        }
    }
    
    updatePageNumbers() {
        console.log('=== UPDATING PAGE NUMBERS ===');
        
        // Get containers specifically from their respective areas
        const pdfContainer = document.getElementById('pdf-container');
        const thumbnailContainer = document.getElementById('page-thumbnails');
        
        const pageContainers = pdfContainer ? 
            Array.from(pdfContainer.querySelectorAll('.pdf-page-container')) : [];
        const thumbnails = thumbnailContainer ? 
            Array.from(thumbnailContainer.querySelectorAll('.page-thumbnail')) : [];
        
        console.log('Found containers to update:', {
            mainPages: pageContainers.length,
            thumbnails: thumbnails.length
        });
        
        // Update main page containers
        pageContainers.forEach((container, index) => {
            const newPageNum = index + 1;
            const oldPageNum = container.dataset.pageNum;
            
            console.log(`Updating main page container: ${oldPageNum} -> ${newPageNum}`);
            
            container.dataset.pageNum = newPageNum;
            
            // Update page label with better selector
            const pageLabel = container.querySelector('.absolute, .page-label, div:last-child');
            if (pageLabel) {
                pageLabel.textContent = `Page ${newPageNum}`;
                console.log(`Updated page label: ${pageLabel.textContent}`);
            }
            
            // Update annotation canvas
            const annotationCanvas = container.querySelector('.annotation-overlay');
            if (annotationCanvas) {
                annotationCanvas.dataset.pageNum = newPageNum;
                console.log(`Updated annotation canvas for page ${newPageNum}`);
            }
            
            // Update annotations mapping if page number changed
            if (oldPageNum !== newPageNum.toString()) {
                const oldAnnotations = editorState.annotations.get(parseInt(oldPageNum));
                if (oldAnnotations) {
                    editorState.annotations.delete(parseInt(oldPageNum));
                    editorState.annotations.set(newPageNum, oldAnnotations);
                    console.log(`Moved annotations: page ${oldPageNum} -> ${newPageNum}`);
                }
                
                // Update pages mapping
                const oldCanvas = this.pages.get(parseInt(oldPageNum));
                if (oldCanvas) {
                    this.pages.delete(parseInt(oldPageNum));
                    this.pages.set(newPageNum, oldCanvas);
                    console.log(`Moved canvas mapping: page ${oldPageNum} -> ${newPageNum}`);
                }
            }
        });
        
        // Update thumbnails
        thumbnails.forEach((thumbnail, index) => {
            const newPageNum = index + 1;
            const oldPageNum = thumbnail.dataset.pageNum;
            
            thumbnail.dataset.pageNum = newPageNum;
            
            // Update page number display
            const pageNumber = thumbnail.querySelector('.page-number');
            if (pageNumber) {
                pageNumber.textContent = newPageNum;
            }
            
            // Update button data attributes
            thumbnail.querySelectorAll('.page-action-btn').forEach(btn => {
                btn.dataset.page = newPageNum;
            });
            
            // Update thumbnails mapping if page number changed
            if (oldPageNum !== newPageNum.toString()) {
                const oldThumbnail = this.thumbnails.get(parseInt(oldPageNum));
                if (oldThumbnail) {
                    this.thumbnails.delete(parseInt(oldPageNum));
                    this.thumbnails.set(newPageNum, thumbnail);
                }
            }
        });
        
        console.log('=== PAGE NUMBERS UPDATE COMPLETE ===');
    }
    
    refreshMainDisplay() {
        console.log('=== REFRESHING MAIN DISPLAY ===');
        
        const pdfContainer = document.getElementById('pdf-container');
        if (!pdfContainer) {
            console.warn('PDF container not found');
            return;
        }
        
        // Get all current page containers
        const pageContainers = Array.from(pdfContainer.querySelectorAll('.pdf-page-container'));
        console.log(`Found ${pageContainers.length} page containers in main display`);
        
        // Re-index and verify each container
        pageContainers.forEach((container, index) => {
            const expectedPageNum = index + 1;
            const currentPageNum = container.dataset.pageNum;
            
            console.log(`Container ${index}: expected=${expectedPageNum}, current=${currentPageNum}`);
            
            // Ensure consistent styling and visibility
            container.style.display = 'block';
            container.classList.add('pdf-page-container');
            
            // Double-check page label
            const pageLabel = container.querySelector('.absolute, .page-label, div:last-child');
            if (pageLabel && !pageLabel.textContent.includes(`Page ${expectedPageNum}`)) {
                pageLabel.textContent = `Page ${expectedPageNum}`;
                console.log(`Fixed page label: ${pageLabel.textContent}`);
            }
        });
        
        // Force a layout recalculation
        pdfContainer.style.display = 'none';
        pdfContainer.offsetHeight; // Trigger reflow
        pdfContainer.style.display = 'block';
        
        console.log('=== MAIN DISPLAY REFRESH COMPLETE ===');
    }
    
    async addNewPage() {
        if (!editorState.pdfDocument || editorState.isRendering) return;
        
        try {
            Utils.showLoading('Adding new page...');
            
            // Get dimensions from the last page or use default
            const lastPageNum = editorState.pdfDocument.numPages;
            const referencePage = await editorState.pdfDocument.getPage(lastPageNum);
            const viewport = referencePage.getViewport({scale: editorState.zoom * PDF_EDITOR_CONFIG.CANVAS_SCALE});
            
            // Create new blank page
            const newPageNum = document.querySelectorAll('.pdf-page-container').length + 1;
            await this.createBlankPage(viewport, newPageNum);
            
            Utils.hideLoading();
            Utils.showSuccess('New blank page added successfully!');
            
        } catch (error) {
            console.error('Error adding new page:', error);
            Utils.hideLoading();
            Utils.showError('Failed to add new page');
        }
    }
    
    async createBlankPage(viewport, pageNum) {
        // Create page container
        const pageContainer = document.createElement('div');
        pageContainer.className = 'pdf-page-container';
        pageContainer.dataset.pageNum = pageNum;
        
        // Create canvases
        const canvas = document.createElement('canvas');
        canvas.className = 'pdf-page';
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        canvas.style.width = `${viewport.width / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        canvas.style.height = `${viewport.height / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        
        const annotationCanvas = document.createElement('canvas');
        annotationCanvas.className = 'annotation-overlay';
        annotationCanvas.width = viewport.width;
        annotationCanvas.height = viewport.height;
        annotationCanvas.style.width = `${viewport.width / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        annotationCanvas.style.height = `${viewport.height / PDF_EDITOR_CONFIG.CANVAS_SCALE}px`;
        annotationCanvas.dataset.pageNum = pageNum;
        
        pageContainer.appendChild(canvas);
        pageContainer.appendChild(annotationCanvas);
        
        // Add page label
        const pageLabel = document.createElement('div');
        pageLabel.className = 'absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-sm';
        pageLabel.textContent = `Page ${pageNum}`;
        pageContainer.appendChild(pageLabel);
        
        // Append to container
        document.getElementById('pdf-container').appendChild(pageContainer);
        
        // Create blank white page
        const context = canvas.getContext('2d');
        context.fillStyle = '#ffffff';
        context.fillRect(0, 0, canvas.width, canvas.height);
        
        // Add subtle page border
        context.strokeStyle = '#e2e8f0';
        context.lineWidth = 1;
        context.strokeRect(0, 0, canvas.width, canvas.height);
        
        // Add "NEW PAGE" watermark
        context.save();
        context.font = '24px Arial';
        context.fillStyle = 'rgba(100, 116, 139, 0.3)';
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        context.fillText('NEW PAGE', canvas.width / 2, canvas.height / 2);
        context.restore();
        
        // Initialize empty annotations for this page
        editorState.annotations.set(pageNum, []);
        
        // Set up event listeners
        this.setupCanvasListeners(annotationCanvas, pageNum);
        this.pages.set(pageNum, annotationCanvas);
        
        // Create blank thumbnail
        await this.createBlankThumbnail(viewport, pageNum);
    }
    
    async createBlankThumbnail(viewport, pageNum) {
        const thumbnailContainer = document.getElementById('page-thumbnails');
        if (!thumbnailContainer) return;
        
        // Create thumbnail canvas
        const thumbnailCanvas = document.createElement('canvas');
        const thumbnailScale = 0.15;
        thumbnailCanvas.width = viewport.width * thumbnailScale;
        thumbnailCanvas.height = viewport.height * thumbnailScale;
        
        const thumbnailContext = thumbnailCanvas.getContext('2d');
        
        // Draw blank white page
        thumbnailContext.fillStyle = '#ffffff';
        thumbnailContext.fillRect(0, 0, thumbnailCanvas.width, thumbnailCanvas.height);
        
        // Add border
        thumbnailContext.strokeStyle = '#e2e8f0';
        thumbnailContext.lineWidth = 1;
        thumbnailContext.strokeRect(0, 0, thumbnailCanvas.width, thumbnailCanvas.height);
        
        // Create thumbnail element
        const thumbnailEl = document.createElement('div');
        thumbnailEl.className = 'page-thumbnail';
        thumbnailEl.dataset.pageNum = pageNum;
        
        thumbnailEl.innerHTML = `
            <div class="thumbnail-image-container">
                <img src="${thumbnailCanvas.toDataURL()}" alt="Page ${pageNum}">
                <div class="page-actions">
                    <button class="page-action-btn duplicate-page-btn" data-page="${pageNum}" title="Duplicate Page">
                        <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
                        </svg>
                    </button>
                    <button class="page-action-btn rotate-page-btn" data-page="${pageNum}" title="Rotate Page">
                        <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                    </button>
                    <button class="page-action-btn delete-page-btn" data-page="${pageNum}" title="Delete Page">
                        <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="page-info">
                <div class="page-number">${pageNum}</div>
                <div class="page-size">${Math.round(viewport.width / PDF_EDITOR_CONFIG.CANVAS_SCALE)}×${Math.round(viewport.height / PDF_EDITOR_CONFIG.CANVAS_SCALE)}</div>
            </div>
        `;
        
        // Add click handler
        const imageContainer = thumbnailEl.querySelector('.thumbnail-image-container img');
        imageContainer.addEventListener('click', () => {
            const pageContainer = document.querySelector(`[data-page-num="${pageNum}"]`);
            if (pageContainer) {
                pageContainer.scrollIntoView({behavior: 'smooth', block: 'center'});
                
                // Update active thumbnail
                document.querySelectorAll('.page-thumbnail').forEach(t => t.classList.remove('active'));
                thumbnailEl.classList.add('active');
            }
        });
        
        // Set up page actions
        this.setupPageActions(thumbnailEl, pageNum);
        
        thumbnailContainer.appendChild(thumbnailEl);
        this.thumbnails.set(pageNum, thumbnailEl);
    }
}

// Initialize PDF renderer
const pdfRenderer = new PDFRenderer();

// Event Listeners Setup
function initializeEventListeners() {
    console.log('Initializing event listeners...');
    
    // File input handling
    const fileInput = document.getElementById('file-input');
    const uploadZone = document.getElementById('upload-zone');
    
    console.log('Elements found:');
    console.log('- File input:', !!fileInput);
    console.log('- Upload zone:', !!uploadZone);
    
    // Upload zone click
    uploadZone?.addEventListener('click', () => {
        console.log('Upload zone clicked');
        if (fileInput) {
            console.log('Triggering file input click');
            fileInput.click();
        } else {
            console.error('File input not found!');
        }
    });
    
    // File drag and drop
    uploadZone?.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });
    
    uploadZone?.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
    });
    
    uploadZone?.addEventListener('drop', async (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            await handleFileUpload(files[0]);
        }
    });
    
    // File input change
    fileInput?.addEventListener('change', async (e) => {
        console.log('File input changed', e.target.files.length, 'files');
        if (e.target.files.length > 0) {
            console.log('Selected file:', e.target.files[0].name);
            await handleFileUpload(e.target.files[0]);
        }
    });
    
    // Tool selection
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const tool = btn.dataset.tool;
            if (tool) {
                setCurrentTool(tool);
            }
        });
    });
    
    // Color picker
    const colorPicker = document.getElementById('color-picker');
    colorPicker?.addEventListener('change', (e) => {
        editorState.currentColor = e.target.value;
        document.getElementById('color-preview').style.backgroundColor = e.target.value;
    });
    
    // Stroke width
    const strokeWidth = document.getElementById('stroke-width');
    const strokeWidthValue = document.getElementById('stroke-width-value');
    strokeWidth?.addEventListener('input', (e) => {
        editorState.currentStrokeWidth = parseInt(e.target.value);
        if (strokeWidthValue) {
            strokeWidthValue.textContent = e.target.value;
        }
    });
    
    // Undo/Redo
    document.getElementById('undo-btn')?.addEventListener('click', () => {
        if (editorState.undo()) {
            console.log('Undo successful');
        }
    });
    
    document.getElementById('redo-btn')?.addEventListener('click', () => {
        if (editorState.redo()) {
            console.log('Redo successful');
        }
    });
    
    // Download button
    document.getElementById('download-btn')?.addEventListener('click', handleDownload);
    
    // Modal close buttons
    document.getElementById('close-error')?.addEventListener('click', () => {
        Utils.hideModal('error-modal');
    });
    
    document.getElementById('close-success')?.addEventListener('click', () => {
        Utils.hideModal('success-modal');
    });
    
    // Text input modal
    document.getElementById('add-text')?.addEventListener('click', () => {
        const textInput = document.getElementById('text-input');
        if (textInput && textInput.value.trim()) {
            pdfRenderer.addTextAnnotation(textInput.value);
            Utils.hideModal('text-input-modal');
        }
    });
    
    document.getElementById('cancel-text')?.addEventListener('click', () => {
        Utils.hideModal('text-input-modal');
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // Zoom controls with debouncing
    let zoomTimeout = null;
    
    document.getElementById('zoom-in-btn')?.addEventListener('click', async () => {
        if (zoomTimeout) clearTimeout(zoomTimeout);
        editorState.zoomIn();
        
        zoomTimeout = setTimeout(async () => {
            await pdfRenderer.rerenderAllPages();
            zoomTimeout = null;
        }, 100);
    });
    
    document.getElementById('zoom-out-btn')?.addEventListener('click', async () => {
        if (zoomTimeout) clearTimeout(zoomTimeout);
        editorState.zoomOut();
        
        zoomTimeout = setTimeout(async () => {
            await pdfRenderer.rerenderAllPages();
            zoomTimeout = null;
        }, 100);
    });
    
    document.getElementById('reset-zoom-btn')?.addEventListener('click', async () => {
        editorState.resetZoom();
        await pdfRenderer.rerenderAllPages();
    });
    
    document.getElementById('fit-width-btn')?.addEventListener('click', async () => {
        await editorState.fitWidth();
        await pdfRenderer.rerenderAllPages();
    });
    
    // Layer controls
    document.getElementById('add-layer-btn')?.addEventListener('click', () => {
        showLayerModal();
    });
    
    document.getElementById('create-layer')?.addEventListener('click', () => {
        const layerName = document.getElementById('layer-name')?.value.trim();
        if (layerName) {
            const layer = editorState.addLayer(layerName);
            updateLayersUI();
            Utils.hideModal('layer-modal');
            document.getElementById('layer-name').value = '';
        }
    });
    
    document.getElementById('cancel-layer')?.addEventListener('click', () => {
        Utils.hideModal('layer-modal');
    });
    
    // Stamp modal
    document.querySelectorAll('.stamp-option').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const stampText = btn.dataset.stamp;
            addStampAnnotation(stampText);
            Utils.hideModal('stamp-modal');
        });
    });
    
    document.getElementById('add-custom-stamp')?.addEventListener('click', () => {
        const customText = document.getElementById('custom-stamp')?.value.trim();
        if (customText) {
            addStampAnnotation(customText);
            Utils.hideModal('stamp-modal');
            document.getElementById('custom-stamp').value = '';
        }
    });
    
    document.getElementById('cancel-stamp')?.addEventListener('click', () => {
        Utils.hideModal('stamp-modal');
    });
    
    // Signature modal
    document.getElementById('draw-sig-tab')?.addEventListener('click', () => {
        switchSignatureTab('draw');
    });
    
    document.getElementById('type-sig-tab')?.addEventListener('click', () => {
        switchSignatureTab('type');
    });
    
    document.getElementById('clear-signature')?.addEventListener('click', () => {
        clearSignatureCanvas();
    });
    
    document.getElementById('add-signature')?.addEventListener('click', () => {
        addSignatureAnnotation();
    });
    
    document.getElementById('cancel-signature')?.addEventListener('click', () => {
        Utils.hideModal('signature-modal');
    });
    
    // Signature canvas drawing
    const signatureCanvas = document.getElementById('signature-canvas');
    if (signatureCanvas) {
        setupSignatureCanvas(signatureCanvas);
    }
    
    // Fill opacity control
    const fillOpacitySlider = document.getElementById('fill-opacity');
    fillOpacitySlider?.addEventListener('input', (e) => {
        editorState.fillOpacity = parseFloat(e.target.value);
    });
    
    // Add new page button
    document.getElementById('add-new-page-btn')?.addEventListener('click', () => {
        pdfRenderer.addNewPage();
    });
    
    // Auto-save
    setInterval(() => {
        if (editorState.isDirty && editorState.pdfDocument) {
            autoSave();
        }
    }, PDF_EDITOR_CONFIG.AUTOSAVE_INTERVAL);
    
    console.log('Event listeners initialized');
}

// File Upload Handler
async function handleFileUpload(file) {
    try {
        console.log('Starting file upload...', file.name, file.size, file.type);
        
        // Validate file
        if (!file) {
            Utils.showError('No file selected');
            return;
        }
        
        if (file.size > PDF_EDITOR_CONFIG.MAX_FILE_SIZE) {
            Utils.showError(`File too large. Maximum size is ${Utils.formatFileSize(PDF_EDITOR_CONFIG.MAX_FILE_SIZE)}`);
            return;
        }
        
        if (file.type !== 'application/pdf') {
            Utils.showError('Invalid file type. Only PDF files are supported.');
            return;
        }
        
        // Show upload progress
        const progressContainer = document.getElementById('upload-progress');
        const progressBar = document.getElementById('progress-bar');
        const uploadStatus = document.getElementById('upload-status');
        
        if (progressContainer) {
            progressContainer.classList.remove('hidden');
            if (progressBar) progressBar.style.width = '10%';
            if (uploadStatus) uploadStatus.textContent = 'Loading PDF...';
        }
        
        // Reset state and store file info
        editorState.reset();
        editorState.filename = file.name;
        editorState.originalFile = file;
        
        Utils.showLoading('Loading PDF...');
        
        console.log('Loading PDF with PDF.js...');
        
        // Upload to backend for processing and load with PDF.js for viewing
        console.log('Uploading to backend...');
        const uploadResult = await PDFEditorAPI.uploadFile(file);
        
        if (uploadResult.success) {
            // Store backend file info
            editorState.fileId = uploadResult.file_id;
            editorState.metadata = uploadResult.metadata;
            
            if (progressBar) progressBar.style.width = '40%';
            if (uploadStatus) uploadStatus.textContent = 'Loading PDF viewer...';
            
            console.log('Backend upload successful, fileId:', editorState.fileId);
        }
        
        // Load PDF with PDF.js for client-side viewing
        await pdfRenderer.loadPDF(file);
        
        if (progressBar) progressBar.style.width = '60%';
        if (uploadStatus) uploadStatus.textContent = 'Rendering pages...';
        
        console.log('Rendering all pages...');
        await pdfRenderer.renderAllPages();
        
        // Update PDF info display
        updatePDFInfo();
        
        if (progressBar) progressBar.style.width = '100%';
        if (uploadStatus) uploadStatus.textContent = 'Complete!';
        
        // Update UI
        setCurrentTool(PDF_EDITOR_CONFIG.TOOLS.SELECT);
        
        // Hide upload progress after delay
        setTimeout(() => {
            if (progressContainer) progressContainer.classList.add('hidden');
        }, 1000);
        
        Utils.hideLoading();
        Utils.showSuccess(`PDF loaded successfully! ${editorState.pdfDocument.numPages} pages ready for editing.`);
        
        console.log('PDF upload and render complete');
        
    } catch (error) {
        Utils.hideLoading();
        Utils.showError(`Failed to load PDF: ${error.message}`);
        console.error('File upload error:', error);
        
        // Hide upload progress on error
        const progressContainer = document.getElementById('upload-progress');
        if (progressContainer) {
            progressContainer.classList.add('hidden');
        }
    }
}

// Tool Management
function setCurrentTool(tool) {
    editorState.currentTool = tool;
    
    // Update UI
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tool === tool);
    });
    
    // Update cursor for canvas elements
    document.querySelectorAll('.annotation-overlay').forEach(canvas => {
        // Remove all mode classes
        canvas.classList.remove('select-mode', 'eraser-mode');
        
        if (tool === PDF_EDITOR_CONFIG.TOOLS.SELECT) {
            canvas.classList.add('select-mode');
            canvas.style.cursor = 'default';
        } else if (tool === PDF_EDITOR_CONFIG.TOOLS.ERASER) {
            canvas.classList.add('eraser-mode');
            // Custom eraser cursor is set via CSS
        } else if (tool === PDF_EDITOR_CONFIG.TOOLS.PAN) {
            canvas.style.cursor = 'grab';
        } else {
            canvas.style.cursor = 'crosshair';
        }
    });
    
    console.log('Current tool:', tool);
}

// PDF Info Display
function updatePDFInfo() {
    const pdfInfoContainer = document.getElementById('pdf-info');
    const metadataContainer = document.getElementById('pdf-metadata');
    
    if (!editorState.metadata || !pdfInfoContainer || !metadataContainer) return;
    
    const metadata = editorState.metadata;
    
    metadataContainer.innerHTML = `
        <div class="pdf-metadata-item">
            <span class="pdf-metadata-label">Pages</span>
            <span class="pdf-metadata-value">${metadata.pages}</span>
        </div>
        <div class="pdf-metadata-item">
            <span class="pdf-metadata-label">Size</span>
            <span class="pdf-metadata-value">${Utils.formatFileSize(metadata.file_size)}</span>
        </div>
        ${metadata.title ? `
        <div class="pdf-metadata-item">
            <span class="pdf-metadata-label">Title</span>
            <span class="pdf-metadata-value">${metadata.title}</span>
        </div>
        ` : ''}
        ${metadata.author ? `
        <div class="pdf-metadata-item">
            <span class="pdf-metadata-label">Author</span>
            <span class="pdf-metadata-value">${metadata.author}</span>
        </div>
        ` : ''}
        <div class="pdf-metadata-item">
            <span class="pdf-metadata-label">Encrypted</span>
            <span class="pdf-metadata-value">${metadata.encrypted ? 'Yes' : 'No'}</span>
        </div>
    `;
    
    pdfInfoContainer.classList.remove('hidden');
}

// Download Handler - FIXED VERSION using backend processing
async function handleDownload() {
    if (!editorState.pdfDocument) {
        Utils.showError('No PDF loaded');
        return;
    }
    
    try {
        Utils.showLoading('Preparing download...');
        
        const hasAnnotations = editorState.annotations.size > 0;
        let totalAnnotations = 0;
        editorState.annotations.forEach(pageAnnotations => {
            totalAnnotations += pageAnnotations.length;
        });
        
        if (!hasAnnotations) {
            // No annotations - download original
            downloadOriginalPDF();
            return;
        }
        
        // Use backend processing for reliable annotation embedding
        console.log('Using backend processing for annotations...');
        
        // Debug: Check fileId and annotations before sending
        console.log('Debug info before processing:', {
            fileId: editorState.fileId,
            hasFileId: !!editorState.fileId,
            annotationsType: typeof editorState.annotations,
            annotationsIsMap: editorState.annotations instanceof Map,
            annotationsSize: editorState.annotations.size,
            totalAnnotations: totalAnnotations
        });
        
        if (!editorState.fileId) {
            throw new Error('File ID not found. Please re-upload the file.');
        }
        
        // Send annotations and page operations to backend for processing
        console.log('Sending to backend processing...');
        console.log('Page operations to send:', editorState.pageOperations);
        const result = await PDFEditorAPI.processAnnotations(editorState.fileId, editorState.annotations, editorState.pageOperations);
        
        if (result.success) {
            // Download processed file from backend
            const downloadUrl = result.download_url;
            const filename = result.filename || 'annotated_document.pdf';
            
            // Create download link
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = filename;
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            Utils.hideLoading();
            const operationsText = editorState.pageOperations.length > 0 ? ` and ${editorState.pageOperations.length} page operations` : '';
            Utils.showSuccess(`PDF with ${totalAnnotations} annotations${operationsText} downloaded successfully!`);
            
            // Mark as clean
            editorState.isDirty = false;
        } else {
            throw new Error('Backend processing failed');
        }
        
    } catch (error) {
        Utils.hideLoading();
        console.error('Download error:', error);
        
        // Fallback to original PDF if backend fails
        Utils.showError(`Annotation processing failed: ${error.message}. Downloading original PDF instead.`);
        downloadOriginalPDF();
    }
}

// Function to download PDF with annotations embedded using PDF-lib
async function downloadPDFWithAnnotations() {
    if (!editorState.originalFile) {
        Utils.hideLoading();
        Utils.showError('Original file data not available');
        return;
    }
    
    try {
        Utils.showLoading('Embedding annotations into PDF...');
        
        // Load the original PDF with PDF-lib
        const originalBytes = await editorState.originalFile.arrayBuffer();
        const pdfDoc = await PDFLib.PDFDocument.load(originalBytes);
        
        // Apply page modifications first (deletions, rotations, duplications)
        await applyPageModifications(pdfDoc);
        
        // Get all pages from the modified PDF
        const pages = pdfDoc.getPages();
        
        // Process each page with annotations
        for (const [pageIndex, annotations] of editorState.annotations.entries()) {
            if (pageIndex >= pages.length) continue; // Skip if page doesn't exist
            
            const page = pages[pageIndex];
            const { width, height } = page.getSize();
            
            // Convert annotations to PDF coordinates and add them
            for (const annotation of annotations) {
                await addAnnotationToPDFPage(page, annotation, width, height);
            }
        }
        
        // Save the modified PDF
        const modifiedBytes = await pdfDoc.save();
        
        // Create download
        const blob = new Blob([modifiedBytes], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        // Add "_annotated" to filename
        const originalName = editorState.filename || 'document.pdf';
        const nameWithoutExt = originalName.replace(/\.pdf$/i, '');
        link.download = `${nameWithoutExt}_annotated.pdf`;
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up
        URL.revokeObjectURL(url);
        
        Utils.hideLoading();
        Utils.showSuccess('PDF with annotations downloaded successfully!');
        
        // Mark as clean
        editorState.isDirty = false;
        
    } catch (error) {
        Utils.hideLoading();
        Utils.showError(`Failed to embed annotations: ${error.message}`);
        console.error('Annotation embedding error:', error);
    }
}

// Helper function to add a single annotation to a PDF page
async function addAnnotationToPDFPage(page, annotation, pageWidth, pageHeight) {
    try {
        // Convert canvas coordinates to PDF coordinates
        // Canvas: origin top-left, PDF: origin bottom-left
        const convertY = (y) => pageHeight - y;
        
        // Get page dimensions for scaling
        const canvasContainer = document.querySelector('.pdf-page-container');
        const canvas = canvasContainer?.querySelector('.pdf-page');
        if (!canvas) return;
        
        const canvasWidth = canvas.width / PDF_EDITOR_CONFIG.CANVAS_SCALE;
        const canvasHeight = canvas.height / PDF_EDITOR_CONFIG.CANVAS_SCALE;
        
        const scaleX = pageWidth / canvasWidth;
        const scaleY = pageHeight / canvasHeight;
        
        switch (annotation.type) {
            case 'text':
                if (annotation.text && annotation.x !== undefined && annotation.y !== undefined) {
                    const fontSize = (annotation.fontSize || 16) * Math.min(scaleX, scaleY);
                    const x = annotation.x * scaleX;
                    const y = convertY(annotation.y * scaleY);
                    
                    page.drawText(annotation.text, {
                        x: x,
                        y: y,
                        size: fontSize,
                        color: PDFLib.rgb(...hexToRgb(annotation.color || '#000000'))
                    });
                }
                break;
                
            case 'rectangle':
                if (annotation.x !== undefined && annotation.y !== undefined && 
                    annotation.width !== undefined && annotation.height !== undefined) {
                    const x = annotation.x * scaleX;
                    const y = convertY((annotation.y + annotation.height) * scaleY);
                    const width = annotation.width * scaleX;
                    const height = annotation.height * scaleY;
                    
                    page.drawRectangle({
                        x: x,
                        y: y,
                        width: width,
                        height: height,
                        borderColor: PDFLib.rgb(...hexToRgb(annotation.color || '#ff0000')),
                        borderWidth: (annotation.strokeWidth || 1) * Math.min(scaleX, scaleY)
                    });
                }
                break;
                
            case 'circle':
                if (annotation.centerX !== undefined && annotation.centerY !== undefined && annotation.radius !== undefined) {
                    const centerX = annotation.centerX * scaleX;
                    const centerY = convertY(annotation.centerY * scaleY);
                    const radius = annotation.radius * Math.min(scaleX, scaleY);
                    
                    page.drawCircle({
                        x: centerX,
                        y: centerY,
                        size: radius,
                        borderColor: PDFLib.rgb(...hexToRgb(annotation.color || '#ff0000')),
                        borderWidth: (annotation.strokeWidth || 1) * Math.min(scaleX, scaleY)
                    });
                }
                break;
                
            case 'line':
                if (annotation.startX !== undefined && annotation.startY !== undefined &&
                    annotation.endX !== undefined && annotation.endY !== undefined) {
                    const startX = annotation.startX * scaleX;
                    const startY = convertY(annotation.startY * scaleY);
                    const endX = annotation.endX * scaleX;
                    const endY = convertY(annotation.endY * scaleY);
                    
                    page.drawLine({
                        start: { x: startX, y: startY },
                        end: { x: endX, y: endY },
                        thickness: (annotation.strokeWidth || 1) * Math.min(scaleX, scaleY),
                        color: PDFLib.rgb(...hexToRgb(annotation.color || '#ff0000'))
                    });
                }
                break;
                
            case 'pen':
            case 'highlighter':
                // For pen/highlighter strokes, we'll approximate with lines
                if (annotation.path && annotation.path.length > 1) {
                    const strokeWidth = (annotation.strokeWidth || 2) * Math.min(scaleX, scaleY);
                    const color = annotation.type === 'highlighter' ? 
                        [...hexToRgb(annotation.color || '#ffff00'), 0.3] : // Add transparency for highlighter
                        hexToRgb(annotation.color || '#ff0000');
                        
                    for (let i = 1; i < annotation.path.length; i++) {
                        const startX = annotation.path[i-1].x * scaleX;
                        const startY = convertY(annotation.path[i-1].y * scaleY);
                        const endX = annotation.path[i].x * scaleX;
                        const endY = convertY(annotation.path[i].y * scaleY);
                        
                        page.drawLine({
                            start: { x: startX, y: startY },
                            end: { x: endX, y: endY },
                            thickness: strokeWidth,
                            color: annotation.type === 'highlighter' ? 
                                PDFLib.rgb(color[0], color[1], color[2]) :
                                PDFLib.rgb(...color),
                            opacity: annotation.type === 'highlighter' ? 0.3 : 1.0
                        });
                    }
                }
                break;
                
            case 'stamp':
                if (annotation.text && annotation.x !== undefined && annotation.y !== undefined) {
                    const fontSize = (annotation.fontSize || 14) * Math.min(scaleX, scaleY);
                    const x = annotation.x * scaleX;
                    const y = convertY(annotation.y * scaleY);
                    
                    // Draw stamp border
                    const textWidth = annotation.text.length * fontSize * 0.6; // Approximate width
                    const textHeight = fontSize * 1.2;
                    
                    page.drawRectangle({
                        x: x - 4,
                        y: y - textHeight,
                        width: textWidth + 8,
                        height: textHeight + 4,
                        borderColor: PDFLib.rgb(...hexToRgb(annotation.color || '#ff0000')),
                        borderWidth: 1 * Math.min(scaleX, scaleY)
                    });
                    
                    // Draw stamp text
                    page.drawText(annotation.text, {
                        x: x,
                        y: y - fontSize,
                        size: fontSize,
                        color: PDFLib.rgb(...hexToRgb(annotation.color || '#ff0000'))
                    });
                }
                break;
        }
    } catch (error) {
        console.warn('Failed to add annotation to PDF:', annotation.type, error);
    }
}

// Helper function to apply page modifications (deletions, rotations, duplications)
async function applyPageModifications(pdfDoc) {
    try {
        // Apply page operations based on the current page order and modifications
        const pages = pdfDoc.getPages();
        const originalPageCount = pages.length;
        
        // If we have page operations stored, apply them
        if (editorState.pageOperations && editorState.pageOperations.length > 0) {
            // Sort operations by timestamp to apply in correct order
            const sortedOps = [...editorState.pageOperations].sort((a, b) => a.timestamp - b.timestamp);
            
            for (const operation of sortedOps) {
                switch (operation.type) {
                    case 'delete':
                        if (operation.pageIndex < pdfDoc.getPageCount()) {
                            pdfDoc.removePage(operation.pageIndex);
                        }
                        break;
                        
                    case 'rotate':
                        if (operation.pageIndex < pdfDoc.getPageCount()) {
                            const page = pdfDoc.getPage(operation.pageIndex);
                            const currentRotation = page.getRotation().angle;
                            const newRotation = (currentRotation + (operation.angle || 90)) % 360;
                            page.setRotation(PDFLib.degrees(newRotation));
                        }
                        break;
                        
                    case 'duplicate':
                        if (operation.sourceIndex < pdfDoc.getPageCount()) {
                            const [copiedPage] = await pdfDoc.copyPages(pdfDoc, [operation.sourceIndex]);
                            const insertIndex = operation.insertIndex || pdfDoc.getPageCount();
                            pdfDoc.insertPage(insertIndex, copiedPage);
                        }
                        break;
                }
            }
        } else {
            // If no explicit operations stored, check current page order against expected order
            // This is a fallback for when page operations weren't tracked
            const currentPageOrder = getCurrentPageOrder();
            if (currentPageOrder && currentPageOrder.length > 0) {
                await applyPageOrderChanges(pdfDoc, currentPageOrder, originalPageCount);
            }
        }
        
    } catch (error) {
        console.warn('Failed to apply page modifications:', error);
    }
}

// Helper function to get current page order from the UI
function getCurrentPageOrder() {
    const thumbnails = document.querySelectorAll('.page-thumbnail');
    return Array.from(thumbnails).map(thumb => {
        const pageNum = thumb.getAttribute('data-page');
        return pageNum ? parseInt(pageNum) - 1 : 0; // Convert to 0-based index
    });
}

// Helper function to apply page order changes
async function applyPageOrderChanges(pdfDoc, newOrder, originalPageCount) {
    try {
        if (newOrder.length === originalPageCount && 
            newOrder.every((pageIndex, i) => pageIndex === i)) {
            // No changes needed - pages are in original order
            return;
        }
        
        // Create a new PDF with pages in the correct order
        const pagesToCopy = [];
        for (const pageIndex of newOrder) {
            if (pageIndex >= 0 && pageIndex < originalPageCount) {
                pagesToCopy.push(pageIndex);
            }
        }
        
        if (pagesToCopy.length > 0) {
            // Copy pages in the new order
            const copiedPages = await pdfDoc.copyPages(pdfDoc, pagesToCopy);
            
            // Remove all original pages
            const totalPages = pdfDoc.getPageCount();
            for (let i = totalPages - 1; i >= 0; i--) {
                pdfDoc.removePage(i);
            }
            
            // Add pages in new order
            for (const copiedPage of copiedPages) {
                pdfDoc.addPage(copiedPage);
            }
        }
        
    } catch (error) {
        console.warn('Failed to apply page order changes:', error);
    }
}

// Helper function to convert hex color to RGB values (0-1)
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
        parseInt(result[1], 16) / 255,
        parseInt(result[2], 16) / 255,
        parseInt(result[3], 16) / 255
    ] : [0, 0, 0];
}

// Helper function to download the original PDF
function downloadOriginalPDF() {
    if (!editorState.originalFile) {
        Utils.hideLoading();
        Utils.showError('Original file data not available');
        return;
    }
    
    try {
        // Create a blob from the original file
        const blob = new Blob([editorState.originalFile], { type: 'application/pdf' });
        
        // Create download link
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        
        // Use original filename or fallback
        const filename = editorState.filename || 'edited-document.pdf';
        link.download = filename.endsWith('.pdf') ? filename : filename + '.pdf';
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up
        URL.revokeObjectURL(url);
        
        Utils.hideLoading();
        Utils.showSuccess('Original PDF downloaded successfully!');
        
        // Mark as clean
        editorState.isDirty = false;
        
    } catch (error) {
        Utils.hideLoading();
        Utils.showError(`Download failed: ${error.message}`);
        console.error('Download error:', error);
    }
}

// Keyboard Shortcuts
function handleKeyboardShortcuts(event) {
    // Don't interfere with text input
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
    }
    
    const key = event.key.toLowerCase();
    const ctrl = event.ctrlKey || event.metaKey;
    
    // Tool shortcuts
    const toolShortcuts = {
        'v': PDF_EDITOR_CONFIG.TOOLS.SELECT,
        'p': PDF_EDITOR_CONFIG.TOOLS.PEN,
        'h': PDF_EDITOR_CONFIG.TOOLS.HIGHLIGHTER,
        'e': PDF_EDITOR_CONFIG.TOOLS.ERASER,
        't': PDF_EDITOR_CONFIG.TOOLS.TEXT,
        'r': PDF_EDITOR_CONFIG.TOOLS.RECTANGLE,
        'c': PDF_EDITOR_CONFIG.TOOLS.CIRCLE,
        'a': PDF_EDITOR_CONFIG.TOOLS.ARROW,
        'l': PDF_EDITOR_CONFIG.TOOLS.LINE,
        's': PDF_EDITOR_CONFIG.TOOLS.STAR,
        'm': PDF_EDITOR_CONFIG.TOOLS.STAMP,
        'g': PDF_EDITOR_CONFIG.TOOLS.SIGNATURE,
        'n': PDF_EDITOR_CONFIG.TOOLS.PAN
    };
    
    if (toolShortcuts[key] && !ctrl) {
        event.preventDefault();
        setCurrentTool(toolShortcuts[key]);
        return;
    }
    
    // Undo/Redo
    if (ctrl && key === 'z' && !event.shiftKey) {
        event.preventDefault();
        editorState.undo();
    } else if (ctrl && (key === 'y' || (key === 'z' && event.shiftKey))) {
        event.preventDefault();
        editorState.redo();
    }
    
    // Download
    if (ctrl && key === 's') {
        event.preventDefault();
        handleDownload();
    }
}

// Auto-save functionality
async function autoSave() {
    if (!editorState.pdfDocument || !editorState.isDirty) return;
    
    try {
        // Simple auto-save - just log for now
        // In production, this could save to localStorage or server
        console.log('Auto-save triggered', {
            filename: editorState.filename,
            annotationCount: Array.from(editorState.annotations.values()).reduce((total, annotations) => total + annotations.length, 0),
            timestamp: new Date().toISOString()
        });
        
        // Mark as saved
        editorState.isDirty = false;
        
    } catch (error) {
        console.error('Auto-save error:', error);
    }
}

// Advanced Feature Functions
function showLayerModal() {
    const modal = document.getElementById('layer-modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('modal-enter');
        document.getElementById('layer-name')?.focus();
    }
}

function updateLayersUI() {
    const layersList = document.getElementById('layers-list');
    if (!layersList) return;
    
    layersList.innerHTML = '';
    
    editorState.layers.forEach(layer => {
        const layerElement = document.createElement('div');
        layerElement.className = `layer-item ${layer.id === editorState.currentLayer ? 'active' : ''}`;
        layerElement.innerHTML = `
            <span class="layer-name">${layer.name}</span>
            <div class="layer-controls">
                <button class="layer-visibility-btn" data-layer="${layer.id}" title="Toggle visibility">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        ${layer.visible ? 
                            '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle>' :
                            '<path d="m9.88 9.88a3 3 0 1 0 4.24 4.24"></path><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 11 8 11 8a13.16 13.16 0 0 1-1.67 2.68"></path><path d="M6.61 6.61A13.526 13.526 0 0 0 1 12s4 8 11 8c1.22 0 2.36-.18 3.39-.5"></path><line x1="2" y1="2" x2="22" y2="22"></line>'
                        }
                    </svg>
                </button>
            </div>
        `;
        
        // Add click event to select layer
        layerElement.addEventListener('click', (e) => {
            if (!e.target.closest('.layer-controls')) {
                editorState.selectLayer(layer.id);
                updateLayersUI();
            }
        });
        
        // Add visibility toggle
        const visibilityBtn = layerElement.querySelector('.layer-visibility-btn');
        visibilityBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            editorState.toggleLayerVisibility(layer.id);
            updateLayersUI();
        });
        
        layersList.appendChild(layerElement);
    });
}

function addStampAnnotation(text) {
    if (!editorState.stampPosition || !text) return;
    
    const annotation = {
        type: 'stamp',
        text: text,
        x: editorState.stampPosition.x,
        y: editorState.stampPosition.y,
        fontSize: 14,
        color: editorState.currentColor,
        layerId: editorState.currentLayer,
        timestamp: Date.now()
    };
    
    editorState.addAnnotation(editorState.stampPosition.pageNum, annotation);
    
    // Render on canvas
    const canvas = pdfRenderer.pages.get(editorState.stampPosition.pageNum);
    if (canvas) {
        editorState.renderStamp(canvas.getContext('2d'), annotation);
    }
    
    editorState.stampPosition = null;
}

function switchSignatureTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`${tab}-sig-tab`)?.classList.add('active');
    
    document.getElementById('draw-signature-panel')?.classList.toggle('hidden', tab !== 'draw');
    document.getElementById('type-signature-panel')?.classList.toggle('hidden', tab !== 'type');
    
    if (tab === 'type') {
        document.getElementById('signature-text')?.focus();
    }
}

function clearSignatureCanvas() {
    const canvas = document.getElementById('signature-canvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
}

function setupSignatureCanvas(canvas) {
    const ctx = canvas.getContext('2d');
    let isDrawing = false;
    
    const startDrawing = (e) => {
        isDrawing = true;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        ctx.beginPath();
        ctx.moveTo(x, y);
    };
    
    const draw = (e) => {
        if (!isDrawing) return;
        
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        ctx.strokeStyle = '#000';
        ctx.lineWidth = document.getElementById('sig-pen-width')?.value || 2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.lineTo(x, y);
        ctx.stroke();
    };
    
    const stopDrawing = () => {
        isDrawing = false;
    };
    
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);
    
    // Touch events
    canvas.addEventListener('touchstart', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousedown', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    });
    
    canvas.addEventListener('touchmove', (e) => {
        e.preventDefault();
        const touch = e.touches[0];
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: touch.clientX,
            clientY: touch.clientY
        });
        canvas.dispatchEvent(mouseEvent);
    });
    
    canvas.addEventListener('touchend', (e) => {
        e.preventDefault();
        const mouseEvent = new MouseEvent('mouseup', {});
        canvas.dispatchEvent(mouseEvent);
    });
}

function addSignatureAnnotation() {
    if (!editorState.signaturePosition) return;
    
    const activeTab = document.querySelector('.tab-btn.active')?.id;
    let signatureData = null;
    
    if (activeTab === 'draw-sig-tab') {
        const canvas = document.getElementById('signature-canvas');
        if (canvas) {
            // Check if there's anything drawn
            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const hasDrawing = imageData.data.some((channel, index) => index % 4 === 3 && channel !== 0);
            
            if (!hasDrawing) {
                Utils.showError('Please draw a signature');
                return;
            }
            
            signatureData = canvas.toDataURL();
        }
    } else {
        const signatureText = document.getElementById('signature-text')?.value.trim();
        const signatureFont = document.getElementById('signature-font')?.value;
        
        if (!signatureText) {
            Utils.showError('Please enter signature text');
            return;
        }
        
        signatureData = { text: signatureText, font: signatureFont };
    }
    
    const annotation = {
        type: 'signature',
        signatureData: signatureData,
        isDrawn: activeTab === 'draw-sig-tab',
        x: editorState.signaturePosition.x,
        y: editorState.signaturePosition.y,
        width: 150,
        height: 50,
        layerId: editorState.currentLayer,
        timestamp: Date.now()
    };
    
    editorState.addAnnotation(editorState.signaturePosition.pageNum, annotation);
    
    // Render on canvas
    const canvas = pdfRenderer.pages.get(editorState.signaturePosition.pageNum);
    if (canvas) {
        editorState.renderSignature(canvas.getContext('2d'), annotation);
    }
    
    Utils.hideModal('signature-modal');
    editorState.signaturePosition = null;
}

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    console.log('PDF Editor Pro initializing...');
    
    try {
        initializeEventListeners();
        
        // Set initial tool
        setCurrentTool(PDF_EDITOR_CONFIG.TOOLS.SELECT);
        
        console.log('PDF Editor Pro ready!');
        
    } catch (error) {
        console.error('Initialization error:', error);
        Utils.showError('Failed to initialize PDF Editor. Please refresh the page.');
    }
});

// Debug function to check for duplicates
function checkForDuplicatePages() {
    const pages = document.querySelectorAll('.pdf-page-container');
    const pageNumbers = {};
    
    pages.forEach(page => {
        const pageNum = page.dataset.pageNum;
        pageNumbers[pageNum] = (pageNumbers[pageNum] || 0) + 1;
    });
    
    console.log('Page count by number:', pageNumbers);
    
    for (const pageNum in pageNumbers) {
        if (pageNumbers[pageNum] > 1) {
            console.warn(`Duplicate pages found for page ${pageNum}: ${pageNumbers[pageNum]} instances`);
        }
    }
}

// Debug function to inspect current DOM structure
function inspectPDFStructure() {
    console.log('\n=== PDF STRUCTURE INSPECTION ===');
    
    const pdfContainer = document.getElementById('pdf-container');
    console.log('PDF Container exists:', !!pdfContainer);
    
    const pageContainers = document.querySelectorAll('.pdf-page-container');
    console.log('Total page containers:', pageContainers.length);
    
    pageContainers.forEach((container, index) => {
        console.log(`Page ${index + 1}:`);
        console.log(`  - data-page-num: "${container.dataset.pageNum}"`);
        console.log(`  - class: "${container.className}"`);
        console.log(`  - parent: ${container.parentElement?.id || 'unknown'}`);
        
        const canvas = container.querySelector('.pdf-page');
        const annotationCanvas = container.querySelector('.annotation-overlay');
        console.log(`  - has pdf canvas: ${!!canvas}`);
        console.log(`  - has annotation canvas: ${!!annotationCanvas}`);
    });
    
    const thumbnails = document.querySelectorAll('.page-thumbnail');
    console.log('\nTotal thumbnails:', thumbnails.length);
    
    thumbnails.forEach((thumbnail, index) => {
        console.log(`Thumbnail ${index + 1}: data-page-num="${thumbnail.dataset.pageNum}"`);
    });
    
    console.log('=== INSPECTION COMPLETE ===\n');
}

// Export for debugging
window.PDFEditor = {
    state: editorState,
    renderer: pdfRenderer,
    api: PDFEditorAPI,
    utils: Utils,
    config: PDF_EDITOR_CONFIG,
    checkDuplicates: checkForDuplicatePages,
    inspectStructure: inspectPDFStructure,
    checkState: function() {
        console.log('=== PDF EDITOR STATE ===');
        console.log('PDF Document loaded:', !!editorState.pdfDocument);
        console.log('Filename:', editorState.filename);
        console.log('Original file:', !!editorState.originalFile);
        console.log('Number of pages:', editorState.pdfDocument?.numPages);
        console.log('Current tool:', editorState.currentTool);
        console.log('Has annotations:', editorState.annotations.size > 0);
        console.log('Is dirty:', editorState.isDirty);
        console.log('========================');
    }
};
