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

## Phase History

### Phase 2 — ✅ Complete

RAG Evaluation (DeepEval)

Leveraged DeepEval to evaluate retrieval-augmented generation pipelines, including faithfulness, answer relevancy, context precision, context recall, and hallucination detection.

### Phase 3 — ✅ Complete

Multi-Model Comparison

Compare multiple models on the same evaluation datasets with parallel execution, cost tracking, and side-by-side reporting.

### Phase 4 — ✅ Complete

Agent Evaluation

Evaluate multi-step AI agent behaviors, tool-use quality, and trajectory correctness.

### Phase 5 — ✅ Complete

Observability and Monitoring

Continuous monitoring, alerting, and dashboarding for evaluation results over time.

---

All originally planned phases are complete. Additional phases are defined below and tracked in ROADMAP.md.

---

## Phase 6 — CI/CD Integration (Planned)

Automate evaluation runs in CI/CD pipelines and surface results in pull requests.

**Key deliverables:**
- GitHub Actions workflow (`harness-eval.yml`) triggered on push and PR
- PR comment reporting with pass/fail breakdown
- Report and dashboard artifact publishing
- Scheduled cron workflows for regression tracking
- Status badge generation

## Phase 7 — Extended Provider Support (Planned)

Add OpenAI-compatible providers (Groq, OpenRouter, OpenAI, Anthropic, etc.) for broader model access.

**Key deliverables:**
- OpenAI-compatible provider client (covers Groq, OpenRouter, OpenAI)
- Environment-variable-based configuration (API keys, base URLs)
- Per-provider cost tracking with token-based pricing
- Retry logic and rate-limit handling
