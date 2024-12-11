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
from app.schemas.responses import OCRResponse, DocumentInfo, DocumentMetadata, DocumentResponse
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


class OCRService:
    def __init__(self, config_path='config.json'):
        self.cache = CacheManager()
        self.validator = Validator()
        self.logger = Logger(__name__).logger
        self.num_threads = multiprocessing.cpu_count()

        try:
            # Đọc và kiểm tra cấu hình
            if not self.validator.validate_file(config_path):
                raise ValueError(f"File cấu hình không hợp lệ: {config_path}")

            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            if not self.validator.validate_config(self.config):
                raise ValueError("Cấu hình không hợp lệ")

            # Khởi tạo các module
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
        """
        Xử lý văn bản từ file
        Args:
            file: Có thể là đường dẫn file (str) hoặc UploadFile
        Returns:
            dict: Kết quả xử lý
        """
        self.logger.info(f"Bắt đầu xử lý tài liệu")
        try:
            # Tạo các thư mục cần thiết
            for dir_path in ['output', 'input_img']:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)

            # Xử lý file input
            if isinstance(file, UploadFile):
                # Tạo tên file với timestamp để tránh trùng lặp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{file.filename}"
                input_path = os.path.join('input_img', filename)
                
                # Lưu file vào thư mục input_img
                with open(input_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                await file.seek(0)
            else:
                input_path = file
                
            try:
                # Đọc và xử lý ảnh
                if input_path.lower().endswith('.pdf'):
                    images = self.preprocessor.convert_from_pdf(input_path)
                    if not images:
                        raise FileError("Không thể chuyển đổi PDF", input_path)
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
                    'input_path': input_path  # Thêm đường dẫn file input vào response
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

                    # Tạo response cho document này
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

    async def save_document(self, document_data: dict, db: Session) -> OCRResponse:
        """
        Lưu thông tin document từ JSON vào database
        Args:
            document_data: JSON kết quả từ API create_document
            db: Database session
        Returns:
            OCRResponse: Thông tin document đã lưu
        """
        try:
            document_responses = []
            for doc in document_data['documents']:
                # Chuyển đổi định dạng ngày tháng
                issue_date_str = doc['document_info'].get('issue_date')
                issue_date = None
                if issue_date_str:
                    try:
                        issue_date = datetime.strptime(issue_date_str, '%d/%m/%Y')
                    except ValueError:
                        self.logger.warning(f"Không thể chuyển đổi ngày tháng: {issue_date_str}")

                # Tạo document trong database
                db_document = Document(
                    document_id=doc['document_info'].get('document_number', ''),
                    extraction_time=datetime.now(),
                    version="1.0",
                    document_type=doc['document_info'].get('document_type'),
                    document_number=doc['document_info'].get('document_number'),
                    issue_location=doc['document_info'].get('issue_location'),
                    issue_date=issue_date,
                    issuing_agency=doc['document_info'].get('issuing_agency'),
                    recipients=doc['document_info'].get('recipients'),
                    recipient_address=doc['document_info'].get('recipient_address'),
                    signer=doc['document_info'].get('signer'),
                    position=doc['document_info'].get('position'),
                    subject=doc['document_info'].get('subject'),
                    content=doc['document_info'].get('content'),
                    page_numbers=doc['document_info'].get('page_numbers', [])
                )

                db.add(db_document)
                db.commit()
                db.refresh(db_document)

                # Tạo response cho document đã lưu
                document_response = DocumentResponse(
                    metadata=DocumentMetadata(
                        document_id=str(db_document.id),
                        extraction_time=db_document.extraction_time,
                        version="1.0"
                    ),
                    document_info=DocumentInfo(
                        document_type=db_document.document_type,
                        document_number=db_document.document_number,
                        issue_location=db_document.issue_location,
                        issue_date=db_document.issue_date,
                        issuing_agency=db_document.issuing_agency,
                        recipients=db_document.recipients,
                        recipient_address=db_document.recipient_address,
                        signer=db_document.signer,
                        position=db_document.position,
                        subject=db_document.subject,
                        content=db_document.content,
                        page_numbers=db_document.page_numbers
                    )
                )
                document_responses.append(document_response)

            return OCRResponse(documents=document_responses)

        except Exception as e:
            db.rollback()
            self.logger.error(f"Error saving document: {str(e)}")
            raise OCRError(f"Failed to save document: {str(e)}")

    async def get_document_list(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 10,
        document_type: str = None
    ) -> List[DocumentResponse]:
        """
        Lấy danh sách documents với phân trang và filter
        Args:
            db: Database session
            skip: Số records bỏ qua
            limit: Số records lấy
            document_type: Loại văn bản để filter
        Returns:
            List[DocumentResponse]: Danh sách documents đã format
        """
        try:
            # Base query
            query = db.query(Document)
            
            # Apply filters
            if document_type:
                query = query.filter(Document.document_type == document_type)
            
            # Get total count for pagination
            total = query.count()
            
            # Apply pagination
            documents = query.offset(skip).limit(limit).all()
            
            # Convert to response format
            responses = []
            for doc in documents:
                responses.append(
                    DocumentResponse(
                        metadata=DocumentMetadata(
                            document_id=str(doc.id),
                            extraction_time=doc.extraction_time,
                            version=doc.version
                        ),
                        document_info=DocumentInfo(
                            document_type=doc.document_type,
                            document_number=doc.document_number,
                            issue_location=doc.issue_location,
                            issue_date=doc.issue_date,
                            issuing_agency=doc.issuing_agency,
                            recipients=doc.recipients,
                            recipient_address=doc.recipient_address,
                            signer=doc.signer,
                            position=doc.position,
                            subject=doc.subject,
                            content=doc.content,
                            page_numbers=doc.page_numbers
                        )
                    )
                )
            
            return responses

        except Exception as e:
            self.logger.error(f"Error getting document list: {str(e)}")
            raise OCRError(f"Failed to get document list: {str(e)}")
