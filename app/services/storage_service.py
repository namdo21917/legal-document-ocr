import io
from minio import Minio
from minio.error import S3Error
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT.replace('http://', '').replace('https://', ''),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_ENDPOINT.startswith('https')
        )
        self.bucket = settings.MINIO_BUCKET
        # Tạo bucket nếu chưa có
        found = self.client.bucket_exists(self.bucket)
        if not found:
            self.client.make_bucket(self.bucket)

    def upload_file(self, file_data: bytes, object_name: str, content_type: str = 'application/octet-stream'):
        try:
            self.client.put_object(
                self.bucket,
                object_name,
                io.BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            return self.get_file_url(object_name)
        except S3Error as e:
            raise Exception(f"MinIO upload error: {e}")

    def get_file_url(self, object_name: str):
        return f"{settings.MINIO_ENDPOINT}/{self.bucket}/{object_name}"

    def download_file(self, object_name: str) -> bytes:
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise Exception(f"MinIO download error: {e}") 