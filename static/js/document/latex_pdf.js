// LaTeX PDF Converter JavaScript

class LatexPDFConverter {
    constructor() {
        this.currentMode = 'latex-to-pdf';
        this.editor = null;
        this.templates = {};
        this.isConverting = false;
        this.validationTimer = null;
        
        this.init();
    }

    init() {
        this.initializeEditor();
        this.bindEvents();
        this.loadTemplates();
        this.checkSystemRequirements();
        this.setupFileUpload();
        this.updateStats();
    }

    initializeEditor() {
        const textarea = document.getElementById('latexInput');
        if (!textarea || !window.CodeMirror) {
            console.warn('CodeMirror not available, falling back to textarea');
            // Add event listener for textarea fallback
            if (textarea) {
                textarea.addEventListener('input', () => {
                    this.updateStats();
                    this.scheduleValidation();
                    
                    // Trigger auto-compile if enabled
                    if (this.autoCompileEnabled) {
                        this.scheduleAutoCompile();
                    }
                });
            }
            return;
        }

        this.editor = CodeMirror.fromTextArea(textarea, {
            mode: 'stex',
            theme: 'default',
            lineNumbers: true,
            lineWrapping: true,
            autoCloseBrackets: true,
            matchBrackets: true,
            indentUnit: 4,
            indentWithTabs: false,
            extraKeys: {
                'Ctrl-Space': 'autocomplete',
                'Tab': 'indentMore',
                'Shift-Tab': 'indentLess',
                'Ctrl-/': 'toggleComment'
            },
            styleActiveLine: true,
            showTrailingSpace: true,
            autoRefresh: true
        });

        this.editor.on('change', () => {
            this.updateStats();
            this.scheduleValidation();
            
            // Trigger auto-compile if enabled
            if (this.autoCompileEnabled) {
                this.scheduleAutoCompile();
            }
        });

        this.editor.setSize('100%', '100%');
    }

    bindEvents() {
        // Mode toggle buttons
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchMode(e.target.dataset.mode));
        });

        // Convert button
        document.getElementById('convertBtn').addEventListener('click', () => this.handleConversion());

        // Panel controls
        document.getElementById('clearInputBtn').addEventListener('click', () => this.clearInput());
        document.getElementById('insertTemplateBtn').addEventListener('click', () => this.showTemplateSelector());
        document.getElementById('validateBtn').addEventListener('click', () => this.validateLatex());
        document.getElementById('downloadBtn').addEventListener('click', () => this.downloadResult());
        document.getElementById('copyOutputBtn').addEventListener('click', () => this.copyOutput());

        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Template cards
        document.querySelectorAll('.template-card').forEach(card => {
            card.addEventListener('click', (e) => this.insertTemplate(e.currentTarget.dataset.template));
        });

        // File input
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }

        // Auto-wrap checkbox
        document.getElementById('autoWrapDocument').addEventListener('change', (e) => {
            this.autoWrapDocument = e.target.checked;
        });

        // Show compile log checkbox
        document.getElementById('showCompileLog').addEventListener('change', (e) => {
            const logTab = document.querySelector('[data-tab="log"]');
            if (logTab) {
                logTab.style.display = e.target.checked ? 'block' : 'none';
            }
        });

        // Preview button
        document.getElementById('previewBtn').addEventListener('click', () => this.previewPDF());

        // Auto-compile checkbox
        document.getElementById('autoCompileOnChange').addEventListener('change', (e) => {
            this.autoCompileEnabled = e.target.checked;
            if (this.autoCompileEnabled) {
                this.showNotification('Auto-compile enabled. PDF will update automatically as you type.', 'info');
            } else {
                this.showNotification('Auto-compile disabled.', 'info');
            }
        });
    }

    switchMode(mode) {
        this.currentMode = mode;
        
        // Update active button
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });

        // Update UI based on mode
        const inputTitle = document.getElementById('inputPanelTitle');
        const outputTitle = document.getElementById('outputPanelTitle');
        const convertBtnText = document.getElementById('convertBtnText');

        if (mode === 'latex-to-pdf') {
            inputTitle.textContent = 'Input (LaTeX)';
            outputTitle.textContent = 'Output (PDF)';
            convertBtnText.textContent = 'Compile PDF';
            document.getElementById('fileInput').accept = '.tex,.latex';
        } else {
            inputTitle.textContent = 'Input (PDF)';
            outputTitle.textContent = 'Output (LaTeX)';
            convertBtnText.textContent = 'Extract LaTeX';
            document.getElementById('fileInput').accept = '.pdf';
        }

        this.clearOutput();
    }

    setupFileUpload() {
        const uploadZone = document.getElementById('fileUploadZone');
        const fileInput = document.getElementById('fileInput');

        // Drag and drop events
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.processFile(files[0]);
            }
        });

        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });
    }

    handleFileUpload(event) {
        const file = event.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    processFile(file) {
        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        if (this.currentMode === 'latex-to-pdf' && ['tex', 'latex'].includes(fileExtension)) {
            // Read LaTeX file content
            const reader = new FileReader();
            reader.onload = (e) => {
                const content = e.target.result;
                if (this.editor) {
                    this.editor.setValue(content);
                } else {
                    document.getElementById('latexInput').value = content;
                }
                this.updateStats();
                this.scheduleValidation();
            };
            reader.readAsText(file);
        } else if (this.currentMode === 'pdf-to-latex' && fileExtension === 'pdf') {
            // Handle PDF file upload for text extraction
            this.uploadPdfForExtraction(file);
        } else {
            this.showNotification('Invalid file type for current mode', 'error');
        }
    }

    uploadPdfForExtraction(file) {
        const formData = new FormData();
        formData.append('file', file);

        this.showProcessing('Extracting text from PDF...');

        fetch('/api/latex-pdf/extract-text', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            this.hideProcessing();
            if (data.success) {
                if (this.editor) {
                    this.editor.setValue(data.text);
                } else {
                    document.getElementById('latexInput').value = data.text;
                }
                this.updateStats();
            } else {
                this.showNotification(data.error || 'Failed to extract text from PDF', 'error');
            }
        })
        .catch(error => {
            this.hideProcessing();
            console.error('Error uploading PDF:', error);
            this.showNotification('Error processing PDF file', 'error');
        });
    }

    handleConversion() {
        if (this.isConverting) return;

        const input = this.getInputContent();
        if (!input.trim()) {
            this.showNotification('Please enter LaTeX content or upload a file', 'warning');
            return;
        }

        if (this.currentMode === 'latex-to-pdf') {
            this.compileLatexToPdf(input);
        } else {
            this.extractLatexFromPdf(input);
        }
    }

    compileLatexToPdf(latexContent) {
        this.isConverting = true;
        this.showCompilationProgress();

        const autoWrap = document.getElementById('autoWrapDocument').checked;
        const showLog = document.getElementById('showCompileLog').checked;

        fetch('/api/latex-pdf/compile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                latex: latexContent,
                auto_wrap: autoWrap,
                show_log: showLog
            })
        })
        .then(response => response.json())
        .then(data => {
            this.isConverting = false;
            this.hideCompilationProgress();

            if (data.success) {
                this.displayPdfResult(data.pdf_url, data.compilation_time);
                if (data.log) {
                    this.displayCompilationLog(data.log);
                }
                this.showNotification('PDF compiled successfully!', 'success');
            } else {
                this.showNotification(data.error || 'Compilation failed', 'error');
                if (data.log) {
                    this.displayCompilationLog(data.log);
                    this.switchTab('log');
                }
            }
        })
        .catch(error => {
            this.isConverting = false;
            this.hideCompilationProgress();
            console.error('Compilation error:', error);
            this.showNotification('Error during compilation', 'error');
        });
    }

    extractLatexFromPdf(pdfContent) {
        // This would be implemented for PDF to LaTeX conversion
        this.showNotification('PDF to LaTeX conversion not yet implemented', 'info');
    }

    displayPdfResult(pdfUrl, compilationTime) {
        const pdfPreview = document.getElementById('pdfPreview');
        const pdfViewer = document.getElementById('pdfViewer');
        const emptyOutput = document.getElementById('emptyOutput');
        const outputInfo = document.getElementById('outputInfo');
        const conversionTime = document.getElementById('conversionTime');
        const downloadBtn = document.getElementById('downloadBtn');

        // Hide empty state, show PDF preview
        emptyOutput.style.display = 'none';
        pdfPreview.style.display = 'block';
        
        // Set PDF viewer source
        pdfViewer.src = pdfUrl;
        
        // Update stats
        outputInfo.textContent = 'PDF generated successfully';
        if (compilationTime) {
            conversionTime.textContent = `Compiled in ${compilationTime}s`;
        }
        
        // Show download and preview buttons
        downloadBtn.style.display = 'block';
        downloadBtn.onclick = () => window.open(pdfUrl, '_blank');
        
        const previewBtn = document.getElementById('previewBtn');
        if (previewBtn) {
            previewBtn.style.display = 'block';
        }
        
        // Switch to result tab
        this.switchTab('result');
    }

    displayCompilationLog(log) {
        const compilationLog = document.getElementById('compilationLog');
        const logTab = document.querySelector('[data-tab="log"]');
        
        if (compilationLog && log) {
            compilationLog.textContent = log;
            logTab.style.display = 'block';
        }
    }

    validateLatex() {
        const input = this.getInputContent();
        if (!input.trim()) {
            this.showValidationResults([{
                type: 'info',
                message: 'Enter LaTeX code to validate'
            }]);
            return;
        }

        fetch('/api/latex-pdf/validate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ latex: input })
        })
        .then(response => response.json())
        .then(data => {
            this.showValidationResults(data.results);
        })
        .catch(error => {
            console.error('Validation error:', error);
            this.showValidationResults([{
                type: 'error',
                message: 'Validation service unavailable'
            }]);
        });
    }

    scheduleValidation() {
        if (this.validationTimer) {
            clearTimeout(this.validationTimer);
        }
        
        this.validationTimer = setTimeout(() => {
            this.validateLatex();
        }, 1000);
    }

    showValidationResults(results) {
        const validationResults = document.getElementById('validationResults');
        validationResults.innerHTML = '';

        results.forEach(result => {
            const statusDiv = document.createElement('div');
            statusDiv.className = `validation-status ${result.type}`;
            statusDiv.innerHTML = `
                <i class="fas fa-${this.getValidationIcon(result.type)}"></i>
                <span>${result.message}</span>
            `;
            validationResults.appendChild(statusDiv);
        });
    }

    getValidationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    loadTemplates() {
        this.templates = {
            resume: `\\documentclass[11pt]{article}
\\usepackage[utf8]{inputenc}
\\usepackage{geometry}
\\usepackage{enumitem}
\\usepackage{titlesec}

\\geometry{margin=0.75in}
\\pagestyle{empty}

\\titleformat{\\section}{\\large\\bfseries}{}{0em}{}[\\titlerule]
\\titlespacing*{\\section}{0pt}{\\baselineskip}{0.5\\baselineskip}

\\begin{document}

\\begin{center}
    {\\LARGE \\textbf{Your Name}}\\\\
    \\vspace{0.2cm}
    Email: your.email@example.com | Phone: +1 (555) 123-4567\\\\
    LinkedIn: linkedin.com/in/yourprofile | GitHub: github.com/yourusername
\\end{center}

\\section{Education}
\\textbf{Your University} \\hfill \\textit{Year - Year}\\\\
Bachelor of Technology - Computer Science \\hfill CGPA: 8.5/10

\\section{Technical Skills}
\\begin{itemize}[leftmargin=*]
    \\item \\textbf{Programming Languages:} Python, Java, JavaScript, C++
    \\item \\textbf{Databases:} MySQL, PostgreSQL, MongoDB
    \\item \\textbf{Tools \\& Technologies:} Git, Docker, AWS, React
\\end{itemize}

\\section{Experience}
\\textbf{Software Developer Intern} \\hfill \\textit{Company Name | Month Year - Month Year}
\\begin{itemize}[leftmargin=*]
    \\item Developed web applications using React and Node.js
    \\item Collaborated with cross-functional teams on agile projects
    \\item Improved application performance by 30\\% through optimization
\\end{itemize}

\\section{Projects}
\\textbf{Project Name} \\hfill \\textit{Technologies Used}
\\begin{itemize}[leftmargin=*]
    \\item Brief description of what the project does
    \\item Key achievements and impact
    \\item Link: github.com/yourusername/project
\\end{itemize}

\\end{document}`,

            article: `\\documentclass[12pt]{article}
\\usepackage[utf8]{inputenc}
\\usepackage{geometry}
\\usepackage{amsmath}
\\usepackage{amsfonts}
\\usepackage{amssymb}
\\usepackage{graphicx}

\\geometry{margin=1in}

\\title{Your Article Title}
\\author{Your Name}
\\date{\\today}

\\begin{document}

\\maketitle

\\begin{abstract}
This is the abstract of your article. Provide a brief summary of the main points and conclusions.
\\end{abstract}

\\section{Introduction}
This is the introduction section. Explain the background and motivation for your work.

\\section{Methodology}
Describe your approach and methods here.

\\subsection{Data Collection}
Explain how you collected your data.

\\subsection{Analysis}
Describe your analysis methods.

\\section{Results}
Present your findings here.

\\section{Conclusion}
Summarize your conclusions and future work.

\\bibliographystyle{plain}
\\bibliography{references}

\\end{document}`,

            report: `\\documentclass[12pt]{report}
\\usepackage[utf8]{inputenc}
\\usepackage{geometry}
\\usepackage{graphicx}
\\usepackage{fancyhdr}
\\usepackage{tocloft}

\\geometry{margin=1in}
\\pagestyle{fancy}

\\title{Report Title}
\\author{Your Name}
\\date{\\today}

\\begin{document}

\\begin{titlepage}
    \\centering
    \\vspace*{2cm}
    
    {\\LARGE\\bfseries Report Title\\par}
    \\vspace{1.5cm}
    
    {\\large Prepared by\\par}
    \\vspace{0.5cm}
    {\\Large Your Name\\par}
    \\vspace{1cm}
    
    {\\large Organization Name\\par}
    \\vspace{2cm}
    
    {\\large \\today\\par}
    
    \\vfill
\\end{titlepage}

\\tableofcontents
\\newpage

\\chapter{Executive Summary}
Provide a high-level overview of your report.

\\chapter{Introduction}
\\section{Background}
Explain the context and background.

\\section{Objectives}
List your objectives and goals.

\\chapter{Analysis}
\\section{Data Overview}
Present your data and methodology.

\\section{Findings}
Discuss your key findings.

\\chapter{Recommendations}
Provide actionable recommendations based on your analysis.

\\chapter{Conclusion}
Summarize the key points and conclusions.

\\end{document}`,

            letter: `\\documentclass{letter}
\\usepackage[utf8]{inputenc}
\\usepackage{geometry}

\\geometry{margin=1in}

\\address{Your Name\\\\Your Address\\\\City, State ZIP\\\\your.email@example.com}

\\begin{document}

\\begin{letter}{Recipient Name\\\\Recipient Title\\\\Company Name\\\\Company Address\\\\City, State ZIP}

\\opening{Dear Recipient Name,}

This is the opening paragraph of your letter. State the purpose of your letter clearly.

This is the body of your letter. Provide details, explanations, or information as needed. You can have multiple paragraphs here.

This is the closing paragraph. Summarize your main points and indicate any next steps or actions you expect.

\\closing{Sincerely,}

\\end{letter}

\\end{document}`
        };
    }

    insertTemplate(templateName) {
        if (!this.templates[templateName]) {
            this.showNotification('Template not found', 'error');
            return;
        }

        const template = this.templates[templateName];
        if (this.editor) {
            this.editor.setValue(template);
        } else {
            document.getElementById('latexInput').value = template;
        }
        
        this.updateStats();
        this.scheduleValidation();
        this.showNotification(`${templateName.charAt(0).toUpperCase() + templateName.slice(1)} template inserted!`, 'success');
    }

    showTemplateSelector() {
        // Scroll to templates section
        const templatesSection = document.querySelector('.template-grid');
        if (templatesSection) {
            templatesSection.scrollIntoView({ behavior: 'smooth' });
        }
    }

    clearInput() {
        if (this.editor) {
            this.editor.setValue('');
        } else {
            document.getElementById('latexInput').value = '';
        }
        this.updateStats();
        this.clearOutput();
    }

    clearOutput() {
        // Hide PDF preview and show empty state
        document.getElementById('pdfPreview').style.display = 'none';
        document.getElementById('latexOutput').style.display = 'none';
        document.getElementById('emptyOutput').style.display = 'flex';
        document.getElementById('downloadBtn').style.display = 'none';
        document.getElementById('copyOutputBtn').style.display = 'none';
        
        // Hide preview button as well
        const previewBtn = document.getElementById('previewBtn');
        if (previewBtn) {
            previewBtn.style.display = 'none';
        }
        
        // Clear stats
        document.getElementById('outputInfo').textContent = 'Ready to compile';
        document.getElementById('conversionTime').textContent = '';
        
        // Clear validation
        this.showValidationResults([{
            type: 'info',
            message: 'Enter LaTeX code to see validation results'
        }]);
    }

    getInputContent() {
        return this.editor ? this.editor.getValue() : document.getElementById('latexInput').value;
    }

    updateStats() {
        const content = this.getInputContent();
        const lines = content.split('\n').length;
        const chars = content.length;
        const latexCommands = (content.match(/\\[a-zA-Z]+/g) || []).length;

        document.getElementById('inputLines').textContent = lines;
        document.getElementById('inputChars').textContent = chars;
        document.getElementById('latexCommands').textContent = latexCommands;
    }

    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.toggle('active', panel.id === `${tabName}Tab`);
        });
    }

    showCompilationProgress() {
        const progress = document.getElementById('compilationProgress');
        const overlay = document.getElementById('processingOverlay');
        
        progress.style.display = 'block';
        overlay.classList.add('active');
        
        // Animate progress steps
        this.animateProgressSteps();
    }

    hideCompilationProgress() {
        const progress = document.getElementById('compilationProgress');
        const overlay = document.getElementById('processingOverlay');
        
        progress.style.display = 'none';
        overlay.classList.remove('active');
        
        // Reset progress
        document.querySelector('.progress-fill').style.width = '0%';
        document.querySelectorAll('.step').forEach(step => {
            step.classList.remove('active', 'completed');
        });
    }

    animateProgressSteps() {
        const steps = ['step1', 'step2', 'step3'];
        const progressFill = document.querySelector('.progress-fill');
        let currentStep = 0;

        const interval = setInterval(() => {
            if (currentStep < steps.length && this.isConverting) {
                // Mark current step as active
                document.getElementById(steps[currentStep]).classList.add('active');
                
                // Update progress bar
                progressFill.style.width = `${((currentStep + 1) / steps.length) * 100}%`;
                
                // Complete previous step
                if (currentStep > 0) {
                    const prevStep = document.getElementById(steps[currentStep - 1]);
                    prevStep.classList.remove('active');
                    prevStep.classList.add('completed');
                }
                
                currentStep++;
            } else {
                clearInterval(interval);
            }
        }, 800);
    }

    showProcessing(message) {
        const overlay = document.getElementById('processingOverlay');
        const messageEl = overlay.querySelector('.processing-message');
        
        if (messageEl) {
            messageEl.textContent = message;
        }
        
        overlay.classList.add('active');
    }

    hideProcessing() {
        document.getElementById('processingOverlay').classList.remove('active');
    }

    checkSystemRequirements() {
        fetch('/api/latex-pdf/requirements')
        .then(response => response.json())
        .then(data => {
            const alert = document.getElementById('systemRequirements');
            const requirementsList = document.getElementById('requirementsList');
            
            if (data.requirements && data.requirements.length > 0) {
                alert.style.display = 'flex';
                
                requirementsList.innerHTML = data.requirements.map(req => 
                    `<div class="requirement-item ${req.met ? 'met' : 'missing'}">
                        <i class="fas fa-${req.met ? 'check' : 'times'}"></i>
                        ${req.name}: ${req.status}
                    </div>`
                ).join('');
            }
        })
        .catch(error => {
            console.error('Requirements check failed:', error);
        });
    }

    downloadResult() {
        // This will be handled by the download button's onclick event
        // which is set when displaying the PDF result
    }

    copyOutput() {
        const outputText = document.getElementById('outputText');
        if (outputText && outputText.value) {
            outputText.select();
            document.execCommand('copy');
            this.showNotification('Output copied to clipboard!', 'success');
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => notification.classList.add('show'), 100);
        
        // Auto hide
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 3000);
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    previewPDF() {
        // Get the current PDF viewer URL
        const pdfViewer = document.getElementById('pdfViewer');
        if (pdfViewer && pdfViewer.src) {
            // Show the PDF in modal popup
            this.showPDFModal(pdfViewer.src);
        } else {
            this.showNotification('No PDF available to preview. Compile your LaTeX first.', 'warning');
        }
    }
    
    scheduleAutoCompile() {
        // If there's an existing timer, clear it
        if (this.autoCompileTimer) {
            clearTimeout(this.autoCompileTimer);
        }
        
        // Set a new timer to compile after a delay
        this.autoCompileTimer = setTimeout(() => {
            const latexContent = this.getInputContent();
            if (latexContent.trim()) {
                this.compileLatexToPdf(latexContent);
            }
        }, 2000); // 2 second delay to prevent too frequent compilations
    }
    
    showPDFModal(pdfUrl) {
        const modal = document.getElementById('pdfModal');
        const modalViewer = document.getElementById('pdfModalViewer');
        const modalDownloadBtn = document.getElementById('pdfModalDownload');
        
        // Set the PDF URL in the modal viewer
        modalViewer.src = pdfUrl;
        
        // Set up download button
        modalDownloadBtn.onclick = () => {
            window.open(pdfUrl, '_blank');
        };
        
        // Show the modal
        modal.style.display = 'flex';
        
        // Add keyboard event listener for ESC key
        const handleKeyPress = (e) => {
            if (e.key === 'Escape') {
                modal.style.display = 'none';
                document.removeEventListener('keydown', handleKeyPress);
            }
        };
        document.addEventListener('keydown', handleKeyPress);
    }
}

// Initialize the converter when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new LatexPDFConverter();
});

// CSS for notifications (can be added to the main CSS file)
const notificationStyles = `
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transform: translateX(400px);
    transition: transform 0.3s ease;
    z-index: 10001;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.notification.show {
    transform: translateX(0);
}

.notification-success { background: var(--success-color); }
.notification-error { background: var(--error-color); }
.notification-warning { background: var(--warning-color); }
.notification-info { background: var(--info-color); }

/* PDF Modal Styles */
.pdf-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 10000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.pdf-modal-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(5px);
}

.pdf-modal-content {
    position: relative;
    width: 90%;
    height: 90%;
    max-width: 1200px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.pdf-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    background: #f8f9fa;
    border-bottom: 1px solid #e9ecef;
}

.pdf-modal-header h3 {
    margin: 0;
    color: #495057;
    font-size: 1.25rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.pdf-modal-controls {
    display: flex;
    gap: 0.5rem;
}

.pdf-modal-controls .btn {
    padding: 0.375rem 0.75rem;
    font-size: 0.875rem;
    border-radius: 6px;
    border: 1px solid transparent;
    cursor: pointer;
    transition: all 0.2s;
}

.pdf-modal-controls .btn-secondary {
    background-color: #6c757d;
    color: white;
}

.pdf-modal-controls .btn-success {
    background-color: #28a745;
    color: white;
}

.pdf-modal-controls .btn-danger {
    background-color: #dc3545;
    color: white;
}

.pdf-modal-controls .btn:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

.pdf-modal-body {
    flex: 1;
    padding: 0;
    overflow: hidden;
}

.pdf-modal-body iframe {
    border: none;
    width: 100%;
    height: 100%;
}
`;

// Inject notification styles
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);
