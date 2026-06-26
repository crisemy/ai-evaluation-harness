# Roadmap

## Phase Overview

| Phase | Focus | CORE Phase Alignment | Status |
| ------- | ------- | ---------------------- | -------- |
| MVP | Prompt Evaluation | Phase 1 — Strategy & Contracts | Definition |
| Phase 2 | RAG Evaluation (DeepEval) | Phase 2 — Execution Setup | ✅ Complete |
| Phase 3 | Multi-Model Comparison | Phase 2 — Execution Setup | ✅ Complete |
| Phase 4 | Agent Evaluation | Phase 2 — Execution Setup | ✅ Complete |
| Phase 5 | Observability & Monitoring | Phase 3 — Monitoring & Operations | ✅ Complete |
| Phase 6 | CI/CD Integration | Phase 4 — Deployment & Automation | Planned |
| Phase 7 | Extended Provider Support | Phase 2 — Execution Setup | Planned |

---

## MVP — Prompt Evaluation

Goal: Establish the core evaluation pipeline for LLM prompt-response evaluation.

### Milestones

| # | Milestone | Description | Status |
| --- | ----------- | ------------- | -------- |
| M1 | Dataset Loader | Load evaluation datasets from files (JSON) | ✅ Complete |
| M2 | Provider Interface | Abstract provider contract with Ollama implementation | ✅ Complete |
| M3 | Prompt Executor | Execute prompts against providers, collect responses | ✅ Complete |
| M4 | Evaluation Engine | Apply metrics (exact_match, contains) to collected responses | ✅ Complete |
| M5 | Report Generator | Generate structured JSON evaluation reports | ✅ Complete |
| M6 | CLI Entry Point | `harness eval` command wiring the full pipeline | ✅ Complete |

### Dependencies

- CORE data contracts for dataset schema
- CORE KPI governance for metric definitions

---

## Phase 2 — RAG Evaluation

Goal: Extend the harness to evaluate Retrieval-Augmented Generation pipelines.

### Phase 2 - Milestones

| # | Milestone | Description | Status |
| --- | ----------- | ------------- | -------- |
| R1 | DeepEval Integration | Integrate DeepEval as the RAG evaluation backend | ✅ Complete |
| R2 | Context Provider | Abstract interface for document retrieval sources | ✅ Complete |
| R3 | RAG Metrics | Faithfulness, answer relevancy, context precision, context recall | ✅ Complete |
| R4 | Chunking & Retrieval Spec | `Document` dataclass + `DatasetContextProvider` for dataset-origin context | ✅ Complete |
| R5 | End-to-End RAG Pipeline | `harness rag-eval` command wiring the full RAG pipeline | ✅ Complete |

### Phase 2 - Dependencies

- MVP must be complete (pipeline pattern established)
- CORE red team suite for adversarial RAG testing

---

## Phase 3 — Multi-Model Comparison

Goal: Compare multiple models on the same evaluation datasets.

### Phase 3 - Milestones

| # | Milestone | Description | Status |
| --- | ----------- | ------------- | -------- |
| C1 | Model Registry | `ModelSpec` dataclass for provider/model configs | ✅ Complete |
| C2 | Parallel Execution | `ThreadPoolExecutor` runs models concurrently | ✅ Complete |
| C3 | Comparison Reports | JSON report with per-model metrics, tokens, latency side-by-side | ✅ Complete |
| C4 | Cost & Latency Tracking | Token count, latency captured per entry per model | ✅ Complete |

### Phase 3 - Dependencies

- Provider interface must support multiple providers
- Reporting layer must support comparative output

---

## Phase 4 — Agent Evaluation

Goal: Evaluate multi-step AI agent behaviors and tool-use quality.

### Phase 4 - Milestones

| # | Milestone | Description | Status |
| --- | ----------- | ------------- | -------- |
| A1 | Trajectory Capture | `AgentStep`, `AgentTrajectory` contracts — store action sequences and intermediate states | ✅ Complete |
| A2 | Step-Level Metrics | `StepCorrectness` — compare actual vs expected steps in a trajectory | ✅ Complete |
| A3 | Outcome Metrics | `GoalAchievement` — evaluate if final answer matches expected output | ✅ Complete |
| A4 | Tool-Use Evaluation | `ToolSelection` — F1-based tool usage scoring + `TrajectoryCoherence` — step sequence quality | ✅ Complete |

---

## Phase 5 — Observability & Monitoring

Goal: Provide continuous monitoring and alerting for evaluation results.

### Phase 5 - Milestones

| # | Milestone | Description | Status |
| --- | ----------- | ------------- | -------- |
| O1 | Execution Tracing | `TraceObserver` — concrete Observer impl that captures evaluation traces in memory and persists to NdJSON | ✅ Complete |
| O2 | Metric Time Series | `TimeSeriesStore` — append-only NdJSON store that records metric snapshots with timestamps for trend analysis | ✅ Complete |
| O3 | Alert Rules | `AlertEngine` — threshold-based alerting (gt/lt/gte/lte/eq) with default rules for pass rate, score, and tool selection | ✅ Complete |
| O4 | Dashboard Templates | `DashboardGenerator` — static HTML dashboard with summary cards, alert table, metric history, and trend indicators | ✅ Complete |

### Phase 5 - Dependencies

- Observer interface must be implemented concretely
- Time series data store for metric persistence
- CLI must expose monitoring commands

---

## Phase 6 — CI/CD Integration

Goal: Automate evaluation runs in CI/CD pipelines and surface results in pull requests.

### Phase 6 - Milestones

| # | Milestone | Description | Status |
| --- | ----------- | ------------- | -------- |
| C1 | GitHub Actions Workflow | `harness-eval.yml` workflow that runs `harness eval` on push/PR | Planned |
| C2 | PR Comment Reporting | Post evaluation summary as a PR comment with pass/fail breakdown | Planned |
| C3 | Artifact Publishing | Upload reports, dashboards, and time series as build artifacts | Planned |
| C4 | Scheduled Regression Runs | Daily/weekly cron workflow that builds time series history over time | Planned |
| C5 | Status Badge | Generate a shields.io-compatible badge showing latest pass rate | Planned |

### Phase 6 - Dependencies

- CLI must support non-interactive / headless mode
- Exit codes must reliably signal pass/fail for CI gating
- Report output paths must be configurable

---

## Phase 7 — Extended Provider Support

Goal: Add OpenAI-compatible providers (Groq, OpenRouter, OpenAI, etc.) for broader model access.

### Phase 7 - Milestones

| # | Milestone | Description | Status |
| --- | ----------- | ------------- | -------- |
| P1 | OpenAI-Compatible Provider | Support Groq, OpenRouter, and any OpenAI-API provider via a shared client | Planned |
| P2 | Provider Configuration | API keys, base URLs, and model selections via environment variables and `.env` | Planned |
| P3 | Cost Tracking | Token-based cost calculation per-provider with configurable pricing | Planned |
| P4 | Retry & Rate Limiting | Exponential backoff, rate-limit handling, and request timeout configuration | Planned |
