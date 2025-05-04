from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from s3_helper import upload_file_to_s3, list_s3_files, delete_s3_file

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'txt'}

def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create Flask app and set folders for static and template files
app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend/template')

# Serve front-end files
@app.route('/')
@app.route('/index.html')
def serve_index():
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/upload.html')
def serve_upload():
    return send_from_directory(app.template_folder, 'upload.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# API Endpoints
@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    files = request.files.getlist('files')
    uploaded_files = []
    for file in files:
        if file.filename == '':
            continue
        if not is_allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed: {file.filename}'}), 400
        metadata = upload_file_to_s3(file, file.filename)
        uploaded_files.append(metadata)
    return jsonify({'message': 'Files uploaded successfully', 'files': uploaded_files})

@app.route('/api/files', methods=['GET'])
def list_files():
    files = list_s3_files()
    return jsonify(files)

@app.route('/api/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    delete_s3_file(filename)
    return jsonify({'message': 'File deleted successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
