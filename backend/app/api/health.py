from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def root():
    return {"service": "clutch-backend"}

@router.get("/healthz")
def healthz():
    return {"status": "ok"}