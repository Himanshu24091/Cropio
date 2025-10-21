// Secure PDF JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
        });
    });
    
    // File upload handling
    setupFileUpload('protect-upload-area', 'protect-file');
    setupFileUpload('unlock-upload-area', 'unlock-file');
    setupFileUpload('qr-upload-area', 'qr-file');
    
    // Password strength checker
    setupPasswordStrength();
    
    // Password confirmation checker
    setupPasswordConfirmation();
    
    // PDF security checker
    setupSecurityChecker();
    
    // QR form handling
    setupQRForm();
    
    // Copy URL functionality
    setupCopyURL();
});

function setupFileUpload(areaId, inputId) {
    const uploadArea = document.getElementById(areaId);
    const fileInput = document.getElementById(inputId);
    
    if (!uploadArea || !fileInput) return;
    
    // Click to upload - only trigger on the upload area itself, not the label
    uploadArea.addEventListener('click', (e) => {
        // Prevent double triggering when clicking on label
        if (e.target.tagName.toLowerCase() === 'label' || e.target.closest('label')) {
            return;
        }
        fileInput.click();
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type === 'application/pdf') {
            fileInput.files = files;
            updateUploadArea(uploadArea, files[0].name);
        } else {
            showNotification('Please select a PDF file', 'error');
        }
    });
    
    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            updateUploadArea(uploadArea, e.target.files[0].name);
        }
    });
}

function updateUploadArea(uploadArea, filename) {
    uploadArea.classList.add('file-selected');
    const uploadText = uploadArea.querySelector('.upload-text');
    const uploadSubtext = uploadArea.querySelector('.upload-subtext');
    
    uploadText.textContent = `Selected: ${filename}`;
    uploadSubtext.textContent = 'Click to change file';
}

function setupPasswordStrength() {
    const passwordInput = document.getElementById('password');
    const strengthBar = document.getElementById('strength-bar');
    const strengthText = document.getElementById('strength-text');
    
    if (!passwordInput || !strengthBar || !strengthText) return;
    
    passwordInput.addEventListener('input', (e) => {
        const password = e.target.value;
        const strength = calculatePasswordStrength(password);
        
        // Remove all strength classes
        strengthBar.classList.remove('weak', 'fair', 'good', 'strong');
        
        if (password.length === 0) {
            strengthText.textContent = '';
            return;
        }
        
        switch (strength.level) {
            case 1:
                strengthBar.classList.add('weak');
                strengthText.textContent = 'Weak';
                strengthText.style.color = '#ef4444';
                break;
            case 2:
                strengthBar.classList.add('fair');
                strengthText.textContent = 'Fair';
                strengthText.style.color = '#f59e0b';
                break;
            case 3:
                strengthBar.classList.add('good');
                strengthText.textContent = 'Good';
                strengthText.style.color = '#10b981';
                break;
            case 4:
                strengthBar.classList.add('strong');
                strengthText.textContent = 'Strong';
                strengthText.style.color = '#059669';
                break;
        }
    });
}

function calculatePasswordStrength(password) {
    let score = 0;
    
    // Length check
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    
    // Character variety checks
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    
    // Determine level
    let level = 1;
    if (score >= 3) level = 2;
    if (score >= 5) level = 3;
    if (score >= 6) level = 4;
    
    return { score, level };
}

function setupPasswordConfirmation() {
    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('confirm-password');
    const matchIndicator = document.getElementById('password-match');
    
    if (!passwordInput || !confirmInput || !matchIndicator) return;
    
    function checkPasswordMatch() {
        const password = passwordInput.value;
        const confirm = confirmInput.value;
        
        if (confirm.length === 0) {
            matchIndicator.classList.add('hidden');
            confirmInput.classList.remove('valid', 'invalid');
            return;
        }
        
        matchIndicator.classList.remove('hidden');
        
        if (password === confirm) {
            matchIndicator.textContent = 'Passwords match ✓';
            matchIndicator.classList.remove('password-match-error');
            matchIndicator.classList.add('password-match-success');
            confirmInput.classList.remove('invalid');
            confirmInput.classList.add('valid');
        } else {
            matchIndicator.textContent = 'Passwords do not match';
            matchIndicator.classList.remove('password-match-success');
            matchIndicator.classList.add('password-match-error');
            confirmInput.classList.remove('valid');
            confirmInput.classList.add('invalid');
        }
    }
    
    passwordInput.addEventListener('input', checkPasswordMatch);
    confirmInput.addEventListener('input', checkPasswordMatch);
}

function setupSecurityChecker() {
    const checkBtn = document.getElementById('check-security-btn');
    const unlockFile = document.getElementById('unlock-file');
    const statusDiv = document.getElementById('pdf-security-status');
    const statusText = document.getElementById('security-status-text');
    
    if (!checkBtn || !unlockFile || !statusDiv || !statusText) return;
    
    checkBtn.addEventListener('click', async () => {
        if (!unlockFile.files.length) {
            showNotification('Please select a PDF file first', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', unlockFile.files[0]);
        
        showLoading(true);
        
        try {
            const response = await fetch('/check-pdf-security', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                statusDiv.classList.remove('hidden');
                
                if (result.is_encrypted) {
                    statusText.textContent = 'This PDF is password protected and can be unlocked.';
                    statusDiv.querySelector('svg').style.color = '#f59e0b';
                } else {
                    statusText.textContent = 'This PDF is not password protected.';
                    statusDiv.querySelector('svg').style.color = '#10b981';
                }
            } else {
                showNotification(result.error || 'Error checking PDF security', 'error');
            }
        } catch (error) {
            console.error('Error checking PDF security:', error);
            showNotification('Error checking PDF security', 'error');
        } finally {
            showLoading(false);
        }
    });
}

function setupQRForm() {
    const qrForm = document.getElementById('qr-form');
    const qrResult = document.getElementById('qr-result');
    const qrImage = document.getElementById('qr-image');
    const unlockUrl = document.getElementById('unlock-url');
    
    if (!qrForm) return;
    
    qrForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(qrForm);
        formData.append('action', 'generate_qr');
        
        showLoading(true);
        
        try {
            const response = await fetch('/secure-pdf', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                // Show QR result
                qrResult.classList.remove('hidden');
                qrImage.src = result.qr_url;
                unlockUrl.value = result.unlock_url;
                
                // Scroll to result
                qrResult.scrollIntoView({ behavior: 'smooth' });
                
                showNotification('QR code generated successfully!', 'success');
            } else {
                showNotification(result.error || 'Error generating QR code', 'error');
            }
        } catch (error) {
            console.error('Error generating QR code:', error);
            showNotification('Error generating QR code', 'error');
        } finally {
            showLoading(false);
        }
    });
}

function setupCopyURL() {
    const copyBtn = document.getElementById('copy-url-btn');
    const unlockUrl = document.getElementById('unlock-url');
    
    if (!copyBtn || !unlockUrl) return;
    
    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(unlockUrl.value);
            
            // Visual feedback
            copyBtn.classList.add('copied');
            copyBtn.textContent = 'Copied!';
            
            setTimeout(() => {
                copyBtn.classList.remove('copied');
                copyBtn.textContent = 'Copy URL';
            }, 2000);
            
            showNotification('URL copied to clipboard!', 'success');
        } catch (error) {
            console.error('Error copying URL:', error);
            
            // Fallback: select the text
            unlockUrl.select();
            document.execCommand('copy');
            
            showNotification('URL copied to clipboard!', 'success');
        }
    });
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(n => n.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification flash-message ${type} fixed top-4 right-4 z-50 max-w-sm`;
    notification.innerHTML = `
        <div class="flex items-center">
            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                ${type === 'success' ? 
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>' :
                    '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>'
                }
            </svg>
            <span>${message}</span>
            <button class="ml-2 text-current opacity-50 hover:opacity-100" onclick="this.parentElement.parentElement.remove()">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Prevent form submission if passwords don't match
document.addEventListener('submit', function(e) {
    if (e.target.querySelector('#password') && e.target.querySelector('#confirm-password')) {
        const password = e.target.querySelector('#password').value;
        const confirm = e.target.querySelector('#confirm-password').value;
        
        if (password !== confirm) {
            e.preventDefault();
            showNotification('Passwords do not match', 'error');
        }
    }
});

// Handle flash messages from server
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
});
