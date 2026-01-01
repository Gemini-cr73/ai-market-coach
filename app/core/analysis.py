# app/core/analysis.py

from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf


def get_price_history(
    ticker: str, period: str = "1y", interval: str = "1d"
) -> pd.DataFrame:
    """
    Download historical price data for a U.S. equity using yfinance.
    Auto-adjusts for splits/dividends.
    """
    data = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )
    if data.empty:
        raise ValueError(f"No price data found for ticker '{ticker}'.")
    return data


def compute_price_metrics(price_df: pd.DataFrame) -> dict:
    """
    Compute basic price & risk metrics from a historical price DataFrame.
    Expects an index of dates and a 'Close' column.
    """
    close = price_df["Close"]
    returns = close.pct_change().dropna()

    metrics: dict = {}

    # Basic price info
    metrics["last_price"] = float(close.iloc[-1])
    metrics["start_price"] = float(close.iloc[0])
    metrics["period_return_pct"] = float((close.iloc[-1] / close.iloc[0] - 1) * 100)

    # Volatility (daily & annualized)
    daily_vol = returns.std()
    metrics["daily_volatility_pct"] = float(daily_vol * 100)
    metrics["annualized_volatility_pct"] = float(daily_vol * np.sqrt(252) * 100)

    # Max drawdown
    running_max = close.cummax()
    drawdown = (close - running_max) / running_max
    metrics["max_drawdown_pct"] = float(drawdown.min() * 100)

    # Simple stats
    metrics["mean_daily_return_pct"] = float(returns.mean() * 100)
    metrics["min_price"] = float(close.min())
    metrics["max_price"] = float(close.max())

    return metrics


def get_company_snapshot(ticker: str) -> dict:
    """
    Get basic company info (name, sector, etc.) and key fundamentals.
    Uses yfinance.Ticker.info (good enough for v1).
    """
    t = yf.Ticker(ticker)
    info = t.info or {}

    snapshot = {
        "ticker": ticker.upper(),
        "short_name": info.get("shortName"),
        "long_name": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "currency": info.get("currency"),
        "exchange": info.get("exchange"),
        "country": info.get("country"),
    }
    return snapshot


def analyze_ticker(ticker: str, period: str = "1y", interval: str = "1d") -> dict:
    """
    High-level function: pulls price data + company info and returns a clean dict
    that we will feed into the learning / quiz parts.
    """
    ticker = ticker.upper()
    price_df = get_price_history(ticker, period=period, interval=interval)
    price_metrics = compute_price_metrics(price_df)
    company_snapshot = get_company_snapshot(ticker)

    return {
        "ticker": ticker,
        "as_of": datetime.utcnow().isoformat() + "Z",
        "period": period,
        "interval": interval,
        "company": company_snapshot,
        "price_metrics": price_metrics,
    }


def _fmt_pct(value: float) -> str:
    """Helper to format a float as a percentage with 2 decimals."""
    return f"{value:.2f}%"


def generate_learning_report(
    ticker: str, analysis: dict, user_level: str, model: str = "offline"
) -> str:
    """
    OFFLINE version of the learning report.

    No OpenAI calls. We generate a structured markdown explanation using
    the computed metrics and company snapshot.
    """
    company = analysis.get("company", {}) or {}
    metrics = analysis.get("price_metrics", {}) or {}

    ticker = analysis.get("ticker", ticker.upper())
    period = analysis.get("period", "1y")
    interval = analysis.get("interval", "1d")

    # Extract with safe defaults
    name = company.get("short_name") or company.get("long_name") or ticker
    sector = company.get("sector") or "N/A"
    industry = company.get("industry") or "N/A"
    country = company.get("country") or "N/A"
    exchange = company.get("exchange") or "N/A"
    currency = company.get("currency") or "N/A"

    last_price = metrics.get("last_price")
    start_price = metrics.get("start_price")
    period_return = metrics.get("period_return_pct")
    daily_vol = metrics.get("daily_volatility_pct")
    ann_vol = metrics.get("annualized_volatility_pct")
    max_dd = metrics.get("max_drawdown_pct")
    mean_ret = metrics.get("mean_daily_return_pct")
    min_price = metrics.get("min_price")
    max_price = metrics.get("max_price")

    # Basic interpretation sentences
    direction = "increased" if (period_return or 0) >= 0 else "decreased"
    risk_level = (
        "low" if (ann_vol or 0) < 15 else "moderate" if (ann_vol or 0) < 30 else "high"
    )

    report = f"""# 1. Company Snapshot

- **Ticker**: `{ticker}`
- **Name**: {name}
- **Sector / Industry**: {sector} / {industry}
- **Exchange / Country**: {exchange} / {country}
- **Trading Currency**: {currency}

This section gives you basic identification information about the company so you
know *what* you are studying before looking at any numbers.

---

# 2. Price & Volatility Overview

We looked at **{ticker}** over a **{period}** period, using a **{interval}** interval.

- **Start price**: {start_price:.2f} {currency} (beginning of period)
- **Last price**: {last_price:.2f} {currency} (most recent)
- **Total price change over the period**: {_fmt_pct(period_return)} ({direction})
- **Daily volatility** (typical day-to-day move): {_fmt_pct(daily_vol)}
- **Annualized volatility** (scaled to a year): {_fmt_pct(ann_vol)} → interpreted as **{risk_level} volatility**
- **Maximum drawdown** (worst peak-to-trough drop): {_fmt_pct(max_dd)}
- **Average daily return**: {_fmt_pct(mean_ret)}
- **Price range** during period: {min_price:.2f} – {max_price:.2f} {currency}

These numbers help you understand both **performance** (returns) and **risk**
(volatility and drawdown).

---

# 3. Fundamentals Overview (High Level)

If available, we also check simple fundamental indicators:

- **Market capitalization**: {company.get("market_cap", "N/A")}
- **Trailing P/E ratio**: {company.get("trailing_pe", "N/A")}
- **Forward P/E ratio**: {company.get("forward_pe", "N/A")}
- **Dividend yield**: {company.get("dividend_yield", "N/A")}
- **Beta (vs. market)**: {company.get("beta", "N/A")}

These numbers describe how expensive the stock is relative to its earnings,
whether it pays dividends, and how much it tends to move compared with the
overall market (via beta).

---

# 4. Key Learning Points for This Stock

1. **Direction of performance**
   Over the selected period, the price has **{direction}** by {_fmt_pct(period_return)}.
   This does *not* mean it will continue doing the same thing in the future—
   it simply tells you what happened historically.

2. **Risk & volatility**
   An annualized volatility of {_fmt_pct(ann_vol)} suggests **{risk_level} price
   fluctuations**. Higher volatility means the stock's price tends to move
   around more from day to day.

3. **Drawdowns matter**
   The maximum drawdown of {_fmt_pct(max_dd)} shows how much the stock could
   fall from a previous peak. This is important for understanding how
   uncomfortable a bad period might feel for an investor.

4. **Daily returns**
   The average daily return of {_fmt_pct(mean_ret)} gives a sense of the
   direction of returns, but it should always be considered together with
   volatility and drawdowns.

5. **Fundamentals (if available)**
   Ratios like P/E and dividend yield help describe how the market is
   currently valuing the company and whether it returns cash to shareholders.

---

# 5. Glossary of Terms (Level: {user_level})

- **Volatility** – A measure of how much the price moves around. Higher
  volatility means larger, more frequent price swings.

- **Annualized volatility** – The daily volatility scaled to a yearly number.
  It allows you to compare risk levels between different stocks.

- **Drawdown** – The percentage drop from a previous high to a later low.
  A large drawdown means the stock experienced a significant downturn.

- **Market capitalization** – The total value of all shares (share price ×
  number of shares). Roughly, how large the company is in the market.

- **P/E ratio (Price/Earnings)** – The stock price divided by earnings per
  share. It is one way of expressing how much investors are paying per unit
  of current or expected earnings.

- **Dividend yield** – Annual dividends per share divided by price. Shows how
  much cash return (as dividends) the stock generates relative to its price.

---

This report is generated in **offline educational mode**: it is designed to
teach you how to read basic market statistics.
**This report is for educational purposes only and is not financial advice.**
"""

    return report
