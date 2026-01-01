# AI Market Coach

Educational-only stock learning assistant.

## Features

- Fetches historical stock prices and basic fundamentals via `yfinance`.
- Computes returns, volatility, and drawdown metrics.
- Uses OpenAI to generate a **teaching-style report** (no investment advice).
- Unique feature: builds a **Learning Deck**:
  - Multiple-choice quiz questions
  - Flashcards exportable to JSON

## Getting Started

```bash
python -m venv .venv
# activate your venv...
pip install -r requirements.txt
