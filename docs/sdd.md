# Software Design Document — AI Evaluation Harness

## 1. Introduction

### 1.1 Purpose

This document describes the software architecture, component design, and interfaces of the AI Evaluation Harness. It is intended for developers, architects, and QA engineers contributing to or extending the framework.

### 1.2 Scope

The document covers the MVP (Prompt Evaluation) and Phase 2 (RAG Evaluation). Future phases are described structurally but not detailed.

### 1.3 Governing Methodology

This project follows the AI QA Core Framework methodology (`ai-qa-core-framework/`). Refer to `ai-qa-core-framework/00_project_methodology.md` for the overall project lifecycle and `ai-qa-core-framework/01_fundamentals/data_contracts.md` for data contract patterns.

---

## 2. System Overview

### 2.1 High-Level Architecture

```
                    ┌─────────────────────────┐
                    │       Integration       │
                    │     CI/CD · CLI · API   │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │      Orchestrator       │
                    │  Pipeline Coordinator   │
                    └──┬──────┬───────┬───────┘
                       │      │       │
              ┌────────▼──┐ ┌─▼──────┐ ┌▼────────┐
              │  Dataset  │ │ LLM    │ │Metrics  │
              │  Loader   │ │Executor│ │Engine   │
              └───────────┘ └────────┘ └─────────┘
                                    │
                           ┌────────▼────────┐
                           │    Reporter     │
                           │  (JSON · HTML)  │
                           └─────────────────┘
```

### 2.2 Architecture Principles

- **Layered**: Each layer has a single responsibility and communicates through defined interfaces.
- **Provider-Agnostic**: No hard dependency on any specific LLM provider.
- **Extensible**: New metrics, providers, and dataset formats can be added without modifying core code.
- **Observable by Default**: Every evaluation produces structured trace data.

---

## 3. Component Specifications

### 3.1 Dataset Loader

**Responsibility**: Load evaluation datasets from files into a standardized internal representation.

**Input**: File path + format identifier.

**Output**: `Dataset` object containing a list of `DatasetEntry` records.

**Supported Formats**:

| Format | Status |
|--------|--------|
| JSON | MVP |
| CSV | MVP |
| YAML | MVP |
| Parquet | Future |

**Key Behaviors**:

- Validate required fields (`id`, `input`, `expected_output`)
- Coerce optional fields (`category`, `difficulty`, `tags`, `metadata`)
- Reject malformed entries with descriptive errors
- Support streaming for large datasets

**Interface**:

```
interface DatasetLoader:
  load(path: str, format: str) → Dataset
  validate(entry: dict) → ValidationResult

struct Dataset:
  entries: list[DatasetEntry]
  metadata: DatasetMetadata

struct DatasetEntry:
  id: str
  input: str
  expected_output: str
  category: optional str
  difficulty: optional str
  tags: optional list[str]
  metadata: optional dict
```

**Error Handling**:

- Missing required fields → `ValidationError` with field name
- Unsupported format → `FormatError`
- IO errors → `LoadError` with file path and system message

### 3.2 LLM Executor

**Responsibility**: Send prompts to configured LLM providers and collect responses.

**Input**: `ExecutionRequest` (prompt, provider config, parameters).

**Output**: `ExecutionResponse` (text, metadata, timing, token usage).

**Key Behaviors**:

- Abstract provider interface (see `provider_interface.md`)
- Support synchronous and streaming execution
- Collect timing and token usage metadata
- Handle provider errors gracefully with retry logic
- Implement rate limiting per provider configuration

**Interface**:

```
interface Executor:
  execute(request: ExecutionRequest) → ExecutionResponse
  execute_batch(requests: list[ExecutionRequest]) → list[ExecutionResponse]

struct ExecutionRequest:
  entry_id: str
  prompt: str
  provider: str
  model: str
  parameters: optional dict

struct ExecutionResponse:
  entry_id: str
  text: str
  provider: str
  model: str
  latency_ms: int
  token_usage: TokenUsage
  timestamp: datetime
  raw_response: optional dict
```

**Error Handling**:

- Provider timeout → `TimeoutError` (configurable threshold)
- Authentication failure → `AuthError`
- Rate limit hit → `RateLimitError` (triggers backoff)
- Model unavailable → `ModelError`

### 3.3 Evaluation Engine

**Responsibility**: Apply evaluation metrics to execution results and compute scores.

**Input**: `EvaluationRequest` (response, expected output, metric config).

**Output**: `EvaluationResult` (metric scores, explanations, metadata).

**Key Behaviors**:

- Metric registry for discoverable metric implementations
- Each metric produces a score, explanation, and optional diagnosis
- Metrics can be composed into evaluation suites
- Metrics can be chained (output of one feeds into another)

**Interface**:

```
interface Metric:
  name: str
  evaluate(response: str, expected: str, context: optional dict) → MetricResult

struct MetricResult:
  metric_name: str
  score: float        # 0.0 - 1.0
  passed: bool        # score >= threshold
  explanation: str    # human-readable reasoning
  diagnosis: optional dict  # machine-readable details
  threshold: float

struct EvaluationResult:
  entry_id: str
  metrics: list[MetricResult]
  overall_score: float
  timestamp: datetime
  duration_ms: int
```

**Supported Metrics (MVP)**:

| Metric | Type | Description |
|--------|------|-------------|
| ExactMatch | Deterministic | Exact string comparison |
| Contains | Deterministic | Substring matching |
| RegexMatch | Deterministic | Pattern matching |
| Similarity | Embedding | Cosine similarity between embeddings |
| Custom | Extensible | User-defined Python functions |

**Error Handling**:

- Missing expected output → `SkippedResult` (metric not applicable)
- Metric execution failure → `MetricError` with trace
- Invalid score range → clamped to [0.0, 1.0]

### 3.4 Reporter

**Responsibility**: Transform evaluation results into structured output formats.

**Input**: `EvaluationSummary` (list of results, configuration metadata).

**Output**: Formatted report (JSON, HTML, Markdown).

**Key Behaviors**:

- Support multiple output formats
- Compute aggregate statistics per metric (mean, min, max, pass rate)
- Support summary and detailed modes
- Include environment and configuration metadata

**Interface**:

```
interface Reporter:
  generate(summary: EvaluationSummary, format: str, options: optional dict) → Report

struct EvaluationSummary:
  results: list[EvaluationResult]
  config: EvaluationConfig
  environment: EnvironmentInfo
  timestamp: datetime
  duration_ms: int

struct Report:
  format: str
  content: str
  metadata: ReportMetadata
```

**Output Formats**:

| Format | Use Case | Status |
|--------|----------|--------|
| JSON | Machine consumption, CI artifacts | MVP |
| Markdown | Human-readable, PR comments | MVP |
| HTML | Rich dashboards | Future |
| JUnit XML | CI pipeline integration | Future |

### 3.5 Observer (Observability)

**Responsibility**: Collect, store, and expose evaluation traces and metrics.

**Input**: Observable events emitted by all other components.

**Output**: Structured trace data for analysis and debugging.

**Key Behaviors**:

- Emit events at every pipeline stage (load, execute, evaluate, report)
- Collect timing data per stage
- Store traces for configurable retention
- Support log and metric exporters

**Interface**:

```
interface Observer:
  emit(event: ObservableEvent) → void
  get_trace(evaluation_id: str) → Trace

struct ObservableEvent:
  event_type: str
  component: str
  timestamp: datetime
  data: dict
  duration_ms: optional int
```

---

## 4. Data Flow

### 4.1 MVP Evaluation Flow

```
Start
  │
  ▼
1. Dataset Loader — Load dataset from file
  │
  ▼
2. Dataset Validator — Validate required fields
  │
  ▼
3. LLM Executor — Send each input to provider
  │
  ▼
4. Evaluation Engine — Apply metrics to each response
  │
  ▼
5. Reporter — Generate structured report
  │
  ▼
6. Observer — Emit trace events throughout
  │
  ▼
End
```

### 4.2 Error Flow

Any component failure follows this escalation:

1. **Retry**: Transient failures (timeout, rate limit) trigger configurable retry
2. **Skip**: Non-critical failures skip the entry and log the error
3. **Abort**: Critical failures (auth, invalid config) abort the evaluation

---

## 5. Configuration

### 5.1 Evaluation Configuration

```json
{
  "evaluation": {
    "name": "my-evaluation",
    "dataset": {
      "path": "./datasets/prompts.json",
      "format": "json"
    },
    "provider": {
      "name": "ollama",
      "model": "llama3",
      "parameters": {
        "temperature": 0.7,
        "max_tokens": 1024
      }
    },
    "metrics": ["exact_match", "similarity"],
    "reporting": {
      "formats": ["json", "markdown"],
      "output_dir": "./reports"
    }
  }
}
```

### 5.2 Provider Configuration

See `provider_interface.md` for detailed provider configuration schema.

---

## 6. Glossary

| Term | Definition |
|------|------------|
| Evaluation | A complete run of loading a dataset, executing prompts, and computing metrics |
| Metric | A measurable criterion applied to an LLM response |
| Dataset | A collection of input/expected-output pairs used for evaluation |
| Provider | An LLM service (local or remote) that generates responses |
| Trace | A time-ordered record of events during an evaluation |
| Harness | The framework itself — the orchestration and execution environment |
