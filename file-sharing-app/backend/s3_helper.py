import boto3
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

load_dotenv()

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)
BUCKET_NAME = os.getenv('AWS_BUCKET_NAME')

def upload_file_to_s3(file, filename):
    """Upload a file to S3 and return metadata."""
    filename = secure_filename(filename)
    s3_client.upload_fileobj(
        file,
        BUCKET_NAME,
        filename,
        ExtraArgs={'ContentType': file.content_type}
    )
    file.seek(0, os.SEEK_END)
    size = file.tell()
    return {
        'name': filename,
        'size': size,
        'type': file.content_type,
        'lastModified': int(os.path.getmtime(file.name)) * 1000 if hasattr(file, 'name') else int(os.time()) * 1000
    }

def list_s3_files():
    """List files in S3 bucket."""
    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
    files = []
    if 'Contents' in response:
        for obj in response['Contents']:
            files.append({
                'name': obj['Key'],
                'size': obj['Size'],
                'type': 'application/octet-stream',  # Simplified
                'lastModified': int(obj['LastModified'].timestamp() * 1000)
            })
    return files

def delete_s3_file(filename):
    """Delete a file from S3."""
    s3_client.delete_object(Bucket=BUCKET_NAME, Key=filename)