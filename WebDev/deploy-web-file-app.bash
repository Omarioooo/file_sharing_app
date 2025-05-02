#!/bin/bash

# Update system and install dependencies
yum update -y
yum install python3 python3-pip -y

# verify pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 not found, reinstalling..."
    yum install python3-pip -y
fi

pip3 install flask boto3

# initializing app.py
cat << 'EOF' > /home/ec2-user/app.py
from flask import Flask, request, render_template
import boto3
from werkzeug.utils import secure_filename

app = Flask(__name__)
BUCKET_NAME = 'file-sharing-app-omariooo'
s3 = boto3.client('s3')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    filename = secure_filename(file.filename)
    allowed_extensions = ['pdf', 'jpg', 'png', 'txt', 'docx']
    if not filename.split('.')[-1].lower() in allowed_extensions:
        return 'File type not allowed', 400
    s3.upload_fileobj(file, BUCKET_NAME, filename)
    download_url = s3.generate_presigned_url('get_object', Params={'Bucket': BUCKET_NAME, 'Key': filename}, ExpiresIn=3600)
    return f'File uploaded! Download link: <a href="{download_url}">{filename}</a>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
EOF

# create templates folder and index.html file
mkdir -p /home/ec2-user/templates
cat << 'EOF' > /home/ec2-user/templates/index.html
<!DOCTYPE html>
<html>
<head><title>File Sharing App</title></head>
<body>
    <h1>Upload a File</h1>
    <form method="post" enctype="multipart/form-data" action="/upload">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <p>Supported file types: .pdf, .jpg, .png, .txt</p>
</body>
</html>
EOF

# automatically run the app and redirect output to a log file
nohup python3 /home/ec2-user/app.py > /home/ec2-user/app.log 2>&1 &

# wait a few seconds and check if the app is running
sleep 5
if netstat -tuln | grep -q ':80'; then
    echo "Flask app is running on port 80"
else
    echo "Flask app failed to start, check /home/ec2-user/app.log for details"
fi