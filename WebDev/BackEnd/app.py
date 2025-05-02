from flask import Flask, render_template, request, jsonify
import boto3
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY, S3_BUCKET_NAME
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'txt', 'docx', 'xlsx'}

# S3 Client
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    
    files = request.files.getlist('file')
    results = []
    
    for file in files:
        if file.filename == '':
            results.append({'success': False, 'error': 'No selected file'})
            continue
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                s3.upload_fileobj(
                    file,
                    S3_BUCKET_NAME,
                    filename,
                    ExtraArgs={'ACL': 'public-read'}
                )
                results.append({'success': True, 'filename': filename})
            except Exception as e:
                results.append({'success': False, 'error': str(e)})
        else:
            results.append({'success': False, 'error': 'File type not allowed'})
    
    return jsonify({'success': all(r['success'] for r in results), 'results': results})

@app.route('/files')
def list_files():
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME)
        files = []
        if 'Contents' in response:
            for item in response['Contents']:
                files.append({
                    'name': item['Key'],
                    'size': item['Size'],
                    'last_modified': item['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                })
        return render_template('files.html', files=files)
    except Exception as e:
        return render_template('files.html', files=[], error=str(e))

@app.route('/download/<filename>')
def download_file(filename):
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': filename},
            ExpiresIn=3600  # 1 hour
        )
        return redirect(url)
    except Exception as e:
        return str(e), 404

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        s3.delete_object(Bucket=S3_BUCKET_NAME, Key=filename)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)