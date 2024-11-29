from typing import Optional
from pydantic import BaseModel

class PageBase(BaseModel):
    document_id: int
    page_number: int
    ocr_text: Optional[str] = None
    image_path: Optional[str] = None

class Page(PageBase):
    id: int

    class Config:
        from_attributes = True 