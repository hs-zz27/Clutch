"""Application-wide error handling.

The goal is twofold: never crash the worker on an unexpected error, and never
leak internal details (stack traces, SQL, secrets) to the client. Full detail
is logged server-side; the client gets a generic message.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("clutch")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # HTTPException / validation errors are handled by FastAPI's own
        # handlers and never reach here. This is the last-resort safety net.
        logger.exception(
            "Unhandled error on %s %s", request.method, request.url.path
        )
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
