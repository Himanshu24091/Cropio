document.addEventListener('DOMContentLoaded', () => {
    const editorApp = document.getElementById('pdf-editor-app');
    if (!editorApp) return;

    // --- DOM Elements ---
    const uploadInput = document.getElementById('pdf-upload');
    const uploadPrompt = document.getElementById('upload-prompt');
    const viewerPanel = document.getElementById('pdf-viewer');
    const thumbnailsPanel = document.getElementById('thumbnails-panel');
    const toolbar = document.getElementById('toolbar');
    const downloadBtn = document.getElementById('download-btn');

    // --- State ---
    let pdfDoc = null;
    let originalPdfBytes = null;
    let activeTool = 'select';
    let edits = {}; // { pageNum: [ {type, ...data} ] }

    // --- PDF.js Setup ---
    // Ensure this path is correct if you host it locally
    pdfjsLib.GlobalWorkerOptions.workerSrc = `https://unpkg.com/pdfjs-dist@3.4.120/build/pdf.worker.min.js`;

    // --- File Handling ---
    uploadInput.addEventListener('change', handleFileUpload);

    async function handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file || file.type !== 'application/pdf') {
            alert('Please upload a valid PDF file.');
            return;
        }

        const fileReader = new FileReader();
        fileReader.onload = async (event) => {
            originalPdfBytes = new Uint8Array(event.target.result);
            const loadingTask = pdfjsLib.getDocument({ data: originalPdfBytes });
            pdfDoc = await loadingTask.promise;
            
            uploadPrompt.classList.add('hidden');
            viewerPanel.classList.remove('hidden');
            viewerPanel.innerHTML = '';
            thumbnailsPanel.innerHTML = '';
            edits = {};

            await renderAllPages();
        };
        fileReader.readAsArrayBuffer(file);
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
        
        // Create thumbnail canvas
        const thumbViewport = page.getViewport({ scale: 0.2 });
        const thumbCanvas = document.createElement('canvas');
        thumbCanvas.className = 'pdf-thumbnail-canvas cursor-pointer border-2 border-transparent hover:border-indigo-500 p-1';
        thumbCanvas.width = thumbViewport.width;
        thumbCanvas.height = thumbViewport.height;
        thumbnailsPanel.appendChild(thumbCanvas);
        
        await page.render({ canvasContext: thumbCanvas.getContext('2d'), viewport: thumbViewport }).promise;
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

            // Example Edit: Add a simple text box to the first page.
            // In a real application, you would iterate through the `edits` object
            // and apply all the user's changes.
            const firstPage = pages[0];
            const { width, height } = firstPage.getSize();
            firstPage.drawText('Edited with PDF EditX!', {
                x: 50,
                y: height - 50,
                font: await pdfDoc.embedFont(StandardFonts.Helvetica),
                size: 24,
                color: rgb(0.95, 0.1, 0.1),
            });

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
