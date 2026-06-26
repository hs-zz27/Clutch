"""Phase 6 - draft a stakeholder renegotiation message with Gemini.

This is the *generation* layer only. It produces a subject + body grounded in a
single commitment. Persistence and sending live elsewhere (outbox / mailer), and
a human must approve before anything goes out.

Feature #8: an optional stakeholder_context (relationship, formality, notes)
lets the drafter match the register to who is being written to.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from app.core.gemini import client, GeminiUnavailable
from app.models.commitment import Commitment

MODEL = "gemini-2.5-flash"

_PROMPT = """You are drafting a short, {tone} message on behalf of someone who is over capacity \
and must renegotiate one of their commitments. They want to ask the stakeholder for an extension \
or a reduced scope - honestly, without over-apologising or inventing excuses.

Commitment: {title}
Stakeholder: {stakeholder}
Deadline: {deadline}
Importance (1-5): {importance}
Minimum acceptable outcome: {mvd}{relationship}

Write the message. Output EXACTLY in this format:
Subject: <a concise subject line>
<blank line>
<email body, under 120 words, plain text>

Do not invent facts, dates, or commitments that are not given above."""

def _format_deadline(dt: datetime) -> str:
    """Human-readable deadline like '21 July 2026, 18:31' — no seconds, no raw ISO."""
    # Day without leading zero, full month name, year, 24h time (no seconds).
    return f"{dt.day} {dt.strftime('%B %Y, %H:%M')}"



def _formality_word(formality: int | None) -> str:
    if formality is None:
        return "appropriately professional"
    if formality <= 2:
        return "warm and casual"
    if formality >= 4:
        return "formal and respectful"
    return "professional"


def _relationship_block(context: dict | None) -> str:
    if not context:
        return ""
    name = context.get("name") or "the stakeholder"
    relationship = context.get("relationship") or "unspecified relationship"
    register = _formality_word(context.get("formality"))
    block = (
        f"\nRelationship context: {name} is a {relationship}; "
        f"keep the register {register}."
    )
    notes = context.get("notes")
    if notes:
        block += f" Notes about them: {notes}"
    return block


async def draft_message(
    commitment: Commitment,
    tone: str,
    stakeholder_context: dict | None = None,
) -> dict:
    """Return {\"subject\": str, \"body\": str}. Raises on Gemini failure."""
    prompt = _PROMPT.format(
        tone=tone,
        title=commitment.title,
        stakeholder=commitment.stakeholder or "the stakeholder",
        deadline=_format_deadline(commitment.deadline),
        importance=commitment.importance,
        mvd=commitment.min_viable_definition or "not specified",
        relationship=_relationship_block(stakeholder_context),
    )
    try:
        resp = await client.aio.models.generate_content(model=MODEL, contents=prompt)
    except GeminiUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    return _split_subject_body(
        resp.text or "", fallback_subject=f"Re: {commitment.title}"
    )


def _split_subject_body(text: str, fallback_subject: str) -> dict:
    body = text.strip()
    subject = fallback_subject
    lines = body.splitlines()
    if lines and lines[0].lower().startswith("subject:"):
        candidate = lines[0].split(":", 1)[1].strip()
        if candidate:
            subject = candidate
        body = "\n".join(lines[1:]).strip()
    return {"subject": subject, "body": body}
