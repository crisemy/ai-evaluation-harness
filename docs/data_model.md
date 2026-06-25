# Data Model Specification

This document defines the core data structures used throughout the AI Evaluation Harness. All schemas follow the CORE framework's data contract patterns (`ai-qa-core-framework/01_fundamentals/data_contracts.md`).

---

## 1. Dataset Schema

### 1.1 Dataset

Container for a collection of evaluation entries.

```json
{
  "format_version": "1.0",
  "dataset": {
    "name": "string",
    "description": "string (optional)",
    "created": "ISO 8601 datetime",
    "entries": ["DatasetEntry"]
  }
}
```

### 1.2 DatasetEntry

A single evaluation record.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier within dataset |
| `input` | string | Yes | Prompt or query to evaluate |
| `expected_output` | string | Yes | Reference/golden answer |
| `category` | string | No | Functional area or domain |
| `difficulty` | enum | No | `easy`, `medium`, `hard` |
| `tags` | string[] | No | Free-form labels |
| `metadata` | object | No | Extensible key-value store |

### 1.3 RAG Dataset Extensions (Phase 2)

For RAG evaluations, each entry extends with:

```json
{
  "id": "rag-001",
  "input": "What is the capital of France?",
  "expected_output": "Paris",
  "context_documents": [
    {
      "id": "doc-1",
      "text": "Paris is the capital and most populous city of France.",
      "source": "encyclopedia_2024.pdf"
    },
    {
      "id": "doc-2",
      "text": "France is a country in Western Europe.",
      "source": "geography_facts.md"
    }
  ],
  "metadata": {
    "num_docs": 2,
    "retrieval_strategy": "semantic"
  }
}
```

| RAG Field | Type | Required | Description |
|-----------|------|----------|-------------|
| `context_documents` | Document[] | Yes | Retrieved context for the query |
| `context_documents[].id` | string | Yes | Document identifier |
| `context_documents[].text` | string | Yes | Document text content |
| `context_documents[].source` | string | No | Source reference |

---

## 2. Execution Schema

### 2.1 Execution Request

Input to the LLM executor.

```json
{
  "entry_id": "string",
  "prompt": "string",
  "provider": "string",
  "model": "string",
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 1024,
    "top_p": 1.0,
    "stop_sequences": ["string"]
  }
}
```

### 2.2 Execution Response

Output from the LLM executor.

```json
{
  "entry_id": "string",
  "text": "string",
  "provider": "string",
  "model": "string",
  "latency_ms": 1234,
  "token_usage": {
    "prompt_tokens": 150,
    "completion_tokens": 200,
    "total_tokens": 350,
    "cost": 0.0025
  },
  "timestamp": "ISO 8601 datetime",
  "finish_reason": "stop",
  "raw_response": {}
}
```

---

## 3. Evaluation Schema

### 3.1 Metric Result

Result of a single metric applied to a single response.

```json
{
  "metric_name": "exact_match",
  "score": 1.0,
  "passed": true,
  "explanation": "Response matches expected output exactly",
  "threshold": 0.5,
  "diagnosis": null
}
```

### 3.2 Evaluation Result

Result of all metrics applied to a single entry.

```json
{
  "entry_id": "entry-001",
  "metrics": [
    {
      "metric_name": "exact_match",
      "score": 1.0,
      "passed": true,
      "explanation": "Response matches expected output exactly",
      "threshold": 0.5
    },
    {
      "metric_name": "similarity",
      "score": 0.92,
      "passed": true,
      "explanation": "Semantic similarity score: 0.92",
      "threshold": 0.7
    }
  ],
  "overall_score": 0.96,
  "overall_passed": true,
  "duration_ms": 4500,
  "timestamp": "ISO 8601 datetime"
}
```

---

## 4. Report Schema

### 4.1 Evaluation Summary

Top-level structure for an evaluation run.

```json
{
  "evaluation_name": "string",
  "evaluation_id": "UUID",
  "timestamp": "ISO 8601 datetime",
  "duration_ms": 60000,
  "config": {
    "dataset_path": "string",
    "dataset_format": "string",
    "provider": "string",
    "model": "string",
    "metrics": ["string"]
  },
  "environment": {
    "harness_version": "string",
    "python_version": "string",
    "platform": "string",
    "provider_versions": {}
  },
  "summary": {
    "total_entries": 100,
    "passed": 85,
    "failed": 10,
    "skipped": 5,
    "pass_rate": 0.85,
    "average_score": 0.82,
    "metrics": {
      "exact_match": {
        "mean": 0.75,
        "min": 0.0,
        "max": 1.0,
        "pass_rate": 0.75
      },
      "similarity": {
        "mean": 0.88,
        "min": 0.45,
        "max": 1.0,
        "pass_rate": 0.92
      }
    }
  },
  "results": ["EvaluationResult"]
}
```

---

## 5. Trace Schema

Observability events emitted during evaluation.

```json
{
  "trace_id": "UUID",
  "evaluation_id": "UUID",
  "events": [
    {
      "event_type": "dataset_loaded",
      "component": "DatasetLoader",
      "timestamp": "ISO 8601 datetime",
      "duration_ms": 15,
      "data": {
        "entry_count": 100,
        "format": "json"
      }
    },
    {
      "event_type": "execution_started",
      "component": "LLMExecutor",
      "timestamp": "ISO 8601 datetime",
      "data": {
        "provider": "ollama",
        "model": "llama3",
        "batch_size": 100
      }
    }
  ]
}
```

---

## 6. Schema Evolution

| Version | Changes |
|---------|---------|
| 1.0 | Initial schema — MVP dataset, execution, evaluation, report |
| 1.1 | Planned — RAG context documents, trace events |

Schema evolution follows CORE data contract versioning rules:

- Backward-compatible additions are additive (new optional fields)
- Breaking changes require a new format version
- Dataset loaders must reject unsupported format versions
