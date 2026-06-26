"""Central Gemini client with bounded retry, backoff, and graceful degradation.

Every LLM-backed service should import `generate_text` / `generate_json` from here
rather than calling the SDK directly, so transient rate-limit / quota errors become
a single typed `GeminiUnavailable` that routers can convert into a clean 503.
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

def _status_of(err: APIError) -> int | None:
    return getattr(err, "code", None) or getattr(err, "status_code", None)

def _call_with_retry(model: str, contents: Any, config: Any | None) -> Any:
    if not _is_configured():
        raise GeminiUnavailable(
            "GEMINI_API_KEY is not set. Add it to the backend environment to enable AI features."
        )

    last_err: Exception | None = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            return client.models.generate_content(model=model, contents=contents, config=config)
        except APIError as err:
            status = _status_of(err)
            last_err = err
            if status not in _RETRYABLE_STATUS or attempt == _MAX_ATTEMPTS:
                break
            delay = _BASE_DELAY * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
            logger.warning(
                "Gemini call failed (status=%s, attempt=%s/%s); retrying in %.2fs",
                status, attempt, _MAX_ATTEMPTS, delay,
            )
            time.sleep(delay)
        except Exception as err:  # network / SDK-level failure
            last_err = err
            if attempt == _MAX_ATTEMPTS:
                break
            time.sleep(_BASE_DELAY * (2 ** (attempt - 1)))

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
        raise ValueError("Empty response from model")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # tolerate ```json fences the model sometimes adds
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(cleaned)
