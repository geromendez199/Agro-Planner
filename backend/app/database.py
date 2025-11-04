"""Configuración de la base de datos y sesión de SQLAlchemy."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import get_settings
from .models import Base

_engine: Optional[AsyncEngine] = None
_SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None


def _normalise_db_url(db_url: str) -> str:
    if db_url.startswith("sqlite:///") and "+" not in db_url:
        return db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    if db_url.startswith("postgresql://") and "+" not in db_url:
        return db_url.replace("postgresql://", "postgresql+asyncpg://")
    return db_url


def get_engine() -> AsyncEngine:
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        url = _normalise_db_url(settings.db_url)
        _engine = create_async_engine(url, echo=False, future=True)
        _SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)
    assert _engine is not None
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        yield session


async def init_db() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

