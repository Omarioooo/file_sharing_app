// General utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Format dates in the file list
document.addEventListener('DOMContentLoaded', function() {
    const dateElements = document.querySelectorAll('.file-date');
    
    dateElements.forEach(el => {
        const date = new Date(el.textContent);
        el.textContent = date.toLocaleString();
    });
    
    // File size formatting
    const sizeElements = document.querySelectorAll('.file-size');
    
    sizeElements.forEach(el => {
        const bytes = parseInt(el.textContent);
        el.textContent = formatFileSize(bytes);
    });
});