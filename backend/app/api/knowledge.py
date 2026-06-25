import os
import tempfile

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.knowledge import (
    DocumentRead,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.services import documents as documents_service
from app.services import knowledge as knowledge_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/documents", response_model=DocumentRead)
async def upload_document(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """Upload a document into the RAG knowledge base and catalog it."""
    data = await file.read()
    suffix = os.path.splitext(file.filename or "")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        await run_in_threadpool(
            knowledge_service.upload_document, tmp_path, file.filename or "document"
        )
    finally:
        os.unlink(tmp_path)

    return await documents_service.create_document(
        db,
        filename=file.filename or "document",
        content_type=file.content_type,
        size_bytes=len(data),
    )


@router.get("/documents", response_model=list[DocumentRead])
async def list_documents(db: AsyncSession = Depends(get_db)):
    return await documents_service.list_documents(db)


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(payload: KnowledgeSearchRequest):
    """Test endpoint: run a grounded retrieval query against the knowledge base."""
    return await knowledge_service.search(payload.query)
