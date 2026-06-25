"""Thin async HTTP client the voice agent uses to drive the Clutch API.

Every voice tool ultimately calls one of these methods, so the spoken agent and
the web agent share exactly the same brain - no duplicated planning or triage
logic. Each call opens and closes its own client to stay safe across the
worker's long-lived, concurrent sessions.
"""
from __future__ import annotations

from typing import Any

import httpx

from . import config


class ClutchClient:
    def __init__(
        self, base_url: str | None = None, timeout: float | None = None
    ) -> None:
        self._base = (base_url or config.CLUTCH_API_BASE).rstrip("/")
        self._timeout = timeout or config.API_TIMEOUT_SECONDS

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        async with httpx.AsyncClient(
            base_url=self._base, timeout=self._timeout
        ) as client:
            resp = await client.request(method, path, **kwargs)
            resp.raise_for_status()
            if resp.status_code == 204 or not resp.content:
                return None
            return resp.json()

    # --- reads -----------------------------------------------------------
    async def list_commitments(self) -> list[dict]:
        return await self._request("GET", "/commitments")

    async def plan(self) -> dict:
        return await self._request("GET", "/plan")

    async def capacity(self, until: str | None = None) -> dict:
        params = {"until": until} if until else None
        return await self._request("GET", "/calendar/capacity", params=params)

    async def search_knowledge(self, query: str) -> dict:
        return await self._request(
            "POST", "/knowledge/search", json={"query": query}
        )

    # --- the full reasoning loop ----------------------------------------
    async def run_agent(self, goal: str) -> dict:
        return await self._request("POST", "/agent", json={"goal": goal})

    # --- actions (always drafts, never auto-sent) -----------------------
    async def draft_renegotiation(
        self, commitment_id: int, tone: str | None = None
    ) -> dict:
        body: dict[str, Any] = {"commitment_id": commitment_id}
        if tone:
            body["tone"] = tone
        return await self._request("POST", "/renegotiation/draft", json=body)
