// Image cropper functionality
document.addEventListener('DOMContentLoaded', () => {
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
