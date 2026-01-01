# app/ui/streamlit_app.py

import os
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("AI_MARKET_COACH_API_URL", "http://127.0.0.1:8000")


def call_analyze_api(ticker: str, period: str, interval: str, user_level: str):
    url = f"{API_URL}/analyze"
    payload = {
        "ticker": ticker,
        "period": period,
        "interval": interval,
        "user_level": user_level,
    }
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def main():
    st.set_page_config(
        page_title="AI Market Coach",
        layout="wide",
    )

    st.title("📈 AI Market Coach")
    st.caption(
        "Educational-only stock learning assistant with quizzes & flashcards (no investment advice)."
    )

    with st.sidebar:
        st.header("Settings")
        ticker = st.text_input("Ticker symbol", value="AAPL")
        period = st.selectbox("History period", ["6mo", "1y", "2y", "5y"], index=1)
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)
        user_level = st.selectbox(
            "Your experience level", ["Beginner", "Intermediate", "Advanced"], index=0
        )
        run_button = st.button("Analyze")

    if run_button:
        if not ticker.strip():
            st.error("Please enter a ticker.")
            return

        with st.spinner("Analyzing and generating learning materials..."):
            try:
                data = call_analyze_api(ticker, period, interval, user_level)
            except Exception as e:
                st.error(f"Error calling API: {e}")
                return

        # Layout
        col1, col2 = st.columns([1.2, 1])

        # --- Left: Report
        with col1:
            st.subheader("📘 Learning Report")
            st.markdown(data["report_markdown"])

        # --- Right: Metrics & quiz
        with col2:
            st.subheader("📊 Quick Metrics")
            pm = data["analysis"]["price_metrics"]
            metrics_df = pd.DataFrame(
                {
                    "Metric": [
                        "Last Price",
                        "Start Price",
                        "Period Return (%)",
                        "Daily Volatility (%)",
                        "Annualized Volatility (%)",
                        "Max Drawdown (%)",
                        "Mean Daily Return (%)",
                        "Min Price",
                        "Max Price",
                    ],
                    "Value": [
                        pm["last_price"],
                        pm["start_price"],
                        pm["period_return_pct"],
                        pm["daily_volatility_pct"],
                        pm["annualized_volatility_pct"],
                        pm["max_drawdown_pct"],
                        pm["mean_daily_return_pct"],
                        pm["min_price"],
                        pm["max_price"],
                    ],
                }
            )
            st.dataframe(metrics_df, hide_index=True)

            st.markdown("---")
            st.subheader("🧠 Quiz Yourself")
            for idx, q in enumerate(data["quiz"]):
                with st.expander(f"Question {idx+1}: {q['question']}"):
                    selected = st.radio(
                        "Choose an answer:",
                        list(enumerate(q["options"])),
                        format_func=lambda t: f"{chr(65 + t[0])}. {t[1]}",
                        key=f"quiz-{idx}",
                    )
                    show_answer = st.checkbox("Show answer", key=f"ans-{idx}")
                    if show_answer:
                        correct_idx = q["correct_option_index"]
                        st.markdown(
                            f"**Correct answer:** {chr(65 + correct_idx)}. {q['options'][correct_idx]}"
                        )
                        st.info(q["explanation"])

            st.markdown("---")
            st.subheader("🗂 Flashcards")
            flashcards = data["flashcards"]
            if not flashcards:
                st.write("No flashcards generated.")
            else:
                for i, card in enumerate(flashcards):
                    with st.expander(f"Card {i+1}: {card['front']}"):
                        st.write(card["back"])

                # Export flashcards as JSON
                st.download_button(
                    label="Download flashcards (JSON)",
                    data=pd.DataFrame(flashcards).to_json(orient="records", indent=2),
                    file_name=f"{ticker.upper()}_flashcards.json",
                    mime="application/json",
                )

        st.markdown(f"> **Disclaimer:** {data['disclaimer']}")


if __name__ == "__main__":
    main()
