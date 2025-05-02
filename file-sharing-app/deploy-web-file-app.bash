#!/bin/bash
yum update -y
yum install python3 git -y
python3 -m venv /home/ec2-user/venv
source /home/ec2-user/venv/bin/activate

# get code from git
cd /home/ec2-user
git clone https://github.com/YourUsername/file-sharing-app.git

cd file-sharing-app
pip install -r requirements.txt


cd backend
nohup python3 app.py &
