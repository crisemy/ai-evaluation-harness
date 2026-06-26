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

Provides integration with CI/CD platforms and external systems via the CLI (`harness eval`).

## Current Package Structure

```
src/harness/
├── __init__.py
├── __main__.py              # python -m harness support
├── cli.py                   # CLI entry point (argparse)
├── errors.py                # Shared error types
├── comparison.py            # ComparisonEngine, ModelSpec, CompareConfig, ComparisonReport
├── evaluator.py             # EvaluationEngine, EvalSample, EvaluationConfigInput
├── evaluator_rag.py         # RAGEvaluator, RAGSample
├── executor.py              # PromptExecutor, ExecutorConfig
├── contracts/               # Data contracts (dataclasses)
│   ├── dataset.py
│   ├── execution.py
│   ├── evaluation.py
│   ├── rag.py               # Document, DocumentChunk, RAGEvaluationInput
│   ├── report.py
│   └── trace.py
├── interfaces/              # Abstract base classes
│   ├── dataset_loader.py
│   ├── provider.py
│   ├── metric.py
│   ├── reporter.py
│   ├── observer.py
│   └── context_provider.py  # ContextProvider — abstract retrieval interface
├── loaders/                 # Concrete dataset loaders
│   ├── __init__.py
│   └── json_loader.py       # JSONDatasetLoader
├── metrics/                 # Concrete metric implementations
│   ├── __init__.py
│   ├── exact_match.py       # ExactMatch — string equality
│   ├── contains.py          # Contains — substring search
│   └── rag/                 # DeepEval-wrapped RAG metrics
│       ├── __init__.py
│       ├── faithfulness.py       # FaithfulnessMetric
│       ├── answer_relevancy.py   # AnswerRelevancyMetric
│       ├── context_precision.py  # ContextualPrecisionMetric
│       └── context_recall.py     # ContextualRecallMetric
├── providers/               # Concrete LLM provider implementations
│   ├── __init__.py
│   ├── ollama.py            # OllamaProvider — HTTP client for local Ollama
│   └── context.py           # DatasetContextProvider — context from dataset entries
└── reporters/               # Concrete report generators
    ├── __init__.py
    └── json_reporter.py     # JSONReporter — writes EvaluationSummary to JSON
```
