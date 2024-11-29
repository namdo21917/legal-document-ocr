from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.page import Page
# from app.services.ocr_service import OCRService

router = APIRouter()

@router.get("/{page_id}", response_model=Page)
async def get_page(
    page_id: int,
    db: Session = Depends(get_db)
):
    """Lấy thông tin của một trang"""
    page = await db.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@router.get("/document/{document_id}", response_model=List[Page])
async def get_document_pages(
    document_id: str,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Lấy danh sách các trang của một tài liệu"""
    return await db.get_pages_by_document(
        document_id=document_id,
        skip=skip,
        limit=limit
    )

@router.get("/{page_id}/image")
async def get_page_image(
    page_id: int,
    db: Session = Depends(get_db)
):
    """Lấy hình ảnh của một trang"""
    page = await db.get_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    # return FileResponse(page.image_path)