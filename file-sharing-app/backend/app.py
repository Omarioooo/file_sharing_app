from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# إعدادات S3
S3_BUCKET = 'your-bucket-name'
S3_REGION = 'your-region'  # مثال: 'us-east-1'

s3 = boto3.client('s3')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("Error: No file part")
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash("Error: No selected file")
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    s3.upload_fileobj(file, S3_BUCKET, filename)

    flash("File uploaded successfully!")
    return redirect(url_for('index'))

@app.route('/files')
def list_files():
    response = s3.list_objects_v2(Bucket=S3_BUCKET)
    files = [item['Key'] for item in response.get('Contents', [])]
    return render_template('files.html', files=files, bucket=S3_BUCKET, region=S3_REGION)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
