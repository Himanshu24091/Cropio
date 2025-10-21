/**
 * Authentication Pages JavaScript
 * Handles login, register, profile forms and validation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all auth page functionality
    initializeFormValidation();
    initializePasswordStrength();
    initializeUIEnhancements();
    initializeFormSubmission();
});

/**
 * Form validation functionality
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input[required]');
        
        inputs.forEach(input => {
            // Real-time validation on input
            input.addEventListener('input', function() {
                validateField(this);
            });
            
            // Validation on blur
            input.addEventListener('blur', function() {
                validateField(this);
            });
        });
        
        // Form submission validation
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                showFormError('Please fix the errors above before submitting.');
            }
        });
    });
}

/**
 * Validate individual form field
 */
function validateField(field) {
    const fieldType = field.type;
    const fieldName = field.name;
    const value = field.value.trim();
    let isValid = true;
    let message = '';

    // Clear previous validation
    clearFieldValidation(field);

    if (field.hasAttribute('required') && !value) {
        isValid = false;
        message = 'This field is required';
    } else if (value) {
        switch (fieldType) {
            case 'email':
                isValid = validateEmail(value);
                message = isValid ? '' : 'Please enter a valid email address';
                break;
                
            case 'password':
                if (fieldName === 'password') {
                    const result = validatePassword(value);
                    isValid = result.isValid;
                    message = result.message;
                    updatePasswordStrength(field, result.strength);
                } else if (fieldName === 'confirm_password') {
                    const passwordField = document.querySelector('input[name="password"]');
                    isValid = passwordField && value === passwordField.value;
                    message = isValid ? '' : 'Passwords do not match';
                }
                break;
                
            case 'text':
                if (fieldName === 'username') {
                    const result = validateUsername(value);
                    isValid = result.isValid;
                    message = result.message;
                }
                break;
        }
    }

    // Show validation result
    if (!isValid && message) {
        showFieldError(field, message);
    } else if (isValid && value) {
        showFieldSuccess(field);
    }

    return isValid;
}

/**
 * Validate entire form
 */
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required]');
    let allValid = true;

    inputs.forEach(input => {
        if (!validateField(input)) {
            allValid = false;
        }
    });

    // Special case: password confirmation
    const passwordField = form.querySelector('input[name="password"]');
    const confirmField = form.querySelector('input[name="confirm_password"]');
    
    if (passwordField && confirmField) {
        if (passwordField.value !== confirmField.value) {
            showFieldError(confirmField, 'Passwords do not match');
            allValid = false;
        }
    }

    return allValid;
}

/**
 * Email validation
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Username validation
 */
function validateUsername(username) {
    let isValid = true;
    let message = '';

    if (username.length < 3) {
        isValid = false;
        message = 'Username must be at least 3 characters long';
    } else if (username.length > 20) {
        isValid = false;
        message = 'Username must be no more than 20 characters long';
    } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
        isValid = false;
        message = 'Username can only contain letters, numbers, and underscores';
    }

    return { isValid, message };
}

/**
 * Password validation and strength checking
 */
function validatePassword(password) {
    let isValid = true;
    let message = '';
    let strength = 0;
    let strengthText = '';

    if (password.length < 6) {
        isValid = false;
        message = 'Password must be at least 6 characters long';
    } else {
        // Calculate strength
        if (password.length >= 8) strength++;
        if (/[a-z]/.test(password)) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) strength++;

        switch (strength) {
            case 0:
            case 1:
                strengthText = 'Weak';
                break;
            case 2:
            case 3:
                strengthText = 'Medium';
                break;
            case 4:
            case 5:
                strengthText = 'Strong';
                break;
        }
    }

    return { isValid, message, strength, strengthText };
}

/**
 * Password strength indicator
 */
function initializePasswordStrength() {
    const passwordInputs = document.querySelectorAll('input[name="password"]');
    
    passwordInputs.forEach(input => {
        const strengthIndicator = document.getElementById('passwordStrength');
        if (strengthIndicator) {
            input.addEventListener('input', function() {
                const result = validatePassword(this.value);
                updatePasswordStrength(this, result.strength);
            });
        }
    });
}

function updatePasswordStrength(field, strength) {
    const strengthIndicator = document.getElementById('passwordStrength');
    if (!strengthIndicator) return;

    const strengthTexts = ['', 'Very Weak', 'Weak', 'Medium', 'Strong', 'Very Strong'];
    const strengthClasses = ['', 'very-weak', 'weak', 'medium', 'strong', 'very-strong'];

    strengthIndicator.className = `password-strength ${strengthClasses[strength] || ''}`;
    strengthIndicator.textContent = strength > 0 ? `Password strength: ${strengthTexts[strength]}` : '';
}

/**
 * Field validation UI
 */
function showFieldError(field, message) {
    clearFieldValidation(field);
    field.classList.add('error');
    
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    
    field.parentNode.appendChild(errorElement);
}

function showFieldSuccess(field) {
    clearFieldValidation(field);
    field.classList.add('success');
}

function clearFieldValidation(field) {
    field.classList.remove('error', 'success');
    
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

function showFormError(message) {
    // Remove existing form errors
    const existingError = document.querySelector('.form-error');
    if (existingError) {
        existingError.remove();
    }

    // Create and show new error
    const errorElement = document.createElement('div');
    errorElement.className = 'alert alert-error form-error';
    errorElement.textContent = message;

    const form = document.querySelector('form');
    if (form) {
        form.insertBefore(errorElement, form.firstChild);
    }
}

/**
 * UI Enhancements
 */
function initializeUIEnhancements() {
    // Toggle password visibility
    addPasswordToggle();
    
    // Loading states
    initializeLoadingStates();
    
    // Auto-hide flash messages
    autoHideFlashMessages();
}

function addPasswordToggle() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
        const container = input.parentNode;
        container.style.position = 'relative';
        
        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'password-toggle';
        toggleButton.innerHTML = '👁️';
        toggleButton.title = 'Show/hide password';
        
        toggleButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (input.type === 'password') {
                input.type = 'text';
                this.innerHTML = '🙈';
                this.title = 'Hide password';
            } else {
                input.type = 'password';
                this.innerHTML = '👁️';
                this.title = 'Show password';
            }
        });
        
        container.appendChild(toggleButton);
    });
}

function initializeLoadingStates() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.textContent;
                submitButton.textContent = 'Processing...';
                submitButton.disabled = true;
                
                // Re-enable after 10 seconds as fallback
                setTimeout(() => {
                    submitButton.textContent = originalText;
                    submitButton.disabled = false;
                }, 10000);
            }
        });
    });
}

function autoHideFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert');
    
    flashMessages.forEach(alert => {
        // Add close button
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '×';
        closeButton.className = 'alert-close';
        closeButton.addEventListener('click', function() {
            alert.remove();
        });
        alert.appendChild(closeButton);
        
        // Auto-hide success messages after 5 seconds
        if (alert.classList.contains('alert-success')) {
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.style.opacity = '0';
                    setTimeout(() => {
                        if (alert.parentNode) {
                            alert.remove();
                        }
                    }, 300);
                }
            }, 5000);
        }
    });
}

/**
 * Form submission enhancements
 */
function initializeFormSubmission() {
    // Prevent double submission
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        let isSubmitting = false;
        
        form.addEventListener('submit', function(e) {
            if (isSubmitting) {
                e.preventDefault();
                return false;
            }
            
            if (validateForm(this)) {
                isSubmitting = true;
            } else {
                e.preventDefault();
            }
        });
    });
}

/**
 * Utility functions
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export for use in other scripts if needed
window.AuthJS = {
    validateEmail,
    validateUsername,
    validatePassword,
    validateForm,
    showFieldError,
    showFieldSuccess,
    clearFieldValidation
};
