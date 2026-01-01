# app/api/main.py

import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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


app = FastAPI(
    title="AI Market Coach API",
    description="Educational-only stock learning API (no investment advice).",
    version="0.2.0",
)

# Allow local Streamlit to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Simple health-check endpoint."""
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalysisRequest):
    """
    Main analysis endpoint.

    - Always tries to return *something* useful.
    - Only fails hard if we cannot even get market data.
    """
    ticker = request.ticker.strip().upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker must not be empty.")

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
        report_markdown = generate_learning_report(
            ticker,
            raw_analysis,
            user_level=request.user_level,
        )
    except Exception as e:
        # If OpenAI or prompt parsing fails, we give a helpful fallback instead
        report_markdown = (
            "### AI learning report unavailable\n\n"
            "The AI explanation could not be generated due to an internal error:\n\n"
            f"`{e}`\n\n"
            "Below is a JSON dump of the raw analysis data so you can still study it:\n\n"
            "```json\n"
            f"{json.dumps(raw_analysis, indent=2)}\n"
            "```"
        )

    # 3) QUIZ + FLASHCARDS (best effort, unique feature)
    quiz = []
    flashcards = []
    try:
        deck = generate_quiz_and_flashcards(
            ticker,
            raw_analysis,
            user_level=request.user_level,
            num_questions=5,
        )
        if isinstance(deck, dict):
            quiz = deck.get("quiz", []) or []
            flashcards = deck.get("flashcards", []) or []
    except Exception:
        # If quiz generation fails, we just skip it silently for now.
        quiz = []
        flashcards = []

    return {
        "ticker": ticker,
        "analysis": raw_analysis,  # whatever analyze_ticker returns
        "report_markdown": report_markdown,
        "quiz": quiz,
        "flashcards": flashcards,
        "disclaimer": (
            "This report is for educational purposes only and is not financial advice."
        ),
    }
