import io
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile

from app.core.config import settings
from app.utils.logger import Logger
from app.utils.exceptions import FileError


class MinIOService:
    """Service để quản lý MinIO object storage"""
    
    def __init__(self):
        self.logger = Logger(__name__).logger
        self.client = None
        self._initialize_client()
        self._ensure_buckets_exist()
    
    def _initialize_client(self):
        """Khởi tạo MinIO client"""
        try:
            self.client = Minio(
                endpoint=settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE
            )
            self.logger.info(f"Đã kết nối MinIO tại {settings.MINIO_ENDPOINT}")
        except Exception as e:
            self.logger.error(f"Lỗi kết nối MinIO: {str(e)}")
            raise FileError(f"Không thể kết nối MinIO: {str(e)}")
    
    def _ensure_buckets_exist(self):
        """Đảm bảo các bucket cần thiết đã tồn tại"""
        buckets = [
            settings.MINIO_INPUT_BUCKET,
            settings.MINIO_OUTPUT_BUCKET,
            settings.MINIO_CACHE_BUCKET
        ]
        
        for bucket_name in buckets:
            try:
                if not self.client.bucket_exists(bucket_name):
                    self.client.make_bucket(bucket_name)
                    self.logger.info(f"Đã tạo bucket: {bucket_name}")
                else:
                    self.logger.debug(f"Bucket đã tồn tại: {bucket_name}")
            except S3Error as e:
                self.logger.error(f"Lỗi tạo bucket {bucket_name}: {str(e)}")
                raise FileError(f"Không thể tạo bucket {bucket_name}: {str(e)}")
    
    async def upload_file(self, 
                         file: Union[UploadFile, str, bytes], 
                         bucket_name: str, 
                         object_name: str,
                         content_type: Optional[str] = None) -> str:
        """
        Upload file lên MinIO
        
        Args:
            file: File để upload (UploadFile, đường dẫn file, hoặc bytes)
            bucket_name: Tên bucket
            object_name: Tên object trong bucket
            content_type: Content type của file
            
        Returns:
            URL của object đã upload
        """
        try:
            if isinstance(file, UploadFile):
                # Upload từ UploadFile
                content = await file.read()
                await file.seek(0)  # Reset file pointer
                
                if not content_type:
                    content_type = file.content_type or 'application/octet-stream'
                
                self.client.put_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    data=io.BytesIO(content),
                    length=len(content),
                    content_type=content_type
                )
                
            elif isinstance(file, str):
                # Upload từ file path
                if not os.path.exists(file):
                    raise FileError(f"File không tồn tại: {file}")
                
                self.client.fput_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    file_path=file,
                    content_type=content_type
                )
                
            elif isinstance(file, bytes):
                # Upload từ bytes
                self.client.put_object(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    data=io.BytesIO(file),
                    length=len(file),
                    content_type=content_type or 'application/octet-stream'
                )
            else:
                raise FileError("Định dạng file không được hỗ trợ")
            
            # Tạo URL cho object
            object_url = f"minio://{bucket_name}/{object_name}"
            self.logger.info(f"Đã upload file: {object_url}")
            return object_url
            
        except S3Error as e:
            self.logger.error(f"Lỗi upload file lên MinIO: {str(e)}")
            raise FileError(f"Không thể upload file: {str(e)}")
        except Exception as e:
            self.logger.error(f"Lỗi không xác định khi upload: {str(e)}")
            raise FileError(f"Lỗi upload file: {str(e)}")
    
    def download_file(self, bucket_name: str, object_name: str, file_path: str) -> bool:
        """
        Download file từ MinIO về local
        
        Args:
            bucket_name: Tên bucket
            object_name: Tên object
            file_path: Đường dẫn lưu file
            
        Returns:
            True nếu thành công
        """
        try:
            # Tạo thư mục nếu chưa tồn tại
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            self.client.fget_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path
            )
            
            self.logger.info(f"Đã download file: {bucket_name}/{object_name} -> {file_path}")
            return True
            
        except S3Error as e:
            self.logger.error(f"Lỗi download file từ MinIO: {str(e)}")
            raise FileError(f"Không thể download file: {str(e)}")
    
    def get_file_content(self, bucket_name: str, object_name: str) -> bytes:
        """
        Lấy nội dung file dưới dạng bytes
        
        Args:
            bucket_name: Tên bucket
            object_name: Tên object
            
        Returns:
            Nội dung file dưới dạng bytes
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            content = response.read()
            response.close()
            response.release_conn()
            
            self.logger.debug(f"Đã đọc nội dung file: {bucket_name}/{object_name}")
            return content
            
        except S3Error as e:
            self.logger.error(f"Lỗi đọc file từ MinIO: {str(e)}")
            raise FileError(f"Không thể đọc file: {str(e)}")
    
    def delete_file(self, bucket_name: str, object_name: str) -> bool:
        """
        Xóa file từ MinIO
        
        Args:
            bucket_name: Tên bucket
            object_name: Tên object
            
        Returns:
            True nếu thành công
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            self.logger.info(f"Đã xóa file: {bucket_name}/{object_name}")
            return True
            
        except S3Error as e:
            self.logger.error(f"Lỗi xóa file từ MinIO: {str(e)}")
            raise FileError(f"Không thể xóa file: {str(e)}")
    
    def file_exists(self, bucket_name: str, object_name: str) -> bool:
        """
        Kiểm tra file có tồn tại không
        
        Args:
            bucket_name: Tên bucket
            object_name: Tên object
            
        Returns:
            True nếu file tồn tại
        """
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def list_files(self, bucket_name: str, prefix: str = "") -> List[str]:
        """
        Liệt kê files trong bucket
        
        Args:
            bucket_name: Tên bucket
            prefix: Prefix để filter
            
        Returns:
            Danh sách tên files
        """
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            self.logger.error(f"Lỗi liệt kê files: {str(e)}")
            return []
    
    def get_presigned_url(self, bucket_name: str, object_name: str, 
                         expires: timedelta = timedelta(hours=1)) -> str:
        """
        Tạo presigned URL để truy cập file
        
        Args:
            bucket_name: Tên bucket
            object_name: Tên object
            expires: Thời gian hết hạn
            
        Returns:
            Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            self.logger.error(f"Lỗi tạo presigned URL: {str(e)}")
            raise FileError(f"Không thể tạo URL: {str(e)}")
    
    @staticmethod
    def parse_minio_url(url: str) -> tuple:
        """
        Parse MinIO URL thành bucket và object name
        
        Args:
            url: MinIO URL (minio://bucket/object)
            
        Returns:
            Tuple (bucket_name, object_name)
        """
        if not url.startswith('minio://'):
            raise ValueError("URL không hợp lệ, phải bắt đầu bằng 'minio://'")
        
        parsed = urlparse(url)
        bucket_name = parsed.netloc
        object_name = parsed.path.lstrip('/')
        
        return bucket_name, object_name


# Singleton instance
minio_service = MinIOService()
