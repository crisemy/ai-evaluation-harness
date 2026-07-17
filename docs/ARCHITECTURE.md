# Architecture

The AI Evaluation Harness is organized around several logical layers.

## Dataset Layer

Stores evaluation datasets, golden answers, and benchmark data.

Includes the `DatasetLoader` interface and concrete implementations:

- **`JSONDatasetLoader`** — Loads datasets from the project's JSON schema (`format_version 1.0`). Validates required fields, format version, and entry structure at load time.
- Error types: `ValidationError`, `FormatError`, `LoadError` (defined in `src/harness/errors.py`).

## Execution Layer

The Execution Layer is responsible for running evaluations against supported AI providers.

Supported providers may include local and remote execution environments.

Examples include:

- Ollama
- OpenAI
- Anthropic
- Gemini
- OpenRouter
- DeepSeek API

Provider implementations should be abstracted behind a common interface.

## Evaluation Layer

Applies evaluation metrics and scoring mechanisms.

## Reporting Layer

Generates evaluation reports and quality dashboards.

## Observability Layer

Collects execution traces, metrics, logs, and diagnostic information.

Components:

- **`TraceObserver`** — Concrete Observer implementation that captures `ObservableEvent`s in memory, groups them by trace, and persists to NdJSON files. Integral with the existing `Observer` interface.
- **`TimeSeriesStore`** — Append-only NdJSON store that records `MetricSnapshot` entries with timestamps, evaluation IDs, and configuration context for trend analysis.
- **`AlertEngine`** — Evaluates threshold-based `AlertRule` definitions (operators: gt/lt/gte/lte/eq) against historical snapshots, producing `AlertResult` objects for triggered rules.
- **`DashboardGenerator`** — Generates a self-contained HTML dashboard page with summary cards, alert table, metric history table, and trend indicators.

## CI/CD Layer (Phase 7)

Provides GitHub Actions workflows for automated evaluation in CI pipelines, PR comments, artifact publishing, scheduled regression runs, and status badge generation.

Components:

- **`.github/workflows/harness-eval.yml`** — CI workflow with 5 parallel jobs: unit tests, evaluation matrix (eval/rag-eval/agent-eval), prompt regression, red team security, and combined summary report. Runs on push/PR. All jobs use CI metadata envelope (`--ci-env`, `--release-id`, `--execution-id`) and coverage enforcement (`--coverage-min 0.9`).
- **`.github/workflows/harness-scheduled.yml`** — Scheduled workflow triggered by cron (Monday/Thursday 06:00 UTC) and `workflow_dispatch` with configurable dataset, model, and entry limit. Runs KPI baseline comparison, release report, badge generation, and rollback trigger on failure.
- **`BadgeGenerator`** (`src/harness/ci.py`) — Generates a shields.io-compatible SVG badge from the latest time series snapshot. Exposed via `harness ci badge --store .harness/timeseries.ndjson -o badge.svg`.
- **`ReleaseReportGenerator`** (`src/harness/ci.py`) — Aggregates risk level, ASR, coverage, and KPI baseline verdicts into a Go/Conditional-Go/No-Go release decision. Exposed via `harness ci report`.
- **`BaselineComparator`** (`src/harness/kpi_baseline.py`) — Compares current metrics against historical baselines and produces Green/Yellow/Red verdicts per KPI using CORE-defined thresholds. Exposed via `harness ci kpi`.
- **PR Comment Reporting** — Uses `actions/github-script@v7` to post a per-job status table as a PR comment after each pipeline run.

## UI Layer (Phase 9 — Interactive Comparison Dashboard)

Provides an interactive Streamlit web application for exploring cross-provider comparison reports visually.

Components:

- **`streamlit_app()`** (`src/harness/ui/__init__.py`) — Entry point launched by `harness ui` CLI command. Spawns `streamlit run` as a subprocess with report or live-comparison arguments.
- **`ComparisonReportLoader`** (`src/harness/ui/loader.py`) — Loads `ComparisonReport` JSON files and normalises the data into pandas DataFrames for charting. Supports loading from file or running a fresh `harness compare` via subprocess.
- **Overview page** (`src/harness/ui/pages/overview.py`) — Summary metric cards (best pass rate, cheapest, fastest) and Plotly bar charts for pass rate, average score, latency, and cost per model.
- **Entries page** (`src/harness/ui/pages/entries.py`) — Searchable table with per-entry response text, latency, tokens, and cost across models. Expandable row view for full response comparison.
- **Cost page** (`src/harness/ui/pages/cost.py`) — Cost per entry grouped by model, cumulative cost bar chart, per-model cost summary table, and monthly cost extrapolator.
- **Trends page** (`src/harness/ui/pages/trends.py`) — Line charts showing pass rate, latency, or cost over time across historical comparison reports auto-detected from `.harness/reports/`.

## Governance Layer (Phase 6 — CORE Governance Integration)

Implements the AI QA Core Framework governance methodology: risk classification, failure escalation, prompt regression testing, red team security evaluation, override management, and continuous scheduling.

Components:

- **`RiskClassifier`** — Classifies changes by type (bugfix, feature, refactor, config, dependency, prompt, emergency) and computes a composite risk score from severity, likelihood, and impact.
- **`EscalationEngine`** — Evaluates evaluation results against severity gate thresholds (none/warning/error/critical/blocker). Maps `FailureCode` (11 codes) to severity levels and blocks or warns based on the configured gate.
- **`PromptRegressionMetric`** — F1-based metric that compares prompt outputs against a registered baseline to detect regressions.
- **`PromptRegistry`** — Stores baseline prompt outputs with versioning and metadata.
- **`RedTeamExecutor`** — Runs security attack tests (jailbreak, prompt injection, role-play extraction) against the model and tracks Attack Success Rate (ASR).
- **`SchedulerEngine`** — JSON-backed registry of scheduled evaluation tasks with configurable intervals.

## Package Structure

```bash
src/harness/
├── __init__.py
├── errors.py             # Shared error types: HarnessError, ValidationError, FormatError, LoadError, MetricError
├── contracts/            # Data contracts (dataclasses)
│   ├── dataset.py        # Dataset, DatasetEntry, DatasetMetadata, Difficulty
│   ├── execution.py      # ExecutionRequest, ExecutionResponse, TokenUsage, StreamChunk
│   ├── evaluation.py     # MetricResult, EvaluationResult, EvaluationSummary
│   ├── report.py         # Report, SummaryStats
│   └── trace.py          # ObservableEvent, Trace
├── interfaces/           # Abstract base classes
│   ├── dataset_loader.py # DatasetLoader (ABC)
│   ├── provider.py       # LLMProvider (ABC)
│   ├── metric.py         # Metric (ABC)
│   ├── reporter.py       # Reporter (ABC)
│   └── observer.py       # Observer (ABC)
└── loaders/              # Concrete dataset loader implementations
    ├── __init__.py
    └── json_loader.py    # JSONDatasetLoader — loads format_version 1.0 JSON datasets
```

## Current Package Structure

## Current Package Structure

```bash
src/harness/
├── __init__.py
├── __main__.py              # python -m harness support
├── cli.py                   # CLI entry point (argparse) — uses create_provider()
├── errors.py                # Shared error types
├── comparison.py            # ComparisonEngine, ModelSpec, CompareConfig, ComparisonReport
├── evaluator.py             # EvaluationEngine, EvalSample, EvaluationConfigInput
├── evaluator_rag.py         # RAGEvaluator, RAGSample
├── evaluator_agent.py       # AgentEvaluator, AgentSample
├── executor.py              # PromptExecutor, ExecutorConfig
├── contracts/               # Data contracts (dataclasses)
│   ├── dataset.py
│   ├── execution.py         # TokenUsage (cost field), ExecutionRequest, ExecutionResponse
│   ├── evaluation.py
│   ├── agent.py              # AgentStep, AgentTrajectory, AgentEvaluationInput
│   ├── rag.py               # Document, DocumentChunk, RAGEvaluationInput
│   ├── report.py
│   ├── risk.py              # ChangeType, RiskLevel, RiskAssessment (CORE governance)
│   ├── security.py          # RedTestCase, RedTestResult, RedTestSummary (CORE governance)
│   └── trace.py
├── interfaces/              # Abstract base classes
│   ├── dataset_loader.py
│   ├── provider.py          # LLMProvider ABC
│   ├── metric.py
│   ├── reporter.py
│   ├── observer.py
│   └── context_provider.py  # ContextProvider — abstract retrieval interface
├── loaders/                 # Concrete dataset loaders
│   ├── __init__.py
│   └── json_loader.py       # JSONDatasetLoader
├── metrics/                 # Concrete metric implementations
│   ├── __init__.py
│   ├── exact_match.py
│   ├── contains.py
│   ├── rag/                 # DeepEval-wrapped RAG metrics
│   │   ├── __init__.py
│   │   ├── faithfulness.py
│   │   ├── answer_relevancy.py
│   │   ├── context_precision.py
│   │   └── context_recall.py
│   └── agent/               # Agent trajectory metrics
│       ├── __init__.py
│       ├── step_correctness.py
│       ├── goal_achievement.py
│       ├── tool_selection.py
│       └── trajectory_coherence.py
├── providers/               # Concrete LLM provider implementations
│   ├── __init__.py          # create_provider() factory, PROVIDER_CONFIGS, .env auto-loader
│   ├── ollama.py            # OllamaProvider — HTTP client for local Ollama
│   ├── chat_completions.py  # ChatCompletionsProvider — /v1/chat/completions API (Groq, OpenRouter)
│   └── context.py           # DatasetContextProvider — context from dataset entries
├── observers/               # Concrete Observer implementations
│   ├── __init__.py
│   └── trace_observer.py    # TraceObserver — in-memory trace collection + NdJSON persistence
├── observability/            # Monitoring & observability tooling
│   ├── __init__.py
│   ├── models.py            # MetricSnapshot, TimeSeriesData, AlertRule, AlertResult, DashboardConfig
│   ├── store.py             # TimeSeriesStore — NdJSON append store for metric snapshots
│   ├── alerts.py            # AlertEngine — threshold-based alert rule evaluation
│   └── dashboard.py         # DashboardGenerator — static HTML dashboard generation
├── escalation.py            # EscalationEngine — severity gate map, failure codes (Phase 6)
├── prompt_regression.py     # PromptRegistry, PromptRegressionMetric (Phase 6)
├── ci.py                    # BadgeGenerator + ReleaseReportGenerator — CI/CD helpers (Phase 7)
├── kpi_baseline.py          # BaselineComparator — KPI comparison & Green/Yellow/Red verdicts (Phase 7)
├── scheduler.py             # SchedulerEngine — interval-based continuous eval (Phase 6)
├── risk/                    # Risk-based prioritization (Phase 6)
│   └── __init__.py          # RiskClassifier
├── red_team/                # Red team security evaluation (Phase 6)
│   └── __init__.py          # RedTeamExecutor
├── ui/                      # Streamlit interactive dashboard (Phase 9)
│   ├── __init__.py          # streamlit_app() entry point
│   ├── app.py               # Streamlit app: sidebar, page routing, layout
│   ├── loader.py            # ComparisonReportLoader — JSON → DataFrames
│   └── pages/
│       ├── __init__.py
│       ├── overview.py      # Model comparison bar charts
│       ├── entries.py       # Per-entry drill-down table
│       ├── cost.py          # Cost analysis charts
│       └── trends.py        # Historical trend line charts
└── reporters/               # Concrete report generators
    ├── __init__.py
    └── json_reporter.py     # JSONReporter — writes EvaluationSummary to JSON
```
