import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_PORT: int
    POSTGRES_PASSWORD: str
    POSTGRES_USER: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_HOSTNAME: str

    CLIENT_ORIGIN: str

    TESSERACT_CMD: str = os.getenv(
        'TESSERACT_CMD',
        'tesseract'
        #if os.name != 'nt' else r'E:\OCR_Resources\Tessaract_OCR\tesseract.exe'
        # r'C:\Users\adminb\Desktop\STUDY\IT\LapTrinhPython\tessaract\tesseract.exe'
    )
    
    POPPLER_PATH: str = os.getenv(
        'POPPLER_PATH',
        '/usr/bin'  # Đường dẫn mặc định trong Ubuntu/Debian container
        # if os.name != 'nt' else r"E:\OCR_Resources\poppler\poppler-24.08.0\Library\bin"
        # r'C:\Users\adminb\Desktop\STUDY\IT\LapTrinhPython\poppler\poppler-24.08.0\Library\bin'
    )

    MINIO_ENDPOINT: str = os.getenv('MINIO_ENDPOINT', 'http://minio:9000')
    MINIO_ACCESS_KEY: str = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY: str = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    MINIO_BUCKET: str = os.getenv('MINIO_BUCKET', 'ocr-bucket')

    class Config:
        env_file = './.env'


settings = Settings()