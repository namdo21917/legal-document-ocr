import os
import json
import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Optional, Any

from app.utils.logger import Logger
from app.services.minio_service import minio_service
from app.core.config import settings
from app.utils.exceptions import FileError


class CacheManager:
    def __init__(self, cache_dir='cache', max_age_days=7, use_minio=True):
        self.logger = Logger(__name__).logger
        self.cache_dir = cache_dir
        self.max_age = timedelta(days=max_age_days)
        self.use_minio = use_minio
        self.minio_service = minio_service if use_minio else None

        if not use_minio:
            # Tạo thư mục cache local nếu chưa tồn tại
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
                self.logger.info(f"Đã tạo thư mục cache: {cache_dir}")

        # Dọn dẹp cache cũ
        self.cleanup_old_cache()

    def generate_key(self, image):
        try:
            # Chuyển ảnh thành bytes
            if hasattr(image, 'tobytes'):
                image_bytes = image.tobytes()
            else:
                image_bytes = image.dumps()

            # Tạo hash từ bytes của ảnh
            hash_object = hashlib.sha256(image_bytes)
            return hash_object.hexdigest()
        except Exception as e:
            self.logger.error(f"Lỗi tạo cache key: {str(e)}")
            return None

    def get(self, key: str) -> Optional[Any]:
        """Lấy dữ liệu từ cache"""
        try:
            if self.use_minio:
                return self._get_from_minio(key)
            else:
                return self._get_from_local(key)
        except Exception as e:
            self.logger.error(f"Lỗi đọc cache: {str(e)}")
            return None

    def _get_from_minio(self, key: str) -> Optional[Any]:
        """Lấy cache từ MinIO"""
        try:
            object_name = f"{key}.pickle"

            if not self.minio_service.file_exists(settings.MINIO_CACHE_BUCKET, object_name):
                return None

            # Lấy nội dung file
            content = self.minio_service.get_file_content(settings.MINIO_CACHE_BUCKET, object_name)
            result = pickle.loads(content)

            self.logger.debug(f"Đã đọc cache từ MinIO: {key}")
            return result

        except Exception as e:
            self.logger.error(f"Lỗi đọc cache từ MinIO: {str(e)}")
            return None

    def _get_from_local(self, key: str) -> Optional[Any]:
        """Lấy cache từ local storage"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.pickle")

            if not os.path.exists(cache_file):
                return None

            # Kiểm tra thời gian cache
            file_age = datetime.now() - datetime.fromtimestamp(
                os.path.getmtime(cache_file)
            )
            if file_age > self.max_age:
                self.logger.debug(f"Cache đã hết hạn: {key}")
                os.remove(cache_file)
                return None

            # Đọc cache
            with open(cache_file, 'rb') as f:
                result = pickle.load(f)
                self.logger.debug(f"Đã đọc cache local: {key}")
                return result

        except Exception as e:
            self.logger.error(f"Lỗi đọc cache local: {str(e)}")
            return None

    def set(self, key: str, value: Any) -> bool:
        """Lưu dữ liệu vào cache"""
        try:
            if self.use_minio:
                return self._set_to_minio(key, value)
            else:
                return self._set_to_local(key, value)
        except Exception as e:
            self.logger.error(f"Lỗi lưu cache: {str(e)}")
            return False

    def _set_to_minio(self, key: str, value: Any) -> bool:
        """Lưu cache lên MinIO"""
        try:
            object_name = f"{key}.pickle"
            content = pickle.dumps(value)

            # Upload lên MinIO
            self.minio_service.client.put_object(
                bucket_name=settings.MINIO_CACHE_BUCKET,
                object_name=object_name,
                data=content,
                length=len(content),
                content_type='application/octet-stream'
            )

            self.logger.debug(f"Đã lưu cache lên MinIO: {key}")
            return True

        except Exception as e:
            self.logger.error(f"Lỗi lưu cache lên MinIO: {str(e)}")
            return False

    def _set_to_local(self, key: str, value: Any) -> bool:
        """Lưu cache vào local storage"""
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.pickle")

            # Lưu cache
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
                self.logger.debug(f"Đã lưu cache local: {key}")
                return True

        except Exception as e:
            self.logger.error(f"Lỗi lưu cache local: {str(e)}")
            return False

    def cleanup_old_cache(self):
        """Dọn dẹp cache cũ"""
        try:
            if self.use_minio:
                self._cleanup_minio_cache()
            else:
                self._cleanup_local_cache()
        except Exception as e:
            self.logger.error(f"Lỗi dọn dẹp cache: {str(e)}")

    def _cleanup_minio_cache(self):
        """Dọn dẹp cache trên MinIO"""
        try:
            # MinIO không có built-in expiration, cần implement logic riêng
            # Có thể sử dụng object metadata hoặc naming convention với timestamp
            objects = self.minio_service.list_files(settings.MINIO_CACHE_BUCKET)
            count = 0

            for object_name in objects:
                if object_name.endswith('.pickle'):
                    # Có thể implement logic kiểm tra thời gian dựa trên metadata
                    # Hiện tại skip để tránh phức tạp
                    pass

            if count > 0:
                self.logger.info(f"Đã xóa {count} file cache cũ từ MinIO")

        except Exception as e:
            self.logger.error(f"Lỗi dọn dẹp cache MinIO: {str(e)}")

    def _cleanup_local_cache(self):
        """Dọn dẹp cache local"""
        try:
            if not os.path.exists(self.cache_dir):
                return

            current_time = datetime.now()
            count = 0

            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pickle'):
                    file_path = os.path.join(self.cache_dir, filename)
                    file_age = current_time - datetime.fromtimestamp(
                        os.path.getmtime(file_path)
                    )

                    if file_age > self.max_age:
                        os.remove(file_path)
                        count += 1

            if count > 0:
                self.logger.info(f"Đã xóa {count} file cache cũ từ local")

        except Exception as e:
            self.logger.error(f"Lỗi dọn dẹp cache local: {str(e)}")

    def clear_all_cache(self):
        """Xóa toàn bộ cache"""
        try:
            if self.use_minio:
                objects = self.minio_service.list_files(settings.MINIO_CACHE_BUCKET)
                for object_name in objects:
                    self.minio_service.delete_file(settings.MINIO_CACHE_BUCKET, object_name)
                self.logger.info("Đã xóa toàn bộ cache từ MinIO")
            else:
                if os.path.exists(self.cache_dir):
                    for filename in os.listdir(self.cache_dir):
                        if filename.endswith('.pickle'):
                            os.remove(os.path.join(self.cache_dir, filename))
                    self.logger.info("Đã xóa toàn bộ cache local")
        except Exception as e:
            self.logger.error(f"Lỗi xóa toàn bộ cache: {str(e)}")