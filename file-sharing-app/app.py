# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template_string
import boto3
import os
from werkzeug.utils import secure_filename
import mimetypes

app = Flask(__name__)
BUCKET = 'upload-bucket-abdo'
s3 = boto3.client('s3')
MAX_SIZE_MB = 10

HTML = '''
<!DOCTYPE html>
<html>
<head>
  <title>File Sharing</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background-color: #121212; color: #e0e0e0; }
    #drop-area {
      border: 2px dashed #0d6efd;
      padding: 30px;
      text-align: center;
      margin-top: 40px;
      background-color: #212529;
      border-radius: 10px;
      color: #ccc;
      transition: all 0.3s ease;
    }
    #drop-area.highlight {
      border-color: #28a745;
      background-color: rgba(40, 167, 69, 0.1);
    }
    .btn, .list-group-item {
      border-radius: 0.5rem !important;
    }
    .list-group-item {
      background-color: #1e1e1e;
      border: 1px solid #333;
    }
    progress {
      width: 100%;
      height: 20px;
      margin-top: 10px;
    }
    .loading-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: rgba(0, 0, 0, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9999;
      visibility: hidden;
      opacity: 0;
      transition: opacity 0.3s, visibility 0.3s;
    }
    .loading-overlay.active {
      visibility: visible;
      opacity: 1;
    }
    .spinner-border {
      width: 3rem;
      height: 3rem;
    }
    .notification {
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 15px 20px;
      border-radius: 5px;
      color: white;
      box-shadow: 0 4px 8px rgba(0,0,0,0.2);
      z-index: 9999;
      opacity: 0;
      transform: translateY(-20px);
      transition: opacity 0.3s, transform 0.3s;
      max-width: 350px;
    }
    .notification.success {
      background-color: #28a745;
    }
    .notification.error {
      background-color: #dc3545;
    }
    .notification.show {
      opacity: 1;
      transform: translateY(0);
    }
    .file-icon {
      width: 24px;
      height: 24px;
      margin-right: 8px;
    }
    .file-type-filter {
      max-width: 300px;
      margin-bottom: 20px;
    }
    .form-select {
      background-color: #333;
      color: #fff;
      border-color: #555;
    }
    .form-select:focus {
      background-color: #444;
      color: #fff;
      border-color: #0d6efd;
      box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
    }
  </style>
</head>
<body>
<div class="container">
  <h2 class="text-center my-4">📁 Universal File Uploader</h2>
  <div id="drop-area" 
       ondrop="dropHandler(event)" 
       ondragover="dragOverHandler(event)" 
       ondragleave="dragLeaveHandler(event)" 
       ondragenter="dragEnterHandler(event)">
    <p>Drop any files here or click to upload</p>
    <input type="file" id="fileElem" multiple style="display:none" onchange="handleFiles(this.files)">
    <button class="btn btn-primary" onclick="document.getElementById('fileElem').click()">Choose Files</button>
    <div class="progress mt-3" style="display:none;">
      <div id="uploadProgress" class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%"></div>
    </div>
  </div>

  <div id="upload-status" class="mt-3"></div>
  
  <div class="d-flex justify-content-between align-items-center mt-5 mb-3">
    <h4 class="mb-0">Uploaded Files</h4>
    <div class="file-type-filter">
      <select id="file-type-filter" class="form-select" onchange="filterFiles()">
        <option value="all">All Files</option>
        <option value="image">Images</option>
        <option value="video">Videos</option>
        <option value="audio">Audio</option>
        <option value="document">Documents</option>
        <option value="compressed">Archives</option>
        <option value="code">Code Files</option>
        <option value="other">Other</option>
      </select>
    </div>
  </div>
  
  <ul id="file-list" class="list-group mb-5"></ul>
</div>

<div class="loading-overlay" id="loading-overlay">
  <div class="spinner-border text-light" role="status">
    <span class="visually-hidden">Loading...</span>
  </div>
</div>

<div id="notification" class="notification"></div>

<script>
const maxSizeMB = 10;

// File type categorization
const fileTypes = {
  image: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'tiff', 'ico'],
  video: ['mp4', 'webm', 'avi', 'mov', 'wmv', 'mkv', 'flv', '3gp'],
  audio: ['mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac', 'wma'],
  document: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'csv', 'odt', 'ods', 'odp'],
  compressed: ['zip', 'rar', '7z', 'tar', 'gz', 'bz2'],
  code: ['html', 'css', 'js', 'json', 'xml', 'py', 'java', 'cpp', 'c', 'cs', 'php', 'rb', 'go', 'ts', 'jsx', 'sh']
};

// File icons mapping
const fileIcons = {
  image: '🖼️',
  video: '🎬',
  audio: '🎵',
  document: '📄',
  compressed: '🗜️',
  code: '📝',
  other: '📎'
};

function getFileTypeCategory(filename) {
  const extension = filename.split('.').pop().toLowerCase();
  
  for (const [category, extensions] of Object.entries(fileTypes)) {
    if (extensions.includes(extension)) {
      return category;
    }
  }
  
  return 'other';
}

function getFileIcon(fileType) {
  return fileIcons[fileType] || fileIcons.other;
}

function showNotification(message, type = 'success') {
  const notification = document.getElementById('notification');
  notification.textContent = message;
  notification.className = `notification ${type}`;
  
  // Force reflow to make sure the transition works
  notification.offsetHeight;
  
  notification.classList.add('show');
  
  setTimeout(() => {
    notification.classList.remove('show');
  }, 3000);
}

function showLoading(show = true) {
  const overlay = document.getElementById('loading-overlay');
  if (show) {
    overlay.classList.add('active');
  } else {
    overlay.classList.remove('active');
  }
}

function dragEnterHandler(ev) {
  ev.preventDefault();
  document.getElementById('drop-area').classList.add('highlight');
}

function dragLeaveHandler(ev) {
  ev.preventDefault();
  document.getElementById('drop-area').classList.remove('highlight');
}

function dragOverHandler(ev) {
  ev.preventDefault();
  document.getElementById('drop-area').classList.add('highlight');
}

function dropHandler(ev) {
  ev.preventDefault();
  document.getElementById('drop-area').classList.remove('highlight');
  
  if (ev.dataTransfer.items) {
    const files = [];
    for (let i = 0; i < ev.dataTransfer.items.length; i++) {
      if (ev.dataTransfer.items[i].kind === 'file') {
        files.push(ev.dataTransfer.items[i].getAsFile());
      }
    }
    handleFiles(files);
  }
}

function handleFiles(files) {
  if (files.length === 0) {
    showNotification('No files selected.', 'error');
    return;
  }
  
  let validFiles = 0;
  
  for (let i = 0; i < files.length; i++) {
    const file = files[i];

    if (file.size > maxSizeMB * 1024 * 1024) {
      showNotification(`"${file.name}" exceeds the maximum size of ${maxSizeMB} MB.`, 'error');
      continue;
    }

    validFiles++;
    uploadFile(file);
  }
  
  if (validFiles === 0) {
    showNotification('No valid files to upload.', 'error');
  }
}

function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload", true);
  
  const progressBar = document.getElementById("uploadProgress");
  const progressContainer = progressBar.parentElement;
  
  progressContainer.style.display = "block";
  
  xhr.upload.onprogress = function (e) {
    if (e.lengthComputable) {
      const percent = Math.round((e.loaded / e.total) * 100);
      progressBar.style.width = percent + '%';
      progressBar.setAttribute('aria-valuenow', percent);
    }
  };
  
  xhr.onload = function () {
    progressContainer.style.display = "none";
    progressBar.style.width = '0%';
    
    if (xhr.status === 200) {
      try {
        const data = JSON.parse(xhr.responseText);
        showNotification(`Successfully uploaded: ${data.name}`);
        loadFiles();
      } catch (e) {
        showNotification('Error processing server response.', 'error');
      }
    } else {
      try {
        const data = JSON.parse(xhr.responseText);
        showNotification(`Upload failed: ${data.error}`, 'error');
      } catch (e) {
        showNotification('Upload failed.', 'error');
      }
    }
  };
  
  xhr.onerror = function() {
    progressContainer.style.display = "none";
    showNotification('Network error during upload.', 'error');
  };
  
  xhr.send(formData);
}

let allFiles = []; // Store all files for filtering

function loadFiles() {
  showLoading(true);
  
  fetch("/files")
    .then(res => {
      if (!res.ok) {
        throw new Error('Failed to load files');
      }
      return res.json();
    })
    .then(data => {
      allFiles = data.map(file => {
        return {
          ...file,
          type: getFileTypeCategory(file.name)
        };
      });
      
      // Apply current filter
      filterFiles();
    })
    .catch(err => {
      console.error("Failed to fetch files:", err);
      showNotification('Failed to load files. Please refresh the page.', 'error');
      document.getElementById("file-list").innerHTML = 
        '<li class="list-group-item text-center text-danger">Failed to load files</li>';
    })
    .finally(() => {
      showLoading(false);
    });
}

function filterFiles() {
  const filterType = document.getElementById('file-type-filter').value;
  let filteredFiles = [];
  
  if (filterType === 'all') {
    filteredFiles = allFiles;
  } else {
    filteredFiles = allFiles.filter(file => file.type === filterType);
  }
  
  renderFileList(filteredFiles);
}

function renderFileList(files) {
  const fileList = document.getElementById("file-list");
  
  if (files.length === 0) {
    fileList.innerHTML = '<li class="list-group-item text-center">No files found</li>';
    return;
  }
  
  let listHtml = '';
  
  files.forEach(file => {
    const fileType = file.type;
    const icon = getFileIcon(fileType);
    
    listHtml += `
      <li class="list-group-item d-flex justify-content-between align-items-center" data-file-type="${fileType}">
        <div>
          <span class="file-icon">${icon}</span>
          <a href="${file.link}" target="_blank" class="text-decoration-none">${file.name}</a>
        </div>
        <div>
          <button class="btn btn-sm btn-outline-light me-1" onclick="copyLink('${file.link}', this)">Copy Link</button>
          <button class="btn btn-sm btn-outline-danger" onclick="deleteFile('${file.name}', this)">Delete</button>
        </div>
      </li>`;
  });
  
  fileList.innerHTML = listHtml;
}

function copyLink(link, btn) {
  // Create temporary input element
  const tempInput = document.createElement("input");
  tempInput.value = link;
  tempInput.style.position = "absolute";
  tempInput.style.left = "-9999px";
  document.body.appendChild(tempInput);
  
  // Select and copy the text
  tempInput.select();
  document.execCommand("copy");
  
  // Remove the temporary element
  document.body.removeChild(tempInput);
  
  // Provide feedback through button
  const originalText = btn.textContent;
  btn.textContent = "Copied!";
  btn.classList.remove("btn-outline-light");
  btn.classList.add("btn-success");
  
  // Show notification
  showNotification('Link copied to clipboard!');
  
  // Reset button after delay
  setTimeout(() => {
    btn.textContent = originalText;
    btn.classList.remove("btn-success");
    btn.classList.add("btn-outline-light");
  }, 2000);
}

function deleteFile(filename, btn) {
  if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;
  
  // Disable button to prevent double-clicks
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Deleting...';
  
  fetch("/delete", {
    method: "POST",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: filename })
  })
  .then(res => {
    if (!res.ok) {
      throw new Error('Server returned error status');
    }
    return res.json();
  })
  .then(data => {
    if (data.success) {
      showNotification(`Successfully deleted: ${filename}`);
      loadFiles();
    } else {
      throw new Error(data.error || 'Unknown error');
    }
  })
  .catch(err => {
    console.error("Failed to delete file:", err);
    showNotification(`Failed to delete: ${err.message}`, 'error');
    // Re-enable button
    btn.disabled = false;
    btn.textContent = "Delete";
  });
}

window.onload = loadFiles;
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    f = request.files['file']
    
    if not f or not f.filename:
        return jsonify({'error': 'No file selected'}), 400

    # Check file size
    f.seek(0, os.SEEK_END)
    size = f.tell()
    if size > MAX_SIZE_MB * 1024 * 1024:
        return jsonify({'error': 'File too large (max {}MB)'.format(MAX_SIZE_MB)}), 400

    f.seek(0)  # Reset file pointer after size check

    # Secure the filename
    filename = secure_filename(f.filename)

    try:
        s3.upload_fileobj(f, BUCKET, filename)
        link = f'https://{BUCKET}.s3.amazonaws.com/{filename}'
        return jsonify({'link': link, 'name': filename})
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Failed to upload file: {str(e)}'}), 500

@app.route('/files')
def list_files():
    try:
        objects = s3.list_objects_v2(Bucket=BUCKET)
        links = []
        for obj in objects.get('Contents', []):
            name = obj['Key']
            url = f'https://{BUCKET}.s3.amazonaws.com/{name}'
            links.append({'name': name, 'link': url})
        return jsonify(links)
    except Exception as e:
        app.logger.error(f"List files error: {str(e)}")
        return jsonify({'error': f'Failed to fetch file list: {str(e)}'}), 500

@app.route('/delete', methods=['POST'])
def delete_file():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'success': False, 'error': 'No filename provided'}), 400
        
    filename = data.get('name')
    
    try:
        s3.delete_object(Bucket=BUCKET, Key=filename)
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Delete error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
