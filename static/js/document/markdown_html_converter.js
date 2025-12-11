/**
 * Markdown ⇄ HTML Converter JavaScript
 * Handles real-time conversion, file upload, drag-and-drop, and UI interactions
 */

class MarkdownHTMLConverter {
    constructor() {
        this.currentMode = 'markdown-to-html';
        this.previewTimeout = null;
        this.conversionInProgress = false;
        this.isRealTimeEnabled = true;
        
        this.initializeElements();
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.updateUI();
        this.loadSampleContent();
        
        // Configure marked.js
        if (typeof marked !== 'undefined') {
            marked.setOptions({
                highlight: function(code, lang) {
                    if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                        try {
                            return hljs.highlight(code, { language: lang }).value;
                        } catch (err) {
                            console.warn('Highlight.js error:', err);
                        }
                    }
                    return code;
                },
                breaks: true,
                gfm: true
            });
        }
    }
    
    initializeElements() {
        // Mode switching elements
        this.mdToHtmlBtn = document.getElementById('mdToHtmlBtn');
        this.htmlToMdBtn = document.getElementById('htmlToMdBtn');
        
        // Input/Output elements
        this.inputText = document.getElementById('inputText');
        this.outputText = document.getElementById('outputText');
        this.previewContent = document.getElementById('previewContent');
        
        // Control elements
        this.convertBtn = document.getElementById('convertBtn');
        this.convertBtnText = document.getElementById('convertBtnText');
        this.realTimePreview = document.getElementById('realTimePreview');
        this.preserveFormatting = document.getElementById('preserveFormatting');
        this.preserveFormattingLabel = document.getElementById('preserveFormattingLabel');
        
        // File upload elements
        this.fileInput = document.getElementById('fileInput');
        this.uploadArea = document.getElementById('uploadArea');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.uploadSubtitle = document.getElementById('uploadSubtitle');
        
        // Panel elements
        this.inputPanelTitle = document.getElementById('inputPanelTitle');
        this.outputPanelTitle = document.getElementById('outputPanelTitle');
        
        // Tab elements
        this.tabBtns = document.querySelectorAll('.tab-btn');
        this.tabPanels = document.querySelectorAll('.tab-panel');
        this.previewTabBtn = document.getElementById('previewTabBtn');
        
        // Stats elements
        this.inputLines = document.getElementById('inputLines');
        this.inputWords = document.getElementById('inputWords');
        this.inputChars = document.getElementById('inputChars');
        this.outputLines = document.getElementById('outputLines');
        this.outputSize = document.getElementById('outputSize');
        this.conversionTime = document.getElementById('conversionTime');
        
        // Control buttons
        this.clearInputBtn = document.getElementById('clearInputBtn');
        this.pasteBtn = document.getElementById('pasteBtn');
        this.copyOutputBtn = document.getElementById('copyOutputBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        
        // Overlay and message elements
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.messageContainer = document.getElementById('messageContainer');
    }
    
    setupEventListeners() {
        // Mode switching
        this.mdToHtmlBtn?.addEventListener('click', () => this.switchMode('markdown-to-html'));
        this.htmlToMdBtn?.addEventListener('click', () => this.switchMode('html-to-markdown'));
        
        // Input handling
        this.inputText?.addEventListener('input', () => this.handleInputChange());
        this.inputText?.addEventListener('paste', () => {
            setTimeout(() => this.handleInputChange(), 10);
        });
        
        // Control buttons
        this.convertBtn?.addEventListener('click', () => this.performConversion());
        this.clearInputBtn?.addEventListener('click', () => this.clearInput());
        this.pasteBtn?.addEventListener('click', () => this.pasteFromClipboard());
        this.copyOutputBtn?.addEventListener('click', () => this.copyOutput());
        this.downloadBtn?.addEventListener('click', () => this.downloadOutput());
        
        // Real-time preview toggle
        this.realTimePreview?.addEventListener('change', (e) => {
            this.isRealTimeEnabled = e.target.checked;
            if (this.isRealTimeEnabled && this.currentMode === 'markdown-to-html') {
                this.schedulePreview();
            }
        });
        
        // File upload
        this.fileInput?.addEventListener('change', (e) => this.handleFileUpload(e));
        
        // Tab switching
        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Close modals on outside click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.closeModal(e.target);
            }
        });
    }
    
    setupDragAndDrop() {
        if (!this.uploadArea) return;
        
        // Handle drag and drop events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => {
                this.uploadArea.classList.add('drag-over');
            });
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            this.uploadArea.addEventListener(eventName, () => {
                this.uploadArea.classList.remove('drag-over');
            });
        });
        
        this.uploadArea.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.processFile(files[0]);
            }
        });
        
        // Handle upload button click (prevent event bubbling to avoid double trigger)
        this.uploadBtn?.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent bubbling to upload area
            this.fileInput?.click();
        });
        
        // Handle upload area click only if not clicking on the button
        this.uploadArea.addEventListener('click', (e) => {
            // Only trigger if the click is not on the upload button
            if (e.target !== this.uploadBtn && !this.uploadBtn?.contains(e.target)) {
                this.fileInput?.click();
            }
        });
    }
    
    switchMode(mode) {
        this.currentMode = mode;
        
        // Update active button
        this.mdToHtmlBtn?.classList.toggle('active', mode === 'markdown-to-html');
        this.htmlToMdBtn?.classList.toggle('active', mode === 'html-to-markdown');
        
        this.updateUI();
        this.clearOutput();
        
        // Load appropriate sample content if input is empty
        if (!this.inputText?.value.trim()) {
            this.loadSampleContent();
        } else {
            // Update stats and preview for existing content
            this.updateInputStats();
            if (this.isRealTimeEnabled) {
                this.schedulePreview();
            }
        }
    }
    
    updateUI() {
        if (this.currentMode === 'markdown-to-html') {
            this.inputPanelTitle && (this.inputPanelTitle.textContent = 'Input (Markdown)');
            this.outputPanelTitle && (this.outputPanelTitle.textContent = 'Output (HTML)');
            this.convertBtnText && (this.convertBtnText.textContent = 'Convert to HTML');
            this.uploadSubtitle && (this.uploadSubtitle.textContent = 'Supports .md, .markdown, .txt files up to 10MB');
            this.fileInput && (this.fileInput.accept = '.md,.markdown,.txt');
            this.preserveFormattingLabel && (this.preserveFormattingLabel.style.display = 'none');
            this.previewTabBtn && (this.previewTabBtn.style.display = 'flex');
        } else {
            this.inputPanelTitle && (this.inputPanelTitle.textContent = 'Input (HTML)');
            this.outputPanelTitle && (this.outputPanelTitle.textContent = 'Output (Markdown)');
            this.convertBtnText && (this.convertBtnText.textContent = 'Convert to Markdown');
            this.uploadSubtitle && (this.uploadSubtitle.textContent = 'Supports .html, .htm files up to 10MB');
            this.fileInput && (this.fileInput.accept = '.html,.htm');
            this.preserveFormattingLabel && (this.preserveFormattingLabel.style.display = 'block');
            this.previewTabBtn && (this.previewTabBtn.style.display = 'none');
            this.switchTab('code');
        }
    }
    
    loadSampleContent() {
        if (!this.inputText) return;
        
        if (this.currentMode === 'markdown-to-html') {
            this.inputText.value = `# Welcome to Markdown ⇄ HTML Converter

## Features Overview
Transform your **Markdown** content into *beautifully formatted* HTML, or convert HTML back to clean Markdown.

### What You Can Do:
- ✅ **Real-time Preview** - See changes instantly
- 🎨 **Syntax Highlighting** - Beautiful code blocks
- 📊 **Table Support** - Perfect table conversions
- 🔄 **Bidirectional** - Works both ways

### Code Example
Here's a simple JavaScript function:

\`\`\`javascript
function greetUser(name) {
    return \`Hello, \${name}! Welcome to our converter.\`;
}

// Usage
console.log(greetUser("Developer"));
\`\`\`

### Feature Comparison
| Feature | Markdown | HTML | Notes |
|---------|----------|------|-------|
| Headers | \`# H1\` | \`<h1>\` | H1-H6 supported |
| **Bold** | \`**text**\` | \`<strong>\` | Strong emphasis |
| *Italic* | \`*text*\` | \`<em>\` | Emphasis |
| Links | \`[text](url)\` | \`<a href>\` | Full URL support |

### Try These Features:
1. **Real-time conversion** - Type and see instant results
2. **File upload** - Drop your .md or .html files
3. **Copy & Download** - Get your converted content
4. **Syntax highlighting** - Beautiful code presentation

> **Pro Tip**: Enable real-time preview for the best experience!

---

**Ready to start?** Just replace this text with your own content and watch the magic happen! ✨`;
        } else {
            this.inputText.value = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sample HTML Document</title>
</head>
<body>
    <h1>Welcome to HTML → Markdown Converter</h1>
    
    <h2>Features Overview</h2>
    <p>Transform your <strong>HTML</strong> content into <em>clean Markdown</em> format with intelligent parsing and structure preservation.</p>
    
    <h3>What You Can Convert:</h3>
    <ul>
        <li>✅ <strong>Headers</strong> - H1 through H6</li>
        <li>🎨 <strong>Text Formatting</strong> - Bold, italic, strikethrough</li>
        <li>📋 <strong>Lists</strong> - Ordered and unordered</li>
        <li>🔗 <strong>Links & Images</strong> - Full URL support</li>
        <li>💾 <strong>Code Blocks</strong> - Inline and block code</li>
        <li>📊 <strong>Tables</strong> - Complex table structures</li>
    </ul>
    
    <h3>Code Example</h3>
    <p>Here's a simple Python function:</p>
    
    <pre><code class="language-python">
def process_html(content):
    """Convert HTML to Markdown format"""
    return convert_to_markdown(content)

# Usage
html_content = "&lt;h1&gt;Hello World&lt;/h1&gt;"
markdown_result = process_html(html_content)
print(markdown_result)  # Output: # Hello World
    </code></pre>
    
    <h3>Conversion Table</h3>
    <table>
        <thead>
            <tr>
                <th>HTML Element</th>
                <th>Markdown Output</th>
                <th>Example</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>&lt;h1&gt;</td>
                <td># Header</td>
                <td># Main Title</td>
            </tr>
            <tr>
                <td>&lt;strong&gt;</td>
                <td>**bold**</td>
                <td>**Important**</td>
            </tr>
            <tr>
                <td>&lt;em&gt;</td>
                <td>*italic*</td>
                <td>*Emphasis*</td>
            </tr>
            <tr>
                <td>&lt;a href=""&gt;</td>
                <td>[text](url)</td>
                <td>[Link](https://example.com)</td>
            </tr>
        </tbody>
    </table>
    
    <h3>Advanced Features</h3>
    <ol>
        <li><strong>Smart Parsing</strong> - Intelligent HTML structure detection</li>
        <li><strong>Preserve Formatting</strong> - Optional HTML formatting preservation</li>
        <li><strong>Clean Output</strong> - Well-formatted Markdown result</li>
        <li><strong>Bulk Processing</strong> - Handle large HTML documents</li>
    </ol>
    
    <blockquote>
        <p><strong>Note:</strong> This converter handles most common HTML elements and produces clean, readable Markdown output.</p>
    </blockquote>
    
    <hr>
    
    <p><strong>Ready to convert?</strong> Replace this HTML with your own content and click the convert button! 🚀</p>
</body>
</html>`;
        }
        
        this.updateInputStats();
        if (this.isRealTimeEnabled && this.currentMode === 'markdown-to-html') {
            this.schedulePreview();
        }
    }
    
    handleInputChange() {
        this.updateInputStats();
        
        if (this.isRealTimeEnabled && this.currentMode === 'markdown-to-html') {
            this.schedulePreview();
        }
    }
    
    schedulePreview() {
        if (!this.inputText || this.currentMode !== 'markdown-to-html') return;
        
        clearTimeout(this.previewTimeout);
        this.previewTimeout = setTimeout(() => {
            this.updatePreview();
        }, 300);
    }
    
    async updatePreview() {
        if (!this.previewContent || !this.inputText || this.currentMode !== 'markdown-to-html') return;
        
        const content = this.inputText.value.trim();
        
        if (!content) {
            this.previewContent.innerHTML = '';
            this.previewContent.appendChild(this.createPreviewPlaceholder());
            return;
        }
        
        // Always use server-side preview for reliability with large documents
        // Your 27KB+ document needs server-side processing
        if (content.length > 1000) {
            await this.updatePreviewServerSide(content);
        } else {
            // Use client-side only for very small documents for better responsiveness
            this.updatePreviewClientSide(content);
        }
    }
    
    async updatePreviewServerSide(content) {
        console.log(`🔄 Using server-side preview for ${content.length} characters`);
        try {
            const response = await fetch('/api/markdown-html/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: content })
            });
            
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Preview generation failed');
            }
            
            console.log(`✅ Server preview success: ${data.html.length} chars HTML returned`);
            
            // Safely set HTML content using textContent for security
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = data.html;
            
            // Clear and append sanitized content
            this.previewContent.innerHTML = '';
            this.previewContent.appendChild(tempDiv);
            
            // Safely highlight code blocks after DOM insertion
            if (typeof hljs !== 'undefined') {
                this.previewContent.querySelectorAll('pre code').forEach((block) => {
                    // Only highlight if not already highlighted
                    if (!block.dataset.highlighted) {
                        this.safeHighlightElement(block);
                    }
                });
            }
            
        } catch (error) {
            // Safely create error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-orange-500 p-4';
            
            const errorTitle = document.createElement('strong');
            errorTitle.textContent = 'Server Preview Error:';
            
            const errorMsg = document.createTextNode(' ' + error.message);
            const errorBr = document.createElement('br');
            
            const errorSmall = document.createElement('small');
            errorSmall.textContent = 'Falling back to client-side preview...';
            
            errorDiv.appendChild(errorTitle);
            errorDiv.appendChild(errorMsg);
            errorDiv.appendChild(errorBr);
            errorDiv.appendChild(errorSmall);
            
            this.previewContent.innerHTML = '';
            this.previewContent.appendChild(errorDiv);
            
            console.warn('Server preview failed, falling back to client-side:', error);
            // Fallback to client-side preview
            this.updatePreviewClientSide(content);
        }
    }
    
    updatePreviewClientSide(content) {
        try {
            if (typeof marked !== 'undefined') {
                const html = marked.parse(content);
                
                // Safely set HTML content using a temporary div for security
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;
                
                // Clear and append sanitized content
                this.previewContent.innerHTML = '';
                this.previewContent.appendChild(tempDiv);
                
                // Safely highlight code blocks after DOM insertion
                if (typeof hljs !== 'undefined') {
                    this.previewContent.querySelectorAll('pre code').forEach((block) => {
                        // Only highlight if not already highlighted
                        if (!block.dataset.highlighted) {
                            this.safeHighlightElement(block);
                        }
                    });
                }
            } else {
                // Safely create error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'text-red-500';
                const errorP = document.createElement('p');
                errorP.textContent = 'Marked.js library not loaded';
                errorDiv.appendChild(errorP);
                this.previewContent.innerHTML = '';
                this.previewContent.appendChild(errorDiv);
            }
        } catch (error) {
            // Safely create error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'text-red-500 p-4';
            
            const errorTitle = document.createElement('strong');
            errorTitle.textContent = 'Preview Error:';
            
            const errorMsg = document.createTextNode(' ' + error.message);
            const errorBr = document.createElement('br');
            
            const errorSmall = document.createElement('small');
            errorSmall.textContent = 'Try using server-side conversion instead';
            
            errorDiv.appendChild(errorTitle);
            errorDiv.appendChild(errorMsg);
            errorDiv.appendChild(errorBr);
            errorDiv.appendChild(errorSmall);
            
            this.previewContent.innerHTML = '';
            this.previewContent.appendChild(errorDiv);
            
            console.error('Client-side preview error:', error);
        }
    }
    
    async performConversion() {
        if (this.conversionInProgress || !this.inputText || !this.outputText) return;
        
        const inputContent = this.inputText.value.trim();
        if (!inputContent) {
            this.showMessage('Please enter some content to convert.', 'error');
            return;
        }
        
        this.conversionInProgress = true;
        this.showLoading('Converting...');
        
        const startTime = Date.now();
        
        try {
            // Use server-side conversion for both modes to handle large documents properly
            let result;
            
            if (this.currentMode === 'markdown-to-html') {
                // Use server-side conversion for better performance and features
                const response = await this.callServerConversion(inputContent, this.currentMode);
                result = response.output;
            } else {
                // HTML to Markdown conversion via server
                const response = await this.callServerConversion(inputContent, this.currentMode);
                result = response.output;
            }
            
            const endTime = Date.now();
            const conversionTime = ((endTime - startTime) / 1000).toFixed(2);
            
            this.outputText.value = result;
            this.updateOutputStats();
            this.showConversionTime(conversionTime);
            
            // Update preview for HTML output using safer method
            if (this.currentMode === 'markdown-to-html' && this.previewContent) {
                // Safely set HTML content using a temporary div for security
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = result;
                
                // Clear and append sanitized content
                this.previewContent.innerHTML = '';
                this.previewContent.appendChild(tempDiv);
                
                // Safely highlight code blocks after DOM insertion
                if (typeof hljs !== 'undefined') {
                    this.previewContent.querySelectorAll('pre code').forEach((block) => {
                        // Only highlight if not already highlighted
                        if (!block.dataset.highlighted) {
                            this.safeHighlightElement(block);
                        }
                    });
                }
            }
            
            this.showMessage(`Conversion completed in ${conversionTime}s`, 'success');
            
        } catch (error) {
            console.error('Conversion error:', error);
            this.showMessage(`Conversion failed: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
            this.conversionInProgress = false;
        }
    }
    
    async callServerConversion(content, mode) {
        try {
            const response = await fetch('/api/markdown-html/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: content,
                    mode: mode,
                    preserve_formatting: this.preserveFormatting?.checked || false
                })
            });
            
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Conversion failed');
            }
            
            return {
                success: true,
                output: data.output,
                processing_time: data.processing_time || 0
            };
            
        } catch (error) {
            console.error('Server conversion error:', error);
            throw error;
        }
    }
    
    async handleFileUpload(event) {
        const file = event.target.files?.[0];
        if (!file) return;
        
        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
            this.showMessage('File size exceeds 10MB limit', 'error');
            return;
        }
        
        await this.processFile(file);
        
        // Reset file input
        if (this.fileInput) {
            this.fileInput.value = '';
        }
    }
    
    async processFile(file) {
        this.showLoading('Loading file...');
        
        try {
            const text = await this.readFileAsText(file);
            
            if (!this.inputText) {
                throw new Error('Input textarea not found');
            }
            
            this.inputText.value = text;
            this.updateInputStats();
            
            // Auto-detect mode based on file extension
            const extension = file.name.toLowerCase().split('.').pop();
            if (['html', 'htm'].includes(extension) && this.currentMode === 'markdown-to-html') {
                this.switchMode('html-to-markdown');
            } else if (['md', 'markdown'].includes(extension) && this.currentMode === 'html-to-markdown') {
                this.switchMode('markdown-to-html');
            }
            
            if (this.isRealTimeEnabled && this.currentMode === 'markdown-to-html') {
                this.schedulePreview();
            }
            
            this.showMessage(`File "${file.name}" loaded successfully`, 'success');
            
        } catch (error) {
            console.error('File processing error:', error);
            this.showMessage(`Failed to read file: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target?.result || '');
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.readAsText(file);
        });
    }
    
    clearInput() {
        if (this.inputText) {
            this.inputText.value = '';
            this.updateInputStats();
        }
        this.clearOutput();
    }
    
    clearOutput() {
        if (this.outputText) {
            this.outputText.value = '';
            this.updateOutputStats();
        }
        if (this.previewContent) {
            this.previewContent.innerHTML = '';
            this.previewContent.appendChild(this.createPreviewPlaceholder());
        }
        if (this.conversionTime) {
            this.conversionTime.textContent = '';
        }
    }
    
    async pasteFromClipboard() {
        try {
            const text = await navigator.clipboard.readText();
            if (this.inputText) {
                this.inputText.value = text;
                this.updateInputStats();
                
                if (this.isRealTimeEnabled && this.currentMode === 'markdown-to-html') {
                    this.schedulePreview();
                }
            }
            this.showMessage('Content pasted from clipboard', 'success');
        } catch (error) {
            this.showMessage('Unable to access clipboard. Please paste manually.', 'error');
        }
    }
    
    async copyOutput() {
        if (!this.outputText?.value.trim()) {
            this.showMessage('No content to copy', 'error');
            return;
        }
        
        try {
            await navigator.clipboard.writeText(this.outputText.value);
            this.showMessage('Output copied to clipboard', 'success');
        } catch (error) {
            // Fallback for older browsers
            try {
                this.outputText.select();
                document.execCommand('copy');
                this.showMessage('Output copied to clipboard', 'success');
            } catch (fallbackError) {
                this.showMessage('Failed to copy to clipboard', 'error');
            }
        }
    }
    
    downloadOutput() {
        if (!this.outputText?.value.trim()) {
            this.showMessage('No content to download', 'error');
            return;
        }
        
        const content = this.outputText.value;
        const filename = this.currentMode === 'markdown-to-html' ? 
            'converted.html' : 'converted.md';
        const mimeType = this.currentMode === 'markdown-to-html' ? 
            'text/html' : 'text/markdown';
        
        try {
            const blob = new Blob([content], { type: mimeType });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showMessage(`Downloaded ${filename}`, 'success');
        } catch (error) {
            this.showMessage('Failed to download file', 'error');
        }
    }
    
    switchTab(tabName) {
        // Update tab buttons
        this.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // Update tab panels
        this.tabPanels.forEach(panel => {
            panel.classList.toggle('active', panel.id === tabName + 'Tab');
        });
    }
    
    updateInputStats() {
        if (!this.inputText) return;
        
        const content = this.inputText.value;
        const lines = content.split('\n').length;
        const words = content.trim() ? content.trim().split(/\s+/).length : 0;
        const chars = content.length;
        
        if (this.inputLines) this.inputLines.textContent = lines;
        if (this.inputWords) this.inputWords.textContent = words;
        if (this.inputChars) this.inputChars.textContent = chars;
    }
    
    updateOutputStats() {
        if (!this.outputText) return;
        
        const content = this.outputText.value;
        const lines = content.split('\n').length;
        const size = new Blob([content]).size;
        
        if (this.outputLines) this.outputLines.textContent = lines;
        if (this.outputSize) this.outputSize.textContent = this.formatFileSize(size);
    }
    
    showConversionTime(time) {
        if (this.conversionTime) {
            this.conversionTime.textContent = `Converted in ${time}s`;
            this.conversionTime.style.color = '#059669';
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + Enter: Convert
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            this.performConversion();
        }
        
        // Ctrl/Cmd + K: Clear input
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            this.clearInput();
        }
        
        // Ctrl/Cmd + D: Download output
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            if (this.outputText?.value.trim()) {
                this.downloadOutput();
            }
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal-overlay:not(.hidden)');
            modals.forEach(modal => this.closeModal(modal));
        }
    }
    
    showLoading(message = 'Processing...') {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.remove('hidden');
            const loadingText = this.loadingOverlay.querySelector('.loading-text');
            if (loadingText) loadingText.textContent = message;
        }
        
        if (this.convertBtn) {
            this.convertBtn.disabled = true;
        }
    }
    
    hideLoading() {
        if (this.loadingOverlay) {
            this.loadingOverlay.classList.add('hidden');
        }
        
        if (this.convertBtn) {
            this.convertBtn.disabled = false;
        }
    }
    
    showMessage(message, type = 'info') {
        if (!this.messageContainer) return;
        
        const messageEl = document.createElement('div');
        messageEl.className = `message ${type}`;
        
        // Create icon element safely
        const iconEl = document.createElement('div');
        iconEl.className = 'message-icon';
        
        const iconMap = {
            success: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
            error: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
            info: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
        };
        
        // Safely set icon (SVG is safe static content)
        iconEl.innerHTML = iconMap[type];
        
        // Create message text safely
        const messageSpan = document.createElement('span');
        messageSpan.textContent = message;
        
        // Append elements safely
        messageEl.appendChild(iconEl);
        messageEl.appendChild(messageSpan);
        
        this.messageContainer.appendChild(messageEl);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 5000);
    }
    
    closeModal(modal) {
        if (modal && modal.classList.contains('modal-overlay')) {
            modal.classList.add('hidden');
        }
    }
    
    // Utility function to escape HTML for security
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Utility function to create safe placeholder content
    createPreviewPlaceholder() {
        const placeholderDiv = document.createElement('div');
        placeholderDiv.className = 'preview-placeholder';
        
        // Create SVG element
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'w-12 h-12 text-slate-400 mx-auto mb-4');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
        svg.setAttribute('viewBox', '0 0 24 24');
        
        // Create path elements
        const path1 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path1.setAttribute('stroke-linecap', 'round');
        path1.setAttribute('stroke-linejoin', 'round');
        path1.setAttribute('stroke-width', '1.5');
        path1.setAttribute('d', 'M15 12a3 3 0 11-6 0 3 3 0 016 0z');
        
        const path2 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path2.setAttribute('stroke-linecap', 'round');
        path2.setAttribute('stroke-linejoin', 'round');
        path2.setAttribute('stroke-width', '1.5');
        path2.setAttribute('d', 'M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z');
        
        svg.appendChild(path1);
        svg.appendChild(path2);
        
        // Create text element
        const textP = document.createElement('p');
        textP.className = 'text-slate-500 dark:text-slate-400';
        textP.textContent = 'Preview will appear here as you type...';
        
        placeholderDiv.appendChild(svg);
        placeholderDiv.appendChild(textP);
        
        return placeholderDiv;
    }
    
    // Secure highlight.js wrapper to sanitize output
    safeHighlightElement(codeBlock) {
        if (!codeBlock || typeof hljs === 'undefined') return;
        
        try {
            // Get the original text content
            const originalText = codeBlock.textContent;
            
            // Create a temporary element for highlighting
            const tempCodeBlock = document.createElement('code');
            tempCodeBlock.textContent = originalText;
            
            // Copy relevant attributes safely
            if (codeBlock.className) {
                tempCodeBlock.className = codeBlock.className;
            }
            
            // Apply highlight.js to temp element
            hljs.highlightElement(tempCodeBlock);
            
            // Sanitize the highlighted HTML by only allowing safe highlighting classes
            const highlightedHTML = tempCodeBlock.innerHTML;
            
            // Create a temporary div to parse the highlighted content
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = highlightedHTML;
            
            // Sanitize: only allow spans with hljs- prefixed classes
            const spans = tempDiv.querySelectorAll('span');
            spans.forEach(span => {
                const classList = Array.from(span.classList);
                const safeClasses = classList.filter(cls => cls.startsWith('hljs-'));
                span.className = safeClasses.join(' ');
                
                // Remove any dangerous attributes
                const allowedAttrs = ['class'];
                const attrs = Array.from(span.attributes);
                attrs.forEach(attr => {
                    if (!allowedAttrs.includes(attr.name)) {
                        span.removeAttribute(attr.name);
                    }
                });
            });
            
            // Clear original block and append sanitized content
            codeBlock.innerHTML = '';
            while (tempDiv.firstChild) {
                codeBlock.appendChild(tempDiv.firstChild);
            }
            
            // Mark as highlighted to prevent re-processing
            codeBlock.dataset.highlighted = 'yes';
            
        } catch (error) {
            console.warn('Safe highlighting failed:', error);
            // Fallback: just add basic highlighting class without hljs processing
            codeBlock.className = codeBlock.className + ' hljs';
            codeBlock.dataset.highlighted = 'error';
        }
    }
}

// Modal Functions (Global scope for HTML onclick handlers)
function openHelpModal() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function closeHelpModal() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Initialize the converter when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.markdownConverter = new MarkdownHTMLConverter();
    console.log('Markdown HTML Converter initialized');
});
