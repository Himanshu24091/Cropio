document.addEventListener('DOMContentLoaded', () => {
    console.log('PDF Editor DOM loaded');
    
    const editorApp = document.getElementById('pdf-editor-app');
    if (!editorApp) {
        console.error('PDF editor app element not found');
        return;
    }

    console.log('PDF Editor app found');

    // --- DOM Elements ---
    const uploadInput = document.getElementById('pdf-upload');
    const uploadPrompt = document.getElementById('upload-prompt');
    const viewerPanel = document.getElementById('pdf-viewer');
    const thumbnailsPanel = document.getElementById('thumbnails-panel');
    const toolbar = document.getElementById('toolbar');
    const downloadBtn = document.getElementById('download-btn');
    
    // Debug: Check if all elements are found
    console.log('DOM Elements found:', {
        uploadInput: !!uploadInput,
        uploadPrompt: !!uploadPrompt,
        viewerPanel: !!viewerPanel,
        thumbnailsPanel: !!thumbnailsPanel,
        toolbar: !!toolbar,
        downloadBtn: !!downloadBtn
    });
    
    if (!uploadInput) {
        console.error('Upload input not found');
        return;
    }

    // --- State ---
    let pdfDoc = null;
    let originalPdfBytes = null;
    let activeTool = 'select';
    let edits = {}; // { pageNum: [ {type, ...data} ] }

    // --- PDF.js Setup ---
    // This path is crucial for the library to work.
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@3.4.120/build/pdf.worker.min.js`;
    
    console.log('PDF Editor initialized successfully');

    // --- File Handling ---
    console.log('Adding file upload event listener');
    uploadInput.addEventListener('change', handleFileUpload);
    
    // Also add click event to the upload prompt area
    if (uploadPrompt) {
        uploadPrompt.addEventListener('click', () => {
            console.log('Upload prompt clicked');
            uploadInput.click();
        });
    }

    async function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) {
            console.log('No file selected');
            return;
        }
        
        if (file.type !== 'application/pdf') {
            alert('Please upload a valid PDF file.');
            return;
        }
        
        console.log('Starting PDF upload:', file.name, 'Size:', file.size, 'bytes');
        
        try {
            const fileReader = new FileReader();
            fileReader.onload = async (event) => {
                try {
                    console.log('File read successfully, loading PDF...');
                    originalPdfBytes = new Uint8Array(event.target.result);
                    const loadingTask = pdfjsLib.getDocument({ data: originalPdfBytes });
                    pdfDoc = await loadingTask.promise;
                    
                    console.log('PDF loaded successfully, pages:', pdfDoc.numPages);
                    
                    uploadPrompt.classList.add('hidden');
                    viewerPanel.classList.remove('hidden');
                    viewerPanel.innerHTML = '';
                    thumbnailsPanel.innerHTML = '';
                    edits = {};

                    await renderAllPages();
                } catch (error) {
                    console.error('Error loading PDF:', error);
                    alert('Error loading PDF: ' + error.message);
                }
            };
            
            fileReader.onerror = (error) => {
                console.error('Error reading file:', error);
                alert('Error reading file.');
            };
            
            fileReader.readAsArrayBuffer(file);
        } catch (error) {
            console.error('Error in handleFileUpload:', error);
            alert('Error uploading file: ' + error.message);
        }
    }

// --- Rendering ---
    async function renderAllPages() {
        for (let i = 1; i <= pdfDoc.numPages; i++) {
            await renderPage(i);
        }
    }

    async function renderPage(pageNum) {
        const page = await pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale: 1.5 });

        // Create main viewer canvas
        const canvas = document.createElement('canvas');
        canvas.className = 'pdf-page-canvas mb-4 shadow-lg';
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        const context = canvas.getContext('2d');
        viewerPanel.appendChild(canvas);

        const renderContext = { canvasContext: context, viewport: viewport };
        await page.render(renderContext).promise;

        // Functionality for text annotations and drawing
        setupPageInteractions(canvas, pageNum);
        
        // Create thumbnail canvas
        const thumbViewport = page.getViewport({ scale: 0.2 });
        const thumbCanvas = document.createElement('canvas');
        thumbCanvas.className = 'pdf-thumbnail-canvas cursor-pointer border-2 border-transparent hover:border-indigo-500 p-1';
        thumbCanvas.width = thumbViewport.width;
        thumbCanvas.height = thumbViewport.height;
        thumbnailsPanel.appendChild(thumbCanvas);
        
        await page.render({ canvasContext: thumbCanvas.getContext('2d'), viewport: thumbViewport }).promise;
    }

    function setupPageInteractions(canvas, pageNum) {
        const ctx = canvas.getContext('2d');
        let isInteracting = false;
        let startX = 0;
        let startY = 0;
        let currentPath = [];

        canvas.addEventListener('mousedown', e => {
            const rect = canvas.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;
            isInteracting = true;

            if (activeTool === 'text') {
                handleTextTool(startX, startY, pageNum);
            } else if (activeTool === 'draw') {
                currentPath = [{ x: startX, y: startY }];
            } else if (activeTool === 'highlight') {
                // Start highlighting
                ctx.globalCompositeOperation = 'multiply';
            }
        });

        canvas.addEventListener('mousemove', e => {
            if (!isInteracting) return;
            
            const rect = canvas.getBoundingClientRect();
            const currentX = e.clientX - rect.left;
            const currentY = e.clientY - rect.top;

            if (activeTool === 'draw') {
                drawLine(ctx, startX, startY, currentX, currentY);
                currentPath.push({ x: currentX, y: currentY });
                startX = currentX;
                startY = currentY;
            } else if (activeTool === 'highlight') {
                drawHighlight(ctx, startX, startY, currentX, currentY);
            }
        });

        canvas.addEventListener('mouseup', () => {
            if (!isInteracting) return;
            
            isInteracting = false;

            if (activeTool === 'draw' && currentPath.length > 0) {
                saveEdit(pageNum, {
                    type: 'draw',
                    path: [...currentPath],
                    color: 'red',
                    lineWidth: 2
                });
            } else if (activeTool === 'highlight') {
                ctx.globalCompositeOperation = 'source-over';
            }
        });

        function handleTextTool(x, y, pageNum) {
            const text = prompt('Enter text:');
            if (text && text.trim()) {
                drawText(ctx, text, x, y);
                saveEdit(pageNum, {
                    type: 'text',
                    text: text.trim(),
                    x: x,
                    y: y,
                    fontSize: 16,
                    color: 'black'
                });
            }
        }

        function drawLine(context, x1, y1, x2, y2) {
            context.beginPath();
            context.strokeStyle = 'red';
            context.lineWidth = 2;
            context.moveTo(x1, y1);
            context.lineTo(x2, y2);
            context.stroke();
            context.closePath();
        }

        function drawText(context, text, x, y) {
            context.font = '16px Arial';
            context.fillStyle = 'black';
            context.fillText(text, x, y);
        }

        function drawHighlight(context, x1, y1, x2, y2) {
            context.globalAlpha = 0.3;
            context.fillStyle = 'yellow';
            context.fillRect(Math.min(x1, x2), Math.min(y1, y2), Math.abs(x2 - x1), Math.abs(y2 - y1));
            context.globalAlpha = 1.0;
        }

        function saveEdit(pageNum, editData) {
            if (!edits[pageNum]) edits[pageNum] = [];
            edits[pageNum].push(editData);
        }
    }

    // --- Toolbar Logic ---
    toolbar.addEventListener('click', (e) => {
        const toolBtn = e.target.closest('.toolbar-btn');
        if (toolBtn) {
            activeTool = toolBtn.dataset.tool;
            document.querySelectorAll('.toolbar-btn').forEach(btn => btn.classList.remove('active'));
            toolBtn.classList.add('active');
            console.log(`Tool changed to: ${activeTool}`);
        }
    });

    // --- Download Logic ---
    downloadBtn.addEventListener('click', savePdf);

    async function savePdf() {
        if (!originalPdfBytes) {
            alert("No PDF loaded!");
            return;
        }

        downloadBtn.textContent = 'Processing...';
        downloadBtn.disabled = true;

        try {
            const { PDFDocument, rgb, StandardFonts } = PDFLib;
            const pdfDoc = await PDFDocument.load(originalPdfBytes);
            const pages = pdfDoc.getPages();

            // Apply all the user's edits
            for (const pageNum in edits) {
                const page = pages[pageNum - 1];
                const { width, height } = page.getSize();
                
            // Use async function to allow awaiting font embedding
            edits[pageNum].forEach(async (edit) => {
                if (edit.type === 'draw' && edit.path) {
                    // Draw path as series of lines
                    for (let i = 1; i < edit.path.length; i++) {
                        const prev = edit.path[i - 1];
                        const curr = edit.path[i];
                        page.drawLine({
                            start: { x: prev.x, y: height - prev.y },
                            end: { x: curr.x, y: height - curr.y },
                            thickness: edit.lineWidth || 2,
                            color: rgb(0.95, 0.1, 0.1),
                        });
                    }
                } else if (edit.type === 'text') {
                    // Add text annotation
                    page.drawText(edit.text, {
                        x: edit.x,
                        y: height - edit.y,
                        size: edit.fontSize || 16,
                        font: await pdfDoc.embedFont(StandardFonts.Helvetica),
                        color: rgb(0, 0, 0),
                    });
                } else if (edit.type === 'highlight') {
                    // Add highlight rectangle
                    page.drawRectangle({
                        x: edit.x,
                        y: height - edit.y - edit.height,
                        width: edit.width,
                        height: edit.height,
                        color: rgb(1, 1, 0),
                        opacity: 0.3,
                    });
                }
            });
            }

            const pdfBytes = await pdfDoc.save();

            // Trigger download
            const blob = new Blob([pdfBytes], { type: 'application/pdf' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            const originalFileName = uploadInput.files[0].name.replace(/\.pdf$/i, '');
            link.download = `${originalFileName}_edited.pdf`;
            link.click();
            URL.revokeObjectURL(link.href);

        } catch (error) {
            console.error('Error saving PDF:', error);
            alert('An error occurred while saving the PDF.');
        } finally {
            downloadBtn.textContent = 'Download PDF';
            downloadBtn.disabled = false;
        }
    }
});
