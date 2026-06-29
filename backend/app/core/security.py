"""Stdlib-only auth primitives: password hashing + signed access tokens.

No third-party crypto/JWT deps (Render reinstalls requirements.txt). Passwords
use pbkdf2_hmac(sha256); tokens are a compact HS256-style JWT built from hmac +
base64url so we never add a dependency.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

from app.core.config import settings

_PBKDF2_ROUNDS = 200_000
_ALGO = "pbkdf2_sha256"

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
    return f"{_ALGO}${_PBKDF2_ROUNDS}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"

def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, b64salt, b64hash = stored.split("$")
        if algo != _ALGO:
            return False
        salt = base64.b64decode(b64salt)
        expected = base64.b64decode(b64hash)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(rounds))
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False

def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")

def _b64url_decode(seg: str) -> bytes:
    pad = "=" * (-len(seg) % 4)
    return base64.urlsafe_b64decode(seg + pad)

def create_access_token(user_id: int, ttl_hours: int | None = None) -> str:
    ttl = settings.ACCESS_TOKEN_TTL_HOURS if ttl_hours is None else ttl_hours
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": str(user_id), "iat": now, "exp": now + ttl * 3600}
    seg = (
        _b64url(json.dumps(header, separators=(",", ":")).encode())
        + "."
        + _b64url(json.dumps(payload, separators=(",", ":")).encode())
    )
    sig = hmac.new(settings.AUTH_SECRET.encode(), seg.encode(), hashlib.sha256).digest()
    return seg + "." + _b64url(sig)

def decode_access_token(token: str) -> int | None:
    """Return the user id if the token is valid + unexpired, else None."""
    try:
        seg_header, seg_payload, seg_sig = token.split(".")
        signing_input = f"{seg_header}.{seg_payload}"
        expected = hmac.new(
            settings.AUTH_SECRET.encode(), signing_input.encode(), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected, _b64url_decode(seg_sig)):
            return None
        payload = json.loads(_b64url_decode(seg_payload))
        if int(payload["exp"]) < int(time.time()):
            return None
        return int(payload["sub"])
    except Exception:
        return None
