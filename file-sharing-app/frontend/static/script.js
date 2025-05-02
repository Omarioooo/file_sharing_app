document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const uploadButton = document.getElementById('uploadButton');

    if (fileInput && uploadButton) {
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                uploadButton.disabled = false;
            } else {
                uploadButton.disabled = true;
            }
        });
    }
});