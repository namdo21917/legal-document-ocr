import logging
import os
from datetime import datetime


class Logger:
    def __init__(self, name):
        # Tạo thư mục logs nếu chưa tồn tại
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Tạo tên file log với timestamp
        log_file = os.path.join(log_dir, f'{datetime.now().strftime("%Y%m%d")}.log')

        # Cấu hình logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Định dạng log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Handler cho file
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Handler cho console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # Thêm handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)