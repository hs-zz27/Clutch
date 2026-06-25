from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.api import (
    health,
    commitments,
    planner,
    agent,
    knowledge,
    renegotiation,
    calendar,
)

app = FastAPI(title="Clutch")

register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(commitments.router)
app.include_router(planner.router)
app.include_router(agent.router)
app.include_router(knowledge.router)
app.include_router(renegotiation.router)
app.include_router(calendar.router)
