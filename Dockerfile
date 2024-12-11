# Sử dụng Python 3.10 base image
FROM python:3.10-slim

# Thiết lập working directory
WORKDIR /app

# Cài đặt các system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-vie \
    poppler-utils \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Cài đặt Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Tạo các thư mục cần thiết
RUN mkdir -p logs cache output static/uploads

# Thiết lập environment variables
ENV PYTHONPATH=/app
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
ENV TESSERACT_CMD=/usr/bin/tesseract
ENV POPPLER_PATH=/usr/lib/x86_64-linux-gnu/poppler
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Command để chạy ứng dụng
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 