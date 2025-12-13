/**
 * Privacy Policy Modal JavaScript
 * Handles opening and closing of Privacy Policy modal
 */

// Privacy Policy content
const privacyContent = `
    <h2>1. Introduction</h2>
    <p>We respect your privacy and are committed to protecting your personal data. This Privacy Policy explains how we collect, use, and safeguard your information.</p>

    <h2>2. Information We Collect</h2>
    <h3>2.1 Personal Information:</h3>
    <ul>
        <li>Username, email address, password (encrypted)</li>
        <li>Profile information (optional)</li>
        <li>Payment information (for premium subscriptions)</li>
    </ul>

    <h3>2.2 Usage Information:</h3>
    <ul>
        <li>Conversion history and statistics</li>
        <li>Device information and IP address</li>
        <li>Browser type and operating system</li>
    </ul>

    <h3>2.3 File Information:</h3>
    <ul>
        <li>File metadata (name, size, format)</li>
        <li>File content (temporarily stored, deleted after 30 minutes)</li>
    </ul>

    <h2>3. How We Use Your Information</h2>
    <ul>
        <li>To provide and improve our Service</li>
        <li>To process your file conversions</li>
        <li>To manage your account and subscriptions</li>
        <li>To provide customer support</li>
        <li>To detect and prevent fraud</li>
    </ul>

    <h2>4. We DO NOT Sell Your Data</h2>
    <p>We do not sell, rent, or trade your personal information to third parties for marketing purposes.</p>

    <h2>5. Data Security</h2>
    <ul>
        <li>Encryption of data in transit (HTTPS/TLS)</li>
        <li>Secure password hashing (bcrypt)</li>
        <li>Automatic file deletion after 30 minutes</li>
        <li>Regular security audits</li>
    </ul>

    <h2>6. Your Rights</h2>
    <ul>
        <li><strong>Access:</strong> View your personal information</li>
        <li><strong>Update:</strong> Correct your account information</li>
        <li><strong>Delete:</strong> Delete your account and data</li>
        <li><strong>Opt-out:</strong> Unsubscribe from marketing emails</li>
    </ul>

    <h2>7. Data Retention</h2>
    <ul>
        <li>Account data: Retained while account is active</li>
        <li>Uploaded files: Automatically deleted after 30 minutes</li>
        <li>Conversion history: Retained for your reference</li>
    </ul>

    <h2>8. GDPR Compliance</h2>
    <p>For EU users, we comply with GDPR regulations. You have the right to access, rectify, erase, restrict processing, and port your data.</p>

    <h2>9. Children's Privacy</h2>
    <p>Cropio is not intended for users under 13. We do not knowingly collect information from children.</p>

    <h2>10. Contact Us</h2>
    <p>For privacy-related questions, contact us at: <strong>privacy@cropio.com</strong></p>

    <p style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; color: #6b7280; font-size: 0.875rem;">
        By using Cropio, you consent to our Privacy Policy.
    </p>
`;

/**
 * Open Privacy Policy modal
 */
function openPrivacyModal() {
    const modal = document.getElementById('privacyModal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }
}

/**
 * Close Privacy Policy modal
 */
function closePrivacyModal() {
    const modal = document.getElementById('privacyModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = ''; // Restore scrolling
    }
}

// Prevent closing modal when clicking on modal content
document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('privacyModal');
    if (modal) {
        const modalContent = modal.querySelector('.privacy-modal-content');
        if (modalContent) {
            modalContent.addEventListener('click', function (event) {
                event.stopPropagation();
            });
        }
    }
});

// Prevent closing modal with Escape key
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('privacyModal');
        if (modal && modal.classList.contains('active')) {
            event.preventDefault();
            // Do nothing - user must click OK button
        }
    }
});
