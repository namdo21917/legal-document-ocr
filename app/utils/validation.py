import os
from PIL import Image
# import magic

class FileValidator:
    ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def validate_file(self, file_path):
        """Kiểm tra tính hợp lệ của file"""
        # Kiểm tra đuôi file
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Không hỗ trợ định dạng file {ext}")

        # Kiểm tra kích thước
        if os.path.getsize(file_path) > self.MAX_FILE_SIZE:
            raise ValueError("File quá lớn")

        # Kiểm tra mime type
        # mime = magic.from_file(file_path, mime=True)
        # if not self._validate_mime_type(mime):
        #     raise ValueError("Định dạng file không hợp lệ")

        return True