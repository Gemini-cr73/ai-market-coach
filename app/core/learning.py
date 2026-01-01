# app/core/learning.py


def generate_quiz_and_flashcards(
    ticker: str,
    analysis: dict,
    user_level: str,
    num_questions: int = 5,
) -> dict[str, list[dict]]:
    """
    OFFLINE quiz + flashcard generator.

    Uses the computed metrics to create simple multiple-choice questions and
    flashcards—no external APIs.
    """
    pm = analysis.get("price_metrics", {}) or {}
    company = analysis.get("company", {}) or {}

    period_return = pm.get("period_return_pct", 0.0)
    ann_vol = pm.get("annualized_volatility_pct", 0.0)
    max_dd = pm.get("max_drawdown_pct", 0.0)

    direction = "increased" if period_return >= 0 else "decreased"

    quiz: list[dict] = []

    # Q1 – Direction of performance
    quiz.append(
        {
            "question": f"Over the selected period, the price of {ticker} has:",
            "options": [
                "Increased in value",
                "Decreased in value",
                "Stayed exactly the same",
                "We do not know from the data",
            ],
            "correct_option_index": 0 if direction == "increased" else 1,
            "explanation": (
                f"The total period return is {period_return:.2f}%. "
                "A positive value means the price increased; a negative value "
                "means it decreased."
            ),
        }
    )

    # Q2 – Volatility interpretation
    quiz.append(
        {
            "question": f"What does an annualized volatility of about {ann_vol:.1f}% mean?",
            "options": [
                "The price moves very little from day to day.",
                "The price tends to move around; larger swings are common.",
                "The company is guaranteed to earn that much each year.",
                "The stock will never lose more than that percentage.",
            ],
            "correct_option_index": 1,
            "explanation": (
                "Volatility measures how much the price moves around. "
                "Higher volatility means bigger and more frequent price swings, "
                "not guaranteed profits or losses."
            ),
        }
    )

    # Q3 – Drawdown
    quiz.append(
        {
            "question": f"If the maximum drawdown is about {max_dd:.1f}%, what does that describe?",
            "options": [
                "The worst peak-to-trough price drop over the period.",
                "The average daily price movement.",
                "The annual return expected every year.",
                "The dividend yield paid each year.",
            ],
            "correct_option_index": 0,
            "explanation": (
                "Drawdown is the percentage fall from a previous high to a later low. "
                "It helps you understand how painful a bad period could feel."
            ),
        }
    )

    # Limit to requested number of questions
    quiz = quiz[:num_questions]

    # --- Flashcards ---
    name = company.get("short_name") or company.get("long_name") or ticker

    flashcards: list[dict] = [
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
    ]

    return {"quiz": quiz, "flashcards": flashcards}
