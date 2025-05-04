document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        fileInput.files = e.dataTransfer.files;
        uploadBtn.disabled = fileInput.files.length === 0;
    });

    fileInput.addEventListener('change', () => {
        uploadBtn.disabled = fileInput.files.length === 0;
    });

    uploadBtn.addEventListener('click', () => {
        const files = fileInput.files;
        if (files.length === 0) return;

        const storedFiles = JSON.parse(localStorage.getItem('uploadedFiles') || '[]');

        Array.from(files).forEach(file => {
            storedFiles.push({
                name: file.name,
                size: file.size,
                type: file.type,
                lastModified: file.lastModified
            });
        });

        localStorage.setItem('uploadedFiles', JSON.stringify(storedFiles));
        alert('Files uploaded successfully!');
        fileInput.value = '';
        uploadBtn.disabled = true;
    });
});