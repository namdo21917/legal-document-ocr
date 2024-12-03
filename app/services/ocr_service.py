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
from app.models.page import Page
from app.schemas.responses import OCRResponse, DocumentInfo, DocumentMetadata, DocumentResponse, PageMetadata, \
    PageRegionInfo, PageResponse
from app.services.document_merger import DocumentMerger
from app.services.image_preprocessing import ImagePreprocessor
from app.services.information_extraction import InformationExtractor
from app.services.ocr import OCRModule
from app.services.region_segmentation import RegionSegmenter
from app.services.table_detector import TableDetector
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
                return {
                    'success': True,
                    'num_pages': len(all_results),
                    'num_documents': len(merged_docs),
                    'documents': merged_docs,
                    'input_path': input_path  # Thêm đường dẫn file input vào response
                }

            except Exception as e:
                self.logger.error(f"Lỗi xử lý tài liệu: {str(e)}")
                raise

        except Exception as e:
            self.logger.error(f"Lỗi xử lý tài liệu: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def process_and_save_document(self, file: UploadFile, db: Session) -> OCRResponse:
        try:
            # Validate file
            if not await self.validator.validate_file(file):
                raise OCRError("Invalid file format")

            # Xử lý OCR
            ocr_result = await self.process_document(file)
            if not ocr_result['success']:
                raise OCRError(ocr_result['error'])

            # Lưu từng document từ kết quả OCR
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

                # Tạo document trong database
                db_document = Document(
                    document_id=doc_info.get('document_number', ''),
                    extraction_time=datetime.now(),
                    version="1.0",
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

                db.add(db_document)
                db.commit()
                db.refresh(db_document)

                # Lưu các pages của document này
                doc_pages = []
                for page_num in doc_info.get('page_numbers', []):
                    # Tìm thông tin page tương ứng từ all_results
                    page_data = next(
                        (p for p in ocr_result.get('all_results', []) 
                         if p.get('page_number') == page_num), 
                        None
                    )
                    
                    if page_data:
                        # Lấy thông tin từ page_info trong info.json
                        page_info = page_data.get('page_info', {})
                        extracted_info = page_info.get('extracted_info', {})

                        # Lưu ảnh trang
                        image_path = self._save_page_image(
                            page_data['processed_image'], 
                            doc_info['document_number'], 
                            page_num
                        )

                        # Tạo page record với thông tin từ info.json
                        db_page = Page(
                            document_id=db_document.id,
                            page_number=page_num,
                            extraction_time=datetime.now(),
                            version="1.0",
                            
                            # Thông tin regions và tables từ page_info
                            text_regions=page_info.get('text_regions', []),
                            tables=page_info.get('tables', []),
                            
                            # OCR text và image path
                            ocr_text=page_data.get('ocr_text', ''),
                            image_path=image_path,
                            
                            # Thông tin trích xuất từ page
                            document_type=extracted_info.get('document_type'),
                            document_number=extracted_info.get('document_number'),
                            issue_location=extracted_info.get('issue_location'),
                            issue_date=issue_date,  # Sử dụng ngày đã chuyển đổi từ document
                            issuing_agency=extracted_info.get('issuing_agency'),
                            recipients=extracted_info.get('recipients'),
                            recipient_address=extracted_info.get('recipient_address'),
                            signer=extracted_info.get('signer'),
                            position=extracted_info.get('position'),
                            subject=extracted_info.get('subject')
                        )
                        
                        db.add(db_page)
                        doc_pages.append(db_page)

                db.commit()
                for page in doc_pages:
                    db.refresh(page)

                # Tạo response cho document này
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
            self.logger.error(f"Error processing document: {str(e)}")
            raise OCRError(f"Failed to process document: {str(e)}")

    def _save_page_image(self, image, document_number: str, page_number: int) -> str:
        """
        Lưu ảnh của trang vào storage
        """
        try:
            # Tạo thư mục lưu trữ
            storage_dir = os.path.join('storage', 'pages', document_number)
            os.makedirs(storage_dir, exist_ok=True)

            # Tạo tên file và đường dẫn
            image_filename = f"page_{str(page_number).zfill(3)}.png"
            image_path = os.path.join(storage_dir, image_filename)

            # Lưu ảnh
            image.save(image_path)

            return image_path

        except Exception as e:
            self.logger.error(f"Error saving page image: {str(e)}")
            raise OCRError(f"Failed to save page image: {str(e)}")

    async def get_page(self, page_id: int, db: Session) -> PageResponse:
        try:
            db_page = db.query(Page).filter(Page.id == page_id).first()
            if not db_page:
                raise OCRError("Page not found")

            return PageResponse(
                metadata=PageMetadata(
                    page_number=db_page.page_number,
                    extraction_time=db_page.extraction_time,
                    version=db_page.version
                ),
                page_info=PageRegionInfo(
                    text_regions=db_page.text_regions,
                    tables=db_page.tables,
                    extracted_info=DocumentInfo(
                        document_type=db_page.document_type,
                        document_number=db_page.document_number,
                        issue_location=db_page.issue_location,
                        issue_date=db_page.issue_date,
                        issuing_agency=db_page.issuing_agency,
                        recipients=db_page.recipients,
                        recipient_address=db_page.recipient_address,
                        signer=db_page.signer,
                        position=db_page.position,
                        subject=db_page.subject
                    )
                )
            )

        except Exception as e:
            self.logger.error(f"Error getting page: {str(e)}")
            raise OCRError(f"Failed to get page: {str(e)}")

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
