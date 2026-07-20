# Phase 10 — Model-Graded Evaluation & Statistical Significance

**Branch:** (to be created)
**Status:** Planned

## Overview

Phase 10 tackles two major gaps in the harness:

1. **Evaluation quality** — Currently limited to `exact_match` and `contains`, which are brittle for generative AI. Model-graded evaluation ("LLM-as-a-Judge") scores free-text responses semantically using another LLM as the evaluator.

2. **Comparison rigor** — The `harness compare` command shows raw numbers but no statistical significance. Phase 10 adds p-values, confidence intervals, and effect sizes so teams know whether "Model A is 2% better" is real or noise.

Both workstreams are independent but complementary — model-graded eval gives richer metrics, and statistical significance makes those metrics trustworthy.

---

## Workstream 1: Model-Graded Evaluation (LLM-as-a-Judge)

### Why

String matching (`exact_match`, `contains`) cannot handle the variety of valid responses a generative AI produces. "Paris is the capital of France" and "The capital city of France is Paris" should both be correct — but `exact_match` fails on the second. An LLM judge evaluates semantically, scoring for correctness, completeness, conciseness, instruction-following, and other rubric dimensions.

### Milestones

| # | Milestone | Description |
|---|-----------|-------------|
| M1 | **Judge interface + base class** | `ModelGradedMetric(LLMJudge)` — abstract judge that takes a prompt template and scoring rubric, sends to a judge LLM via `ChatCompletionsProvider`, and returns a score |
| M2 | **Built-in rubrics** | Ship 3-5 default rubrics: `Correctness`, `Completeness`, `Conciseness`, `InstructionFollowing`, `Coherence`. Each is a prompt template + scoring scale (1-5 or binary pass/fail). |
| M3 | **Custom rubric support** | Users define rubrics as JSON/YAML: `{"name": "my_rubric", "scale": "1-5", "prompt_template": "...", "judge_model": "openai/gpt-4o-mini"}`. Pass via `--judge-rubric my_rubric.json`. |
| M4 | **Self-evaluation / consistency** | Judge evaluates the same response N times (default 3) and reports mean ± std deviation. Mitigates judge LLM variance. |

### How it works

```
┌──────────┐    ┌──────────────┐    ┌───────────────┐
│ Response │───▶│ PromptBuilder│───▶│  Judge LLM    │
│  text    │    │ rubric + resp│    │  (any Chat-   │
│          │    │  → judge msg │    │  Completions) │
└──────────┘    └──────────────┘    └───────┬───────┘
                                            │
                                    ┌───────▼───────┐
                                    │ ScoreParser   │
                                    │ (1-5, pass/   │
                                    │  fail, or     │
                                    │  custom)      │
                                    └───────┬───────┘
                                            │
                                    ┌───────▼───────┐
                                    │ MetricResult  │
                                    │ (score, reason│
                                    │  raw_judgment)│
                                    └───────────────┘
```

### CLI

```bash
# Eval with model-graded correctness rubric
harness eval -d datasets/qa_kaggle.json -m phi3 \
  --metrics model_graded \
  --judge-rubric correctness \
  --judge-model groq/llama-3.3-70b-versatile

# Custom rubric from file
harness eval -d datasets/qa_kaggle.json -m phi3 \
  --metrics model_graded \
  --judge-rubric my_company_rubric.json

# RAG eval with completeness rubric
harness rag-eval -d datasets/rag_dataset.json -m phi3 \
  --metrics model_graded \
  --judge-rubric completeness
```

### Files to create

| File | Purpose |
|------|---------|
| `src/harness/metrics/model_graded/__init__.py` | ModelGradedMetric, ScoreParser |
| `src/harness/metrics/model_graded/rubrics/__init__.py` | Built-in rubric loader |
| `src/harness/metrics/model_graded/rubrics/correctness.json` | Correctness rubric template |
| `src/harness/metrics/model_graded/rubrics/completeness.json` | Completeness rubric template |
| `src/harness/metrics/model_graded/rubrics/conciseness.json` | Conciseness rubric template |
| `src/harness/metrics/model_graded/rubrics/instruction_following.json` | Instruction-following rubric |
| `src/harness/metrics/model_graded/rubrics/coherence.json` | Coherence rubric template |

---

## Workstream 2: A/B Testing & Statistical Significance

### Why

`harness compare` shows side-by-side metrics (pass rate 80% vs 82%), but doesn't tell you if the difference is meaningful. With small entry counts (e.g., 20-50 entries), a 2% difference could be random noise. Adding p-values and confidence intervals turns comparison reports into statistically grounded A/B test results.

### Milestones

| # | Milestone | Description |
|---|-----------|-------------|
| S1 | **Statistical test engine** | `StatisticalTest` interface with McNemar's test (paired binary outcomes) and bootstrap confidence intervals (continuous scores). Output: p-value, effect size, 95% CI. |
| S2 | **Enhanced comparison report** | The `ComparisonReport.to_dict()` gains a `statistics` block: `{"model_a_vs_b": {"p_value": 0.03, "effect_size": 0.15, "ci_95": [0.02, 0.28], "significant": true}}`. CLI prints significance summary. Dashboard shows significance badges. |

### How it works

```
ComparisonReport
  ├── models: [groq, openrouter, ollama]
  └── statistics:                          ← NEW
      ├── groq_vs_openrouter:
      │   ├── p_value: 0.03
      │   ├── effect_size: 0.15
      │   ├── ci_95: [0.02, 0.28]
      │   └── significant: true
      ├── groq_vs_ollama:
      │   ├── p_value: 0.001
      │   ├── ...
      │   └── significant: true
      └── openrouter_vs_ollama:
          ├── ...
```

### CLI integration

```bash
# Compare with statistical significance
harness compare -d datasets/qa_kaggle.json \
  --models groq/llama-3.3-70b-versatile openrouter/openai/gpt-4o-mini ollama/phi3 \
  --limit 20 \
  --significance 0.05    # default alpha level

# Output includes significance section
```

### Dashboard integration

The Phase 9 `harness ui` dashboard will show significance badges (✅ significant / ⚠️ not significant) next to each model comparison on the Overview page.

---

## Combined Deliverables

| # | Deliverable | Workstream |
|---|-------------|------------|
| 1 | `ModelGradedMetric` abstract class + `ScoreParser` | M1 |
| 2 | 5 built-in rubrics (correctness, completeness, conciseness, instruction-following, coherence) | M2 |
| 3 | Custom rubric loader (JSON/YAML) | M3 |
| 4 | Multi-sample consistency scoring (N-judge calls) | M4 |
| 5 | `StatisticalTest` interface + McNemar's test + bootstrap CI | S1 |
| 6 | Enhanced `ComparisonReport` with significance block + CLI output | S2 |
| 7 | Dashboard significance badges in `harness ui` | S2 |

## Dependencies

- **M1-M4**: `ChatCompletionsProvider` (Phase 8) — judge LLM calls reuse existing provider + retry logic
- **M3**: JSON/YAML loader — can reuse `JSONDatasetLoader` patterns
- **S1**: `scipy` for McNemar's test (`scipy.stats.mcnemar`) — new dependency candidate (or implement manually)
- **S1**: `numpy` for bootstrap — already via `pandas` dependency
- **S2**: Phase 3 `ComparisonReport` — extending existing data structure
- **S2**: Phase 9 `harness ui` dashboard — adding significance display

## Test Strategy

- **M1-M4**: Mock judge LLM responses with known scores; verify metric output matches expected rubric scoring
- **S1**: Statistical tests against known distributions (e.g., McNemar with known p-value)
- **S2**: Integration test: full compare run with `--significance` flag, verify statistics block in output

## Open Questions

1. **Judge model cost** — Running a judge LLM for every response doubles API cost. Options: (a) use cheaper judge models, (b) judge on a sample, (c) cache judge results by response hash.
2. **Judge bias** — LLMs prefer certain response styles (longer, more assertive). Mitigation: multi-sample scoring (M4) and recording judge reasoning.
3. **Statistical test choice** — McNemar's is ideal for paired pass/fail. For continuous scores (1-5), bootstrap CI is more appropriate. The S1 milestone should support both depending on metric type.
