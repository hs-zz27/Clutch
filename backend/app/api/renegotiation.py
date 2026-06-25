from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.renegotiation import (
    RenegotiationGenerateRequest,
    RenegotiationRead,
    RenegotiationUpdate,
)
from app.services import commitments as commitments_service
from app.services import mailer
from app.services import outbox as outbox_service
from app.services import renegotiation as renegotiation_service
from app.services import stakeholders as stakeholders_service

router = APIRouter(prefix="/renegotiation", tags=["renegotiation"])


@router.post("/draft", response_model=RenegotiationRead)
async def create_draft(
    payload: RenegotiationGenerateRequest, db: AsyncSession = Depends(get_db)
):
    """Draft (but do not send) a renegotiation message for a commitment."""
    commitment = await commitments_service.get_commitment(db, payload.commitment_id)
    if commitment is None:
        raise HTTPException(status_code=404, detail="Commitment not found")

    # feature #8: tailor tone using the stakeholder relationship model if known
    context = await stakeholders_service.get_context_by_name(
        db, commitment.stakeholder
    )

    try:
        drafted = await renegotiation_service.draft_message(
            commitment, payload.tone, context
        )
    except Exception:
        raise HTTPException(
            status_code=502, detail="Failed to generate the renegotiation draft."
        )

    return await outbox_service.create_draft(
        db,
        commitment_id=commitment.id,
        subject=drafted["subject"],
        body=drafted["body"],
        recipient=commitment.stakeholder,
    )


@router.get("", response_model=list[RenegotiationRead])
async def list_drafts(db: AsyncSession = Depends(get_db)):
    return await outbox_service.list_messages(db)


@router.patch("/{message_id}", response_model=RenegotiationRead)
async def edit_draft(
    message_id: int,
    payload: RenegotiationUpdate,
    db: AsyncSession = Depends(get_db),
):
    msg = await outbox_service.get_message(db, message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return await outbox_service.update_draft(
        db,
        msg,
        recipient=payload.recipient,
        subject=payload.subject,
        body=payload.body,
    )


@router.post("/{message_id}/send", response_model=RenegotiationRead)
async def send_draft(message_id: int, db: AsyncSession = Depends(get_db)):
    """Send a drafted message via Gmail SMTP. Degrades gracefully if unconfigured."""
    msg = await outbox_service.get_message(db, message_id)
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    if not msg.recipient:
        raise HTTPException(
            status_code=400, detail="No recipient set for this message."
        )
    if not mailer.is_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Email sending is not configured. Set GMAIL_SENDER and "
                "GMAIL_APP_PASSWORD, or send the drafted message manually."
            ),
        )

    try:
        await run_in_threadpool(
            mailer.send_email, msg.recipient, msg.subject, msg.body
        )
    except Exception as exc:
        await outbox_service.mark_failed(db, msg, str(exc))
        raise HTTPException(status_code=502, detail="Failed to send the email.")

    return await outbox_service.mark_sent(db, msg)
