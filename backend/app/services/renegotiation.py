"""Phase 6 - draft a stakeholder renegotiation message with Gemini.

This is the *generation* layer only. It produces a subject + body grounded in a
single commitment. Persistence and sending live elsewhere (outbox / mailer), and
a human must approve before anything goes out.
"""
from __future__ import annotations

from app.core.gemini import client
from app.models.commitment import Commitment

MODEL = "gemini-2.5-flash"

_PROMPT = """You are drafting a short, {tone} message on behalf of someone who is over capacity \
and must renegotiate one of their commitments. They want to ask the stakeholder for an extension \
or a reduced scope - honestly, without over-apologising or inventing excuses.

Commitment: {title}
Stakeholder: {stakeholder}
Deadline: {deadline}
Importance (1-5): {importance}
Minimum acceptable outcome: {mvd}

Write the message. Output EXACTLY in this format:
Subject: <a concise subject line>
<blank line>
<email body, under 120 words, plain text>

Do not invent facts, dates, or commitments that are not given above."""


async def draft_message(commitment: Commitment, tone: str) -> dict:
    """Return {\"subject\": str, \"body\": str}. Raises on Gemini failure."""
    prompt = _PROMPT.format(
        tone=tone,
        title=commitment.title,
        stakeholder=commitment.stakeholder or "the stakeholder",
        deadline=commitment.deadline.isoformat(),
        importance=commitment.importance,
        mvd=commitment.min_viable_definition or "not specified",
    )
    resp = await client.aio.models.generate_content(model=MODEL, contents=prompt)
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
