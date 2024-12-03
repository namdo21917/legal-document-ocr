from typing import Dict, List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services.ocr_service import OCRService
from app.utils.exceptions import OCRError
from app.schemas.responses import OCRResponse, DocumentResponse
from app.models.document import Document

router = APIRouter()

@router.post("/", response_model=OCRResponse)
async def create_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        ocr_service = OCRService()
        result = await ocr_service.save_document(file, db)
        return result
    except OCRError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    document_type: str = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Lấy danh sách documents với phân trang và filter
    """
    try:
        ocr_service = OCRService()
        return await ocr_service.get_document_list(
            db=db,
            skip=skip,
            limit=limit,
            document_type=document_type
        )
    except OCRError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
