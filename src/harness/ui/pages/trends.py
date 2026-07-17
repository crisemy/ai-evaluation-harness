from __future__ import annotations

import streamlit as st
import plotly.express as px
import pandas as pd


def render(historical_data: list[dict]):
    st.header("Trends Over Time")

    if not historical_data:
        st.info(
            "No historical reports found. "
            "Run `harness compare` multiple times with `-o .harness/reports/comparison_report_<date>.json` "
            "to build up history."
        )
        return

    df = pd.DataFrame(historical_data)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

    if df.empty:
        st.info("No valid timestamp data in historical reports.")
        return

    metric_cols = [c for c in df.columns if c not in ("filename", "timestamp")]
    metric_choice = st.selectbox("Metric", sorted(metric_cols))

    fig = px.line(
        df,
        x="timestamp",
        y=metric_choice,
        title=f"{metric_choice} Over Time",
        markers=True,
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Historical Report Table"):
        display = df.copy()
        if "timestamp" in display.columns:
            display["timestamp"] = display["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(display, use_container_width=True)
