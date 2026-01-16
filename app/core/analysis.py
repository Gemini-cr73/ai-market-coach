# app/core/analysis.py
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf


def get_price_history(
    ticker: str, period: str = "1y", interval: str = "1d"
) -> pd.DataFrame:
    """
    Download historical price data using yfinance.
    auto_adjust=True often removes 'Adj Close' and adjusts OHLC.
    Depending on versions, columns can vary, so we normalize later.
    """
    data = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
        group_by="column",
    )

    if data is None or data.empty:
        raise ValueError(f"No price data found for ticker '{ticker}'.")

    return data


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    yfinance sometimes returns MultiIndex columns, especially in certain setups.
    This flattens them so we can safely reference OHLC columns.
    """
    if isinstance(df.columns, pd.MultiIndex):
        # Typical MultiIndex: ('Close', 'AAPL') or ('AAPL', 'Close') depending on version
        # We'll join with '_' then later search for close-like columns.
        df = df.copy()
        df.columns = [
            "_".join([str(x) for x in col if x is not None]).strip()
            for col in df.columns.values
        ]
    return df


def _extract_close_series(price_df: pd.DataFrame) -> pd.Series:
    """
    Return a 'close' price series from a yfinance DataFrame, handling
    different column layouts and names.
    """
    df = _normalize_columns(price_df)

    # Most common cases
    if "Close" in df.columns:
        return df["Close"]
    if "Adj Close" in df.columns:
        return df["Adj Close"]

    # MultiIndex flattened cases might look like: "Close_AAPL" or "AAPL_Close"
    close_candidates = [c for c in df.columns if "close" in c.lower()]

    # Prefer something that looks like "Close_*" over "*_Close"
    close_candidates_sorted = sorted(
        close_candidates,
        key=lambda c: (0 if c.lower().startswith("close") else 1, len(c)),
    )

    if close_candidates_sorted:
        return df[close_candidates_sorted[0]]

    raise ValueError(
        f"Price data is missing a close column. Available columns: {list(df.columns)}"
    )


def compute_price_metrics(price_df: pd.DataFrame) -> dict:
    """
    Compute basic price & risk metrics from historical price data.
    Robust to different yfinance column layouts.
    """
    close = _extract_close_series(price_df).dropna()
    if close.empty:
        raise ValueError("Close series is empty after dropping NA values.")

    returns = close.pct_change().dropna()

    metrics: dict = {}

    metrics["last_price"] = float(close.iloc[-1])
    metrics["start_price"] = float(close.iloc[0])
    metrics["period_return_pct"] = float((close.iloc[-1] / close.iloc[0] - 1) * 100)

    daily_vol = returns.std() if not returns.empty else 0.0
    metrics["daily_volatility_pct"] = float(daily_vol * 100)
    metrics["annualized_volatility_pct"] = float(daily_vol * np.sqrt(252) * 100)

    running_max = close.cummax()
    drawdown = (close - running_max) / running_max
    metrics["max_drawdown_pct"] = float(drawdown.min() * 100)

    metrics["mean_daily_return_pct"] = float(
        (returns.mean() * 100) if not returns.empty else 0.0
    )
    metrics["min_price"] = float(close.min())
    metrics["max_price"] = float(close.max())

    return metrics


def get_company_snapshot(ticker: str) -> dict:
    """
    Get basic company info and key fundamentals.
    """
    t = yf.Ticker(ticker)
    info = t.info or {}

    return {
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


def analyze_ticker(ticker: str, period: str = "1y", interval: str = "1d") -> dict:
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
    return f"{value:.2f}%"


def generate_learning_report(
    ticker: str, analysis: dict, user_level: str, model: str = "offline"
) -> str:
    """
    OFFLINE version of the learning report (no external AI calls).
    """
    company = analysis.get("company", {}) or {}
    metrics = analysis.get("price_metrics", {}) or {}

    ticker = analysis.get("ticker", ticker.upper())
    period = analysis.get("period", "1y")
    interval = analysis.get("interval", "1d")

    name = company.get("short_name") or company.get("long_name") or ticker
    sector = company.get("sector") or "N/A"
    industry = company.get("industry") or "N/A"
    country = company.get("country") or "N/A"
    exchange = company.get("exchange") or "N/A"
    currency = company.get("currency") or "N/A"

    last_price = metrics.get("last_price", 0.0)
    start_price = metrics.get("start_price", 0.0)
    period_return = metrics.get("period_return_pct", 0.0)
    daily_vol = metrics.get("daily_volatility_pct", 0.0)
    ann_vol = metrics.get("annualized_volatility_pct", 0.0)
    max_dd = metrics.get("max_drawdown_pct", 0.0)
    mean_ret = metrics.get("mean_daily_return_pct", 0.0)
    min_price = metrics.get("min_price", 0.0)
    max_price = metrics.get("max_price", 0.0)

    direction = "increased" if period_return >= 0 else "decreased"
    risk_level = "low" if ann_vol < 15 else "moderate" if ann_vol < 30 else "high"

    report = f"""# 1. Company Snapshot

- **Ticker**: `{ticker}`
- **Name**: {name}
- **Sector / Industry**: {sector} / {industry}
- **Exchange / Country**: {exchange} / {country}
- **Trading Currency**: {currency}

---

# 2. Price & Volatility Overview

We looked at **{ticker}** over **{period}** using **{interval}** data.

- **Start price**: {start_price:.2f} {currency}
- **Last price**: {last_price:.2f} {currency}
- **Total return**: {_fmt_pct(period_return)} ({direction})
- **Daily volatility**: {_fmt_pct(daily_vol)}
- **Annualized volatility**: {_fmt_pct(ann_vol)} → **{risk_level} volatility**
- **Maximum drawdown**: {_fmt_pct(max_dd)}
- **Average daily return**: {_fmt_pct(mean_ret)}
- **Price range**: {min_price:.2f} – {max_price:.2f} {currency}

---

# 3. Fundamentals Overview (High Level)

- **Market capitalization**: {company.get("market_cap", "N/A")}
- **Trailing P/E ratio**: {company.get("trailing_pe", "N/A")}
- **Forward P/E ratio**: {company.get("forward_pe", "N/A")}
- **Dividend yield**: {company.get("dividend_yield", "N/A")}
- **Beta (vs. market)**: {company.get("beta", "N/A")}

---

**Educational mode only. Not financial advice.**
"""
    return report
