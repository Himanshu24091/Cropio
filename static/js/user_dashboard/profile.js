document.addEventListener('DOMContentLoaded', function() {
    // Animate usage bar
    const usageFill = document.querySelector('.usage-fill');
    if (usageFill) {
        const targetWidth = usageFill.style.width;
        usageFill.style.width = '0%';
        setTimeout(() => {
            usageFill.style.width = targetWidth;
        }, 100);
    }
});