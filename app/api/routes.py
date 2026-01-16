# app/api/routes.py
from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.analysis import analyze_ticker, generate_learning_report
from app.core.learning import generate_quiz_and_flashcards

router = APIRouter()


class AnalysisRequest(BaseModel):
    """
    Request body for /analyze.
    """

    ticker: str = Field(..., description="US stock ticker (e.g., AAPL, MSFT)")
    period: str = Field("1y", description="History period: '6mo', '1y', '2y', '5y'")
    interval: str = Field("1d", description="Data interval: '1d', '1wk', '1mo'")
    user_level: str = Field(
        "Beginner", description="Learning level: Beginner | Intermediate | Advanced"
    )


def stable_seed(ticker: str, period: str, interval: str, user_level: str) -> int:
    """
    Deterministic seed so:
    - Same inputs => same quiz/flashcards (no reshuffle on reruns)
    - Different ticker/period/interval/level => different quiz set
    """
    # normalize to avoid accidental differences due to whitespace/casing
    t = (ticker or "").strip().upper()
    p = (period or "").strip()
    i = (interval or "").strip()
    u = (user_level or "").strip()

    key = f"{t}|{p}|{i}|{u}".encode()
    digest = hashlib.sha256(key).hexdigest()
    return int(digest[:8], 16)


@router.post("/analyze")
def analyze(request: AnalysisRequest) -> dict[str, Any]:
    ticker = request.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker must not be empty.")

    period = request.period.strip()
    interval = request.interval.strip()
    user_level = request.user_level.strip()

    # 1) CORE ANALYSIS (must succeed)
    try:
        raw_analysis = analyze_ticker(
            ticker,
            period=period,
            interval=interval,
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error while processing market data: {e}",
        )

    # 2) LEARNING REPORT (best effort)
    try:
        report_markdown = generate_learning_report(
            ticker,
            raw_analysis,
            user_level=user_level,
        )
    except Exception as e:
        report_markdown = (
            "### Learning report unavailable\n\n"
            f"**Error:** `{e}`\n\n"
            "### Raw analysis data\n"
            "```json\n"
            f"{json.dumps(raw_analysis, indent=2, default=str)}\n"
            "```"
        )

    # 3) QUIZ + FLASHCARDS (seeded for stable variation)
    quiz: list[dict[str, Any]] = []
    flashcards: list[dict[str, Any]] = []
    quiz_error: str | None = None

    seed = stable_seed(ticker, period, interval, user_level)

    try:
        deck = generate_quiz_and_flashcards(
            ticker=ticker,
            analysis=raw_analysis,
            user_level=user_level,
            num_questions=5,
            seed=seed,
        )
        if isinstance(deck, dict):
            quiz = deck.get("quiz", []) or []
            flashcards = deck.get("flashcards", []) or []
    except Exception as e:
        # keep API resilient: still return analysis+report even if quiz fails
        quiz_error = str(e)
        quiz = []
        flashcards = []

    response: dict[str, Any] = {
        "ticker": ticker,
        "analysis": raw_analysis,
        "report_markdown": report_markdown,
        "quiz": quiz,
        "flashcards": flashcards,
        "disclaimer": "This content is for educational purposes only and is not financial advice.",
    }

    # Optional but helpful during dev
    if quiz_error:
        response["quiz_error"] = quiz_error

    return response
