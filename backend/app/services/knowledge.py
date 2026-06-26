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

from app.core.gemini import client, GeminiUnavailable

MODEL = "gemini-2.5-flash"
STORE_DISPLAY_NAME = "clutch-knowledge"

# cached resolved store resource name (e.g. "fileSearchStores/clutch-knowledge-xxxx")
_store_name: str | None = None


def _resolve_store_name() -> str:
    """Return the Clutch store's resource name, creating it once if needed."""
    global _store_name
    if _store_name:
        return _store_name

    for store in client.file_search_stores.list():
        if getattr(store, "display_name", None) == STORE_DISPLAY_NAME:
            _store_name = store.name
            return _store_name

    store = client.file_search_stores.create(
        config={"display_name": STORE_DISPLAY_NAME}
    )
    _store_name = store.name
    return _store_name


def upload_document(path: str, display_name: str) -> None:
    """Upload + import a local file into the knowledge store (blocking).

    Run this via run_in_threadpool from async endpoints.
    """
    store_name = _resolve_store_name()
    operation = client.file_search_stores.upload_to_file_search_store(
        file=path,
        file_search_store_name=store_name,
        config={"display_name": display_name},
    )
    # importing/embedding is async on Gemini's side - wait until it finishes
    while not operation.done:
        time.sleep(2)
        operation = client.operations.get(operation)


async def search(query: str) -> dict:
    """Answer a query grounded on the knowledge store. Returns answer + citations."""
    store_name = await run_in_threadpool(_resolve_store_name)
    try:
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
