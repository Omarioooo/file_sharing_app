#!/bin/bash

# Update system and install dependencies
yum update -y
yum install python3 python3-pip -y

# Clone project repository
git clone https://github.com/Omarioooo/file_sharing_app.git /home/ec2-user/file-share-app
cd /home/ec2-user/file-share-app

# Install Python requirements
pip3 install -r requirements.txt

# verify pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 not found, reinstalling..."
    yum install python3-pip -y
fi

pip3 install flask boto3

# Create config file with environment variables
cat > /home/ec2-user/file-share-app/config.py <<EOL
AWS_ACCESS_KEY = 'YOUR_ACCESS_KEY'
AWS_SECRET_KEY = 'YOUR_SECRET_KEY'
S3_BUCKET_NAME = 'file-sharing-app-omariooo'
EOL

# Set proper permissions
chown -R ec2-user:ec2-user /home/ec2-user/file-share-app
chmod -R 755 /home/ec2-user/file-share-app

# Install and configure Nginx as reverse proxy
yum install -y nginx
systemctl start nginx
systemctl enable nginx

cat > /etc/nginx/conf.d/flaskapp.conf <<EOL
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOL

# Restart Nginx
systemctl restart nginx

# Create systemd service for automatic startup
cat > /etc/systemd/system/flaskapp.service <<EOL
[Unit]
Description=Flask File Share App
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/file-share-app
ExecStart=/usr/bin/python3 /home/ec2-user/file-share-app/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Enable and start the service
systemctl daemon-reload
systemctl start flaskapp
systemctl enable flaskapp

# Check service status
if systemctl is-active --quiet flaskapp; then
    echo "Flask app is running successfully"
else
    echo "Flask app failed to start. Check logs with: journalctl -u flaskapp -b"
fi