import json
import multiprocessing
import os
from datetime import datetime
from typing import List

from PIL import Image
from fastapi import UploadFile
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile

from app.models.document import Document
from app.schemas.documents import OCRResponse, DocumentInfo, DocumentMetadata, DocumentResponse
from app.services.document_merger_service import DocumentMerger
from app.services.image_preprocessing_service import ImagePreprocessor
from app.services.information_extraction_service import InformationExtractor
from app.services.ocr_process_service import OCRModule
from app.services.region_segmentation_service import RegionSegmenter
from app.services.table_detector_service import TableDetector
from app.utils.cache_manager import CacheManager
from app.utils.exceptions import FileError, OCRProcessError, OCRError
from app.utils.logger import Logger
from app.utils.validation import Validator
from app.services.storage_service import StorageService


class OCRService:
    def __init__(self, config_path='config.json'):
        self.cache = CacheManager()
        self.validator = Validator()
        self.logger = Logger(__name__).logger
        self.num_threads = multiprocessing.cpu_count()
        self.storage = StorageService()

        try:
            if not self.validator.validate_file(config_path):
                raise ValueError(f"File cấu hình không hợp lệ: {config_path}")

            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            if not self.validator.validate_config(self.config):
                raise ValueError("Cấu hình không hợp lệ")

            self.preprocessor = ImagePreprocessor(self.config)
            self.segmenter = RegionSegmenter(self.config)
            self.ocr = OCRModule()
            self.extractor = InformationExtractor(self.config)
            self.table_detector = TableDetector(self.config)
            self.document_merger = DocumentMerger(self.config)

            self.logger.info("Khởi tạo các module thành công")

        except Exception as e:
            self.logger.error(f"Lỗi khởi tạo hệ thống: {str(e)}")
            raise

    async def process_document(self, file):
        self.logger.info(f"Bắt đầu xử lý tài liệu")
        try:
            # Tạo các thư mục cần thiết (chỉ còn output cho kết quả)
            if not os.path.exists('output'):
                os.makedirs('output')

            # Xử lý file input
            if isinstance(file, UploadFile):
                # Tạo tên file với timestamp để tránh trùng lặp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{file.filename}"
                # Đọc nội dung file
                content = await file.read()
                await file.seek(0)
                # Upload lên MinIO
                minio_url = self.storage.upload_file(content, f"input/{filename}", file.content_type or 'application/octet-stream')
                input_path = filename  # Lưu tên file để xử lý tiếp
            else:
                input_path = file
                
            try:
                # Đọc và xử lý ảnh
                file_bytes = None
                if isinstance(file, UploadFile) or (isinstance(input_path, str) and not os.path.exists(input_path)):
                    minio_key = f"input/{input_path}" if not input_path.startswith("input/") else input_path
                    file_bytes = self.storage.download_file(minio_key)

                if input_path.lower().endswith('.pdf'):
                    if file_bytes:
                        # Lưu tạm file pdf để dùng convert_from_pdf
                        tmp_pdf = f"/tmp/{input_path}"
                        with open(tmp_pdf, "wb") as f:
                            f.write(file_bytes)
                        images = self.preprocessor.convert_from_pdf(tmp_pdf)
                        os.remove(tmp_pdf)
                    else:
                        images = self.preprocessor.convert_from_pdf(input_path)
                    if not images:
                        raise FileError("Không thể chuyển đổi PDF", input_path)
                else:
                    if file_bytes:
                        from io import BytesIO
                        images = [Image.open(BytesIO(file_bytes))]
                    else:
                        images = [Image.open(input_path)]

                all_results = []
                # Xử lý từng trang
                for page_num, image in enumerate(images, 1):
                    self.logger.info(f"Xử lý trang {page_num}/{len(images)}")
                    try:
                        # Tiền xử lý ảnh
                        binary_image = self.preprocessor.preprocess(image)

                        # Tìm các vùng văn bản
                        regions = self.segmenter.find_text_regions(binary_image)
                        if not regions:
                            self.logger.warning(f"Không tìm thấy vùng văn bản nào trong trang {page_num}")
                            continue

                        # Vẽ khung vùng văn bản
                        marked_image = self.segmenter.draw_regions(image, regions)

                        # Trích xuất và OCR các vùng
                        region_images = self.segmenter.extract_regions(image, regions)
                        ocr_results = self.ocr.recognize_regions(region_images)

                        # Kết hợp kết quả OCR
                        full_text = '\n'.join([result['text'] for result in ocr_results])

                        # Trích xuất thông tin
                        extracted_info = self.extractor.extract_information(full_text)['document_info']

                        # Phát hiện bảng
                        tables = self.table_detector.detect_tables(binary_image)
                        if tables:
                            self.logger.info(f"Đã phát hiện {len(tables)} bảng trong trang {page_num}")
                            for table in tables:
                                marked_image = self.table_detector.draw_table_boundaries(marked_image, table)

                        # Lưu kết quả trang
                        page_result = {
                            'page_number': page_num,
                            'processed_image': marked_image,
                            'ocr_text': full_text,
                            'extracted_info': extracted_info,
                            'regions': regions,
                            'tables': tables if tables else []
                        }
                        all_results.append(page_result)

                    except Exception as e:
                        self.logger.error(f"Lỗi xử lý trang {page_num}: {str(e)}")
                        continue

                if not all_results:
                    raise OCRProcessError("Không xử lý được trang nào")

                # Gộp các văn bản liên quan
                merged_docs = self.document_merger.merge_documents(all_results)

                # Lưu kết quả đã gộp
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                self.document_merger.save_merged_documents(
                    merged_docs,
                    'output',
                    base_name
                )

                self.logger.info(f"Xử lý thành công {len(all_results)} trang")
                ocr_result = {
                    'success': True,
                    'num_pages': len(all_results),
                    'num_documents': len(merged_docs),
                    'documents': merged_docs,
                    'input_path': input_path
                }

                document_responses = []
                for doc in ocr_result['documents']:
                    doc_info = doc['document_info']

                    # Chuyển đổi định dạng ngày tháng
                    issue_date_str = doc_info.get('issue_date')
                    issue_date = None
                    if issue_date_str:
                        try:
                            issue_date = datetime.strptime(issue_date_str, '%d/%m/%Y')
                        except ValueError:
                            self.logger.warning(f"Không thể chuyển đổi ngày tháng: {issue_date_str}")

                    document_response = DocumentResponse(
                        metadata=DocumentMetadata(
                            document_id=doc_info.get('document_number', ''),
                            extraction_time=datetime.now(),
                            version="1.0"
                        ),
                        document_info=DocumentInfo(
                            document_type=doc_info.get('document_type'),
                            document_number=doc_info.get('document_number'),
                            issue_location=doc_info.get('issue_location'),
                            issue_date=issue_date,
                            issuing_agency=doc_info.get('issuing_agency'),
                            recipients=doc_info.get('recipients'),
                            recipient_address=doc_info.get('recipient_address'),
                            signer=doc_info.get('signer'),
                            position=doc_info.get('position'),
                            subject=doc_info.get('subject'),
                            content=doc_info.get('content'),
                            page_numbers=doc_info.get('page_numbers', [])
                        )
                    )
                    document_responses.append(document_response)

                return OCRResponse(documents=document_responses)

            except Exception as e:
                self.logger.error(f"Lỗi xử lý tài liệu: {str(e)}")
                raise

        except Exception as e:
            self.logger.error(f"Lỗi xử lý tài liệu: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


