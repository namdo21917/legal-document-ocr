from typing import Dict, List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services.document_service import DocumentService
from app.services.ocr_service import OCRService
from app.utils.exceptions import OCRError
from app.schemas.documents import OCRResponse, DocumentResponse, DocumentDeleteResponse
from app.models.document import Document

router = APIRouter()
ocr_service = OCRService()
document_service = DocumentService()

@router.post("/", response_model=OCRResponse)
async def create_document(
    file: UploadFile = File(...),
):
    try:
        result = await ocr_service.process_document(file)
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
        return await document_service.get_document_list(
            db=db,
            skip=skip,
            limit=limit,
            document_type=document_type
        )
    except OCRError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save", response_model=OCRResponse)
async def save_document(
    document_data: dict,
    db: Session = Depends(get_db)
):
    """
    Lưu thông tin document vào database
    """
    try:
        result = await document_service.save_document(document_data, db)
        return result
    except OCRError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}/delete", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
        db: Session = Depends(get_db),
):
    """
    Lưu thông tin document vào database
    """
    try:
        result = await document_service.delete_document(document_id, db)
        return result
    except OCRError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Lấy thông tin chi tiết của một document theo ID
    """
    try:
        result = await document_service.get_document_by_id(document_id, db)
        return result
    except OCRError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_data: dict,
    db: Session = Depends(get_db)
):
    """
    Cập nhật thông tin của một document
    """
    try:
        result = await document_service.update_document(document_id, document_data, db)
        return result
    except OCRError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
