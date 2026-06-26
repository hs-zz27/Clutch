"""Central Gemini client with bounded retry, backoff, graceful degradation, and
verbose diagnostics.

Every LLM-backed service should import `generate_text` / `generate_json` from here
rather than calling the SDK directly, so transient rate-limit / quota errors become
a single typed `GeminiUnavailable` that routers can convert into a clean 503.

All failures are logged under the "clutch.gemini" logger with the upstream status
code, reason, and response body, so a 502/503 in the UI can be traced back to the
real Gemini error (quota, bad key, wrong model, ...).
"""
from __future__ import annotations

import json
import logging
import random
import time
from typing import Any

from google import genai
from google.genai import types as genai_types
from google.genai.errors import APIError

from app.core.config import settings

logger = logging.getLogger("clutch.gemini")

# Make sure these diagnostics are actually visible. Under some run setups the
# "clutch.*" loggers inherit a WARNING level and/or have no handler attached, so
# useful detail never reaches the console. Force INFO, and only add a fallback
# handler when nothing is configured yet (avoids duplicate log lines under
# uvicorn, which already installs root handlers).
logger.setLevel(logging.INFO)
if not logger.handlers and not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

# Public client (kept for callers that still reference `gemini.client` directly).
client = genai.Client(api_key=settings.GEMINI_API_KEY or "missing-api-key")

DEFAULT_MODEL = "gemini-2.0-flash"
_MAX_ATTEMPTS = 4
_BASE_DELAY = 0.6  # seconds; grows 0.6 -> 1.2 -> 2.4 (+ jitter)
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class GeminiUnavailable(RuntimeError):
    """Raised when the model can't be reached after retries (quota/outage/no key)."""


def _is_configured() -> bool:
    return bool(settings.GEMINI_API_KEY)


def _status_of(err: Exception) -> int | None:
    return getattr(err, "code", None) or getattr(err, "status_code", None)


def _detail_of(err: Exception) -> str:
    """Best-effort one-line summary of a Gemini/SDK error for logs."""
    parts: list[str] = []
    code = _status_of(err)
    if code is not None:
        parts.append(f"status={code}")
    status = getattr(err, "status", None)
    if status:
        parts.append(f"reason={status}")
    message = getattr(err, "message", None)
    if message:
        parts.append(f"message={message}")
    # google-genai usually carries the upstream JSON body on one of these.
    body = getattr(err, "response_json", None) or getattr(err, "details", None)
    if body:
        parts.append(f"body={body}")
    if not parts:
        parts.append(repr(err))
    return ", ".join(str(p) for p in parts)


def _call_with_retry(model: str, contents: Any, config: Any | None) -> Any:
    if not _is_configured():
        logger.error("Gemini call skipped: GEMINI_API_KEY is not set in the backend environment.")
        raise GeminiUnavailable(
            "GEMINI_API_KEY is not set. Add it to the backend environment to enable AI features."
        )

    last_err: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            logger.info("Gemini request (model=%s, attempt=%s/%s)", model, attempt, _MAX_ATTEMPTS)
            return client.models.generate_content(model=model, contents=contents, config=config)
        except APIError as err:
            status = _status_of(err)
            last_err = err
            logger.warning(
                "Gemini API error (model=%s, attempt=%s/%s): %s",
                model, attempt, _MAX_ATTEMPTS, _detail_of(err),
            )
            if status not in _RETRYABLE_STATUS or attempt == _MAX_ATTEMPTS:
                break
            delay = _BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
            logger.warning("Retrying Gemini call in %.2fs (status=%s)", delay, status)
            time.sleep(delay)
        except Exception as err:  # network / SDK-level failure
            last_err = err
            logger.warning(
                "Gemini SDK/network error (model=%s, attempt=%s/%s): %s",
                model, attempt, _MAX_ATTEMPTS, _detail_of(err),
            )
            if attempt == _MAX_ATTEMPTS:
                break
            time.sleep(_BASE_DELAY * (2 ** (attempt - 1)))

    logger.error(
        "Gemini permanently unavailable after %s attempt(s) (model=%s): %s",
        _MAX_ATTEMPTS, model, _detail_of(last_err) if last_err else "unknown error",
        exc_info=last_err,
    )
    raise GeminiUnavailable(f"Gemini is temporarily unavailable: {last_err}") from last_err


def generate_text(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    system_instruction: str | None = None,
    temperature: float = 0.4,
) -> str:
    """Single-shot text generation with retry. Raises GeminiUnavailable on failure."""
    config = genai_types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction,
    )
    resp = _call_with_retry(model, prompt, config)
    return (getattr(resp, "text", None) or "").strip()


def generate_json(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    system_instruction: str | None = None,
    temperature: float = 0.2,
) -> Any:
    """Generate and parse a JSON response. Raises GeminiUnavailable or ValueError."""
    config = genai_types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction,
        response_mime_type="application/json",
    )
    resp = _call_with_retry(model, prompt, config)
    raw = (getattr(resp, "text", None) or "").strip()
    if not raw:
        logger.error("Gemini returned an empty response (model=%s)", model)
        raise ValueError("Empty response from model")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # tolerate ```json fences the model sometimes adds
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error("Gemini returned non-JSON output (model=%s): %s", model, raw[:500])
            raise