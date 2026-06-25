"""Multimodal capture endpoint (feature #7).

POST /commitments/parse-image (multipart: file) -> list[CommitmentRead]

Gemini Vision reads a screenshot/photo/PDF of tasks (syllabus, brief, email,
whiteboard, to-do list) and extracts structured commitments, which are then
persisted and recorded in the decision ledger. Text-only capture still lives at
POST /commitments/parse.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.gemini import client
from app.schemas.commitment import CommitmentCreate, CommitmentRead
from app.services import commitments as service
from app.services import ledger as ledger_service

router = APIRouter(prefix="/commitments", tags=["vision"])

_ALLOWED_MIME = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "image/heic",
    "image/heif",
    "application/pdf",
}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/parse-image", response_model=list[CommitmentRead])
async def parse_image(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    mime = file.content_type or "application/octet-stream"
    if mime not in _ALLOWED_MIME:
        raise HTTPException(415, f"Unsupported file type: {mime}")

    data = await file.read()
    if not data:
        raise HTTPException(400, "Empty file")
    if len(data) > _MAX_BYTES:
        raise HTTPException(413, "File too large (max 10 MB)")

    now = datetime.now(timezone.utc).isoformat()
    prompt = f"""You extract commitments/tasks from an image: a screenshot or photo of a
syllabus, assignment brief, email, whiteboard, or to-do list.
The current datetime (UTC) is {now}.
Resolve all relative dates (\"Friday 5pm\", \"next week\") into absolute ISO 8601 datetimes.
Estimate est_effort_minutes realistically. Set importance 1-5 (5 = critical).
If a stakeholder/person is mentioned, fill it in; otherwise leave it null.
Extract every distinct task you can see. If none are present, return an empty list."""

    try:
        resp = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=data, mime_type=mime),
                prompt,
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": list[CommitmentCreate],
            },
        )
        parsed: list[CommitmentCreate] = list(resp.parsed or [])
    except Exception:
        raise HTTPException(502, "Failed to read commitments from the image")

    created = await service.create_commitments(db, parsed)
    for obj in created:
        await ledger_service.record(
            db,
            action="create_commitment",
            target_type="commitment",
            target_id=obj.id,
            summary=f"Captured '{obj.title}' from an image",
            reasoning="Extracted via multimodal (Gemini Vision) capture.",
            reversible=True,
            commit=False,
        )
    await db.commit()
    return created
