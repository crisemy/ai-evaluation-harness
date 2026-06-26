# AI Evaluation Harness

AI Evaluation Harness is an open-source framework designed to evaluate, validate, and monitor AI-powered systems.

The project aims to provide a structured and repeatable approach to AI Quality Engineering, helping teams assess the reliability and performance of:

* Large Language Models (LLMs)
* Retrieval-Augmented Generation (RAG) systems
* AI Agents
* AI Assistants
* Prompt-based applications

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

Project Stage: **Phase 2 Complete** — RAG Evaluation

### MVP (Prompt Evaluation)

| # | Milestone | Status |
|---|-----------|--------|
| — | Contracts & Interfaces | ✅ Complete |
| M1 | Dataset Loader | ✅ Complete |
| M2 | Provider Interface (Ollama) | ✅ Complete |
| M3 | Prompt Executor | ✅ Complete |
| M4 | Evaluation Engine | ✅ Complete |
| M5 | Report Generator | ✅ Complete |
| M6 | CLI Entry Point | ✅ Complete |

### Phase 2 — RAG Evaluation

| # | Milestone | Status |
|---|-----------|--------|
| R1 | DeepEval Integration | ✅ Complete |
| R2 | Context Provider | ✅ Complete |
| R3 | RAG Metrics (Faithfulness, Relevancy, Precision, Recall) | ✅ Complete |
| R4 | Context & Chunking Spec | ✅ Complete |
| R5 | End-to-End RAG Pipeline (`harness rag-eval`) | ✅ Complete |

### Phase 3 — Multi-Model Comparison

| # | Milestone | Status |
|---|-----------|--------|
| C1 | Model Registry (`ModelSpec`) | ✅ Complete |
| C2 | Parallel Execution (`ThreadPoolExecutor`) | ✅ Complete |
| C3 | Comparison Report (side-by-side metrics, tokens, latency) | ✅ Complete |
| C4 | Cost & Latency Tracking | ✅ Complete |

The full evaluation pipeline works end-to-end: **load dataset → execute prompts → evaluate metrics → generate report**.

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
|----------|-------------|
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

This project follows the methodology defined in the [AI QA Core Framework](ai-qa-core-framework/) (`ai-qa-core-framework/`). The CORE framework provides the governing methodology, contracts, and skills; this project is the concrete implementation of an AI evaluation tool within that framework.

## Setup

### Prerequisites

- Python 3.12+
- PowerShell 7+ (Windows)

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

```
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
└── loaders/              # Concrete dataset loaders
    ├── __init__.py
    └── json_loader.py    # JSONDatasetLoader
```

## Python Conventions

- **Source code** goes under `src/harness/`
- **Contracts** (dataclasses) go under `src/harness/contracts/`
- **Interfaces** (abstract classes) go under `src/harness/interfaces/`
- **Dataset preparation scripts** go under `scripts/`
- **Tests** go under `tests/`
- Use `requirements.txt` for pinned dependencies (add as you go)

## Running Tests

```powershell
.\.venv\Scripts\Activate.ps1
pytest tests/ -v
```

## License

TBD
