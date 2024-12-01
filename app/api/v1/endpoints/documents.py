from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.document import Document
from app.services.ocr_service import OCRService
from app.utils.exceptions import OCRError
from app.utils.validation import Validator

router = APIRouter()
validator = Validator()

@router.post("/", response_model=Document)
async def create_document(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    try:
        await validator.validate_file(file)
        ocr_service = OCRService()
        document_data = await ocr_service.process_document(file)
        return await ocr_service.save_document(db, document_data)
    except OCRError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{document_id}", response_model=Document)
async def get_document(
        document_id: str,
        db: Session = Depends(get_db)
):
    document = await db.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/", response_model=List[Document])
async def list_documents(
        skip: int = 0,
        limit: int = 10,
        document_type: Optional[str] = None,
        db: Session = Depends(get_db)
):
    filters = {}
    if document_type:
        filters["document_type"] = document_type
    return await db.get_documents(skip=skip, limit=limit, filters=filters)
