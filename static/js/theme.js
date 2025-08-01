// Theme toggle functionality
document.addEventListener('DOMContentLoaded', () => {
    // --- Dark Mode Toggle ---
    const themeToggleButton = document.getElementById('theme-toggle');
    const lightIcon = document.getElementById('theme-toggle-light-icon');
    const darkIcon = document.getElementById('theme-toggle-dark-icon');

    // Function to update icon visibility based on the current theme
    const updateIcons = () => {
        if (document.documentElement.classList.contains('dark')) {
            themeToggleButton.setAttribute('aria-label', 'Switch to light mode');
            darkIcon.classList.add('hidden');
            lightIcon.classList.remove('hidden');
        } else {
            themeToggleButton.setAttribute('aria-label', 'Switch to dark mode');
            darkIcon.classList.remove('hidden');
            lightIcon.classList.add('hidden');
        }
    }

    if (themeToggleButton && lightIcon && darkIcon) {
        // Set initial icon state on page load
        updateIcons();

        // Add click listener to the button
        themeToggleButton.addEventListener('click', () => {
            // Toggle the .dark class on the <html> element
            document.documentElement.classList.toggle('dark');

            // Update localStorage with the new theme state
            if (document.documentElement.classList.contains('dark')) {
                localStorage.setItem('theme', 'dark');
            } else {
                localStorage.setItem('theme', 'light');
            }

            // Update the icons to reflect the new theme
            updateIcons();
        });
    }
});
