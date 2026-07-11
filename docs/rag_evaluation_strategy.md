# RAG Evaluation Strategy — Phase 2

This document defines the strategy for extending the AI Evaluation Harness to evaluate Retrieval-Augmented Generation (RAG) pipelines using DeepEval.

---

## 1. Decision Summary

DeepEval has been selected as the RAG evaluation framework for Phase 2 (see docs/DECISIONS.md ADR-002).

### Why DeepEval

| Factor | Assessment |
|--------|------------|
| Built-in RAG metrics | Faithfulness, answer relevancy, context precision, context recall, hallucination |
| Metric explainability | Every metric produces human-readable explanations |
| Custom metric support | Extendable via Python (aligns with harness custom metric pattern) |
| Integration pattern | Python library, no external service needed |
| Output format | Structured results that map to harness report schema |
| Local-first | Can run with local models, consistent with architecture principle |

---

## 2. RAG Pipeline Architecture

```
                    ┌──────────────┐
                    │   Dataset    │
                    │ RAG Entries  │
                    └──────┬───────┘
                           │
              ┌────────────▼────────────┐
              │   Context Provider      │
              │  (documents per query)  │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   LLM Executor          │
              │  (prompt + context →    │
              │   response)             │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   DeepEval Metrics      │
              │  faithfulness, relevancy│
              │  precision, recall      │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   Reporter              │
              │  (extended for RAG)     │
              └─────────────────────────┘
```

---

## 3. DeepEval Integration Points

### 3.1 Metric Mapping

| Harness Metric | DeepEval Class | Inputs Required |
|----------------|----------------|-----------------|
| faithfulness | `FaithfulnessMetric` | response, context_documents |
| answer_relevancy | `AnswerRelevancyMetric` | query, response |
| context_precision | `ContextPrecisionMetric` | query, context_documents |
| context_recall | `ContextRecallMetric` | query, context_documents, expected_response |
| hallucination | `HallucinationMetric` | response, context_documents |

### 3.2 Integration Layer

DeepEval metrics will be wrapped in the harness Metric interface:

```python
from harness.metrics import Metric, MetricResult
from deepeval.metrics import FaithfulnessMetric as DeepEvalFaithfulness

class Faithfulness(Metric):
    def __init__(self, threshold: float = 0.5):
        self._metric = DeepEvalFaithfulness(threshold=threshold)
        self._threshold = threshold

    @property
    def name(self) -> str:
        return "faithfulness"

    def evaluate(self, response, expected, context=None):
        context_docs = (context or {}).get("context_documents", [])
        result = self._metric.measure(response, context_docs)

        return MetricResult(
            metric_name=self.name,
            score=result.score,
            passed=result.score >= self._threshold,
            explanation=result.reason,
            threshold=self._threshold,
            diagnosis=result
        )
```

### 3.3 Registration

```python
from harness.metrics import registry
registry.register(Faithfulness(threshold=0.7))
```

---

## 4. Dataset Requirements

RAG evaluation requires extended dataset entries with context documents. See `data_model.md` section 1.3 for the schema.

### Dataset Example

```json
{
  "format_version": "1.1",
  "dataset": {
    "name": "rag-qa-baseline",
    "entries": [
      {
        "id": "rag-001",
        "input": "What is the refund policy?",
        "expected_output": "Full refund within 30 days of purchase",
        "context_documents": [
          {
            "id": "policy-1",
            "text": "Customers may request a full refund within 30 days of purchase.",
            "source": "refund_policy.md"
          },
          {
            "id": "policy-2",
            "text": "Refunds are processed within 5-10 business days.",
            "source": "refund_policy.md"
          }
        ]
      }
    ]
  }
}
```

---

## 5. Implementation Plan

### Step 1: DeepEval Dependency

Add DeepEval as an optional dependency:

```
pip install deepeval  # optional, RAG-specific
```

The harness must function without DeepEval installed (graceful degradation).

### Step 2: Wrapper Implementation

Implement wrapper classes in `harness/metrics/rag/`:

```
harness/metrics/rag/
├── __init__.py
├── faithfulness.py
├── answer_relevancy.py
├── context_precision.py
├── context_recall.py
├── hallucination.py
└── registry.py
```

### Step 3: Context Provider Interface

The context provider abstraction allows plugging different retrieval systems:

```python
class ContextProvider(ABC):
    @abstractmethod
    def get_context(self, query: str) -> list[Document]: ...
```

Built-in providers:

| Provider | Description |
|----------|-------------|
| DatasetContextProvider | Context from dataset entries (for isolated RAG evaluation) |
| ChromaContextProvider | Context from ChromaDB vector store |
| CustomContextProvider | User-defined retrieval logic |

### Step 4: RAG Evaluation Pipeline

Extend the existing pipeline to handle RAG datasets:

```
1. Detect RAG dataset (contains context_documents)
2. For each entry:
   a. Retrieve context (from provider or dataset)
   b. Construct prompt: query + context
   c. Execute against LLM
   d. Apply RAG metrics (DeepEval)
3. Generate extended report with RAG-specific sections
```

### Step 5: Reporting Extension

Extend the reporter to include RAG-specific sections:

- Per-metric RAG scores
- Context quality analysis (precision vs recall tradeoff)
- Hallucination frequency report

---

## 6. Risks

| Risk | Mitigation |
|------|------------|
| DeepEval version changes | Pin dependency version, lock wrapper interfaces |
| Embedding model dependency | Cache embeddings, allow configurable models |
| Context provider reliability | Graceful degradation when context is missing |
| Metric interpretation differences | Document expected ranges and interpretations per metric |
