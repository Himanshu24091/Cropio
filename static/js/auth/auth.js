/**
 * Authentication Pages JavaScript
 * Handles login, registration, and password management functionality
 */

// Password visibility toggle functionality
function togglePassword(inputId, button) {
    const input = document.getElementById(inputId);
    const icon = button.querySelector('.password-icon');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.textContent = '🙈';
        button.setAttribute('aria-label', 'Hide password');
    } else {
        input.type = 'password';
        icon.textContent = '👁️';
        button.setAttribute('aria-label', 'Show password');
    }
}

// Password strength checker
function checkPasswordStrength(password) {
    let strength = 0;
    let feedback = [];

    if (password.length >= 8) strength++;
    else feedback.push('At least 8 characters');

    if (/[a-z]/.test(password)) strength++;
    else feedback.push('Lowercase letter');

    if (/[A-Z]/.test(password)) strength++;
    else feedback.push('Uppercase letter');

    if (/[0-9]/.test(password)) strength++;
    else feedback.push('Number');

    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    else feedback.push('Special character');

    let strengthText, strengthClass;
    if (strength < 2) {
        strengthText = 'Weak';
        strengthClass = 'strength-weak';
    } else if (strength < 4) {
        strengthText = 'Medium';
        strengthClass = 'strength-medium';
    } else {
        strengthText = 'Strong';
        strengthClass = 'strength-strong';
    }

    return { strength, text: strengthText, class: strengthClass, feedback };
}

// Update password strength indicator
function updatePasswordStrength(passwordInput, strengthElement) {
    const password = passwordInput.value;
    
    if (password.length === 0) {
        strengthElement.innerHTML = '';
        passwordInput.classList.remove('error', 'success');
        return;
    }
    
    const result = checkPasswordStrength(password);
    
    let html = `<span class="${result.class}">Password strength: ${result.text}</span>`;
    if (result.feedback.length > 0 && result.strength < 4) {
        html += `<br><span class="text-gray-500 text-xs">Missing: ${result.feedback.join(', ')}</span>`;
    }
    
    strengthElement.innerHTML = html;
    
    if (result.strength < 2) {
        passwordInput.classList.add('error');
        passwordInput.classList.remove('success');
    } else if (result.strength >= 4) {
        passwordInput.classList.remove('error');
        passwordInput.classList.add('success');
    } else {
        passwordInput.classList.remove('error', 'success');
    }
}

// Check password match
function checkPasswordMatch(newPassword, confirmPassword, matchElement) {
    if (confirmPassword.length === 0) {
        matchElement.innerHTML = '';
        return true;
    }

    if (newPassword === confirmPassword) {
        matchElement.innerHTML = '<span class="validation-success">✓ Passwords match</span>';
        return true;
    } else {
        matchElement.innerHTML = '<span class="validation-error">❌ Passwords do not match</span>';
        return false;
    }
}

// Email validation
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Username validation
function validateUsername(username) {
    if (username.length < 3) return { valid: false, message: 'Username must be at least 3 characters long' };
    if (username.length > 20) return { valid: false, message: 'Username must be less than 20 characters' };
    if (!/^[a-zA-Z0-9_]+$/.test(username)) return { valid: false, message: 'Username can only contain letters, numbers, and underscores' };
    return { valid: true, message: '✓ Username looks good' };
}

// Set input validation state
function setInputValidation(input, validationElement, isValid, message) {
    if (isValid) {
        input.classList.remove('error');
        input.classList.add('success');
        validationElement.innerHTML = `<span class="validation-success">${message}</span>`;
    } else {
        input.classList.add('error');
        input.classList.remove('success');
        validationElement.innerHTML = `<span class="validation-error">${message}</span>`;
    }
}

// Show loading state on button
function showButtonLoading(button, originalText) {
    button.classList.add('loading');
    button.disabled = true;
    button.setAttribute('data-original-text', originalText);
    button.textContent = 'Processing...';
}

// Hide loading state on button
function hideButtonLoading(button) {
    button.classList.remove('loading');
    button.disabled = false;
    const originalText = button.getAttribute('data-original-text');
    if (originalText) {
        button.textContent = originalText;
        button.removeAttribute('data-original-text');
    }
}

// Login page initialization
function initLoginPage() {
    const form = document.querySelector('#loginForm, form[action*="login"]');
    const usernameInput = document.getElementById('username_or_email');
    const passwordInput = document.getElementById('password');
    const submitBtn = form?.querySelector('button[type="submit"]');

    if (!form || !usernameInput || !passwordInput) return;

    // Auto-focus on first empty input
    if (!usernameInput.value) {
        usernameInput.focus();
    }

    // Form submission handling
    form.addEventListener('submit', function(e) {
        const username = usernameInput.value.trim();
        const password = passwordInput.value;
        
        if (!username || !password) {
            e.preventDefault();
            alert('Please fill in all fields');
            return;
        }
        
        if (username.length < 3) {
            e.preventDefault();
            alert('Username or email must be at least 3 characters long');
            usernameInput.focus();
            return;
        }

        if (submitBtn) {
            showButtonLoading(submitBtn, submitBtn.textContent);
        }
    });

    // Real-time validation
    usernameInput.addEventListener('blur', function() {
        const value = this.value.trim();
        if (value && value.length < 3) {
            this.classList.add('error');
        } else if (value) {
            this.classList.remove('error');
            this.classList.add('success');
        }
    });
}

// Registration page initialization
function initRegisterPage() {
    const form = document.getElementById('registerForm');
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const submitBtn = document.getElementById('submitBtn');
    const termsCheckbox = document.getElementById('terms_accepted');

    if (!form) return;

    // Validation elements
    const usernameValidation = document.getElementById('usernameValidation');
    const emailValidation = document.getElementById('emailValidation');
    const passwordStrength = document.getElementById('passwordStrength');
    const confirmPasswordValidation = document.getElementById('confirmPasswordValidation');

    // Username validation
    if (usernameInput && usernameValidation) {
        usernameInput.addEventListener('input', function() {
            const validation = validateUsername(this.value.trim());
            setInputValidation(this, usernameValidation, validation.valid, validation.message);
        });
    }

    // Email validation
    if (emailInput && emailValidation) {
        emailInput.addEventListener('input', function() {
            const isValid = validateEmail(this.value.trim());
            const message = isValid ? '✓ Email looks good' : 'Please enter a valid email address';
            setInputValidation(this, emailValidation, isValid, message);
        });
    }

    // Password strength validation
    if (passwordInput && passwordStrength) {
        passwordInput.addEventListener('input', function() {
            updatePasswordStrength(this, passwordStrength);
            // Also check confirm password if it has a value
            if (confirmPasswordInput && confirmPasswordInput.value && confirmPasswordValidation) {
                const match = checkPasswordMatch(this.value, confirmPasswordInput.value, confirmPasswordValidation);
                confirmPasswordInput.classList.toggle('success', match);
                confirmPasswordInput.classList.toggle('error', !match);
            }
        });
    }

    // Confirm password validation
    if (confirmPasswordInput && confirmPasswordValidation && passwordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            const match = checkPasswordMatch(passwordInput.value, this.value, confirmPasswordValidation);
            this.classList.toggle('success', match);
            this.classList.toggle('error', !match);
        });
    }

    // Form submission validation
    form.addEventListener('submit', function(e) {
        let isValid = true;
        const errors = [];

        // Validate all inputs
        if (usernameInput) {
            const validation = validateUsername(usernameInput.value.trim());
            if (!validation.valid) {
                isValid = false;
                errors.push('Username: ' + validation.message);
                usernameInput.classList.add('error');
            }
        }

        if (emailInput && !validateEmail(emailInput.value.trim())) {
            isValid = false;
            errors.push('Please enter a valid email address');
            emailInput.classList.add('error');
        }

        if (passwordInput) {
            const result = checkPasswordStrength(passwordInput.value);
            if (result.strength < 2) {
                isValid = false;
                errors.push('Password is too weak');
                passwordInput.classList.add('error');
            }
        }

        if (confirmPasswordInput && passwordInput && passwordInput.value !== confirmPasswordInput.value) {
            isValid = false;
            errors.push('Passwords do not match');
            confirmPasswordInput.classList.add('error');
        }

        if (termsCheckbox && !termsCheckbox.checked) {
            isValid = false;
            errors.push('Please accept the Terms of Service and Privacy Policy');
        }

        if (!isValid) {
            e.preventDefault();
            if (submitBtn) {
                submitBtn.textContent = 'Please fix errors above';
                submitBtn.classList.add('error');
                setTimeout(() => {
                    submitBtn.textContent = 'Create Account';
                    submitBtn.classList.remove('error');
                }, 3000);
            }
            
            // Show first error in alert
            if (errors.length > 0) {
                alert(errors[0]);
            }
        } else if (submitBtn) {
            showButtonLoading(submitBtn, submitBtn.textContent);
        }
    });
}

// Change password page initialization
function initChangePasswordPage() {
    const form = document.getElementById('changePasswordForm');
    const currentPasswordInput = document.getElementById('currentPassword');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    
    if (!form) return;

    const passwordStrengthElement = document.getElementById('passwordStrengthText');
    const passwordMatchElement = document.getElementById('passwordMatch');

    // New password strength checking
    if (newPasswordInput && passwordStrengthElement) {
        newPasswordInput.addEventListener('input', function() {
            updatePasswordStrengthIndicator(this.value, passwordStrengthElement);
            if (confirmPasswordInput && passwordMatchElement) {
                checkPasswordMatchIndicator(this.value, confirmPasswordInput.value, passwordMatchElement);
            }
        });
    }

    // Confirm password matching
    if (confirmPasswordInput && passwordMatchElement && newPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            checkPasswordMatchIndicator(newPasswordInput.value, this.value, passwordMatchElement);
        });
    }
}

// Update password strength indicator for change password page
function updatePasswordStrengthIndicator(password, strengthTextElement) {
    const strengthBars = document.querySelectorAll('#passwordStrength div');
    
    if (password.length === 0) {
        strengthBars.forEach(bar => bar.className = 'h-2 w-full bg-slate-200 dark:bg-slate-600 rounded');
        strengthTextElement.textContent = 'Enter a password';
        strengthTextElement.style.color = '';
        return;
    }
    
    const result = checkPasswordStrength(password);
    
    let color = '#ef4444'; // red
    if (result.strength >= 4) color = '#16a34a'; // green
    else if (result.strength >= 3) color = '#22c55e'; // light green
    else if (result.strength >= 2) color = '#eab308'; // yellow
    
    strengthBars.forEach((bar, index) => {
        if (index < result.strength) {
            bar.style.backgroundColor = color;
            bar.className = 'h-2 w-full rounded';
        } else {
            bar.className = 'h-2 w-full bg-slate-200 dark:bg-slate-600 rounded';
        }
    });
    
    strengthTextElement.textContent = result.text;
    strengthTextElement.style.color = color;
}

// Check password match for change password page
function checkPasswordMatchIndicator(newPassword, confirmPassword, matchElement) {
    const matchIcon = document.getElementById('matchIcon');
    const matchText = document.getElementById('matchText');

    if (!matchIcon || !matchText) return;

    if (confirmPassword.length === 0) {
        matchElement.classList.add('hidden');
        return;
    }

    matchElement.classList.remove('hidden');

    if (newPassword === confirmPassword) {
        matchIcon.textContent = '✅';
        matchText.textContent = 'Passwords match';
        matchText.className = 'text-sm text-green-600 dark:text-green-400';
    } else {
        matchIcon.textContent = '❌';
        matchText.textContent = 'Passwords do not match';
        matchText.className = 'text-sm text-red-600 dark:text-red-400';
    }
}

// Delete account page initialization
function initDeleteAccountPage() {
    const form = document.getElementById('deleteAccountForm');
    if (!form) return;

    const deleteButton = document.getElementById('deleteButton');
    const confirmDelete = document.getElementById('confirmDelete');
    const confirmNoBackup = document.getElementById('confirmNoBackup');
    const typeDeleteInput = document.getElementById('typeDelete');

    function validateDeleteForm() {
        const isValid = confirmDelete?.checked && 
                       confirmNoBackup?.checked && 
                       typeDeleteInput?.value.trim().toUpperCase() === 'DELETE';
        
        if (deleteButton) {
            deleteButton.disabled = !isValid;
            deleteButton.classList.toggle('bg-red-400', !isValid);
            deleteButton.classList.toggle('cursor-not-allowed', !isValid);
            deleteButton.classList.toggle('bg-red-600', isValid);
            deleteButton.classList.toggle('hover:bg-red-700', isValid);
        }
    }

    // Add event listeners for validation
    [confirmDelete, confirmNoBackup, typeDeleteInput].forEach(element => {
        if (element) {
            element.addEventListener('change', validateDeleteForm);
            element.addEventListener('input', validateDeleteForm);
        }
    });

    // Form submission confirmation
    form.addEventListener('submit', function(e) {
        if (!confirm('Are you absolutely sure you want to delete your account? This action cannot be undone!')) {
            e.preventDefault();
            return false;
        }
        
        if (deleteButton) {
            deleteButton.disabled = true;
            deleteButton.innerHTML = '⏳ Deleting Account...';
        }
    });

    // Initial validation
    validateDeleteForm();
}

// Initialize authentication pages based on current page
document.addEventListener('DOMContentLoaded', function() {
    // Determine which page we're on and initialize accordingly
    const currentPath = window.location.pathname;
    
    if (currentPath.includes('/login')) {
        initLoginPage();
    } else if (currentPath.includes('/register')) {
        initRegisterPage();
    } else if (currentPath.includes('/change-password')) {
        initChangePasswordPage();
    } else if (currentPath.includes('/delete-account')) {
        initDeleteAccountPage();
    }

    // Initialize password toggles for any page
    document.querySelectorAll('.password-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const inputId = this.getAttribute('data-target');
            if (inputId) {
                togglePassword(inputId, this);
            }
        });
    });

    // Add ARIA labels to password toggles
    document.querySelectorAll('.password-toggle').forEach(button => {
        button.setAttribute('aria-label', 'Show password');
        button.setAttribute('type', 'button');
    });

    // Enhanced form validation feedback
    document.querySelectorAll('.form-input').forEach(input => {
        // Remove error class on focus
        input.addEventListener('focus', function() {
            this.classList.remove('error');
        });

        // Add subtle animations for better UX
        input.addEventListener('blur', function() {
            if (this.value.trim() === '' && this.hasAttribute('required')) {
                this.classList.add('error');
            }
        });
    });

    // Keyboard navigation improvements
    document.addEventListener('keydown', function(e) {
        // Enter key in form inputs should submit the form
        if (e.key === 'Enter' && e.target.classList.contains('form-input')) {
            const form = e.target.closest('form');
            if (form) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    submitBtn.click();
                }
            }
        }
    });
});

// Export functions for global use
window.AuthJS = {
    togglePassword,
    checkPasswordStrength,
    updatePasswordStrength,
    validateEmail,
    validateUsername,
    showButtonLoading,
    hideButtonLoading
};
