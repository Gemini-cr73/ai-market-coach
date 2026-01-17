# app/db/database.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _load_env_for_local_dev() -> None:
    """
    Load .env for local development only.
    - Does NOT override existing env vars (important for Docker/Azure).
    - Looks for .env in repo root first, then current working directory.
    """
    candidates = [
        # repo root (two levels up from app/db/database.py -> repo/)
        Path(__file__).resolve().parents[2] / ".env",
        # current working directory (where you run uvicorn from)
        Path.cwd() / ".env",
    ]
    for p in candidates:
        if p.exists():
            load_dotenv(dotenv_path=p, override=False)
            return


_load_env_for_local_dev()

# Accept common keys (some setups used DATABASE_URL, others DATABASE_URI)
DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("DATABASE_URI")
    or os.getenv("DATABASE_URL")  # harmless alias if you ever used it
    or ""
).strip()

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Put it in your .env (local) or set it as an environment variable (Docker/Azure)."
    )

# Normalize common variant: postgres:// -> postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Optional debug print (won't leak password). Enable with DEBUG_DB=1
if os.getenv("DEBUG_DB", "").strip() == "1":
    safe = DATABASE_URL
    try:
        prefix, rest = safe.split("://", 1)
        creds, tail = rest.split("@", 1)
        user = creds.split(":", 1)[0]
        safe = f"{prefix}://{user}:***@{tail}"
    except Exception:
        pass
    print(f"[db] using {safe}")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
