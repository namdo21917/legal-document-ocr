from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.models.document import Document
from app.schemas.responses import OCRResponse, DocumentResponse, DocumentMetadata, DocumentInfo, DocumentDeleteResponse
from app.utils.exceptions import OCRError


class DocumentService:

    async def save_document(self, document_data: dict, db: Session) -> OCRResponse:
        """
        Lưu thông tin document từ JSON vào database
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

    async def delete_document(self, document_id: str, db: Session) -> DocumentDeleteResponse:
        """
        Xóa document theo document_id
        
        Args:
            document_id: ID của document cần xóa
            db: Database session
            
        Returns:
            DocumentDeleteResponse: Thông tin về kết quả xóa document
            
        Raises:
            OCRError: Nếu có lỗi trong quá trình xóa
        """
        try:
            # Tìm document cần xóa
            document = db.query(Document).filter(Document.document_id == document_id).first()
            
            # Kiểm tra document có tồn tại không
            if document is None:
                raise OCRError(f"Không tìm thấy document với ID: {document_id}")
            
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
        """
        Lấy thông tin chi tiết của một document theo ID
        """
        try:
            document = db.query(Document).filter(Document.document_id == document_id).first()
            if document is None:
                raise OCRError(f"Không tìm thấy document với ID: {document_id}")

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

        except Exception as e:
            self.logger.error(f"Lỗi khi lấy thông tin document {document_id}: {str(e)}")
            raise OCRError(f"Không thể lấy thông tin document: {str(e)}")

    async def update_document(self, document_id: str, document_data: dict, db: Session) -> DocumentResponse:
        """
        Cập nhật thông tin của một document
        """
        try:
            document = db.query(Document).filter(Document.document_id == document_id).first()
            if document is None:
                raise OCRError(f"Không tìm thấy document với ID: {document_id}")

            # Cập nhật các trường thông tin
            for field, value in document_data.items():
                if hasattr(document, field):
                    # Xử lý đặc biệt cho trường issue_date
                    if field == 'issue_date' and value:
                        try:
                            value = datetime.strptime(value, '%d/%m/%Y')
                        except ValueError:
                            self.logger.warning(f"Không thể chuyển đổi ngày tháng: {value}")
                            continue
                    setattr(document, field, value)

            db.commit()
            db.refresh(document)

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

        except Exception as e:
            db.rollback()
            self.logger.error(f"Lỗi khi cập nhật document {document_id}: {str(e)}")
            raise OCRError(f"Không thể cập nhật document: {str(e)}")