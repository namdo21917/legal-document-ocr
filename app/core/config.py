import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'  # Bỏ qua các field không được định nghĩa
    )

    DATABASE_PORT: int = 5432
    POSTGRES_PASSWORD: str = 'postgres'
    POSTGRES_USER: str = 'postgres'
    POSTGRES_DB: str = 'legal_document_ocr_db'
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_HOSTNAME: str = 'localhost'

    CLIENT_ORIGIN: str = 'http://localhost:5173'

    TESSERACT_CMD: str = os.getenv(
        'TESSERACT_CMD',
        'tesseract'
        #if os.name != 'nt' else r'E:\OCR_Resources\Tessaract_OCR\tesseract.exe'
        # r'C:\Users\adminb\Desktop\STUDY\IT\LapTrinhPython\tessaract\tesseract.exe'
    )
    
    POPPLER_PATH: str = os.getenv(
        'POPPLER_PATH',
        '/usr/lib/x86_64-linux-gnu/poppler'
        # if os.name != 'nt' else r"E:\OCR_Resources\poppler\poppler-24.08.0\Library\bin"
        # r'C:\Users\adminb\Desktop\STUDY\IT\LapTrinhPython\poppler\poppler-24.08.0\Library\bin'
    )

    # MinIO Configuration
    MINIO_ROOT_USER: str = 'minioadmin'
    MINIO_ROOT_PASSWORD: str = 'minioadmin123'
    MINIO_API_PORT: int = 9000
    MINIO_CONSOLE_PORT: int = 9001

    MINIO_ENDPOINT: str = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_ACCESS_KEY: str = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY: str = os.getenv('MINIO_SECRET_KEY', 'minioadmin123')
    MINIO_SECURE: bool = os.getenv('MINIO_SECURE', 'false').lower() == 'true'

    # MinIO Buckets
    MINIO_INPUT_BUCKET: str = 'input-files'
    MINIO_OUTPUT_BUCKET: str = 'output-files'
    MINIO_CACHE_BUCKET: str = 'cache-files'





settings = Settings()