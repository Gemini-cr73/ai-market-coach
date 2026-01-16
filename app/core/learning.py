# app/core/learning.py
from __future__ import annotations

import random
from typing import Any


def _safe_float(x: Any, default: float | None = None) -> float | None:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _fmt_pct(x: float | None) -> str:
    if x is None:
        return "N/A"
    return f"{x:.2f}%"


def _fmt_num(x: Any) -> str:
    if x is None:
        return "N/A"

    if isinstance(x, int) and not isinstance(x, bool):
        return f"{x:,}"

    try:
        xf = float(x)
        if xf.is_integer():
            return f"{int(xf):,}"
        return f"{xf:,.4f}"
    except Exception:
        return str(x)


def _market_cap_bucket(market_cap: float | None) -> str:
    if market_cap is None:
        return "N/A"
    if market_cap >= 200e9:
        return "Large-cap"
    if market_cap >= 10e9:
        return "Mid-cap"
    if market_cap >= 2e9:
        return "Small-cap"
    return "Micro-cap"


def _vol_bucket(ann_vol: float | None) -> str:
    if ann_vol is None:
        return "N/A"
    if ann_vol < 15:
        return "Low"
    if ann_vol < 30:
        return "Moderate"
    return "High"


def _shuffle_options_keep_answer(
    options: list[str],
    correct_index: int,
    rng: random.Random,
) -> tuple[list[str], int]:
    """
    Shuffle options while keeping the correct answer index valid.
    Returns (shuffled_options, new_correct_index).
    """
    indexed = list(enumerate(options))
    rng.shuffle(indexed)

    new_options = [opt for _, opt in indexed]

    # Find where the original correct option ended up
    new_correct_index = 0
    for new_i, (old_i, _) in enumerate(indexed):
        if old_i == correct_index:
            new_correct_index = new_i
            break

    return new_options, new_correct_index


def _make_question(
    question: str,
    options: list[str],
    correct_option_index: int,
    explanation: str,
    rng: random.Random,
    shuffle: bool = True,
) -> dict[str, Any]:
    if shuffle and len(options) >= 2:
        options, correct_option_index = _shuffle_options_keep_answer(
            options, correct_option_index, rng
        )

    return {
        "question": question,
        "options": options,
        "correct_option_index": correct_option_index,
        "explanation": explanation,
    }


def generate_quiz_and_flashcards(
    ticker: str,
    analysis: dict[str, Any],
    user_level: str,
    num_questions: int = 5,
    seed: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    OFFLINE quiz + flashcard generator (section-aware).

    Builds a question bank using:
      1) Company Snapshot
      2) Price & Volatility Overview
      3) Fundamentals Overview

    Then randomly selects num_questions questions (if available).

    NOTE:
      - If routes.py passes a deterministic seed based on
        (ticker + period + interval + user_level),
        then different tickers/settings => different quiz set,
        and same inputs => stable quiz (no reshuffle on reruns).
    """
    rng = random.Random(seed)

    company = analysis.get("company") or {}
    pm = analysis.get("price_metrics") or {}

    # -----------------------------
    # Pull values (N/A-safe)
    # -----------------------------
    name = company.get("short_name") or company.get("long_name") or ticker
    sector = company.get("sector")
    industry = company.get("industry")
    exchange = company.get("exchange")
    country = company.get("country")
    currency = company.get("currency")

    market_cap = _safe_float(company.get("market_cap"))
    trailing_pe = company.get("trailing_pe")
    dividend_yield = company.get("dividend_yield")
    beta = company.get("beta")

    period_return = _safe_float(pm.get("period_return_pct"), 0.0) or 0.0
    ann_vol = _safe_float(pm.get("annualized_volatility_pct"))
    daily_vol = _safe_float(pm.get("daily_volatility_pct"))
    max_dd = _safe_float(pm.get("max_drawdown_pct"))
    min_price = _safe_float(pm.get("min_price"))
    max_price = _safe_float(pm.get("max_price"))

    direction = "increased" if period_return >= 0 else "decreased"
    vol_bucket = _vol_bucket(ann_vol)
    cap_bucket = _market_cap_bucket(market_cap)

    # -----------------------------
    # Question banks by section
    # -----------------------------
    bank: list[dict[str, Any]] = []

    # 1) Company Snapshot questions (only if data exists)
    if sector:
        bank.append(
            _make_question(
                question=f"Which sector is {ticker} primarily classified under?",
                options=[sector, "Technology", "Healthcare", "Financial Services"],
                correct_option_index=0,
                explanation=f"Based on the company snapshot, {ticker} is listed under the {sector} sector.",
                rng=rng,
            )
        )

    if exchange:
        bank.append(
            _make_question(
                question=f"Where is {ticker} listed (exchange)?",
                options=[exchange, "NYSE", "NASDAQ", "AMEX"],
                correct_option_index=0,
                explanation=f"The company snapshot lists the exchange as {exchange}.",
                rng=rng,
            )
        )

    if country:
        bank.append(
            _make_question(
                question=f"Which country is {ticker} associated with in the snapshot?",
                options=[country, "United States", "Canada", "United Kingdom"],
                correct_option_index=0,
                explanation=f"The snapshot lists the country as {country}.",
                rng=rng,
            )
        )

    if currency:
        bank.append(
            _make_question(
                question=f"What currency is {ticker} quoted in (according to the snapshot)?",
                options=[currency, "USD", "EUR", "GBP"],
                correct_option_index=0,
                explanation=f"The snapshot lists the trading currency as {currency}.",
                rng=rng,
            )
        )

    if industry:
        bank.append(
            _make_question(
                question=f"The industry for {ticker} is best described as:",
                options=[industry, "Banks", "Oil & Gas", "Utilities"],
                correct_option_index=0,
                explanation=f"The snapshot lists the industry as {industry}.",
                rng=rng,
            )
        )

    # 2) Price & Volatility Overview questions (always include at least one)
    bank.append(
        _make_question(
            question=f"Over the selected period, the price of {ticker} has:",
            options=[
                "Increased in value",
                "Decreased in value",
                "Stayed exactly the same",
                "We do not know from the data",
            ],
            correct_option_index=0 if direction == "increased" else 1,
            explanation=f"The total period return is {_fmt_pct(period_return)}. Positive means up; negative means down.",
            rng=rng,
        )
    )

    if ann_vol is not None:
        bank.append(
            _make_question(
                question=f"The annualized volatility for {ticker} is about {_fmt_pct(ann_vol)}. This is generally considered:",
                options=[
                    "Low volatility",
                    "Moderate volatility",
                    "High volatility",
                    "Guaranteed return",
                ],
                correct_option_index={"Low": 0, "Moderate": 1, "High": 2}.get(
                    vol_bucket, 1
                ),
                explanation="Volatility measures how much price fluctuates. Higher volatility means larger swings—not guaranteed profit.",
                rng=rng,
            )
        )

    if max_dd is not None:
        bank.append(
            _make_question(
                question=f"If maximum drawdown is about {_fmt_pct(max_dd)}, what does it describe?",
                options=[
                    "The worst peak-to-trough drop over the period",
                    "The average daily price movement",
                    "The annual return guaranteed every year",
                    "The dividend yield paid each year",
                ],
                correct_option_index=0,
                explanation="Drawdown is the percentage fall from a previous high to a later low—useful for understanding downside risk.",
                rng=rng,
            )
        )

    if min_price is not None and max_price is not None and min_price != max_price:
        bank.append(
            _make_question(
                question=f"What does the price range ({_fmt_num(min_price)} to {_fmt_num(max_price)}) tell you?",
                options=[
                    "The lowest and highest prices observed in the selected period",
                    "The guaranteed future trading range",
                    "The company’s book value range",
                    "The dividend range per share",
                ],
                correct_option_index=0,
                explanation="Min/Max prices are historical extremes over the chosen window; they do not guarantee future bounds.",
                rng=rng,
            )
        )

    if daily_vol is not None:
        bank.append(
            _make_question(
                question=f"Daily volatility is approximately {_fmt_pct(daily_vol)}. This is best interpreted as:",
                options=[
                    "Typical day-to-day price movement magnitude (in percent terms)",
                    "The company’s annual profit margin",
                    "A guaranteed daily profit",
                    "The maximum possible daily loss",
                ],
                correct_option_index=0,
                explanation="Daily volatility summarizes how much returns fluctuate day-to-day; it’s a risk/variability measure.",
                rng=rng,
            )
        )

    # 3) Fundamentals questions (only if data exists)
    if market_cap is not None:
        bank.append(
            _make_question(
                question=f"Based on the market cap, {ticker} would typically be considered:",
                options=["Large-cap", "Mid-cap", "Small-cap", "Micro-cap"],
                correct_option_index={
                    "Large-cap": 0,
                    "Mid-cap": 1,
                    "Small-cap": 2,
                    "Micro-cap": 3,
                }.get(cap_bucket, 1),
                explanation=f"With market cap ~{_fmt_num(market_cap)}, this fits {cap_bucket} (rule-of-thumb).",
                rng=rng,
            )
        )

    if trailing_pe is not None:
        bank.append(
            _make_question(
                question="What does the P/E ratio (Price/Earnings) represent?",
                options=[
                    "Price per share divided by earnings per share",
                    "Earnings per share divided by price per share",
                    "Dividend per share divided by price per share",
                    "Revenue divided by market cap",
                ],
                correct_option_index=0,
                explanation=f"P/E is a valuation ratio. (For {ticker}, trailing P/E is shown as {_fmt_num(trailing_pe)} when available.)",
                rng=rng,
            )
        )

    if dividend_yield is not None:
        bank.append(
            _make_question(
                question="Dividend yield is best described as:",
                options=[
                    "Annual dividends per share divided by stock price",
                    "Stock price divided by annual dividends per share",
                    "Market cap divided by dividends paid",
                    "Profit divided by market cap",
                ],
                correct_option_index=0,
                explanation=f"Dividend yield is the dividend return relative to price. (For {ticker}, dividend yield is shown as {_fmt_num(dividend_yield)} when available.)",
                rng=rng,
            )
        )

    if beta is not None:
        bank.append(
            _make_question(
                question="Beta (vs. the overall market) is best interpreted as:",
                options=[
                    "How sensitive the stock is to broad market moves",
                    "How many shares exist",
                    "How much dividend is paid each quarter",
                    "How many years the company has existed",
                ],
                correct_option_index=0,
                explanation=f"Beta is a relative risk measure vs. the market. (For {ticker}, beta is shown as {_fmt_num(beta)} when available.)",
                rng=rng,
            )
        )

    # -----------------------------
    # Select questions
    # -----------------------------
    rng.shuffle(bank)
    quiz = bank[: max(1, min(num_questions, len(bank)))]

    # -----------------------------
    # Flashcards
    # -----------------------------
    flashcards: list[dict[str, Any]] = [
        {
            "front": "What is volatility?",
            "back": (
                "A measure of how much a stock's price moves around. "
                "Higher volatility means larger, more frequent price swings."
            ),
        },
        {
            "front": "What is maximum drawdown?",
            "back": (
                "The biggest drop from a previous peak to a later low over a period. "
                "It shows how severe a downturn could have been."
            ),
        },
        {
            "front": "What does a positive period return mean?",
            "back": (
                f"For {name}, a positive period return means the price increased over "
                "the chosen time window. A negative return means it decreased."
            ),
        },
        {
            "front": "What is the P/E ratio (Price/Earnings)?",
            "back": (
                "The stock price divided by earnings per share. It is one way of "
                "describing how highly the market values the company's earnings."
            ),
        },
        {
            "front": "What is dividend yield?",
            "back": (
                "Annual dividends per share divided by the stock price. "
                "It indicates how much cash return you receive as dividends relative "
                "to the price."
            ),
        },
        {
            "front": "What is market capitalization?",
            "back": (
                "The total value of all outstanding shares (share price × shares). "
                "It’s a common way to describe how large a company is in the market."
            ),
        },
        {
            "front": "What is beta?",
            "back": (
                "A measure of how much a stock tends to move relative to the overall market. "
                "A beta above 1 means more sensitive; below 1 means less sensitive."
            ),
        },
    ]

    return {"quiz": quiz, "flashcards": flashcards}
