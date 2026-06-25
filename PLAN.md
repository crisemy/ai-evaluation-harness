# PLAN

## MVP Scope

The initial version of AI Evaluation Harness will focus exclusively on Prompt Evaluation.

The MVP must be capable of:

* Loading evaluation datasets.
* Executing prompts against AI providers.
* Collecting responses.
* Applying evaluation metrics.
* Generating evaluation reports.

The MVP explicitly excludes:

* RAG Evaluation
* Agent Evaluation
* Workflow Evaluation
* Multi-Model Benchmarking
* Observability Dashboards

These capabilities may be introduced in future phases.

---

## Future Directions

### Phase 2

RAG Evaluation (DeepEval)

Leverage DeepEval to evaluate retrieval-augmented generation pipelines, including faithfulness, answer relevancy, context precision, context recall, and hallucination detection.

### Phase 3

Multi-Model Comparison

Compare multiple models on the same evaluation datasets with parallel execution, cost tracking, and side-by-side reporting.

### Phase 4

Agent Evaluation

Evaluate multi-step AI agent behaviors, tool-use quality, and trajectory correctness.

### Phase 5

Observability and Monitoring

Continuous monitoring, alerting, and dashboarding for evaluation results over time.
