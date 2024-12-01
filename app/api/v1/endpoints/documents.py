from typing import Dict
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services.ocr_service import OCRService
from app.utils.exceptions import OCRError
from app.schemas.responses import OCRResponse

router = APIRouter()

@router.post("/", response_model=OCRResponse)
async def create_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload và xử lý OCR cho một tài liệu"""
    try:
        ocr_service = OCRService()
        result = await ocr_service.process_and_save_document(file, db)
        return result
    except OCRError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
