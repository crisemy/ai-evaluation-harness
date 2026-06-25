# Testing Framework Overview

This document describes the testing methodology applied to the AI Evaluation Harness itself. It follows the AI QA Core Framework's project methodology (`ai-qa-core-framework/00_project_methodology.md`) and uses its phases as the basis for testing phases.

---

## 1. Testing Phases

The testing strategy follows the CORE framework phases, adapted for evaluation harness validation:

| Phase | CORE Phase | Focus | Scope |
|-------|------------|-------|-------|
| T0 — Inception | Phase 0 | Test strategy definition | Plans, contracts, risk assessment |
| T1 — Contract & Component | Phase 1 | Unit & integration tests | Data contracts, provider interface, metrics |
| T2 — Pipeline | Phase 2 | End-to-end evaluation flow | Dataset → Executor → Metrics → Report |
| T3 — Regression | Phase 2 | Continuous quality | Regression detection, comparison baselines |
| T4 — Operations | Phase 3 | Production monitoring | Trace validation, alert testing |

---

## 2. T0 — Inception

### Goal

Define the testing strategy, identify risks, and establish quality contracts before implementation begins.

### Artifacts

| Artifact | CORE Template | Purpose |
|----------|---------------|---------|
| Risk Model Card | `templates/risk_model_card.md` | Identify testing risks (provider reliability, metric correctness) |
| Test Strategy | This document | Define scope, approach, resources |
| Quality KPIs | `kpi_governance.md` | Define pass thresholds, coverage targets |

### Key Risks

| Risk | Mitigation |
|------|------------|
| Provider API changes | Provider interface abstraction, contract tests |
| Metric score inconsistency | Golden datasets with known expected scores |
| Flaky evaluation results | Statistical aggregation over multiple runs |
| Dataset quality | Validation layer with schema enforcement |

---

## 3. T1 — Contract & Component Tests

### Goal

Validate individual components in isolation with mocked dependencies.

### Test Types

#### 3.1 Data Contract Tests

Validate dataset loading, validation, and serialization.

```
Dataset Loader Tests:
  ✓ Load valid JSON dataset → returns Dataset with correct entries
  ✓ Load valid CSV dataset → returns Dataset with correct entries
  ✓ Load file with missing required field → ValidationError
  ✓ Load empty file → LoadError
  ✓ Load unsupported format → FormatError
  ✓ Load entry with all optional fields → correctly populated DatasetEntry
```

#### 3.2 Provider Interface Tests

Validate provider abstraction with mock providers.

```
Provider Interface Tests:
  ✓ Mock provider returns expected response → ExecutionResponse with correct text
  ✓ Provider timeout → TimeoutError with configurable threshold
  ✓ Rate limit exceeded → RateLimitError with backoff trigger
  ✓ Invalid credentials → AuthError
  ✓ Batch execution returns correct number of responses
```

#### 3.3 Metric Engine Tests

Validate metric correctness with known inputs.

```
Metric Tests:
  ✓ ExactMatch — identical strings → score 1.0
  ✓ ExactMatch — different strings → score 0.0
  ✓ Contains — substring present → score 1.0
  ✓ Contains — substring absent → score 0.0
  ✓ RegexMatch — pattern matches → score 1.0
  ✓ RegexMatch — pattern does not match → score 0.0
  ✓ Similarity — identical embeddings → score 1.0
  ✓ Similarity — orthogonal embeddings → score ~0.0
  ✓ Custom metric — user-defined function executes correctly
  ✓ Metric with missing expected_output → SkippedResult
```

#### 3.4 Reporter Tests

Validate output format correctness.

```
Reporter Tests:
  ✓ Generate JSON report → valid JSON with expected structure
  ✓ Generate Markdown report → valid Markdown with summary table
  ✓ Report with zero results → empty report (not error)
  ✓ Report includes environment metadata
```

---

## 4. T2 — Pipeline Tests

### Goal

Validate the end-to-end evaluation flow with real (or realistic) components.

### Test Scenarios

| Scenario | Description | Validation |
|----------|-------------|------------|
| Happy path | Load dataset → execute → evaluate → report | All steps complete, report generated |
| Partial failure | One provider call fails mid-batch | Remaining entries evaluated, error logged |
| Empty dataset | Load empty valid dataset | Zero evaluations, empty report |
| Large dataset | 1000+ entries | Pipeline completes within expected time |
| Invalid entry in dataset | One malformed entry among valid ones | Valid entries processed, malformed skipped |

### Pipeline Integration Test

```python
# Pseudocode for pipeline integration test
dataset = DatasetLoader.load("test_fixtures/valid_3_entries.json")
responses = Executor.execute_batch(dataset.entries, mock_provider)
results = EvaluationEngine.evaluate(responses, dataset.entries, [ExactMatch()])
report = Reporter.generate(results, "json")

assert len(report.entries) == 3
assert all(r.metrics[0].score in [0.0, 1.0] for r in results)
```

---

## 5. T3 — Regression Tests

### Goal

Detect regressions in evaluation results across code changes.

### Approach

- Maintain a golden dataset with known expected metric scores
- Run evaluations as part of CI
- Compare new scores against baselines
- Flag deviations beyond configurable thresholds

### Regression Detection

| Change Type | Expected Impact | Detection Method |
|-------------|-----------------|------------------|
| Metric implementation change | Score change | Baseline comparison |
| Provider response change | Latency, content | Timing + content diff |
| Dataset format change | Entry count, structure | Schema validation |
| Dependency update | Behavior change | Full pipeline test |

---

## 6. T4 — Operations Tests

### Goal

Validate observability, monitoring, and operational behavior.

### Test Types

- **Trace emission**: Every component emits correct events
- **Trace completeness**: End-to-end trace contains all expected stages
- **Alert trigger**: Metric below threshold triggers alert
- **Retry behavior**: Transient failure triggers expected retries
- **Configuration reload**: Configuration change without restart

---

## 7. Testing Principles

These principles extend the CORE framework's evaluation guidelines for harness testing:

1. **Deterministic Where Possible**: Use mock providers and golden datasets
2. **Isolate External Dependencies**: Every external call should be mockable
3. **Test Metrics with Oracles**: Every metric needs known-input-known-output pairs
4. **Pipeline Tests Are Integration Tests**: Test the happy path end-to-end, not every permutation
5. **Regression Tests Run in CI**: Every PR triggers the golden dataset evaluation
6. **Observability Tests Are Mandatory**: If it's not observable, it's not testable

---

## 8. CORE Framework References

| CORE Resource | Usage in Testing |
|---------------|------------------|
| `01_fundamentals/data_contracts.md` | Dataset schema validation tests |
| `01_fundamentals/kpi_governance.md` | Metric threshold and KPI definitions |
| `01_fundamentals/risk_prioritization_contracts.md` | Testing risk classification |
| `03_personal_tooling/workflows/ci_pipeline_workflow.md` | CI integration for regression tests |
| `03_personal_tooling/workflows/regression_workflow.md` | Regression test workflow |
| `03_personal_tooling/templates/risk_model_card.md` | Testing risk documentation |
