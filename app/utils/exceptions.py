class OCRException(Exception):
    """Base exception for OCR service"""
    pass

class FileValidationError(OCRException):
    """Raised when file validation fails"""
    pass

class PreprocessingError(OCRException):
    """Raised when image preprocessing fails"""
    pass

class OCRError(OCRException):
    """Raised when OCR process fails"""
    pass

class TableExtractionError(OCRException):
    """Raised when table extraction fails"""
    pass

class DatabaseError(OCRException):
    """Raised when database operations fail"""
    pass 