/**
 * Password Strength Checker
 * Provides real-time password strength validation with visual feedback
 */

class PasswordStrengthChecker {
    constructor(passwordInputId, strengthIndicatorId, requirementsListId) {
        this.passwordInput = document.getElementById(passwordInputId);
        this.strengthIndicator = document.getElementById(strengthIndicatorId);
        this.requirementsList = document.getElementById(requirementsListId);

        if (this.passwordInput) {
            this.init();
        }
    }

    init() {
        this.passwordInput.addEventListener('input', () => this.checkStrength());
        this.passwordInput.addEventListener('focus', () => this.showRequirements());
        this.passwordInput.addEventListener('blur', () => this.hideRequirements());
    }

    checkStrength() {
        const password = this.passwordInput.value;
        const strength = this.calculateStrength(password);
        this.updateUI(strength, password);
    }

    calculateStrength(password) {
        const requirements = {
            length: password.length >= 8,
            lowercase: /[a-z]/.test(password),
            uppercase: /[A-Z]/.test(password),
            number: /[0-9]/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };

        const score = Object.values(requirements).filter(Boolean).length;

        let strength = {
            score: score,
            level: 'weak',
            color: '#ef4444',
            text: 'Weak',
            percentage: 0,
            requirements: requirements
        };

        if (score === 5) {
            strength = {
                ...strength,
                level: 'strong',
                color: '#22c55e',
                text: 'Strong',
                percentage: 100
            };
        } else if (score >= 3) {
            strength = {
                ...strength,
                level: 'medium',
                color: '#f59e0b',
                text: 'Medium',
                percentage: 60
            };
        } else if (score > 0) {
            strength = {
                ...strength,
                level: 'weak',
                color: '#ef4444',
                text: 'Weak',
                percentage: 30
            };
        }

        return strength;
    }

    updateUI(strength, password) {
        if (!this.strengthIndicator) return;

        // Update strength bar
        const bar = this.strengthIndicator.querySelector('.strength-bar');
        const text = this.strengthIndicator.querySelector('.strength-text');

        if (bar && password.length > 0) {
            bar.style.width = strength.percentage + '%';
            bar.style.backgroundColor = strength.color;
            this.strengthIndicator.style.display = 'block';
        } else {
            this.strengthIndicator.style.display = 'none';
        }

        if (text) {
            text.textContent = strength.text;
            text.style.color = strength.color;
        }

        // Update requirements list
        if (this.requirementsList && password.length > 0) {
            this.updateRequirements(strength.requirements);
        }
    }

    updateRequirements(requirements) {
        const items = {
            length: this.requirementsList.querySelector('[data-requirement="length"]'),
            lowercase: this.requirementsList.querySelector('[data-requirement="lowercase"]'),
            uppercase: this.requirementsList.querySelector('[data-requirement="uppercase"]'),
            number: this.requirementsList.querySelector('[data-requirement="number"]'),
            special: this.requirementsList.querySelector('[data-requirement="special"]')
        };

        Object.keys(requirements).forEach(key => {
            const item = items[key];
            if (item) {
                const icon = item.querySelector('.requirement-icon');
                if (requirements[key]) {
                    item.classList.add('met');
                    item.classList.remove('unmet');
                    if (icon) icon.textContent = '✓';
                } else {
                    item.classList.add('unmet');
                    item.classList.remove('met');
                    if (icon) icon.textContent = '○';
                }
            }
        });
    }

    showRequirements() {
        if (this.requirementsList) {
            this.requirementsList.style.display = 'block';
        }
    }

    hideRequirements() {
        // Keep visible if password is being entered
        if (this.passwordInput.value.length === 0 && this.requirementsList) {
            setTimeout(() => {
                if (document.activeElement !== this.passwordInput) {
                    this.requirementsList.style.display = 'none';
                }
            }, 200);
        }
    }

    isStrong() {
        const password = this.passwordInput.value;
        const strength = this.calculateStrength(password);
        return strength.score >= 4; // At least 4 out of 5 requirements
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    // For registration page
    if (document.getElementById('password')) {
        window.passwordChecker = new PasswordStrengthChecker(
            'password',
            'passwordStrength',
            'passwordRequirements'
        );

        // Add form submission validation for registration
        const registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', function (e) {
                if (!window.passwordChecker.isStrong()) {
                    e.preventDefault();

                    // Show error message
                    const existingError = document.getElementById('weakPasswordError');
                    if (existingError) {
                        existingError.remove();
                    }

                    const errorDiv = document.createElement('div');
                    errorDiv.id = 'weakPasswordError';
                    errorDiv.className = 'alert alert-error';
                    errorDiv.style.marginBottom = '1rem';
                    errorDiv.innerHTML = '⚠️ <strong>Weak Password:</strong> Your password must meet all requirements above. Please create a stronger password.';

                    registerForm.insertBefore(errorDiv, registerForm.firstChild);

                    // Scroll to error
                    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });

                    // Show requirements if hidden
                    const requirements = document.getElementById('passwordRequirements');
                    if (requirements) {
                        requirements.style.display = 'block';
                    }

                    return false;
                }
            });
        }
    }

    // For password reset page
    if (document.getElementById('new_password')) {
        window.passwordChecker = new PasswordStrengthChecker(
            'new_password',
            'passwordStrength',
            'passwordRequirements'
        );
    }

    // For change password page
    if (document.getElementById('new_password') && document.getElementById('current_password')) {
        window.passwordChecker = new PasswordStrengthChecker(
            'new_password',
            'passwordStrength',
            'passwordRequirements'
        );
    }
});
