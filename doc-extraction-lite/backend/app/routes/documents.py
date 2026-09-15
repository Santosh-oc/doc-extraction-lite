from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.db import get_db, Document
from app.schemas import DocumentUploadResponse, DocumentResponse
from app.pdf_service import extract_text_per_page, validate_pdf, PDFServiceError

router = APIRouter()

@router.post("/documents/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., media_type="application/pdf"),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed.")

    file_content = await file.read()

    try:
        validate_pdf(file_content)
        page_texts = extract_text_per_page(file_content)
    except PDFServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    page_count = len(page_texts)
    if page_count == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF contains no readable text.")

    new_document = Document(
        filename=file.filename,
        size_bytes=len(file_content),
        page_count=page_count,
        page_text=page_texts
    )
    db.add(new_document)
    await db.commit()
    await db.refresh(new_document)

    return DocumentUploadResponse(
        id=new_document.id,
        filename=new_document.filename,
        page_count=new_document.page_count,
        created_at=new_document.created_at
    )

@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).filter(Document.id == document_id))
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        size_bytes=document.size_bytes,
        page_count=document.page_count,
        page_text=document.page_text,
        created_at=document.created_at
    )
