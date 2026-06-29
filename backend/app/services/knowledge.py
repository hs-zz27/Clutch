"""Phase 5 - managed RAG via the Gemini File Search tool.

Gemini File Search is a fully managed RAG system: we upload documents into a
*File Search store* and Gemini handles chunking, embedding (gemini-embedding),
indexing, retrieval and citation. We never run our own vector DB.

This module owns three things:
  1. resolving (create-or-reuse) the single Clutch knowledge store, by display
     name, so it survives restarts without any extra config;
  2. uploading a file into that store (blocking import op, polled to done);
  3. answering a query grounded on the store, returning the answer + citations.

Store/upload calls use the blocking client and are meant to be run via
`run_in_threadpool` from the async API layer. `search` is async (it is called
from inside the agent's event loop) and uses the async client.
"""
from __future__ import annotations

import time

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from google.genai import types

from app.core.gemini import client, GeminiUnavailable, GeminiQuotaExceeded, guard_gemini

MODEL = "gemini-2.5-flash"
DEMO_STORE_DISPLAY_NAME = "clutch-knowledge"  # keep the originally-seeded store for the demo user

# cache: store display name -> resolved resource name
_store_names: dict[str, str] = {}

def _store_display_name(user_id: int, is_demo: bool) -> str:
    return DEMO_STORE_DISPLAY_NAME if is_demo else f"clutch-knowledge-u{user_id}"

def _resolve_store_name(display_name: str) -> str:
    """Return the resource name for a store display name, creating it once if needed."""
    cached = _store_names.get(display_name)
    if cached:
        return cached
    for store in client.file_search_stores.list():
        if getattr(store, "display_name", None) == display_name:
            _store_names[display_name] = store.name
            return store.name
    store = client.file_search_stores.create(config={"display_name": display_name})
    _store_names[display_name] = store.name
    return store.name


def upload_document(path: str, doc_display_name: str, user_id: int, is_demo: bool) -> None:
    """Upload + import a local file into the knowledge store (blocking).

    Run this via run_in_threadpool from async endpoints.
    """
    store_name = _resolve_store_name(_store_display_name(user_id, is_demo))
    operation = client.file_search_stores.upload_to_file_search_store(
        file=path,
        file_search_store_name=store_name,
        config={"display_name": doc_display_name},
    )
    # importing/embedding is async on Gemini's side - wait until it finishes
    while not operation.done:
        time.sleep(2)
        operation = client.operations.get(operation)


def purge_documents_by_name(doc_display_name: str, user_id: int, is_demo: bool) -> int:
    """Delete every store document whose display name matches (blocking).

    Returns how many were removed. Run via a background task / threadpool. The
    catalog has no stored Gemini doc id, so we match on the display name we set
    at upload time. Missing docs are a no-op; this is best-effort cleanup.
    """
    store_name = _resolve_store_name(_store_display_name(user_id, is_demo))
    removed = 0
    for doc in client.file_search_stores.documents.list(parent=store_name):
        if getattr(doc, "display_name", None) == doc_display_name:
            client.file_search_stores.documents.delete(name=doc.name, force=True)
            removed += 1
    return removed


async def search(query: str, user_id: int, is_demo: bool) -> dict:
    """Answer a query grounded on the knowledge store. Returns answer + citations."""
    store_name = await run_in_threadpool(
        _resolve_store_name, _store_display_name(user_id, is_demo)
    )
    try:
        with guard_gemini():
            resp = await client.aio.models.generate_content(
                model=MODEL,
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(file_search_store_names=[store_name])
                        )
                    ]
                ),
            )
    except GeminiQuotaExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except GeminiUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"answer": resp.text or "", "citations": _extract_citations(resp)}


def _extract_citations(resp) -> list[str]:
    """Pull unique source titles out of the grounding metadata, defensively."""
    titles: list[str] = []
    for candidate in getattr(resp, "candidates", None) or []:
        grounding = getattr(candidate, "grounding_metadata", None)
        if grounding is None:
            continue
        for chunk in getattr(grounding, "grounding_chunks", None) or []:
            context = getattr(chunk, "retrieved_context", None)
            title = getattr(context, "title", None) if context else None
            if title:
                titles.append(title)

    seen: set[str] = set()
    unique: list[str] = []
    for title in titles:
        if title not in seen:
            seen.add(title)
            unique.append(title)
    return unique
