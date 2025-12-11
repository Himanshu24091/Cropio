/**
 * Global CSRF Token Handling for AJAX Requests
 * Automatically includes CSRF tokens in all AJAX requests
 */

// Get CSRF token from meta tag or global variable
function getCSRFToken() {
    // Try to get from global variable first
    if (window.csrfToken) {
        return window.csrfToken;
    }
    
    // Try to get from meta tag
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }
    
    // Try to get from hidden input in any form
    const hiddenInput = document.querySelector('input[name="csrf_token"]');
    if (hiddenInput) {
        return hiddenInput.value;
    }
    
    return null;
}

// Set up jQuery CSRF token handling if jQuery is available
if (typeof $ !== 'undefined') {
    // Set CSRF token for all AJAX requests
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                const token = getCSRFToken();
                if (token) {
                    xhr.setRequestHeader("X-CSRFToken", token);
                }
            }
        }
    });
}

// Set up fetch API CSRF token handling
if (typeof fetch !== 'undefined') {
    const originalFetch = window.fetch;
    
    window.fetch = function(...args) {
        const [url, options = {}] = args;
        
        // Only add CSRF token to POST, PUT, PATCH, DELETE requests
        if (options.method && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(options.method.toUpperCase())) {
            const token = getCSRFToken();
            if (token) {
                options.headers = options.headers || {};
                if (options.headers instanceof Headers) {
                    options.headers.set('X-CSRFToken', token);
                } else {
                    options.headers['X-CSRFToken'] = token;
                }
            }
        }
        
        return originalFetch.apply(this, [url, options]);
    };
}

// Helper function for manual AJAX requests
window.addCSRFToken = function(data) {
    const token = getCSRFToken();
    if (token) {
        if (data instanceof FormData) {
            data.append('csrf_token', token);
        } else if (typeof data === 'object' && data !== null) {
            data.csrf_token = token;
        }
    }
    return data;
};

// Helper function to get CSRF headers
window.getCSRFHeaders = function() {
    const token = getCSRFToken();
    return token ? { 'X-CSRFToken': token } : {};
};

console.log('CSRF token handling initialized');
