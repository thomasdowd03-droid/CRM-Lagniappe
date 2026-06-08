"""Database engine, session, and base model.

Uses a hosted database when one is configured (Vercel/Neon inject POSTGRES_URL*),
and falls back to a local SQLite file for development. The URL is the only thing
that changes between local and production.
"""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_database_url() -> str:
    for key in ("DATABASE_URL", "POSTGRES_URL", "POSTGRES_PRISMA_URL", "POSTGRES_URL_NON_POOLING"):
        url = os.environ.get(key)
        if url:
            # SQLAlchemy requires the 'postgresql://' scheme, not 'postgres://'.
            if url.startswith("postgres://"):
                url = "postgresql://" + url[len("postgres://"):]
            return url
    return f"sqlite:///{BASE_DIR / 'lagniappe.db'}"


DATABASE_URL = _resolve_database_url()

_engine_kwargs = {"future": True, "pool_pre_ping": True}
if DATABASE_URL.startswith("postgresql"):
    # Serverless-friendly: open a fresh connection per use rather than pooling
    # across function invocations.
    _engine_kwargs["poolclass"] = NullPool

engine = create_engine(DATABASE_URL, **_engine_kwargs)


class Base(DeclarativeBase):
    pass


SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
)


def init_db() -> None:
    """Create tables for all registered models."""
    from . import models  # noqa: F401  (imported so models register on Base)

    Base.metadata.create_all(engine)
