"""
s3.py
Loader for fetching documents from S3.
"""
import boto3
import os

class S3Loader:
    def __init__(self):
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "kaiser-docs")
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )

    def load(self, file_key: str) -> str:
        print(f"Loading file from S3: {self.bucket_name}/{file_key}")
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_key)
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"Error loading S3 object: {e}")
            raise e
