# app/ui/streamlit_app.py

import os

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("AI_MARKET_COACH_API_URL", "http://127.0.0.1:8000")


def call_analyze_api(ticker: str, period: str, interval: str, user_level: str) -> dict:
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


def _ensure_state():
    """
    Streamlit reruns the script on every widget interaction.
    We store the latest API result in session_state so quiz clicks
    won't wipe the report and force you to click Analyze again.
    """
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "analyze_error" not in st.session_state:
        st.session_state.analyze_error = None
    if "last_payload" not in st.session_state:
        st.session_state.last_payload = None


def main():
    st.set_page_config(
        page_title="AI Market Coach",
        layout="wide",
    )

    _ensure_state()

    st.title("📈 AI Market Coach")
    st.caption(
        "Educational-only stock learning assistant with quizzes & flashcards (no investment advice)."
    )

    # ------------------------------
    # Sidebar inputs (use a FORM)
    # ------------------------------
    with st.sidebar:
        st.header("Settings")

        ticker = st.text_input("Ticker symbol", value="AAPL").strip().upper()
        period = st.selectbox("History period", ["6mo", "1y", "2y", "5y"], index=1)
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)
        user_level = st.selectbox(
            "Your experience level", ["Beginner", "Intermediate", "Advanced"], index=0
        )

        # Using a form prevents weird "button resets" and keeps the UX clean.
        with st.form("analyze_form", clear_on_submit=False):
            run_button = st.form_submit_button("Analyze")

        st.write("API:", API_URL)

    # ------------------------------
    # Run analysis (store in state)
    # ------------------------------
    if run_button:
        if not ticker:
            st.session_state.analysis_result = None
            st.session_state.analyze_error = "Please enter a ticker."
        else:
            st.session_state.analyze_error = None
            payload = {
                "ticker": ticker,
                "period": period,
                "interval": interval,
                "user_level": user_level,
            }
            st.session_state.last_payload = payload

            with st.spinner("Analyzing and generating learning materials..."):
                try:
                    st.session_state.analysis_result = call_analyze_api(
                        ticker, period, interval, user_level
                    )
                except Exception as e:
                    st.session_state.analysis_result = None
                    st.session_state.analyze_error = f"Error calling API: {e}"

    # ------------------------------
    # Render errors (if any)
    # ------------------------------
    if st.session_state.analyze_error:
        st.error(st.session_state.analyze_error)

    # ------------------------------
    # Render results from session_state
    # ------------------------------
    data = st.session_state.analysis_result
    if data is None:
        st.info("Enter settings and click **Analyze** to generate a learning report.")
        return

    # Layout
    col1, col2 = st.columns([1.2, 1])

    # --- Left: Report
    with col1:
        st.subheader("📘 Learning Report")
        st.markdown(data.get("report_markdown", ""))

    # --- Right: Metrics & quiz
    with col2:
        st.subheader("📊 Quick Metrics")

        analysis = data.get("analysis", {}) or {}
        pm = analysis.get("price_metrics", {}) or {}

        # Safer gets (avoid KeyError if a field is missing)
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
                    pm.get("last_price"),
                    pm.get("start_price"),
                    pm.get("period_return_pct"),
                    pm.get("daily_volatility_pct"),
                    pm.get("annualized_volatility_pct"),
                    pm.get("max_drawdown_pct"),
                    pm.get("mean_daily_return_pct"),
                    pm.get("min_price"),
                    pm.get("max_price"),
                ],
            }
        )
        st.dataframe(metrics_df, hide_index=True)

        st.markdown("---")
        st.subheader("🧠 Quiz Yourself")

        quiz = data.get("quiz", []) or []
        if not quiz:
            st.write("No quiz questions generated.")
        else:
            for idx, q in enumerate(quiz):
                q_text = q.get("question", f"Question {idx + 1}")
                options = q.get("options", []) or []

                with st.expander(f"Question {idx + 1}: {q_text}", expanded=False):
                    # IMPORTANT:
                    # - stable unique keys for each widget
                    # - do NOT use list(enumerate()) as options; it can confuse Streamlit state
                    selected = st.radio(
                        "Choose an answer:",
                        options,
                        key=f"quiz_choice_{idx}",
                    )

                    show_answer = st.checkbox("Show answer", key=f"quiz_show_{idx}")
                    if show_answer and options:
                        correct_idx = int(q.get("correct_option_index", 0) or 0)
                        correct_idx = max(0, min(correct_idx, len(options) - 1))
                        st.markdown(
                            f"**Correct answer:** {chr(65 + correct_idx)}. {options[correct_idx]}"
                        )
                        explanation = q.get("explanation", "")
                        if explanation:
                            st.info(explanation)

        st.markdown("---")
        st.subheader("🗂 Flashcards")

        flashcards = data.get("flashcards", []) or []
        if not flashcards:
            st.write("No flashcards generated.")
        else:
            for i, card in enumerate(flashcards):
                front = card.get("front", f"Card {i + 1}")
                back = card.get("back", "")
                with st.expander(f"Card {i + 1}: {front}"):
                    st.write(back)

            # Export flashcards as JSON
            st.download_button(
                label="Download flashcards (JSON)",
                data=pd.DataFrame(flashcards).to_json(orient="records", indent=2),
                file_name=f"{(analysis.get('ticker') or 'TICKER').upper()}_flashcards.json",
                mime="application/json",
            )

    disclaimer = data.get("disclaimer", "")
    if disclaimer:
        st.markdown(f"> **Disclaimer:** {disclaimer}")


if __name__ == "__main__":
    main()
