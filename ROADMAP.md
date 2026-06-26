# Roadmap

## Phase Overview

| Phase | Focus | CORE Phase Alignment | Status |
|-------|-------|----------------------|--------|
| MVP | Prompt Evaluation | Phase 1 — Strategy & Contracts | Definition |
| Phase 2 | RAG Evaluation (DeepEval) | Phase 2 — Execution Setup | ✅ Complete |
| Phase 3 | Multi-Model Comparison | Phase 2 — Execution Setup | Planned |
| Phase 4 | Agent Evaluation | Phase 2 — Execution Setup | Planned |
| Phase 5 | Observability & Monitoring | Phase 3 — Monitoring & Operations | Planned |

---

## MVP — Prompt Evaluation

Goal: Establish the core evaluation pipeline for LLM prompt-response evaluation.

### Milestones

| # | Milestone | Description | Status |
|---|-----------|-------------|--------|
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

### Milestones

| # | Milestone | Description | Status |
|---|-----------|-------------|--------|
| R1 | DeepEval Integration | Integrate DeepEval as the RAG evaluation backend | ✅ Complete |
| R2 | Context Provider | Abstract interface for document retrieval sources | ✅ Complete |
| R3 | RAG Metrics | Faithfulness, answer relevancy, context precision, context recall | ✅ Complete |
| R4 | Chunking & Retrieval Spec | `Document` dataclass + `DatasetContextProvider` for dataset-origin context | ✅ Complete |
| R5 | End-to-End RAG Pipeline | `harness rag-eval` command wiring the full RAG pipeline | ✅ Complete |

### Dependencies

- MVP must be complete (pipeline pattern established)
- CORE red team suite for adversarial RAG testing

---

## Phase 3 — Multi-Model Comparison

Goal: Compare multiple models on the same evaluation datasets.

### Milestones

| # | Milestone | Description |
|---|-----------|-------------|
| C1 | Model Registry | Manage multiple provider/model configurations |
| C2 | Parallel Execution | Run evaluations across models simultaneously |
| C3 | Comparison Reports | Side-by-side metric comparison with visualizations |
| C4 | Cost & Latency Tracking | Track token usage, cost, and response time per model |

### Dependencies

- Provider interface must support multiple providers
- Reporting layer must support comparative output

---

## Phase 4 — Agent Evaluation

Goal: Evaluate multi-step AI agent behaviors and tool-use quality.

### Milestones

| # | Milestone | Description |
|---|-----------|-------------|
| A1 | Trajectory Capture | Record agent action sequences and intermediate states |
| A2 | Step-Level Metrics | Evaluate correctness of each step in a trajectory |
| A3 | Outcome Metrics | Evaluate whether the agent achieved the goal |
| A4 | Tool-Use Evaluation | Validate tool selection and parameter correctness |

---

## Phase 5 — Observability & Monitoring

Goal: Provide continuous monitoring and alerting for evaluation results.

### Milestones

| # | Milestone | Description |
|---|-----------|-------------|
| O1 | Execution Tracing | Capture full evaluation traces with timing data |
| O2 | Metric Time Series | Store metric results with timestamps for trend analysis |
| O3 | Alert Rules | Define threshold-based alerting for metric regressions |
| O4 | Dashboard Templates | Pre-built dashboards for evaluation health |
