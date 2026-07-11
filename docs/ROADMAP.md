# Roadmap

## Phase Overview

| Phase | Focus | CORE Phase Alignment | Status |
| ------- | ------- | ---------------------- | -------- |
| MVP | Prompt Evaluation | Phase 1 — Strategy & Contracts | Definition |
| Phase 2 | RAG Evaluation (DeepEval) | Phase 2 — Execution Setup | ✅ Complete |
| Phase 3 | Multi-Model Comparison | Phase 2 — Execution Setup | ✅ Complete |
| Phase 4 | Agent Evaluation | Phase 2 — Execution Setup | ✅ Complete |
| Phase 5 | Observability & Monitoring | Phase 3 — Monitoring & Operations | ✅ Complete |
| Phase 6 | CORE Governance Integration | Phase 3 — Monitoring & Operations | ✅ Complete |
| Phase 7 | CI/CD Integration | Phase 4 — Deployment & Automation | ✅ Complete |
| Phase 8 | Extended Provider Support | Phase 2 — Execution Setup | Planned |

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

## Phase 6 — CORE Governance Integration

Goal: Integrate the AI QA Core Framework governance methodology — risk classification, failure escalation, prompt regression testing, red team security evaluation, override management, and continuous scheduling.

### Phase 6 - Milestones

| # | Milestone | Description | Status |
| --- | ----------- | ------------- | -------- |
| G1 | Risk-Based Prioritization | `RiskClassifier` with 7 change types, composite risk formula, `--risk` and `--risk-threshold` CLI flags | ✅ Complete |
| G2 | Failure Escalation | `EscalationEngine` with severity gate map (none/warning/error/critical/blocker), 11 `FailureCode` values, `--gate` CLI flag | ✅ Complete |
| G3 | Prompt Regression Testing | `PromptRegistry` for baseline storage, `PromptRegressionMetric` (F1-based), `harness prompt-regress` CLI command | ✅ Complete |
| G4 | Red Team Security Evaluation | `RedTeamExecutor` with 3 default LLM attack tests (jailbreak, prompt injection, role-play extraction), ASR tracking, `harness red-team` CLI | ✅ Complete |
| G5 | Operations Tooling | `harness override request/list/approve/reject` CLI stubs, `docs/rollback_checklist.md` | ✅ Complete |
| G6 | Continuous Scheduling | `SchedulerEngine` with JSON-backed schedule registry, `harness scheduler add/list/run` CLI | ✅ Complete |

### Phase 6 - Dependencies

- Phase 5 observability must be complete (time series store for ASR tracking, alerting for gate violations)
- CLI must support flag injection for risk/gate parameters
- Evaluation contracts must be extensible for risk and security metadata

---

## Phase 7 — CI/CD Integration

Goal: Automate evaluation runs in CI/CD pipelines and surface results in pull requests.

### Phase 7 - Milestones

| # | Milestone | Description | Status |
| --- | ----------- | ------------- | -------- |
| C1 | GitHub Actions Workflow | `harness-eval.yml` — runs eval/rag-eval/agent-eval in parallel with smoke-test limits on push and PR | ✅ Complete |
| C2 | PR Comment Reporting | Posts evaluation summary as a PR comment via `actions/github-script@v7` with per-job status table | ✅ Complete |
| C3 | Artifact Publishing | Uploads reports, dashboards, time series, and logs as `actions/upload-artifact@v4` per job | ✅ Complete |
| C4 | Scheduled Regression Runs | `harness-scheduled.yml` — cron triggers (Mon/Thu 06:00 UTC) + `workflow_dispatch` with configurable dataset/model/limit | ✅ Complete |
| C5 | Status Badge | `BadgeGenerator` in `src/harness/ci.py` — generates shields.io-compatible SVG badge; `harness ci badge` CLI command | ✅ Complete |
| C6 | CORE Alignment | CI metadata envelope, KPI baseline comparison, release quality report, ASR gating, coverage enforcement, failure code alignment | ✅ Complete |

### Phase 7 - Dependencies

- CLI must support non-interactive / headless mode ✅ (already satisfied)
- Exit codes must reliably signal pass/fail for CI gating ✅ (0=pass, 1=fail, 2=block)
- Report output paths must be configurable ✅ (--output/-o on all eval commands)

### Phase 7 - CORE Alignment (C6)

Additional changes to align with the AI QA Core Framework CI/CD specifications:

| Item | Change | CORE Reference |
|------|--------|----------------|
| CI Metadata Envelope | `EvaluationConfig` now carries `environment`, `release_id`, `execution_id`, `owner` fields; eval commands accept `--ci-env`, `--release-id`, `--execution-id`, `--owner` | data_contracts.md metadata envelope |
| KPI Baseline Comparison | `BaselineComparator` in `kpi_baseline.py` — Green/Yellow/Red per KPI using CORE thresholds, `harness ci kpi` | kpi_governance.md thresholds |
| Release Quality Report | `ReleaseReportGenerator` in `ci.py` — Go/Conditional-Go/No-Go aggregating risk, ASR, coverage, KPI verdicts; `harness ci report` | release_quality_report.md template |
| ASR Gating | `--asr-threshold` on `harness red-team` — gates CI pipeline when attack success rate exceeds threshold (default 10%) | red_team_suite.md Section 5.4 |
| Coverage Enforcement | `--coverage-min` on eval/rag-eval/agent-eval — fails if limit drops coverage below minimum | kpi_governance.md Evaluation Coverage KPI |
| Failure Code Alignment | `CXT_ERR` added for Context Overflow; `CON_ERR` re-mapped for Consistency Failure; code severity table aligned | risk_prioritization_contracts.md Section 5.1 |
| Rollback in CI | Scheduled workflow includes rollback trigger step on failure, logs last known good version and references rollback_checklist.md | 02_operations/rollback_procedure.md |

---

## Phase 8 — Extended Provider Support

Goal: Add OpenAI-compatible providers (Groq, OpenRouter, OpenAI, etc.) for broader model access.

### Phase 8 - Milestones

| # | Milestone | Description | Status |
| --- | ----------- | ------------- | -------- |
| P1 | OpenAI-Compatible Provider | Support Groq, OpenRouter, and any OpenAI-API provider via a shared client | Planned |
| P2 | Provider Configuration | API keys, base URLs, and model selections via environment variables and `.env` | Planned |
| P3 | Cost Tracking | Token-based cost calculation per-provider with configurable pricing | Planned |
| P4 | Retry & Rate Limiting | Exponential backoff, rate-limit handling, and request timeout configuration | Planned |
