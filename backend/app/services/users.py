from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password, verify_password

DEMO_EMAIL = "demo@clutch.app"

async def get_user(db: AsyncSession, user_id: int) -> User | None:
    return await db.get(User, user_id)

async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).where(func.lower(User.email) == email.strip().lower())
    )
    return result.scalars().first()

async def create_user(
    db: AsyncSession, email: str, password: str, display_name: str | None = None
) -> User:
    user = User(
        email=email.strip().lower(),
        password_hash=hash_password(password),
        display_name=(display_name or None),
        is_demo=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_by_email(db, email)
    if user is None or user.is_demo:
        return None  # demo account has no usable password
    if not verify_password(password, user.password_hash):
        return None
    return user

async def get_demo_user(db: AsyncSession) -> User | None:
    return await get_by_email(db, DEMO_EMAIL)
