FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-vie \
    poppler-utils \
    libpoppler-cpp-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Verify poppler installation
RUN which pdftoppm && pdftoppm -h || echo "Poppler not found in PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p logs cache output static/uploads

ENV PYTHONPATH=/app
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
ENV TESSERACT_CMD=/usr/bin/tesseract
ENV POPPLER_PATH=/usr/lib/x86_64-linux-gnu/poppler
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
