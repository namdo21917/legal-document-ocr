from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class DocumentBase(BaseModel):
    document_id: str
    document_type: Optional[str] = None
    content: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    extraction_time: datetime

    class Config:
        from_attributes = True 