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

    def validate_config(self, config):
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