#!/usr/bin/env python3
"""
Script khởi tạo MinIO buckets và cấu hình cần thiết
"""

import os
import sys
import time
from minio import Minio
from minio.error import S3Error

# Thêm thư mục gốc vào Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.utils.logger import Logger

logger = Logger(__name__).logger

def wait_for_minio(client, max_retries=30, delay=2):
    """Đợi MinIO service sẵn sàng"""
    for i in range(max_retries):
        try:
            # Thử list buckets để kiểm tra kết nối
            client.list_buckets()
            logger.info("MinIO service đã sẵn sàng")
            return True
        except Exception as e:
            logger.info(f"Đang đợi MinIO service... (lần thử {i+1}/{max_retries})")
            time.sleep(delay)
    
    logger.error("Không thể kết nối đến MinIO service")
    return False

def create_bucket_if_not_exists(client, bucket_name):
    """Tạo bucket nếu chưa tồn tại"""
    try:
        if client.bucket_exists(bucket_name):
            logger.info(f"Bucket '{bucket_name}' đã tồn tại")
            return True
        
        client.make_bucket(bucket_name)
        logger.info(f"Đã tạo bucket '{bucket_name}'")
        return True
        
    except S3Error as e:
        logger.error(f"Lỗi tạo bucket '{bucket_name}': {e}")
        return False

def set_bucket_policy(client, bucket_name, policy):
    """Thiết lập policy cho bucket"""
    try:
        client.set_bucket_policy(bucket_name, policy)
        logger.info(f"Đã thiết lập policy cho bucket '{bucket_name}'")
        return True
    except S3Error as e:
        logger.error(f"Lỗi thiết lập policy cho bucket '{bucket_name}': {e}")
        return False

def create_public_read_policy(bucket_name):
    """Tạo policy cho phép đọc public"""
    return f"""{{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Effect": "Allow",
            "Principal": {{"AWS": ["*"]}},
            "Action": ["s3:GetObject"],
            "Resource": ["arn:aws:s3:::{bucket_name}/*"]
        }}
    ]
}}"""

def main():
    """Hàm chính"""
    logger.info("Bắt đầu khởi tạo MinIO...")
    
    try:
        # Tạo MinIO client
        client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        
        # Đợi MinIO service sẵn sàng
        if not wait_for_minio(client):
            sys.exit(1)
        
        # Danh sách buckets cần tạo
        buckets = [
            settings.MINIO_INPUT_BUCKET,
            settings.MINIO_OUTPUT_BUCKET,
            settings.MINIO_CACHE_BUCKET
        ]
        
        # Tạo các buckets
        success_count = 0
        for bucket_name in buckets:
            if create_bucket_if_not_exists(client, bucket_name):
                success_count += 1
        
        if success_count == len(buckets):
            logger.info(f"Đã tạo thành công {success_count}/{len(buckets)} buckets")
            
            # Thiết lập policy cho output bucket (cho phép đọc public)
            output_policy = create_public_read_policy(settings.MINIO_OUTPUT_BUCKET)
            set_bucket_policy(client, settings.MINIO_OUTPUT_BUCKET, output_policy)
            
            logger.info("Khởi tạo MinIO hoàn tất!")
            return True
        else:
            logger.error(f"Chỉ tạo được {success_count}/{len(buckets)} buckets")
            return False
            
    except Exception as e:
        logger.error(f"Lỗi khởi tạo MinIO: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
