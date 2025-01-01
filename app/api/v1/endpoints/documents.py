from typing import Dict, List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services.document_service import DocumentService
from app.services.ocr_service import OCRService
from app.utils.exceptions import OCRError
from app.schemas.documents import OCRResponse, DocumentResponse, DocumentDeleteResponse, PaginatedDocumentResponse
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

@router.get("/", response_model=PaginatedDocumentResponse)
async def get_documents(
    page: int = Query(default=1, ge=1, description="Số trang"),
    size: int = Query(default=10, ge=1, le=100, description="Số bản ghi trên một trang"),
    document_type: str = Query(default=None, description="Loại document để lọc"),
    db: Session = Depends(get_db)
):
    try:
        # Convert page to skip
        skip = (page - 1) * size
        
        return await document_service.get_document_list(
            db=db,
            skip=skip,
            limit=size,
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
    try:
        result = await document_service.update_document(document_id, document_data, db)
        return result
    except OCRError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
