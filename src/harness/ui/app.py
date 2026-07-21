from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

from harness.ui.loader import ComparisonReportLoader
from harness.ui.pages.overview import render as render_overview
from harness.ui.pages.entries import render as render_entries
from harness.ui.pages.cost import render as render_cost
from harness.ui.pages.trends import render as render_trends

st.set_page_config(
    page_title="AI Evaluation Harness — Comparison Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("AI Evaluation Harness — Comparison Dashboard")

args_raw = sys.argv[1:]
report_path = None
dataset = None
models = None
limit = 0

def _parse_args(raw: list[str]):
    global report_path, dataset, models, limit
    it = iter(raw)
    for arg in it:
        if arg == "--report":
            report_path = next(it)
        elif arg == "--dataset":
            dataset = next(it)
        elif arg == "--models":
            models = []
            for val in it:
                if val.startswith("--"):
                    if val == "--limit":
                        limit = int(next(it))
                    break
                models.append(val)
            break
        elif arg == "--limit":
            limit = int(next(it))

_parse_args(args_raw)

if report_path:
    loader = ComparisonReportLoader(report_path)
elif dataset and models:
    try:
        loader = ComparisonReportLoader.from_compare_command(dataset, models, limit)
        st.success(f"Comparison completed — {loader.total_entries} entries evaluated.")
    except RuntimeError as e:
        st.error(f"Failed to run comparison: {e}")
        st.stop()
else:
    st.info(
        "No comparison data provided.\n\n"
        "Launch with:\n"
        "- `harness ui --report comparison_report.json`\n"
        "- `harness ui --dataset datasets/qa_kaggle.json --models groq/llama-3.3-70b-versatile openrouter/openai/gpt-4o-mini ollama/phi3 --limit 5`"
    )
    st.stop()

df = loader.to_dataframe()
per_entry_df = loader.per_entry_df()
historical = ComparisonReportLoader.historical_reports()

st.sidebar.header("About")
st.sidebar.markdown(
    f"- **Dataset:** `{loader.dataset_path}`\n"
    f"- **Entries:** {loader.total_entries}\n"
    f"- **Duration:** {loader.duration_ms} ms\n"
    f"- **Timestamp:** {loader.timestamp}\n"
)

st.sidebar.header("Navigation")
page = st.sidebar.radio("Page", ["Overview", "Entries", "Cost", "Trends"])

if page == "Overview":
    render_overview(df)
elif page == "Entries":
    render_entries(per_entry_df)
elif page == "Cost":
    render_cost(per_entry_df, df)
elif page == "Trends":
    render_trends(historical)

st.sidebar.markdown("---")
st.sidebar.caption("AI Evaluation Harness — Phase 9")
