"""Optional outbound email via Gmail SMTP.

Uses a Gmail App Password (not OAuth) so it is fully testable without a Google
Cloud project. When credentials are unset, the app keeps working and the send
path degrades gracefully (callers surface a clear 'not configured' error and
the draft simply stays unsent). Secrets are read from settings and never logged.
"""
from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465  # implicit TLS
SMTP_TIMEOUT = 20  # seconds - never hang a worker on a stuck connection


def is_configured() -> bool:
    return bool(settings.GMAIL_SENDER and settings.GMAIL_APP_PASSWORD)


def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text email. Blocking - call via run_in_threadpool.

    Raises RuntimeError if not configured, or smtplib errors on failure.
    """
    if not is_configured():
        raise RuntimeError(
            "Email sending is not configured (set GMAIL_SENDER and GMAIL_APP_PASSWORD)."
        )

    message = EmailMessage()
    message["From"] = settings.GMAIL_SENDER
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(
        SMTP_HOST, SMTP_PORT, context=context, timeout=SMTP_TIMEOUT
    ) as server:
        server.login(settings.GMAIL_SENDER, settings.GMAIL_APP_PASSWORD)
        server.send_message(message)
