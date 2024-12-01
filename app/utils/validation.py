import os
from PIL import Image
import json

from app.utils.logger import Logger


class Validator:
    ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', 'json'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self):
        self.logger = Logger(__name__).logger

    def validate_file(self, file_path):
        """
        Kiểm tra tính hợp lệ của đường dẫn file
        Args:
            file_path: Đường dẫn file cần kiểm tra
            allowed_extensions: List các phần mở rộng được cho phép
        Returns:
            bool: True nếu hợp lệ, False nếu không hợp lệ
        """
        try:
            # Kiểm tra file có tồn tại
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in self.ALLOWED_EXTENSIONS:
                raise ValueError(f"Không hỗ trợ định dạng file {ext}")

            return True
        except Exception as e:
            self.logger.error(f"Lỗi kiểm tra đường dẫn file: {str(e)}")
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
        Kiểm tra tính hợp lệ của c���u hình
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