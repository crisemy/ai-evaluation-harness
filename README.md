# AI Evaluation Harness

AI Evaluation Harness is an open-source framework designed to evaluate, validate, and monitor AI-powered systems.

The project aims to provide a structured and repeatable approach to AI Quality Engineering, helping teams assess the reliability and performance of:

* Large Language Models (LLMs)
* Retrieval-Augmented Generation (RAG) systems
* AI Agents
* AI Assistants
* Prompt-based applications

## Architecture

```mermaid
flowchart LR
    CLI["harness CLI"]
    DS["Kaggle Dataset"]
    LOADER["JSONDatasetLoader"]
    OLLAMA["Ollama"]
    PE["PromptExecutor"]
    EE["Eval Engine"]
    RE["RAG Eval"]
    AE["Agent Eval"]
    CE["Compare Engine"]
    TR["TraceObserver"]
    TS["TimeSeriesStore"]
    AL["AlertEngine"]
    DG["DashboardGen"]
    JR["JSONReporter"]

    CLI --> LOADER
    CLI --> PE
    CLI --> EE & RE & AE & CE
    CLI --> TR & TS & AL & DG
    CLI --> JR

    LOADER --> DS
    PE --> OLLAMA
    EE --> PE
    RE --> PE
    CE --> PE

    EE & RE & AE & CE --> JR
    EE & RE & AE & CE --> TS
    EE & RE & AE & CE --> TR
    TS --> AL
    TS --> DG
```

## Why This Project Exists

Traditional software testing relies on deterministic outputs and exact assertions.

AI systems behave differently.

The same input may produce multiple valid outputs, making conventional testing approaches insufficient.

AI Evaluation Harness aims to provide:

* Repeatable evaluations
* Objective quality metrics
* Regression detection
* Automated validation
* CI/CD integration

## Current Status

Project Stage: **Phase 5 Complete** — Observability & Monitoring

### MVP (Prompt Evaluation)

| # | Milestone | Status |
| --- | ----------- | -------- |
| — | Contracts & Interfaces | ✅ Complete |
| M1 | Dataset Loader | ✅ Complete |
| M2 | Provider Interface (Ollama) | ✅ Complete |
| M3 | Prompt Executor | ✅ Complete |
| M4 | Evaluation Engine | ✅ Complete |
| M5 | Report Generator | ✅ Complete |
| M6 | CLI Entry Point | ✅ Complete |

### Phase 2 — RAG Evaluation

| # | Milestone | Status |
| --- | ----------- | -------- |
| R1 | DeepEval Integration | ✅ Complete |
| R2 | Context Provider | ✅ Complete |
| R3 | RAG Metrics (Faithfulness, Relevancy, Precision, Recall) | ✅ Complete |
| R4 | Context & Chunking Spec | ✅ Complete |
| R5 | End-to-End RAG Pipeline (`harness rag-eval`) | ✅ Complete |

### Phase 3 — Multi-Model Comparison

| # | Milestone | Status |
| --- | ----------- | -------- |
| C1 | Model Registry (`ModelSpec`) | ✅ Complete |
| C2 | Parallel Execution (`ThreadPoolExecutor`) | ✅ Complete |
| C3 | Comparison Report (side-by-side metrics, tokens, latency) | ✅ Complete |
| C4 | Cost & Latency Tracking | ✅ Complete |

### Phase 4 — Agent Evaluation

| # | Milestone | Status |
| --- | ----------- | -------- |
| A1 | Trajectory Capture (`AgentStep`, `AgentTrajectory`) | ✅ Complete |
| A2 | Step-Level Metrics (`StepCorrectness`) | ✅ Complete |
| A3 | Outcome Metrics (`GoalAchievement`) | ✅ Complete |
| A4 | Tool-Use Metrics (`ToolSelection`, `TrajectoryCoherence`) | ✅ Complete |

### Phase 5 — Observability & Monitoring

| # | Milestone | Status |
| --- | ----------- | -------- |
| O1 | Execution Tracing (`TraceObserver`) — captures evaluation events with timing, persists to NdJSON | ✅ Complete |
| O2 | Metric Time Series (`TimeSeriesStore`) — appends metric results with timestamps for trend analysis | ✅ Complete |
| O3 | Alert Rules (`AlertEngine`) — threshold-based alerting (gt/lt/gte/lte/eq) with default rules | ✅ Complete |
| O4 | Dashboard Templates (`DashboardGenerator`) — generates static HTML dashboards with summary cards, alerts, metric history, trends | ✅ Complete |

The full evaluation pipeline works end-to-end: **load dataset → execute prompts → evaluate metrics → generate report**.

### Upcoming Phases

| Phase | Focus | Status |
| ------- | ------- | -------- |
| Phase 6 | CI/CD Integration — GitHub Actions workflows, PR comments, artifact publishing | Planned |
| Phase 7 | Extended Provider Support — Groq, OpenRouter, OpenAI, cost tracking | Planned |

## Target Audience

* AI Engineers
* QA Engineers
* Reliability Engineers
* Automation Engineers
* Software Engineers building AI systems

## Project Goals

* Standardize AI evaluation practices.
* Enable automated AI quality validation.
* Support multiple AI providers.
* Integrate seamlessly with CI/CD workflows.
* Promote explainable and observable evaluations.

## Documentation

| Document | Description |
| ---------- | ------------- |
| `VISION.md` | Project vision and long-term goals |
| `CONTEXT.md` | Problem context and motivation |
| `ARCHITECTURE.md` | High-level architecture overview |
| `PLAN.md` | Scope and future phase roadmap |
| `ROADMAP.md` | Milestones, timeline, and dependencies |
| `DECISIONS.md` | Architecture decision records |
| `EVALUATION_PRINCIPLES.md` | Core evaluation principles |
| `DATASET_SPEC.md` | Dataset format specification |
| `docs/sdd.md` | Software Design Document (detailed) |
| `docs/testing_framework_overview.md` | Testing methodology for the harness |
| `docs/provider_interface.md` | Provider abstraction contract |
| `docs/metrics_spec.md` | Metric definitions and scoring |
| `docs/data_model.md` | Schemas and data contracts |
| `docs/rag_evaluation_strategy.md` | RAG evaluation strategy (Phase 2) |

## Relationship to AI QA Core Framework

This project follows the methodology defined in the AI QA Core Framework. The CORE framework provides the governing methodology, contracts, and skills; this project is the concrete implementation of an AI evaluation tool within that framework.

## Setup

### Prerequisites

a. Install Python 3.12+
b. PowerShell 7+ (Windows)

### Virtual Environment

```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

> The `.venv` directory is git-ignored. Activate it before running any harness commands.

### Deactivate

```powershell
deactivate
```

## Package Structure

```bash
src/harness/
├── __init__.py
├── errors.py             # Shared error types
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
├── loaders/              # Concrete dataset loaders
│   ├── __init__.py
│   └── json_loader.py    # JSONDatasetLoader
├── observers/            # Concrete Observer implementations
│   ├── __init__.py
│   └── trace_observer.py # TraceObserver — trace capture + NdJSON persistence
├── observability/        # Monitoring & alerting
│   ├── __init__.py
│   ├── models.py         # MetricSnapshot, AlertRule, AlertResult
│   ├── store.py          # TimeSeriesStore — NdJSON metric history
│   ├── alerts.py         # AlertEngine — threshold-based alerting
│   └── dashboard.py      # DashboardGenerator — HTML dashboard
```

## Python Conventions

a. **Source code** goes under `src/harness/`
b. **Tests** go under `tests/`
c. **Contracts** (dataclasses) go under `src/harness/contracts/`
d. **Interfaces** (abstract classes) go under `src/harness/interfaces/`
e. **Dataset preparation scripts** go under `scripts/`
f. **Tests** go under `tests/`
g. Use `requirements.txt` for pinned dependencies (add as you go)

## CLI Usage

### Evaluation Commands

```powershell
# Standard evaluation (1456 QA entries, runs against phi3)
harness eval -d datasets/qa_kaggle.json -m phi3 --metrics exact_match contains --limit 5

# RAG evaluation (requires a dataset with context_documents in metadata)
harness rag-eval -d datasets/rag_dataset.json -m phi3 --metrics faithfulness answer_relevancy

# Agent trajectory evaluation (requires trajectory data in metadata)
harness agent-eval -d datasets/agent_dataset.json -m phi3 --metrics step_correctness goal_achievement

# Multi-model comparison
harness compare -d datasets/qa_kaggle.json --models phi3 llama3.2 --metrics exact_match contains --limit 5
```

> Use `--limit 5` for quick smoke tests. Omit it to run against all entries.

### Observability Commands (Phase 5)

After running evaluations, traces and time series data are automatically recorded to `.harness/traces/` and `.harness/timeseries.ndjson`.

```powershell
# Show latest metric scores from history
harness monitor status

# Evaluate default alert rules (Low Pass Rate, Score Drop, Tool Selection)
harness monitor alerts

# Generate an HTML observability dashboard
harness monitor dashboard -o dashboard.html

# Open the dashboard
start dashboard.html
```

### Full Pipeline (end-to-end)

```powershell
# 1. Run tests
pytest tests/ -v

# 2. Quick eval (5 entries)
harness eval -d datasets/qa_kaggle.json -m phi3 --limit 5

# 3. Check results
harness monitor status

# 4. Generate dashboard
harness monitor dashboard -o dashboard.html
```

## Running Tests

```powershell
.\.venv\Scripts\Activate.ps1
pytest tests/ -v
```

## License

MIT
