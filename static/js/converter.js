// Generic converter functionality for all converter pages
document.addEventListener('DOMContentLoaded', () => {
    const converterForm = document.querySelector('form');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file');
    const filePreview = document.getElementById('file-preview');
    
    // Check if event listeners have already been added (to prevent duplicate listeners from index.js)
    if (converterForm && dropZone && fileInput && filePreview && !dropZone.hasAttribute('data-listeners-added')) {
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
                fileIcon.innerHTML = `<svg class="w-full h-full text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">` +
                                    `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>` +
                                    `</svg>`;
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
        
        // Mark that listeners have been added
        dropZone.setAttribute('data-listeners-added', 'true');
    }
});
