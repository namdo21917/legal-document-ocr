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
        'tesseract' if os.name != 'nt' else r'C:\Users\adminb\Desktop\STUDY\IT\LapTrinhPython\tessaract\tesseract.exe'
        #r'E:\OCR_Resources\Tessaract_OCR\tesseract.exe'
    )
    
    POPPLER_PATH: str = os.getenv(
        'POPPLER_PATH',
        '/usr/lib/x86_64-linux-gnu/poppler' if os.name != 'nt' else r'C:\Users\adminb\Desktop\STUDY\IT\LapTrinhPython\poppler\poppler-24.08.0\Library\bin'
        #r"E:\OCR_Resources\poppler\poppler-24.08.0\Library\bin"
    )

    class Config:
        env_file = './.env'


settings = Settings()