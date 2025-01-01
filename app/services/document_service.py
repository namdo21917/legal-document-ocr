from datetime import datetime
from typing import List
from math import ceil

from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.documents import OCRResponse, DocumentResponse, DocumentMetadata, DocumentInfo, DocumentDeleteResponse, PaginatedDocumentResponse
from app.utils.exceptions import OCRError
from app.utils.logger import Logger


class DocumentService:
    def __init__(self):
        self.logger = Logger(__name__).logger

    async def save_document(self, document_data: dict, db: Session) -> OCRResponse:
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
    ) -> PaginatedDocumentResponse:
        try:
            # Base query
            query = db.query(Document)

            # Apply filters
            if document_type:
                query = query.filter(Document.document_type == document_type)

            # Get total count for pagination
            total = query.count()

            # Calculate pagination info
            page = skip // limit + 1
            total_pages = ceil(total / limit) if total > 0 else 0

            # Get records for current page
            documents = query.offset(skip).limit(limit).all()

            # Convert to response format
            document_responses = [self.get_document_response(doc) for doc in documents]

            return PaginatedDocumentResponse(
                items=document_responses,
                total=total,
                page=page,
                size=limit,
                pages=total_pages
            )

        except Exception as e:
            self.logger.error(f"Error getting document list: {str(e)}")
            raise OCRError(f"Failed to get document list: {str(e)}")

    async def delete_document(self, document_id: str, db: Session) -> DocumentDeleteResponse:
        try:
            # Tìm document cần xóa
            document = db.query(Document).filter(Document.id == document_id).first()
            
            # Kiểm tra document có tồn tại không
            if document is None:
                raise OCRError(f"Không tìm thấy document với ID: {id}")
            
            # Thực hiện xóa document
            db.delete(document)
            db.commit()
            
            # Trả về response
            return DocumentDeleteResponse(
                success=True,
                message=f"Đã xóa thành công document có ID: {document_id}",
                document_id=document_id
            )

        except Exception as e:
            # Rollback trong trường hợp có lỗi
            db.rollback()
            self.logger.error(f"Lỗi khi xóa document {document_id}: {str(e)}")
            raise OCRError(f"Không thể xóa document: {str(e)}")

    async def get_document_by_id(self, document_id: str, db: Session) -> DocumentResponse:
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document is None:
                raise OCRError(f"Không tìm thấy document với ID: {document_id}")

            return self.get_document_response(document)

        except Exception as e:
            self.logger.error(f"Lỗi khi lấy thông tin document {document_id}: {str(e)}")
            raise OCRError(f"Không thể lấy thông tin document: {str(e)}")

    async def update_document(self, document_id: str, document_data: dict, db: Session) -> DocumentResponse:
        try:
            # Tìm document cần cập nhật
            document = db.query(Document).filter(Document.id == document_id).first()
            if document is None:
                raise OCRError(f"Không tìm thấy document với ID: {document_id}")

            # Mapping dữ liệu từ document_data vào document
            if 'document_info' in document_data:
                doc_info = document_data['document_info']
                
                # Cập nhật các trường trong document_info
                document.document_type = doc_info.get('document_type', document.document_type)
                document.document_number = doc_info.get('document_number', document.document_number)
                document.issue_location = doc_info.get('issue_location', document.issue_location)
                document.issuing_agency = doc_info.get('issuing_agency', document.issuing_agency)
                document.recipients = doc_info.get('recipients', document.recipients)
                document.recipient_address = doc_info.get('recipient_address', document.recipient_address)
                document.signer = doc_info.get('signer', document.signer)
                document.position = doc_info.get('position', document.position)
                document.subject = doc_info.get('subject', document.subject)
                document.content = doc_info.get('content', document.content)
                document.page_numbers = doc_info.get('page_numbers', document.page_numbers)
                
                # Xử lý đặc biệt cho trường issue_date
                issue_date = doc_info.get('issue_date')
                if issue_date:
                    try:
                        if isinstance(issue_date, str):
                            document.issue_date = datetime.strptime(issue_date, '%d/%m/%Y')
                        else:
                            document.issue_date = issue_date
                    except ValueError as e:
                        self.logger.warning(f"Không thể chuyển đổi ngày tháng: {issue_date}, error: {str(e)}")

            # Cập nhật metadata nếu có
            if 'metadata' in document_data:
                metadata = document_data['metadata']
                document.version = metadata.get('version', document.version)
                # Không cho phép cập nhật document_id và extraction_time từ bên ngoài
                
            # Lưu thay đổi vào database
            db.commit()
            db.refresh(document)

            # Tạo và trả về response
            return self.get_document_response(document)

        except Exception as e:
            db.rollback()
            self.logger.error(f"Lỗi khi cập nhật document {document_id}: {str(e)}")
            raise OCRError(f"Không thể cập nhật document: {str(e)}")

    def get_document_response(self, document: Document) -> DocumentResponse:
        return DocumentResponse(
            metadata=DocumentMetadata(
                document_id=str(document.id),
                extraction_time=document.extraction_time,
                version=document.version
            ),
            document_info=DocumentInfo(
                document_type=document.document_type,
                document_number=document.document_number,
                issue_location=document.issue_location,
                issue_date=document.issue_date,
                issuing_agency=document.issuing_agency,
                recipients=document.recipients,
                recipient_address=document.recipient_address,
                signer=document.signer,
                position=document.position,
                subject=document.subject,
                content=document.content,
                page_numbers=document.page_numbers
            )
        )

