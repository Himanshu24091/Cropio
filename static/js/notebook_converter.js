// Notebook Converter Specific JavaScript
document.addEventListener('DOMContentLoaded', function() {
    
    // Format selection enhancement
    const formatSelect = document.getElementById('format');
    const pdfNoteBox = document.querySelector('.pdf-note-box');
    
    if (formatSelect && pdfNoteBox) {
        // Show/hide PDF warning based on selection
        formatSelect.addEventListener('change', function() {
            const selectedFormat = this.value;
            
            if (selectedFormat === 'pdf') {
                pdfNoteBox.style.display = 'block';
                // Add a subtle highlight animation
                pdfNoteBox.style.animation = 'pulse 1s ease-in-out';
            } else {
                pdfNoteBox.style.display = 'block'; // Keep visible for info
                pdfNoteBox.style.animation = 'none';
            }
        });
    }
    
    // File validation for .ipynb files
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Check file extension
                const fileName = file.name.toLowerCase();
                if (!fileName.endsWith('.ipynb')) {
                    alert('Please select a valid Jupyter Notebook file (.ipynb)');
                    this.value = '';
                    return;
                }
                
                // Check file size (max 50MB)
                const maxSize = 50 * 1024 * 1024; // 50MB in bytes
                if (file.size > maxSize) {
                    alert('File size exceeds 50MB limit. Please choose a smaller notebook file.');
                    this.value = '';
                    return;
                }
                
                // Basic JSON validation
                const reader = new FileReader();
                reader.onload = function(e) {
                    try {
                        const content = JSON.parse(e.target.result);
                        if (!content.cells || !content.nbformat) {
                            throw new Error('Invalid notebook format');
                        }
                        console.log('Valid Jupyter Notebook detected');
                    } catch (error) {
                        alert('Invalid Jupyter Notebook file. Please ensure the file is a valid .ipynb format.');
                        fileInput.value = '';
                    }
                };
                reader.readAsText(file);
            }
        });
    }
    
    // Enhanced form submission with loading state
    const form = document.querySelector('form');
    const submitButton = form?.querySelector('button[type="submit"]');
    
    if (form && submitButton) {
        form.addEventListener('submit', function(e) {
            // Show loading state
            submitButton.disabled = true;
            submitButton.innerHTML = `
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A8 8 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Converting...
            `;
            
            // Add a timeout to restore button if something goes wrong
            setTimeout(() => {
                if (submitButton.disabled) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = 'Convert Notebook';
                }
            }, 30000); // 30 seconds timeout
        });
    }
    
    // Format recommendation based on file analysis
    function recommendFormat(notebookContent) {
        try {
            const notebook = JSON.parse(notebookContent);
            const cells = notebook.cells || [];
            
            let hasCode = false;
            let hasMarkdown = false;
            let hasOutputs = false;
            
            cells.forEach(cell => {
                if (cell.cell_type === 'code') {
                    hasCode = true;
                    if (cell.outputs && cell.outputs.length > 0) {
                        hasOutputs = true;
                    }
                } else if (cell.cell_type === 'markdown') {
                    hasMarkdown = true;
                }
            });
            
            // Provide format recommendations
            let recommendation = '';
            if (hasOutputs) {
                recommendation = 'HTML recommended for preserving outputs and interactive content';
            } else if (hasCode && hasMarkdown) {
                recommendation = 'Markdown or HTML recommended for mixed content';
            } else if (hasMarkdown) {
                recommendation = 'Markdown or PDF recommended for documentation';
            } else {
                recommendation = 'Any format suitable for your needs';
            }
            
            // Show recommendation (could be displayed in UI)
            console.log('Format recommendation:', recommendation);
            
        } catch (error) {
            console.log('Could not analyze notebook for recommendations');
        }
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            if (form && !submitButton.disabled) {
                form.submit();
            }
        }
    });
});

// CSS animation helper
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.7;
        }
    }
`;
document.head.appendChild(style);
