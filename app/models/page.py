from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base

class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    page_number = Column(Integer)
    extraction_time = Column(DateTime)
    version = Column(String(50))
    
    # Page info
    text_regions = Column(JSON)  # Store as JSON array of arrays
    tables = Column(JSON, default=[])  # Store table detection results
    ocr_text = Column(String)  # Full OCR text
    image_path = Column(String)  # Path to stored image
    
    # Extracted info (same fields as document for each page)
    document_type = Column(String(100))
    document_number = Column(String(100))
    issue_location = Column(String(200))
    issue_date = Column(String(50))
    issuing_agency = Column(String(200))
    recipients = Column(String(500))
    recipient_address = Column(String(500))
    signer = Column(String(200))
    position = Column(String(200))
    subject = Column(String)
    
    document = relationship("Document", back_populates="pages")