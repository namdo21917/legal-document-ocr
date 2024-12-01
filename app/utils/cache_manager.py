import os
import json
import hashlib
import pickle
from datetime import datetime, timedelta
from logger import Logger


class CacheManager:
    def __init__(self, cache_dir='cache', max_age_days=7):
        """
        Khởi tạo CacheManager
        Args:
            cache_dir: Thư mục lưu cache
            max_age_days: Số ngày tối đa lưu cache
        """
        self.logger = Logger(__name__).logger
        self.cache_dir = cache_dir
        self.max_age = timedelta(days=max_age_days)

        # Tạo thư mục cache nếu chưa tồn tại
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            self.logger.info(f"Đã tạo thư mục cache: {cache_dir}")

        # Dọn dẹp cache cũ
        self.cleanup_old_cache()

    def generate_key(self, image):
        """
        Tạo key cho cache từ ảnh
        Args:
            image: PIL Image hoặc numpy array
        Returns:
            str: Key của cache
        """
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

    def get(self, key):
        """
        Lấy kết quả từ cache
        Args:
            key: Key của cache
        Returns:
            dict: Kết quả OCR hoặc None nếu không tìm thấy
        """
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
                self.logger.debug(f"Đã đọc cache: {key}")
                return result

        except Exception as e:
            self.logger.error(f"Lỗi đọc cache: {str(e)}")
            return None

    def set(self, key, value):
        """
        Lưu kết quả vào cache
        Args:
            key: Key của cache
            value: Giá trị cần lưu
        """
        try:
            cache_file = os.path.join(self.cache_dir, f"{key}.pickle")

            # Lưu cache
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
                self.logger.debug(f"Đã lưu cache: {key}")

        except Exception as e:
            self.logger.error(f"Lỗi lưu cache: {str(e)}")

    def cleanup_old_cache(self):
        """
        Dọn dẹp các file cache cũ
        """
        try:
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
                self.logger.info(f"Đã xóa {count} file cache cũ")

        except Exception as e:
            self.logger.error(f"Lỗi dọn dẹp cache: {str(e)}")