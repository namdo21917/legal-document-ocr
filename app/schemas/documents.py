from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

# Document Response Models
class DocumentMetadata(BaseModel):
    document_id: str
    extraction_time: datetime
    version: str

class DocumentInfo(BaseModel):
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    issue_location: Optional[str] = None
    issue_date: Optional[datetime] = None
    issuing_agency: Optional[str] = None
    recipients: Optional[str] = None
    recipient_address: Optional[str] = None
    signer: Optional[str] = None
    position: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    page_numbers: List[int]

class DocumentResponse(BaseModel):
    metadata: DocumentMetadata
    document_info: DocumentInfo

class DocumentDeleteResponse(BaseModel):
    success: bool
    message: str
    document_id: str

class OCRResponse(BaseModel):
    documents: List[DocumentResponse] 