from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.db import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.services import users as users_service

router = APIRouter(prefix="/auth", tags=["auth"])

def _token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserRead.model_validate(user),
    )

@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if await users_service.get_by_email(db, payload.email) is not None:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    user = await users_service.create_user(
        db, payload.email, payload.password, payload.display_name
    )
    return _token_response(user)

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await users_service.authenticate(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return _token_response(user)

@router.post("/demo", response_model=TokenResponse)
async def demo_login(db: AsyncSession = Depends(get_db)):
    user = await users_service.get_demo_user(db)
    if user is None:
        raise HTTPException(status_code=503, detail="Demo account is not available.")
    return _token_response(user)

@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_user)):
    return user
