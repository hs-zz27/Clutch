"""CRUD for the document catalog (metadata for files in the RAG store)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


async def create_document(
    db: AsyncSession,
    filename: str,
    user_id: int,
    content_type: str | None = None,
    size_bytes: int | None = None,
) -> Document:
    doc = Document(filename=filename, user_id=user_id, content_type=content_type, size_bytes=size_bytes)
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def list_documents(db: AsyncSession, user_id: int) -> list[Document]:
    result = await db.execute(select(Document).where(Document.user_id == user_id).order_by(Document.uploaded_at.desc()))
    return list(result.scalars().all())


async def get_document(db: AsyncSession, document_id: int, user_id: int) -> Document | None:
    result = await db.execute(select(Document).where(Document.id == document_id, Document.user_id == user_id))
    return result.scalars().first()


async def delete_document(db: AsyncSession, doc: Document) -> None:
    await db.delete(doc)
    await db.commit()
