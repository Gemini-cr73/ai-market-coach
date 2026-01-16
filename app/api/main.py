# app/api/main.py

from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from app.core.analysis import analyze_ticker, generate_learning_report
from app.core.learning import generate_quiz_and_flashcards


class AnalysisRequest(BaseModel):
    """
    Request body for /analyze.

    Expected JSON from the front-end:
    {
      "ticker": "AAPL",
      "period": "1y",
      "interval": "1d",
      "user_level": "Beginner"
    }
    """

    ticker: str = Field(..., description="US stock ticker (e.g., AAPL, MSFT)")
    period: str = Field("1y", description="History period: '6mo', '1y', '2y', '5y'")
    interval: str = Field("1d", description="Data interval: '1d', '1wk', '1mo'")
    user_level: str = Field(
        "Beginner",
        description="Learning level: 'Beginner', 'Intermediate', or 'Advanced'",
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = (v or "").strip().upper()
        if not v:
            raise ValueError("Ticker must not be empty.")
        return v

    @field_validator("period")
    @classmethod
    def validate_period(cls, v: str) -> str:
        allowed = {"6mo", "1y", "2y", "5y"}
        v = (v or "").strip()
        if v not in allowed:
            raise ValueError(f"Invalid period '{v}'. Allowed: {sorted(allowed)}")
        return v

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v: str) -> str:
        allowed = {"1d", "1wk", "1mo"}
        v = (v or "").strip()
        if v not in allowed:
            raise ValueError(f"Invalid interval '{v}'. Allowed: {sorted(allowed)}")
        return v

    @field_validator("user_level")
    @classmethod
    def validate_user_level(cls, v: str) -> str:
        allowed = {"Beginner", "Intermediate", "Advanced"}
        v = (v or "Beginner").strip()
        # normalize common variants
        v_norm = v.capitalize()
        if v_norm not in allowed:
            raise ValueError(f"Invalid user_level '{v}'. Allowed: {sorted(allowed)}")
        return v_norm


app = FastAPI(
    title="AI Market Coach API",
    description="Educational-only stock learning API (no investment advice).",
    version="0.2.0",
)

# Allow Streamlit to talk to this API (local + deploy).
# Tighten allow_origins later to your deployed UI domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "ai-market-coach",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    """Simple health-check endpoint."""
    return {"status": "ok"}


def _safe_json_dump(obj: Any) -> str:
    """Best-effort JSON serialization for fallback output."""
    try:
        return json.dumps(obj, indent=2, default=str)
    except Exception:
        return json.dumps({"repr": repr(obj)}, indent=2)


@app.post("/analyze")
def analyze(request: AnalysisRequest) -> dict[str, Any]:
    """
    Main analysis endpoint.

    - Always tries to return *something* useful.
    - Only fails hard if we cannot even get market data.
    """
    ticker = request.ticker  # already validated + normalized

    # 1) CORE ANALYSIS (must succeed, otherwise we error)
    try:
        raw_analysis = analyze_ticker(
            ticker,
            period=request.period,
            interval=request.interval,
        )
    except ValueError as ve:
        # e.g. invalid ticker / no data
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        # serious internal error in the data layer
        raise HTTPException(
            status_code=500,
            detail=f"Internal error while fetching/processing data: {e}",
        )

    # 2) AI LEARNING REPORT (best effort)
    report_markdown = ""
    try:
        # Support both common signatures:
        #   generate_learning_report(ticker, raw_analysis, user_level=...)
        #   generate_learning_report(raw_analysis, user_level=...)
        try:
            report_markdown = generate_learning_report(
                ticker,
                raw_analysis,
                user_level=request.user_level,
            )
        except TypeError:
            report_markdown = generate_learning_report(
                raw_analysis,
                user_level=request.user_level,
            )
    except Exception as e:
        report_markdown = (
            "### AI learning report unavailable\n\n"
            "The AI explanation could not be generated due to an internal error:\n\n"
            f"`{e}`\n\n"
            "Below is a JSON dump of the raw analysis data so you can still study it:\n\n"
            "```json\n"
            f"{_safe_json_dump(raw_analysis)}\n"
            "```"
        )

    # 3) QUIZ + FLASHCARDS (best effort, unique feature)
    quiz = []
    flashcards = []
    try:
        # Support both signatures:
        #   generate_quiz_and_flashcards(ticker, raw_analysis, user_level=..., num_questions=...)
        #   generate_quiz_and_flashcards(ticker, raw_analysis, user_level=...)
        try:
            deck = generate_quiz_and_flashcards(
                ticker,
                raw_analysis,
                user_level=request.user_level,
                num_questions=5,
            )
        except TypeError:
            deck = generate_quiz_and_flashcards(
                ticker,
                raw_analysis,
                user_level=request.user_level,
            )

        if isinstance(deck, dict):
            quiz = deck.get("quiz", []) or []
            flashcards = deck.get("flashcards", []) or []
    except Exception:
        quiz = []
        flashcards = []

    return {
        "ticker": ticker,
        "analysis": raw_analysis,
        "report_markdown": report_markdown,
        "quiz": quiz,
        "flashcards": flashcards,
        "disclaimer": "This report is for educational purposes only and is not financial advice.",
    }
