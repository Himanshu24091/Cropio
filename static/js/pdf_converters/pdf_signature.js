document.addEventListener('DOMContentLoaded', function() {
    let signaturePad;
    let currentSignatureData = null;
    let uploadedPDFFile = null;
    let pdfDocument = null;
    let currentPage = 1;
    let totalPages = 1;
    
    // Initialize the app
    initializePDFUpload();
    initializeSignatureTabs();
    initializeSignaturePad();
    initializeSignatureUpload();
    initializeTextSignature();
    initializePositioning();
    
    function initializePDFUpload() {
        const dropzone = document.querySelector('.upload-zone');

        if (dropzone) {
            // Prevent default drag behaviors
            ;['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropzone.addEventListener(eventName, (e) => e.preventDefault());
                document.body.addEventListener(eventName, (e) => e.preventDefault());
            });

            // Highlight when drag is over
            ;['dragenter', 'dragover'].forEach(eventName => {
                dropzone.addEventListener(eventName, () => {
                    dropzone.classList.add('dragging');
                });
            });

            ;['dragleave', 'drop'].forEach(eventName => {
                dropzone.addEventListener(eventName, () => {
                    dropzone.classList.remove('dragging');
                });
            });

            // Handle dropped files
            dropzone.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                handleFileUpload(files);
            });

            // Handle browse click
            dropzone.addEventListener('click', () => {
                const fileInput = document.createElement('input');
                fileInput.type = 'file';
                fileInput.accept = 'application/pdf';
                fileInput.onchange = (e) => handleFileUpload(e.target.files);
                fileInput.click();
            });
        }
    }
    
    function initializeSignatureTabs() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('data-tab');
                
                // Update active tab button
                tabButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                // Update active tab content
                tabContents.forEach(content => content.classList.remove('active'));
                const targetTab = document.getElementById(`${tabName}-tab`);
                if (targetTab) {
                    targetTab.classList.add('active');
                }
            });
        });
    }
    
function initializeSignaturePad() {
    const canvas = document.getElementById('signature-pad');
    if (canvas && typeof SignaturePad !== 'undefined') {
        let signatureHistory = [];
        
        function resizeCanvas() {
            const container = canvas.parentElement;
            const containerWidth = container.offsetWidth;
            const maxWidth = 700;
            const width = Math.min(containerWidth - 40, maxWidth);
            const height = 150;  // Adjust the height for comfort drawing
            
            canvas.style.width = width + 'px';
            canvas.style.height = height + 'px';
            
            const scale = window.devicePixelRatio || 1;
            canvas.width = width * scale;
            canvas.height = height * scale;
            
            canvas.getContext('2d').scale(scale, scale);
            
            if (signaturePad) {
                signaturePad.clear();
                signatureHistory = [];
            }
        }
        
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
        
        signaturePad = new SignaturePad(canvas, {
            backgroundColor: 'rgba(255, 255, 255, 0)', 
            penColor: 'rgb(0, 0, 0)',
            minWidth: 0.5,
            maxWidth: 2.5, // Adjust the width range for finer strokes
            throttle: 0,
            minDistance: 1.0, // Make it 1 to filter out noise
            velocityFilterWeight: 0.7
        });
        
        signaturePad.addEventListener('beginStroke', () => {
            signatureHistory.push(signaturePad.toData());
            if (signatureHistory.length > 50) signatureHistory.shift();
        });

        const penColorInput = document.getElementById('pen-color');
        if (penColorInput) {
            penColorInput.addEventListener('change', (e) => {
                signaturePad.penColor = e.target.value;
            });
        }

        const penSizeInput = document.getElementById('pen-size');
        const penSizeValue = document.getElementById('pen-size-value');
        if (penSizeInput && penSizeValue) {
            penSizeInput.addEventListener('input', (e) => {
                const size = parseInt(e.target.value);
                signaturePad.minWidth = size * 0.5;
                signaturePad.maxWidth = size * 1.5;
                penSizeValue.textContent = size + 'px';
            });
        }

        // Background color control
        const bgColorSelect = document.getElementById('bg-color');
        if (bgColorSelect) {
            bgColorSelect.addEventListener('change', (e) => {
                const bgColor = e.target.value === 'white' ? 'rgb(255, 255, 255)' : 'rgba(255, 255, 255, 0)';
                signaturePad.backgroundColor = bgColor;
                signaturePad.clear(); // Clear and redraw with new background
            });
        }

        const undoBtn = document.getElementById('undo-signature');
        if (undoBtn) {
            undoBtn.addEventListener('click', () => {
                if (signatureHistory.length > 0) {
                    signatureHistory.pop();
                    signaturePad.clear();
                    if (signatureHistory.length > 0) {
                        signaturePad.fromData(signatureHistory[signatureHistory.length - 1]);
                    }
                }
            });
        }

        const clearBtn = document.getElementById('clear-signature');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                signaturePad.clear();
                signatureHistory = [];
            });
        }

        const saveBtn = document.getElementById('save-signature');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                if (!signaturePad.isEmpty()) {
                    const dataURL = signaturePad.toDataURL('image/png');
                    showSignaturePreview(dataURL);
                    currentSignatureData = dataURL;
                } else {
                    showAlert('Please draw your signature first', 'error');
                }
            });
        }
    }
}
    
    function initializeSignatureUpload() {
        const uploadZone = document.getElementById('signature-upload-zone');
        const fileInput = document.getElementById('signature-upload');
        
        if (uploadZone && fileInput) {
            uploadZone.addEventListener('click', () => {
                fileInput.click();
            });
            
            fileInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        const dataURL = e.target.result;
                        showSignaturePreview(dataURL);
                        currentSignatureData = dataURL;
                    };
                    reader.readAsDataURL(file);
                }
            });
        }
    }
    
    function initializeTextSignature() {
        const textInput = document.getElementById('signature-text');
        const fontSelect = document.getElementById('font-style');
        const fontWeightSelect = document.getElementById('font-weight');
        const textStyleSelect = document.getElementById('text-style');
        const fontSizeRange = document.getElementById('font-size');
        const fontSizeValue = document.getElementById('font-size-value');
        const createBtn = document.getElementById('create-text-signature');
        const previewText = document.getElementById('preview-text');
        const previewPlaceholder = document.getElementById('preview-placeholder');
        
        // Update live preview function
        function updateLivePreview() {
            const text = textInput.value.trim();
            const fontSize = fontSizeRange.value;
            const fontStyle = fontSelect.value;
            const fontWeight = fontWeightSelect.value;
            const textStyle = textStyleSelect.value;
            
            if (text) {
                previewText.textContent = text;
                previewText.style.fontSize = fontSize + 'px';
                previewText.style.fontFamily = getFontFamily(fontStyle);
                previewText.style.fontWeight = fontWeight;
                previewText.style.fontStyle = textStyle;
                previewText.classList.remove('hidden');
                previewPlaceholder.classList.add('hidden');
            } else {
                previewText.classList.add('hidden');
                previewPlaceholder.classList.remove('hidden');
            }
        }
        
        // Add event listeners for live preview
        if (textInput) {
            textInput.addEventListener('input', updateLivePreview);
        }
        
        if (fontSelect) {
            fontSelect.addEventListener('change', updateLivePreview);
        }
        
        if (fontWeightSelect) {
            fontWeightSelect.addEventListener('change', updateLivePreview);
        }
        
        if (textStyleSelect) {
            textStyleSelect.addEventListener('change', updateLivePreview);
        }
        
        if (fontSizeRange && fontSizeValue) {
            fontSizeRange.addEventListener('input', () => {
                fontSizeValue.textContent = fontSizeRange.value + 'px';
                updateLivePreview();
            });
        }
        
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                const text = textInput.value.trim();
                if (text) {
                    const fontSize = fontSizeRange.value;
                    const fontStyle = fontSelect.value;
                    const fontWeight = fontWeightSelect.value;
                    const textStyle = textStyleSelect.value;
                    const dataURL = createTextSignature(text, fontStyle, fontSize, fontWeight, textStyle);
                    showSignaturePreview(dataURL);
                    currentSignatureData = dataURL;
                } else {
                    showAlert('Please enter your name', 'error');
                }
            });
        }
    }
    
    function getFontFamily(fontStyle) {
        const fontMap = {
            'arial': 'Arial, sans-serif',
            'times': 'Times New Roman, serif',
            'georgia': 'Georgia, serif',
            'brush-script': 'Brush Script MT, cursive',
            'dancing-script': 'Dancing Script, cursive',
            'great-vibes': 'Great Vibes, cursive',
            'sacramento': 'Sacramento, cursive',
            'alex-brush': 'Alex Brush, cursive',
            'allura': 'Allura, cursive',
            'kaushan': 'Kaushan Script, cursive'
        };
        return fontMap[fontStyle] || 'Arial, sans-serif';
    }
    
    function createTextSignature(text, fontStyle, fontSize, fontWeight = 'normal', textStyle = 'normal') {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Set canvas size (make it larger for better quality)
        canvas.width = 600;
        canvas.height = 150;
        
        // Get font family
        const fontFamily = getFontFamily(fontStyle);
        
        // Build font string
        let fontString = '';
        if (textStyle === 'italic') fontString += 'italic ';
        fontString += `${fontWeight} ${fontSize}px ${fontFamily}`;
        
        ctx.font = fontString;
        ctx.fillStyle = 'black';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Fill with transparent background
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw text with shadow for better visibility
        ctx.shadowColor = 'rgba(0, 0, 0, 0.1)';
        ctx.shadowBlur = 2;
        ctx.shadowOffsetX = 1;
        ctx.shadowOffsetY = 1;
        
        ctx.fillText(text, canvas.width / 2, canvas.height / 2);
        
        // Reset shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
        
        return canvas.toDataURL('image/png');
    }
    
    function showSignaturePreview(dataURL) {
        const preview = document.getElementById('signature-preview');
        const image = document.getElementById('signature-image');
        
        if (preview && image) {
            image.src = dataURL;
            preview.classList.remove('hidden');
            
            // Show positioning section
            document.getElementById('positioning-section').classList.remove('hidden');
            
            // Initialize signature overlay
            initializeSignatureOverlay(dataURL);
            
            // Initialize edit button
            const editBtn = document.getElementById('edit-signature');
            if (editBtn) {
                editBtn.onclick = () => {
                    preview.classList.add('hidden');
                    document.getElementById('positioning-section').classList.add('hidden');
                    const overlay = document.getElementById('signature-overlay');
                    if (overlay) overlay.classList.add('hidden');
                    currentSignatureData = null;
                };
            }
        }
    }
    
    function showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container');
        if (alertContainer) {
            const alert = document.createElement('div');
            alert.className = `alert alert-${type}`;
            alert.textContent = message;
            
            alertContainer.appendChild(alert);
            
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }
    }

    function initializePositioning() {
        const applyBtn = document.getElementById('apply-signature');
        const resetBtn = document.getElementById('reset-position');
        
        if (applyBtn) {
            applyBtn.addEventListener('click', async () => {
                if (currentSignatureData && uploadedPDFFile) {
                    showLoadingModal(true);
                    
                    try {
                        // First upload the PDF and get the filename
                        const pdfFormData = new FormData();
                        pdfFormData.append('file', uploadedPDFFile);
                        
                        const uploadResponse = await fetch('/api/pdf-signature/upload', {
                            method: 'POST',
                            body: pdfFormData
                        });
                        
                        if (!uploadResponse.ok) {
                            throw new Error('Failed to upload PDF');
                        }
                        
                        const uploadResult = await uploadResponse.json();
                        
                        // Then save the signature
                        const signatureResponse = await fetch('/api/pdf-signature/save-drawn', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                signature_data: currentSignatureData
                            })
                        });
                        
                        if (!signatureResponse.ok) {
                            throw new Error('Failed to save signature');
                        }
                        
                        const signatureResult = await signatureResponse.json();
                        
                        // Get signature position
                        const overlay = document.getElementById('signature-overlay');
                        const position = {
                            x: parseInt(overlay.style.left) || 50,
                            y: parseInt(overlay.style.top) || 50,
                            width: parseInt(overlay.style.width) || 200,
                            height: parseInt(overlay.style.height) || 100
                        };
                        
                        // Apply signature to PDF
                        const applyData = {
                            pdf_filename: uploadResult.filename,
                            signature_filename: signatureResult.signature_filename,
                            page_number: currentPage, // Apply to current page
                            x: position.x,
                            y: position.y,
                            width: position.width,
                            height: position.height
                        };
                        
                        const response = await fetch('/api/pdf-signature/apply', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(applyData)
                        });
                        
                        if (response.ok) {
                            // Check if response is PDF or JSON
                            const contentType = response.headers.get('Content-Type');
                            
                            if (contentType && contentType.includes('application/pdf')) {
                                // Response is PDF file
                                const blob = await response.blob();
                                const url = URL.createObjectURL(blob);
                                
                                showAlert('Signature applied successfully!', 'success');
                                document.getElementById('download-section').classList.remove('hidden');
                                
                                // Create download link for signed PDF
                                const downloadContent = document.getElementById('download-content');
                                const originalName = uploadedPDFFile.name.replace('.pdf', '');
                                downloadContent.innerHTML = `
                                    <a href="${url}" download="${originalName}_signed.pdf">
                                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-4-4m4 4l4-4m-4-4V3m0 3L8 9m4-3l4 3"></path>
                                        </svg>
                                        Download Signed PDF
                                    </a>
                                `;
                            } else {
                                // Response is JSON (success message)
                                const result = await response.json();
                                showAlert(result.message || 'Signature applied successfully!', 'success');
                                document.getElementById('download-section').classList.remove('hidden');
                            }
                        } else {
                            // Handle error response
                            try {
                                const errorData = await response.json();
                                showAlert('Error: ' + (errorData.error || 'Failed to apply signature'), 'error');
                            } catch {
                                showAlert('Error: Failed to apply signature', 'error');
                            }
                        }
                        
                    } catch (error) {
                        showAlert('Error processing signature: ' + error.message, 'error');
                    } finally {
                        showLoadingModal(false);
                    }
                } else {
                    if (!uploadedPDFFile) {
                        showAlert('Please upload a PDF file first', 'error');
                    } else {
                        showAlert('Please create a signature first', 'error');
                    }
                }
            });
        }
        
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                const overlay = document.getElementById('signature-overlay');
                if (overlay) {
                    overlay.style.left = '50px';
                    overlay.style.top = '50px';
                    overlay.style.width = '200px';
                    overlay.style.height = '100px';
                }
            });
        }
    }
    
    function initializeSignatureOverlay(dataURL) {
        const overlay = document.getElementById('signature-overlay');
        const overlayImg = document.getElementById('overlay-signature');
        const pdfPreview = document.getElementById('pdf-preview');
        
        if (overlay && overlayImg) {
            overlayImg.src = dataURL;
            overlay.classList.remove('hidden');
            
            // Set initial position and size
            overlay.style.left = '50px';
            overlay.style.top = '50px';
            overlay.style.width = '200px';
            overlay.style.height = '100px';
            overlay.style.position = 'absolute';
            
            // Enable Apply button
            const applyBtn = document.getElementById('apply-signature');
            if (applyBtn) {
                applyBtn.disabled = false;
            }
            
            // Make draggable
            let isDragging = false;
            let startX, startY, initialLeft, initialTop;
            
            overlay.addEventListener('mousedown', (e) => {
                if (e.target.classList.contains('resize-handle')) return;
                isDragging = true;
                startX = e.clientX;
                startY = e.clientY;
                initialLeft = parseInt(overlay.style.left);
                initialTop = parseInt(overlay.style.top);
                overlay.style.cursor = 'grabbing';
            });
            
            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                const deltaX = e.clientX - startX;
                const deltaY = e.clientY - startY;
                overlay.style.left = (initialLeft + deltaX) + 'px';
                overlay.style.top = (initialTop + deltaY) + 'px';
            });
            
            document.addEventListener('mouseup', () => {
                isDragging = false;
                overlay.style.cursor = 'move';
            });
        }
        
        // Load actual PDF preview if we have an uploaded file
        loadPDFPreview();
    }
    
    function handleFileUpload(files) {
        if (files.length > 0) {
            const file = files[0];
            console.log('File received:', file);
            
            // Store the uploaded PDF file
            uploadedPDFFile = file;
            
            // Display PDF info and show the next step
            const pdfInfo = document.getElementById('pdf-info');
            document.getElementById('pdf-name').textContent = file.name;
            document.getElementById('pdf-details').textContent = `Size: ${(file.size / 1024 / 1024).toFixed(2)} MB`;
            pdfInfo.classList.remove('hidden');

            // Proceed to the signature creation step
            document.getElementById('signature-section').classList.remove('hidden');
        }
    }
    
    function loadPDFPreview() {
        if (uploadedPDFFile) {
            const reader = new FileReader();
            reader.onload = async function (e) {
                const arrayBuffer = e.target.result;
                const url = URL.createObjectURL(new Blob([arrayBuffer], { type: 'application/pdf' }));
                pdfDocument = await pdfjsLib.getDocument(url).promise;
                totalPages = pdfDocument.numPages;
                
                // Update page info
                updatePageInfo();
                
                // Load the first page
                await renderPage(currentPage);
                
                // Initialize page navigation
                initializePageNavigation();
            };
            reader.readAsArrayBuffer(uploadedPDFFile);
        }
    }
    
    async function renderPage(pageNum) {
        if (!pdfDocument) return;
        
        const page = await pdfDocument.getPage(pageNum);
        const scale = 1.5;
        const viewport = page.getViewport({ scale });
        
        // Prepare canvas using PDF page dimensions
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        // Render PDF page into canvas context
        const renderContext = {
            canvasContext: context,
            viewport: viewport
        };
        await page.render(renderContext).promise;
        
        // Set thumbnail to canvas image
        const pdfPageImg = document.getElementById('pdf-page-image');
        pdfPageImg.src = canvas.toDataURL();
        
        // Update page info
        updatePageInfo();
    }
    
    function updatePageInfo() {
        const pageInfo = document.getElementById('page-info');
        if (pageInfo) {
            pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        }
        
        // Update navigation buttons
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        
        if (prevBtn) {
            prevBtn.disabled = currentPage <= 1;
        }
        
        if (nextBtn) {
            nextBtn.disabled = currentPage >= totalPages;
        }
    }
    
    function initializePageNavigation() {
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', async () => {
                if (currentPage > 1) {
                    currentPage--;
                    await renderPage(currentPage);
                }
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', async () => {
                if (currentPage < totalPages) {
                    currentPage++;
                    await renderPage(currentPage);
                }
            });
        }
    }
    
    // Helper functions
    function showLoadingModal(show) {
        const modal = document.getElementById('loading-modal');
        if (modal) {
            if (show) {
                modal.classList.remove('hidden');
            } else {
                modal.classList.add('hidden');
            }
        }
    }
    
    function simulateProcessing() {
        return new Promise(resolve => {
            setTimeout(resolve, 2000); // Simulate 2 second processing time
        });
    }
});

