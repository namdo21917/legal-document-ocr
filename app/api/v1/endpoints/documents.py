from typing import Dict, List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from app.db.base import get_db
from app.services.document_service import DocumentService
from app.services.ocr_service import OCRService
from app.services.minio_service import minio_service
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

@router.get("/{document_id}/download/{file_type}")
async def download_file(
    document_id: str,
    file_type: str,  # 'input', 'output', 'summary'
    db: Session = Depends(get_db)
):
    """Download file từ MinIO storage"""
    try:
        # Lấy thông tin document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document không tồn tại")

        # Xác định URL file cần download
        file_url = None
        filename = None
        content_type = "application/octet-stream"

        if file_type == "input" and document.input_file_url:
            file_url = document.input_file_url
            filename = f"input_{document_id}"

        elif file_type == "summary" and document.output_urls:
            file_url = document.output_urls.get("summary")
            filename = f"summary_{document_id}.json"
            content_type = "application/json"

        elif file_type.startswith("page_") and document.output_urls:
            file_url = document.output_urls.get(file_type)
            if file_type.endswith("_image"):
                filename = f"{file_type}_{document_id}.png"
                content_type = "image/png"
            elif file_type.endswith("_text"):
                filename = f"{file_type}_{document_id}.txt"
                content_type = "text/plain"
            else:
                filename = f"{file_type}_{document_id}.json"
                content_type = "application/json"

        if not file_url:
            raise HTTPException(status_code=404, detail="File không tồn tại")

        # Parse MinIO URL và download
        bucket_name, object_name = minio_service.parse_minio_url(file_url)
        file_content = minio_service.get_file_content(bucket_name, object_name)

        # Trả về file content
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi download file: {str(e)}")

@router.get("/{document_id}/files")
async def list_document_files(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Liệt kê tất cả files của document"""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document không tồn tại")

        files = {}

        # Input file
        if document.input_file_url:
            files["input"] = {
                "url": document.input_file_url,
                "type": "input",
                "description": "File gốc được upload"
            }

        # Output files
        if document.output_urls:
            for key, url in document.output_urls.items():
                files[key] = {
                    "url": url,
                    "type": "output",
                    "description": f"File kết quả: {key}"
                }

        return {
            "document_id": document_id,
            "files": files,
            "total_files": len(files)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi liệt kê files: {str(e)}")
