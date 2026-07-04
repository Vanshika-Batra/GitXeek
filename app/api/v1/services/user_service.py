from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import conflict, unauthorized
from app.core.security import hash_password, verify_password
from app.models.user import User


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_github_id(db: AsyncSession, github_id: str) -> User | None:
    result = await db.execute(select(User).where(User.github_id == github_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str) -> User:
    existing = await get_user_by_email(db, email)
    if existing:
        raise conflict("Email already registered")

    hashed_password = hash_password(password)
    user = User(email=email, password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.password):
        raise unauthorized("Invalid email or password")
    return user


async def update_github_credentials(
    db: AsyncSession, user: User, github_id: str, github_token: str
) -> User:
    existing = await get_user_by_github_id(db, github_id)
    if existing and existing.id != user.id:
        raise conflict("GitHub account already linked to another user")

    user.github_id = github_id
    user.github_token = github_token
    await db.commit()
    await db.refresh(user)
    return user


async def disconnect_github(db: AsyncSession, user: User) -> User:
    user.github_id = None
    user.github_token = None
    await db.commit()
    await db.refresh(user)
    return user
