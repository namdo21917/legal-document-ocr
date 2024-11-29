from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(100), unique=True, index=True)
    extraction_time = Column(DateTime)
    version = Column(String(50))
    document_type = Column(String(100))
    document_number = Column(String(100))
    issue_location = Column(String(200))
    issue_date = Column(DateTime)
    issuing_agency = Column(String(200))
    recipients = Column(String(500))
    recipient_address = Column(Text)
    signer = Column(String(200))
    position = Column(String(200))
    subject = Column(Text)
    content = Column(Text)
    page_numbers = Column(JSON)

    pages = relationship("Page", back_populates="document") 