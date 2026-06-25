# Metrics Specification

This document defines the evaluation metrics supported by the AI Evaluation Harness. Metrics are the core measurement instruments of the framework.

---

## 1. Metric Interface

Every metric implements the following contract:

```python
class Metric(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def evaluate(
        self,
        response: str,
        expected: str,
        context: dict | None = None
    ) -> MetricResult: ...

@dataclass
class MetricResult:
    metric_name: str
    score: float          # normalized 0.0 - 1.0
    passed: bool          # score >= threshold
    explanation: str      # human-readable reasoning
    diagnosis: dict | None = None  # machine-readable details
    threshold: float = 0.5
```

All scores are normalized to `[0.0, 1.0]` where:
- `1.0` = perfect match
- `0.0` =完全不一致 (complete mismatch)
- Intermediate values indicate partial quality

---

## 2. MVP Metrics

### 2.1 ExactMatch

| Property | Value |
|----------|-------|
| Type | Deterministic |
| Dependencies | None |
| Use Case | Verbatim correctness (codes, IDs, specific phrases) |

Logic:

```
score = 1.0 if response.strip() == expected.strip() else 0.0
```

### 2.2 Contains

| Property | Value |
|----------|-------|
| Type | Deterministic |
| Dependencies | None |
| Use Case | Required information presence |

Logic:

```
score = 1.0 if expected in response else 0.0
```

### 2.3 RegexMatch

| Property | Value |
|----------|-------|
| Type | Deterministic |
| Dependencies | None |
| Use Case | Pattern validation (emails, dates, formats) |

Logic:

```
score = 1.0 if re.search(expected, response) else 0.0
```

Expected field contains the regex pattern.

### 2.4 Similarity (Embedding-Based)

| Property | Value |
|----------|-------|
| Type | Statistical |
| Dependencies | Embedding model (local via sentence-transformers) |
| Use Case | Semantic similarity, paraphrased answers |

Logic:

```
embedding_response = embed(response)
embedding_expected = embed(expected)
score = cosine_similarity(embedding_response, embedding_expected)
```

Threshold guidance:

| Score Range | Interpretation |
|-------------|---------------|
| 0.90 - 1.00 | Semantically identical |
| 0.70 - 0.89 | Highly similar |
| 0.50 - 0.69 | Moderately similar |
| 0.00 - 0.49 | Low similarity |

---

## 3. Phase 2 RAG Metrics (DeepEval)

Introduced in Phase 2 via DeepEval integration. See `rag_evaluation_strategy.md` for detailed integration plan.

| Metric | DeepEval Equivalent | Description |
|--------|-------------------|-------------|
| Faithfulness | `FaithfulnessMetric` | Response stays faithful to retrieved context |
| AnswerRelevancy | `AnswerRelevancyMetric` | Response addresses the query |
| ContextPrecision | `ContextPrecisionMetric` | Retrieved context is relevant to query |
| ContextRecall | `ContextRecallMetric` | Retrieved context covers necessary information |
| Hallucination | `HallucinationMetric` | Response contains information not in context |

---

## 4. Metric Configuration

Metrics are configured in the evaluation configuration:

```json
{
  "metrics": [
    {
      "name": "exact_match",
      "threshold": 1.0
    },
    {
      "name": "similarity",
      "threshold": 0.7,
      "params": {
        "embedding_model": "all-MiniLM-L6-v2"
      }
    }
  ]
}
```

Each metric in the configuration can override:

| Field | Default | Description |
|-------|---------|-------------|
| `threshold` | 0.5 | Pass/fail boundary |
| `weight` | 1.0 | Weight in composite score |
| `params` | `{}` | Metric-specific parameters |

---

## 5. Composite Scoring

When multiple metrics are configured, the evaluation computes:

```
overall_score = Σ(metric.score × metric.weight) / Σ(metric.weight)
overall_passed = overall_score >= overall_threshold
```

---

## 6. Custom Metrics

Users can define custom metrics as Python callables:

```python
from harness.metrics import Metric, MetricResult

class MyCustomMetric(Metric):
    @property
    def name(self) -> str:
        return "my_custom_metric"

    def evaluate(self, response, expected, context=None):
        # Custom logic here
        score = 0.0
        explanation = "Custom metric explanation"
        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=score >= self.threshold,
            explanation=explanation
        )
```

Custom metrics are registered via the metric registry:

```python
registry.register(MyCustomMetric(threshold=0.8))
```

---

## 7. CORE Framework Alignment

This metric specification follows patterns defined in:

- `ai-qa-core-framework/01_fundamentals/kpi_governance.md` — KPI definition and threshold governance
- `ai-qa-core-framework/01_fundamentals/data_contracts.md` — Result data contract patterns
