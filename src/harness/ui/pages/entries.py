from __future__ import annotations

import streamlit as st
import pandas as pd


def render(per_entry_df: pd.DataFrame):
    st.header("Per-Entry Drill-Down")

    if per_entry_df.empty:
        st.info("No entry data available.")
        return

    entry_ids = sorted(per_entry_df["entry_id"].unique())
    selected_entry = st.selectbox("Filter by Entry ID", ["All"] + entry_ids)

    filtered = per_entry_df
    if selected_entry != "All":
        filtered = filtered[filtered["entry_id"] == selected_entry]

    search = st.text_input("Search responses", "")
    if search:
        filtered = filtered[filtered["response"].str.contains(search, case=False, na=False)]

    pivot = filtered.pivot_table(
        index="entry_id",
        columns="label",
        values=["response", "latency_ms", "tokens", "cost_label"],
        aggfunc="first",
    )
    pivot.columns = [f"{col[1]} ({col[0]})" for col in pivot.columns]
    pivot = pivot.reset_index()

    st.dataframe(pivot, use_container_width=True)

    if selected_entry != "All":
        st.subheader(f"Response Comparison — {selected_entry}")
        entry_data = per_entry_df[per_entry_df["entry_id"] == selected_entry]
        cols = st.columns(len(entry_data))
        for i, (_, row) in enumerate(entry_data.iterrows()):
            with cols[i]:
                st.markdown(f"**{row['label']}**")
                st.text(row["response"])
                st.caption(f"Latency: {row['latency_ms']} ms | Tokens: {row['tokens']} | Cost: {row['cost_label']}")

    with st.expander("Raw Entry Data"):
        st.dataframe(filtered, use_container_width=True)
