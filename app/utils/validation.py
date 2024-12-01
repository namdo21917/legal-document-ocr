import os
from starlette.datastructures import UploadFile
from PIL import Image
import json

from app.utils.logger import Logger


class Validator:
    ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.json'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self):
        self.logger = Logger(__name__).logger

    async def validate_file(self, file):
        """
        Kiểm tra tính hợp lệ của file
        Args:
            file: Có thể là đường dẫn file (str) hoặc UploadFile
        Returns:
            bool: True nếu hợp lệ, False nếu không hợp lệ
        """
        try:
            if isinstance(file, (UploadFile, "starlette.datastructures.UploadFile".__class__)):
                # Kiểm tra file upload
                filename = file.filename
                # Kiểm tra kích thước file
                file_size = 0
                chunk_size = 1024  # 1KB
                while chunk := await file.read(chunk_size):
                    file_size += len(chunk)
                await file.seek(0)  # Reset file pointer
                
                if file_size > self.MAX_FILE_SIZE:
                    self.logger.error(f"File quá lớn: {file_size} bytes")
                    return False
                    
            elif isinstance(file, (str, bytes, os.PathLike)):
                # Kiểm tra đường dẫn file
                filename = str(file)
                if not os.path.exists(filename):
                    self.logger.error(f"File không tồn tại: {filename}")
                    return False
                    
                if os.path.getsize(filename) > self.MAX_FILE_SIZE:
                    self.logger.error(f"File quá lớn: {filename}")
                    return False
            else:
                self.logger.error(f"Kiểu file không hợp lệ: {type(file)}")
                return False

            # Kiểm tra phần mở rộng
            ext = os.path.splitext(filename)[1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                self.logger.error(f"Không hỗ trợ định dạng file {ext}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Lỗi kiểm tra file: {str(e)}")
            return False

    def validate_image(self, image):
        """
        Kiểm tra tính hợp lệ của ảnh
        Args:
            image: Đối tượng ảnh (PIL Image hoặc numpy array)
        Returns:
            bool: True nếu hợp lệ, False nếu không hợp lệ
        """
        try:
            if isinstance(image, Image.Image):
                # Kiểm tra kích thước ảnh
                if image.size[0] < 100 or image.size[1] < 100:
                    self.logger.error("Kích thước ảnh quá nhỏ")
                    return False
                # Kiểm tra mode ảnh
                if image.mode not in ['RGB', 'L']:
                    self.logger.error(f"Mode ảnh không được hỗ trợ: {image.mode}")
                    return False
            else:
                self.logger.error("Định dạng ảnh không được hỗ trợ")
                return False

            return True
        except Exception as e:
            self.logger.error(f"Lỗi kiểm tra ảnh: {str(e)}")
            return False

    def validate_config(self, config):
        """
        Kiểm tra tính hợp lệ của cấu hình
        Args:
            config: Dict cấu hình
        Returns:
            bool: True nếu hợp lệ, False nếu không hợp lệ
        """
        required_sections = ['preprocessing', 'segmentation', 'extraction_patterns']
        required_preprocessing = [
            'clahe_clip_limit', 'clahe_grid_size',
            'gaussian_kernel_size', 'gaussian_sigma',
            'morph_kernel_size', 'adaptive_block_size', 'adaptive_c'
        ]
        required_segmentation = [
            'min_contour_area', 'min_aspect_ratio', 'max_aspect_ratio'
        ]

        try:
            # Kiểm tra các section bắt buộc
            for section in required_sections:
                if section not in config:
                    self.logger.error(f"Thiếu section trong config: {section}")
                    return False

            # Kiểm tra các tham số tiền xử lý
            for param in required_preprocessing:
                if param not in config['preprocessing']:
                    self.logger.error(f"Thiếu tham số tiền xử lý: {param}")
                    return False

            # Kiểm tra các tham số phân đoạn
            for param in required_segmentation:
                if param not in config['segmentation']:
                    self.logger.error(f"Thiếu tham số phân đoạn: {param}")
                    return False

            return True
        except Exception as e:
            self.logger.error(f"Lỗi kiểm tra cấu hình: {str(e)}")
            return False