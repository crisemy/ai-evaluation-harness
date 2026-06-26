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

## Package Structure

```
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

## Integration Layer

Provides integration with CI/CD platforms and external systems.
