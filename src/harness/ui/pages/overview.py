from __future__ import annotations

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


def render(df):
    st.header("Model Comparison Overview")

    if df.empty:
        st.info("No model data available.")
        return

    best_pass_rate = df.loc[df["pass_rate"].idxmax()]
    cheapest = df.loc[df["cost"].idxmin()] if df["has_cost"].any() else None
    fastest = df.loc[df["avg_latency_ms"].idxmin()]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Best Pass Rate", f"{best_pass_rate['pass_rate']:.1f}%", best_pass_rate["label"])
    with col2:
        if cheapest is not None:
            st.metric("Cheapest", f"${cheapest['cost']:.6f}", cheapest["label"])
        else:
            st.metric("Cheapest", "N/A")
    with col3:
        st.metric("Fastest", f"{fastest['avg_latency_ms']:.0f} ms", fastest["label"])

    col_a, col_b = st.columns(2)

    with col_a:
        fig = px.bar(
            df, x="label", y="pass_rate",
            title="Pass Rate (%)",
            color="label",
            text="pass_rate",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig, use_container_width=True)

        fig3 = px.bar(
            df, x="label", y="avg_latency_ms",
            title="Average Latency (ms)",
            color="label",
            text=df["avg_latency_ms"].round(0).astype(int),
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig3.update_traces(texttemplate="%{text} ms", textposition="outside")
        fig3.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig3, use_container_width=True)

    with col_b:
        fig2 = px.bar(
            df, x="label", y="average_score",
            title="Average Score",
            color="label",
            text=df["average_score"].round(3),
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig2.update_traces(texttemplate="%{text}", textposition="outside")
        fig2.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig2, use_container_width=True)

        cost_df = df[df["has_cost"]]
        if not cost_df.empty:
            fig4 = px.bar(
                cost_df, x="label", y="cost",
                title="Total Cost ($)",
                color="label",
                text=cost_df["cost"].apply(lambda x: f"${x:.6f}"),
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig4.update_traces(texttemplate="%{text}", textposition="outside")
            fig4.update_layout(showlegend=False, height=350)
            st.plotly_chart(fig4, use_container_width=True)

    with st.expander("Raw Comparison Data"):
        display = df.drop(columns=["has_cost"])
        st.dataframe(display, use_container_width=True)
