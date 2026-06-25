# Dataset Specification

## 1. Format

Datasets are stored as JSON or YAML files with the following top-level structure:

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

## 2. Dataset Entry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier within dataset |
| `input` | string | Yes | Prompt or query to evaluate |
| `expected_output` | string | Yes | Reference/golden answer |
| `category` | string | No | Functional area or domain |
| `difficulty` | string | No | `easy`, `medium`, `hard` |
| `tags` | string[] | No | Free-form labels |
| `metadata` | object | No | Extensible key-value store |

## 3. Example

```json
{
  "format_version": "1.0",
  "dataset": {
    "name": "basic-qa",
    "description": "Basic question-answer pairs for prompt evaluation",
    "created": "2026-06-24T12:00:00Z",
    "entries": [
      {
        "id": "qa-001",
        "input": "What is the capital of France?",
        "expected_output": "Paris",
        "category": "geography",
        "difficulty": "easy",
        "tags": ["capital", "europe"]
      },
      {
        "id": "qa-002",
        "input": "Explain the concept of recursion.",
        "expected_output": "Recursion is a programming technique where a function calls itself to solve smaller instances of the same problem.",
        "category": "computer_science",
        "difficulty": "medium",
        "tags": ["programming", "algorithms"]
      }
    ]
  }
}
```

## 4. Validation Rules

- `id` must be unique within a dataset
- `input` and `expected_output` must be non-empty strings
- `difficulty` must be one of: `easy`, `medium`, `hard` (if provided)
- `format_version` must be a supported version

## 5. Supported Formats

| Format | Extension | Status |
|--------|-----------|--------|
| JSON | `.json` | MVP |
| CSV | `.csv` | MVP |
| YAML | `.yaml`, `.yml` | MVP |

## 6. RAG Extension (Phase 2)

For RAG evaluation, each entry may include a `context_documents` array. See `docs/data_model.md` section 1.3 for the RAG extension schema.
