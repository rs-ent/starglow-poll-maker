
from google.cloud import storage
import os
import json
import datetime
from google.oauth2 import service_account

def upload_image(image_path, destination_blob_name):
    google_service_account_str = os.environ.get('GOOGLE_SERVICE_ACCOUNT')
    if not google_service_account_str:
        raise ValueError('GOOGLE_SERVICE_ACCOUNT 환경 변수가 설정되어 있지 않습니다.')
    google_service_account_info = json.loads(google_service_account_str)
    credentials = service_account.Credentials.from_service_account_info(google_service_account_info)
    client = storage.Client(credentials=credentials, project=credentials.project_id)
    bucket = client.bucket('starglow-voting.firebasestorage.app')
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    base, ext = os.path.splitext(destination_blob_name)
    destination_blob_name = f'{base}_{timestamp}{ext}'
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(image_path)
    print(f'Image {image_path} uploaded to {destination_blob_name} in Firebase Storage.')
    return f'https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{destination_blob_name}?alt=media'