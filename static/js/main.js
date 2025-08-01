document.addEventListener('DOMContentLoaded', () => {
    // --- Dark Mode Toggle ---
    const themeToggleButton = document.getElementById('theme-toggle');
    const lightIcon = document.getElementById('theme-toggle-light-icon');
    const darkIcon = document.getElementById('theme-toggle-dark-icon');

    // Function to update icon visibility based on the current theme
    const updateIcons = () => {
        if (document.documentElement.classList.contains('dark')) {
            themeToggleButton.setAttribute('aria-label', 'Switch to light mode');
            darkIcon.classList.add('hidden');
            lightIcon.classList.remove('hidden');
        } else {
            themeToggleButton.setAttribute('aria-label', 'Switch to dark mode');
            darkIcon.classList.remove('hidden');
            lightIcon.classList.add('hidden');
        }
    }

    if (themeToggleButton && lightIcon && darkIcon) {
        // Set initial icon state on page load
        updateIcons();

        // Add click listener to the button
        themeToggleButton.addEventListener('click', () => {
            // Toggle the .dark class on the <html> element
            document.documentElement.classList.toggle('dark');

            // Update localStorage with the new theme state
            if (document.documentElement.classList.contains('dark')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }

            // Update the icons to reflect the new theme
            updateIcons();
        });
    }

    // --- File Converter Specific Logic ---
    const converterForm = document.querySelector('form');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file');
    const filePreview = document.getElementById('file-preview');
    if (converterForm && dropZone && fileInput && filePreview) {
        const handleFileSelect = (file) => {
            if (!file) return;

            // Display file name
            const fileNameDisplay = document.getElementById('file-name');
            if (fileNameDisplay) {
                fileNameDisplay.textContent = file.name;
                fileNameDisplay.classList.add('text-muted-light', 'dark:text-muted-dark');
            }

            // Clear previous previews
            filePreview.querySelectorAll('#preview-img, #file-icon').forEach(el => el.remove());

            // Display image preview or a generic icon
            const fileType = file.type.split('/')[0];
            if (fileType === 'image') {
                const img = document.createElement('img');
                img.id = 'preview-img';
                img.classList.add('max-w-full', 'max-h-36', 'rounded-lg', 'mx-auto', 'border', 'border-light', 'dark:border-dark');
                filePreview.prepend(img);

                const reader = new FileReader();
                reader.onload = (e) => {
                    img.src = e.target.result;
                };
                reader.readAsDataURL(file);
            } else {
                const fileIcon = document.createElement('div');
                fileIcon.id = 'file-icon';
                fileIcon.classList.add('w-16', 'h-16', 'mx-auto', 'my-4');
                fileIcon.innerHTML = `<svg class="w-full h-full text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>`;
                filePreview.prepend(fileIcon);
            }
        };

        dropZone.addEventListener('click', () => fileInput.click());

        ['dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        dropZone.addEventListener('dragover', () => dropZone.classList.add('dragover'));
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

        dropZone.addEventListener('drop', (e) => {
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length) {
                fileInput.files = files;
                handleFileSelect(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            const files = e.target.files;
            if (files.length) {
                handleFileSelect(files[0]);
            }
        });

    }

    // --- COMPRESSOR PAGE LOGIC ---
    const compressorApp = document.getElementById('compressor-app');
    if (compressorApp) {
        const dropZone = compressorApp.querySelector('#drop-zone');
        const fileInput = compressorApp.querySelector('#file-input');
        const filePreviewArea = compressorApp.querySelector('#file-preview-area');
        const optionsArea = compressorApp.querySelector('#options-area');
        const compressBtn = compressorApp.querySelector('#compress-btn');
        const resultsArea = compressorApp.querySelector('#results-area');
        const resultsContainer = compressorApp.querySelector('#results-container');
        const clearBtn = compressorApp.querySelector('#clear-btn');

        let filesToProcess = [];

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('border-indigo-500'); });
        dropZone.addEventListener('dragleave', (e) => { e.preventDefault(); dropZone.classList.remove('border-indigo-500'); });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-indigo-500');
            handleFiles(e.dataTransfer.files);
        });

        fileInput.addEventListener('change', () => handleFiles(fileInput.files));

        const handleFiles = (files) => {
            filesToProcess = Array.from(files);
            filePreviewArea.innerHTML = '';
            optionsArea.classList.remove('hidden');
            filesToProcess.forEach(file => {
                const filePreview = document.createElement('div');
                filePreview.className = 'bg-slate-100 dark:bg-slate-700 p-3 rounded-lg flex items-center justify-between';
                filePreview.innerHTML = `<span class="truncate font-medium">${file.name}</span><span class="text-sm text-slate-500">${formatBytes(file.size)}</span>`;
                filePreviewArea.appendChild(filePreview);
            });
        };

        const formatBytes = (bytes, decimals = 2) => {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const dm = decimals < 0 ? 0 : decimals;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
        };

        compressBtn.addEventListener('click', async () => {
            if (filesToProcess.length === 0) return;
            const level = compressorApp.querySelector('input[name="level"]:checked').value;
            const formData = new FormData();
            filesToProcess.forEach(file => formData.append('files[]', file));
            formData.append('level', level);

            setLoading(true);
            try {
                const response = await fetch('/compress', { method: 'POST', body: formData });
                const contentType = response.headers.get('content-type');
                if (!response.ok) {
                    let errorMsg = 'A server error occurred.';
                    if (contentType && contentType.includes('application/json')) {
                        errorMsg = (await response.json()).error || errorMsg;
                    } else {
                        errorMsg = `Server returned an error (Status: ${response.status}). Check server logs.`;
                    }
                    throw new Error(errorMsg);
                }
                const data = await response.json();
                displayResults(data.results);
            } catch (error) {
                alert(`Error: ${error.message}`);
            } finally {
                setLoading(false);
            }
        });

        const setLoading = (isLoading) => {
            const btnText = compressorApp.querySelector('#compress-btn-text');
            const btnIcon = compressorApp.querySelector('#compress-btn-icon');
            compressBtn.disabled = isLoading;
            compressBtn.classList.toggle('opacity-50', isLoading);
            btnText.textContent = isLoading ? 'Compressing...' : 'Compress Files';
            btnIcon.innerHTML = isLoading
                ? `<svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A8 8 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>`
                : `<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>`;
        };

        const displayResults = (results) => {
            resultsArea.classList.remove('hidden');
            resultsContainer.innerHTML = '';
            results.forEach(result => {
                const resultEl = document.createElement('div');
                resultEl.className = 'bg-white dark:bg-slate-800 p-4 rounded-lg shadow-md border';
                let content = `<h4 class="font-bold text-lg truncate">${result.filename}</h4>`;
                if (result.error) {
                    content += `<p class="text-red-500 mt-2">${result.error}</p>`;
                } else {
                    content += `
                        <div class="grid md:grid-cols-2 gap-4 mt-3">
                            <div>
                                <div class="flex justify-between text-sm"><span class="text-slate-500">Original Size:</span><span class="font-medium">${formatBytes(result.original_size)}</span></div>
                                <div class="flex justify-between text-sm mt-1"><span class="text-slate-500">New Size:</span><span class="font-medium text-green-500">${formatBytes(result.compressed_size)}</span></div>
                                <div class="mt-3 pt-3 border-t"><div class="flex justify-between font-semibold"><span>Savings:</span><span class="text-indigo-500">${result.reduction_percent}%</span></div></div>
                                <a href="${result.download_url}" class="download-btn">Download</a>
                            </div>
                            ${result.preview_url ? `<div class="border-l pl-4"><p class="text-sm text-center mb-2 text-slate-500">Preview</p><img src="${result.preview_url}" alt="Preview" class="rounded-md max-h-32 object-contain mx-auto"></div>` : ''}
                        </div>`;
                }
                resultEl.innerHTML = content;
                resultsContainer.appendChild(resultEl);
            });
        };

        clearBtn.addEventListener('click', () => {
            filesToProcess = [];
            filePreviewArea.innerHTML = '';
            resultsContainer.innerHTML = '';
            optionsArea.classList.add('hidden');
            resultsArea.classList.add('hidden');
            fileInput.value = '';
        });
    }

    // --- IMAGE CROPPER PAGE LOGIC ---
    const cropperApp = document.getElementById('cropper-app');

    if (cropperApp) {
        const uploadSection = cropperApp.querySelector('#upload-section');
        const cropperSection = cropperApp.querySelector('#cropper-section');
        const imageInput = cropperApp.querySelector('#upload-image');
        const image = cropperApp.querySelector('#image-to-crop');
        const aspectRatioBtns = cropperApp.querySelector('#aspect-ratio-btns');
        const cropBtn = cropperApp.querySelector('#crop-btn');
        const resetBtn = cropperApp.querySelector('#reset-btn'); // Get the reset button
        const outputFormatSelect = cropperApp.querySelector('#output-format');
        const loadingOverlay = cropperApp.querySelector('#cropper-loading-overlay');

        let cropper;
        let originalFile;

        const initCropper = (imageUrl) => {
            image.src = imageUrl;
            uploadSection.classList.add('hidden');
            cropperSection.classList.remove('hidden');

            if (cropper) {
                cropper.destroy();
            }

            cropper = new Cropper(image, {
                aspectRatio: NaN, viewMode: 1, background: false, responsive: true,
                restore: false, guides: true, center: true, highlight: true,
                cropBoxMovable: true, cropBoxResizable: true,
            });
        };

        imageInput.addEventListener('change', async (e) => {
            const files = e.target.files;
            if (!files || files.length === 0) return;

            originalFile = files[0];

            if (originalFile.type === 'application/pdf') {
                loadingOverlay.style.display = 'flex';
                uploadSection.classList.add('hidden');
                cropperSection.classList.remove('hidden');

                const formData = new FormData();
                formData.append('file', originalFile);

                try {
                    const response = await fetch('/pdf-to-image-preview', {
                        method: 'POST',
                        body: formData,
                    });
                    if (!response.ok) {
                        const error = await response.json();
                        throw new Error(error.error || 'Failed to generate preview.');
                    }
                    const data = await response.json();
                    initCropper(data.preview_url);
                } catch (error) {
                    alert(`Error: ${error.message}`);
                    resetCropper();
                } finally {
                    loadingOverlay.style.display = 'none';
                }
            } else {
                const reader = new FileReader();
                reader.onload = (event) => {
                    initCropper(event.target.result);
                };
                reader.readAsDataURL(originalFile);
            }
        });

        aspectRatioBtns.addEventListener('click', (e) => {
            if (e.target.tagName === 'BUTTON') {
                const ratio = parseFloat(e.target.getAttribute('data-aspect-ratio'));
                cropper.setAspectRatio(ratio);
                aspectRatioBtns.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
            }
        });

        cropBtn.addEventListener('click', async () => {
            if (!cropper || !originalFile) return;

            const cropData = cropper.getData(true);
            const outputFormat = outputFormatSelect.value;

            const formData = new FormData();
            formData.append('file', originalFile);
            formData.append('crop_data', JSON.stringify(cropData));
            formData.append('output_format', outputFormat);

            cropBtn.textContent = 'Cropping...';
            cropBtn.disabled = true;

            try {
                const response = await fetch('/crop-image', {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to crop image');
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;

                const originalName = originalFile.name.split('.').slice(0, -1).join('.');
                a.download = `${originalName}_cropped.${outputFormat}`;

                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();

            } catch (error) {
                alert(`Error: ${error.message}`);
            } finally {
                cropBtn.textContent = 'Crop & Download';
                cropBtn.disabled = false;
            }
        });

        // Function to reset the entire cropper UI
        const resetCropper = () => {
            if (cropper) cropper.destroy();
            image.src = '';
            imageInput.value = ''; // Clear the file input
            uploadSection.classList.remove('hidden');
            cropperSection.classList.add('hidden');
            originalFile = null;
            // Reset aspect ratio button to "Free"
            aspectRatioBtns.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
            aspectRatioBtns.querySelector('button[data-aspect-ratio="NaN"]').classList.add('active');
        };

        // Add event listener for the new reset button
        resetBtn.addEventListener('click', resetCropper);
    }

});

