document.addEventListener('DOMContentLoaded', () => {
    const fileList = document.getElementById('fileList');

    // Function to render the file list
    const renderFileList = () => {
        fileList.innerHTML = ''; // Clear current list
        const files = JSON.parse(localStorage.getItem('uploadedFiles') || '[]');

        if (files.length === 0) {
            fileList.innerHTML = '<li>No files uploaded yet.</li>';
            return;
        }

        files.forEach((file, index) => {
            const li = document.createElement('li');
            li.innerHTML = `${file.name} (${(file.size / 1024).toFixed(2)} KB, ${file.type || 'unknown type'})`;
            
            // Create remove button
            const removeBtn = document.createElement('button');
            removeBtn.textContent = 'Remove';
            removeBtn.className = 'remove-btn';
            removeBtn.addEventListener('click', () => {
                // Remove file from localStorage
                files.splice(index, 1);
                localStorage.setItem('uploadedFiles', JSON.stringify(files));
                // Re-render the list
                renderFileList();
            });

            li.appendChild(removeBtn);
            fileList.appendChild(li);
        });
    };

    // Initial render
    renderFileList();
});