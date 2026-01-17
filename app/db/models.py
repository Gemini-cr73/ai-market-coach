from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    sessions: Mapped[list["MarketSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    signals: Mapped[list["LearningSignal"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class MarketSession(Base):
    __tablename__ = "market_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    period: Mapped[str] = mapped_column(String(32), nullable=False, default="1y")

    # flexible: can evolve without breaking schema each time
    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="sessions")


class LearningSignal(Base):
    __tablename__ = "learning_signals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)

    concept: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)

    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="signals")
