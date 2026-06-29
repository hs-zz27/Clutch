"""Knowledge base (RAG) endpoints.

Uploads are validated (type + size) and cataloged immediately, then indexed into
the Gemini File Search store in the background so the request returns fast even
for large PDFs. We never execute or render uploaded files - they go straight to
Gemini's managed store - but we still reject script/markup/executable types and
cap the size as defense in depth.
"""
import logging
import os
import re
import tempfile

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.knowledge import (
    DocumentRead,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.services import documents as documents_service
from app.services import knowledge as knowledge_service

logger = logging.getLogger("clutch.knowledge")

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

# Defense in depth: cap size and only accept document types we can ground on.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".markdown", ".csv", ".tsv",
    ".json", ".doc", ".docx", ".rtf", ".pptx", ".xlsx", ".log",
}
_ALLOWED_LABEL = "PDF, TXT, MD, CSV, TSV, JSON, DOC(X), RTF, PPTX, XLSX, LOG"

def _safe_filename(name: str | None) -> str:
    """Strip any path and unusual characters so a crafted name can't traverse
    directories or inject control characters into the catalog / temp path."""
    base = os.path.basename((name or "").strip())
    base = re.sub(r"[^A-Za-z0-9._ -]", "_", base)
    base = base.lstrip(".") or "document"
    return base[:120]

def _index_document(tmp_path: str, display_name: str, user_id: int, is_demo: bool) -> None:
    """Blocking import into the RAG store. Runs as a background task (threadpool)
    so the upload request can return immediately. Always cleans up the temp file."""
    try:
        knowledge_service.upload_document(tmp_path, display_name, user_id, is_demo)
    except Exception:
        logger.exception("Background indexing failed for %s", display_name)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

def _purge_document(display_name: str, user_id: int, is_demo: bool) -> None:
    """Best-effort removal of a file's embeddings from the RAG store."""
    try:
        knowledge_service.purge_documents_by_name(display_name, user_id, is_demo)
    except Exception:
        logger.exception("Background purge from RAG store failed for %s", display_name)

@router.post("/documents", response_model=DocumentRead)
async def upload_document(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Validate, catalog, and (in the background) index a document for RAG."""
    safe_name = _safe_filename(file.filename)
    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext or 'unknown'}'. Allowed: {_ALLOWED_LABEL}.",
        )

    data = await file.read()
    size = len(data)
    if size == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"That file is {size / (1024 * 1024):.1f} MB, over the "
                f"{MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit. "
                "Upload a smaller document."
            ),
        )

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
    except OSError:
        logger.exception("Could not buffer upload %s to disk", safe_name)
        raise HTTPException(
            status_code=503, detail="Could not process the upload. Try again."
        )

    # Catalog right away so the UI shows the file instantly...
    doc = await documents_service.create_document(
        db,
        filename=safe_name,
        user_id=user.id,
        content_type=file.content_type,
        size_bytes=size,
    )
    # ...then do the slow Gemini chunk/embed/index off the request path.
    background.add_task(_index_document, tmp_path, safe_name, user.id, user.is_demo)
    return doc

@router.get("/documents", response_model=list[DocumentRead])
async def list_documents(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await documents_service.list_documents(db, user.id)

@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Remove a document from the catalog and purge it from the RAG store."""
    doc = await documents_service.get_document(db, document_id, user.id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    background.add_task(_purge_document, doc.filename, user.id, user.is_demo)
    await documents_service.delete_document(db, doc)
    return None

@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(payload: KnowledgeSearchRequest, user: User = Depends(get_current_user)):
    """Test endpoint: run a grounded retrieval query against the knowledge base."""
    return await knowledge_service.search(payload.query, user.id, user.is_demo)
