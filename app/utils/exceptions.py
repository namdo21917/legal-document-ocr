class OCRError(Exception):
    """Lớp cơ sở cho các ngoại lệ trong hệ thống OCR"""
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class FileError(OCRError):
    """Ngoại lệ liên quan đến xử lý file"""
    def __init__(self, message, file_path=None):
        super().__init__(message, error_code='FILE_ERROR')
        self.file_path = file_path

class ImageError(OCRError):
    """Ngoại lệ liên quan đến xử lý ảnh"""
    def __init__(self, message, image_info=None):
        super().__init__(message, error_code='IMAGE_ERROR')
        self.image_info = image_info

class ConfigError(OCRError):
    """Ngoại lệ liên quan đến cấu hình"""
    def __init__(self, message, config_key=None):
        super().__init__(message, error_code='CONFIG_ERROR')
        self.config_key = config_key

class OCRProcessError(OCRError):
    """Ngoại lệ liên quan đến quá trình OCR"""
    def __init__(self, message, region_index=None):
        super().__init__(message, error_code='OCR_ERROR')
        self.region_index = region_index

class ValidationError(OCRError):
    """Ngoại lệ liên quan đến validation"""
    def __init__(self, message, validation_target=None):
        super().__init__(message, error_code='VALIDATION_ERROR')
        self.validation_target = validation_target

class ExtractionError(OCRError):
    """Ngoại lệ liên quan đến trích xuất thông tin"""
    def __init__(self, message, field_name=None):
        super().__init__(message, error_code='EXTRACTION_ERROR')
        self.field_name = field_name

class CacheError(OCRError):
    """Ngoại lệ liên quan đến cache"""
    def __init__(self, message, cache_key=None):
        super().__init__(message, error_code='CACHE_ERROR')
        self.cache_key = cache_key