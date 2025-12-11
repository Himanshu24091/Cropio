// JavaScript for PDF Merge Page

document.addEventListener("DOMContentLoaded", function() {
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const fileListSection = document.getElementById("fileListSection");
    const fileList = document.getElementById("fileList");
    const uploadProgress = document.getElementById("uploadProgress");
    const progressFill = document.getElementById("progressFill");
    const mergeBtn = document.getElementById("mergeBtn");
    const clearAllBtn = document.getElementById("clearAllBtn");
    const resultSection = document.getElementById("resultSection");
    const resultContent = document.getElementById("resultContent");
    const alertContainer = document.getElementById("alertContainer");
    const loadingModal = document.getElementById("loadingModal");
    
    const uploadedFiles = [];

    // Initialize SortableJS on the fileList element
    const sortable = new Sortable(fileList, {
        animation: 150,
        onEnd: function(evt) {
            console.log("File order changed!", evt);
        }
    });

    dropzone.addEventListener("click", () => fileInput.click());

    fileInput.addEventListener("change", (e) => handleFiles(e.target.files));

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragging");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragging");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragging");
        handleFiles(e.dataTransfer.files);
    });

    function handleFiles(files) {
        if (!files.length) return;

        Array.from(files).forEach(file => {
            if (!file.type.includes("pdf")) {
                showAlert("Only PDF files are allowed.", "error");
                return;
            }

            const reader = new FileReader();
            reader.onload = function(evt) {
                uploadFile(file, evt.target.result);
            };
            reader.readAsDataURL(file);
        });
    }

    function uploadFile(file, fileDataURL) {
        const formData = new FormData();
        formData.append('files[]', file, file.name);

        showProgress(true);
        fetch('/api/pdf-merge/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addFilesToList(data.files);
                showProgress(false);
                mergeBtn.disabled = false;
                showAlert(data.message, "success");
            } else {
                showAlert(data.error, "error");
                showProgress(false);
            }
        })
        .catch(error => {
            console.error('Error uploading file:', error);
            showAlert('Failed to upload files.', "error");
            showProgress(false);
        });
    }

    function addFilesToList(files) {
        if (files.length) fileListSection.classList.remove('hidden');

        files.forEach(file => {
            const fileItem = document.createElement("div");
            fileItem.classList.add("file-item");
            fileItem.setAttribute("data-id", file.id);  // Use data-id for sortable
            fileItem.setAttribute("data-filename", file.unique_filename);

            const thumbnail = file.thumbnail ? `<img src="${file.thumbnail}" class="file-thumbnail" alt="Preview">` : '';

            fileItem.innerHTML = `
                <div class="file-thumbnail-container">${thumbnail}</div>
                <div class="file-info">
                    <div class="file-name">${file.filename}</div>
                    <div class="file-size">${file.size_formatted} • ${file.page_count} pages</div>
                </div>
                <div class="drag-handle" style="cursor: move; padding: 8px;">
                    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16"></path>
                    </svg>
                </div>
            `;

            fileList.appendChild(fileItem);
            uploadedFiles.push(file);
        });
    }

    function mergePDFs() {
        // Get current order of files from the DOM
        const fileItems = Array.from(fileList.children);
        const file_order = fileItems.map(item => item.getAttribute('data-filename'));
        
        const data = {
            file_order: file_order
        };

        showLoading(true);

        fetch('/api/pdf-merge/merge', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showResult(data);
            } else {
                showAlert(data.error, "error");
            }
            showLoading(false);
        })
        .catch(error => {
            console.error('Error merging PDFs:', error);
            showAlert('Failed to merge PDFs.', "error");
            showLoading(false);
        });
    }

    mergeBtn.addEventListener("click", mergePDFs);

    clearAllBtn.addEventListener("click", () => {
        while (fileList.firstChild) {
            fileList.removeChild(fileList.firstChild);
        }
        fileListSection.classList.add('hidden');
        uploadedFiles.length = 0;
        mergeBtn.disabled = true;
    });

    function showProgress(visible) {
        uploadProgress.classList.toggle('hidden', !visible);
    }

    function showLoading(visible) {
        loadingModal.classList.toggle('hidden', !visible);
    }

    function showResult(data) {
        resultSection.classList.remove('hidden');
        resultContent.innerHTML = `
            <div class="mb-4">
                <img src="${data.thumbnail}" class="file-thumbnail" alt="Preview">
            </div>
            <a href="/api/pdf-merge/download/${data.output_file}" class="btn btn-green mt-4">Download Merged PDF</a>
        `;
    }

    function showAlert(message, type) {
        const alert = document.createElement("div");
        alert.innerText = message;
        alert.className = `alert alert-${type}`;
        alertContainer.appendChild(alert);
        setTimeout(() => alert.remove(), 4000);
        setTimeout(() => alert.classList.add('fade'), 3000);
    }
});

