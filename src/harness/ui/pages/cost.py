from __future__ import annotations

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def render(per_entry_df: pd.DataFrame, summary_df: pd.DataFrame):
    st.header("Cost Analysis")

    if per_entry_df.empty:
        st.info("No cost data available.")
        return

    cost_data = per_entry_df[per_entry_df["cost"] > 0].copy()

    if cost_data.empty:
        st.info("No cost data available (models may be free/local like Ollama).")
    else:
        fig = px.bar(
            cost_data,
            x="entry_id",
            y="cost",
            color="label",
            title="Cost per Entry by Model",
            barmode="group",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

        cumulative = cost_data.groupby("label")["cost"].sum().reset_index()
        fig2 = px.bar(
            cumulative,
            x="label",
            y="cost",
            title="Cumulative Cost by Model",
            color="label",
            text=cumulative["cost"].apply(lambda x: f"${x:.6f}"),
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig2.update_traces(texttemplate="%{text}", textposition="outside")
        fig2.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Per-Model Cost Summary")
    cost_summary = per_entry_df.groupby("label").agg(
        total_tokens=("tokens", "sum"),
        total_latency_ms=("latency_ms", "sum"),
        total_cost=("cost", "sum"),
        entry_count=("entry_id", "nunique"),
    ).reset_index()

    cost_summary["avg_cost_per_entry"] = cost_summary.apply(
        lambda r: r["total_cost"] / r["entry_count"] if r["total_cost"] > 0 else 0, axis=1
    )
    cost_summary["cost_per_1k_tokens"] = cost_summary.apply(
        lambda r: (r["total_cost"] / r["total_tokens"]) * 1000 if r["total_cost"] > 0 and r["total_tokens"] > 0 else 0,
        axis=1,
    )

    cost_summary["total_cost"] = cost_summary["total_cost"].apply(lambda x: f"${x:.6f}")
    cost_summary["avg_cost_per_entry"] = cost_summary["avg_cost_per_entry"].apply(lambda x: f"${x:.6f}")
    cost_summary["cost_per_1k_tokens"] = cost_summary["cost_per_1k_tokens"].apply(lambda x: f"${x:.6f}")

    st.dataframe(cost_summary, use_container_width=True)

    with st.expander("Monthly Cost Estimate"):
        st.markdown("""
        **Assumptions:**
        - 1,000 evaluations per day
        - 30-day month
        - Current average cost per evaluation
        """)
        monthly = cost_summary.copy()
        monthly["avg_cost_per_entry"] = monthly["avg_cost_per_entry"].apply(
            lambda x: float(x.replace("$", ""))
        )
        monthly["monthly_estimate"] = monthly["avg_cost_per_entry"] * 1000 * 30
        monthly["monthly_estimate_display"] = monthly["monthly_estimate"].apply(
            lambda x: f"${x:.2f}"
        )
        for _, row in monthly.iterrows():
            st.metric(
                label=f"{row['label']} — Monthly Estimate",
                value=row["monthly_estimate_display"],
                delta=f"Based on 30K evaluations/month",
            )
