# Phase 9 — Interactive Comparison Dashboard

**Branch:** `phase-9-streamlit-dashboard`

## Goal

Replace static JSON comparison reports with an **interactive Streamlit dashboard** that visualises cross-provider evaluation results — pass rates, latency, tokens, and cost — across models at a glance.

## Why Streamlit?

| Option | Verdict |
|--------|---------|
| Static HTML (existing) | Works but no interactivity — no filtering, sorting, or drill-down |
| Streamlit | Single Python file per page, built-in widgets, easy deployment |
| React / Vue | Heavy frontend dependency, separate build step, overkill |
| Panel / Dash | Fewer contributors, smaller ecosystem than Streamlit |

Streamlit adds one dependency and converts comparison reports into a living, filterable, explorable dashboard with **~200 lines of app code**.

## Milestones

| # | Milestone | Description |
|---|-----------|-------------|
| D1 | **Streamlit scaffold** | `harness ui` CLI command, `src/harness/ui/` package, sidebar nav with page routing |
| D2 | **Comparison report loader** | Load comparison report JSON, normalise into pandas DataFrames, handle missing fields |
| D3 | **Model comparison view** | Bar charts: pass rate, avg score, latency, cost per model — colour-coded, sortable |
| D4 | **Per-entry drill-down** | Searchable table with per-model responses, expandable rows, entry selector |
| D5 | **Cost analysis view** | Per-model cost breakdown, cumulative cost, per-entry cost distribution |
| D6 | **Trends over time** | Line charts across historical comparison reports (pass rate, latency, cost) |

## Data Sources

- **Primary**: `comparison_report.json` — output of `harness compare`
- **Live**: If no report is provided, the CLI runs `harness compare` internally and feeds the result to the app
- **Historical**: `.harness/reports/comparison_report_*.json` files auto-detected for the Trends page

## Architecture

```
src/harness/ui/
├── __init__.py         # Package + streamlit_app() entry point
├── app.py              # Streamlit app: sidebar, page routing, layout
├── loader.py           # ComparisonReportLoader — JSON → DataFrames
└── pages/
    ├── __init__.py     # Page imports
    ├── overview.py     # Model comparison bar charts
    ├── entries.py      # Per-entry drill-down table
    ├── cost.py         # Cost analysis charts
    └── trends.py       # Historical trend line charts
```

### Data flow

```
comparison_report.json
        │
        ▼
ComparisonReportLoader
  ├── to_dataframe()       → pd.DataFrame (one row per model)
  ├── per_entry_df()       → pd.DataFrame (one row per entry per model)
  └── historical_reports() → list[dict] for trend pages
        │
        ▼
StreamlitApp
  ├── Overview page   ← to_dataframe()
  ├── Entries page    ← per_entry_df()
  ├── Cost page       ← per_entry_df()
  └── Trends page     ← historical_reports()
```

## CLI

```bash
# Launch dashboard from existing comparison report
harness ui --report comparison_report.json

# Launch dashboard and run fresh comparison first
harness ui --dataset datasets/qa_kaggle.json \
  --models groq/llama-3.3-70b-versatile openrouter/openai/gpt-4o-mini ollama/phi3 \
  --limit 20

# Custom port
harness ui --port 8502
```

## Views

### Overview
```
┌──────────────────────────────────────────────────┐
│  Best Model: groq/llama  │ Pass Rate: 80%        │
│  Cheapest: ollama/phi3   │ Cost: $0.0002         │
├──────────────────────────────────────────────────┤
│  Pass Rate        Avg Latency      Avg Cost       │
│  ┌────┬────┬────┐ ┌────┬────┬────┐ ┌────┬────┐  │
│  │███ │ ██ │ ██ │ │ ██ │████│ ██ │ │ ██ │ ██ │  │
│  └────┴────┴────┘ └────┴────┴────┘ └────┴────┘  │
│  groq  or   oll      groq  or  oll    groq  or   │
└──────────────────────────────────────────────────┘
```

### Entries
```
┌───────────────────────────────────────────────────────┐
│ Entry  │ Groq Resp    │ OpenRouter   │ Ollama  │ Cost │
├────────│──────────────│──────────────│─────────│──────┤
│ ci-001 │ Paris is...  │ The capital  │ Paris.. │ $0.3 │
│ ci-002 │ Berlin...    │ Berlin is..  │ Berlin  │ $0.2 │
└───────────────────────────────────────────────────────┘
```

### Cost
```
┌──────────────────────────────────────────┐
│ Cost per Entry by Model                  │
│  ███ ███ ███ ███ ███ ███ ███            │
│  ██  ██  ██  ██  ██  ██  ██             │
│  entry 1 2 3 4 5 6 7                    │
│                                          │
│ Cumulative Cost: groq $0.0012 / $0.0008  │
└──────────────────────────────────────────┘
```

## Dependencies

```
streamlit>=1.35
plotly>=5.20
```

## Rationale

- **Streamlit over static HTML**: The existing `DashboardGenerator` produces a static HTML page. For comparison data, users need to explore, filter, and compare — which is cumbersome in a static page.
- **Plotly over st.bar_chart**: Plotly provides tooltips, legends, and interactive zoom — essential for comparing 3+ models side-by-side.
- **Loader decoupling**: The `ComparisonReportLoader` separates data loading from rendering, making it testable and reusable if we later add a REST API or export feature.
