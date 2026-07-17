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

### Phase 6 — ✅ Complete

CORE Governance Integration

Integrated the AI QA Core Framework governance methodology into the harness:

* Risk-based prioritization (RiskClassifier, 7 change types, risk gates)
* Failure escalation (EscalationEngine, severity/failure codes, --gate flag)
* Prompt regression testing (PromptRegistry, F1 regression metric)
* Red team security evaluation (RedTeamExecutor, ASR tracking)
* Operations tooling (override CLI stubs, rollback checklist)
* Continuous scheduling (SchedulerEngine, interval-based auto-eval)

### Phase 7 — ✅ Complete

CI/CD Integration

Automated evaluation runs in CI/CD pipelines with GitHub Actions:

* `.github/workflows/harness-eval.yml` — CI workflow triggered on push/PR with 5 parallel jobs (test, evaluate matrix of 3, regress, security, report)
* `.github/workflows/harness-scheduled.yml` — Scheduled workflow (Mon/Thu) + manual dispatch with configurable dataset/model/limit
* PR Comment Reporting — `actions/github-script@v7` posts a status table per-pipeline-run
* Artifact Publishing — `actions/upload-artifact@v4` saves reports, dashboards, time series, and logs per job
* Status Badge — `BadgeGenerator` in `src/harness/ci.py` generates shields.io-compatible SVG badge; `harness ci badge` CLI command
* CORE Alignment — CI metadata envelope (`--ci-env`, `--release-id`), KPI baseline comparison (`harness ci kpi`), release quality report (`harness ci report`), ASR gating (`--asr-threshold`), coverage enforcement (`--coverage-min`), failure code alignment (CXT_ERR added), rollback trigger in scheduled workflow

All originally planned phases are complete. Additional phases are defined below and tracked in ROADMAP.md.

---

## Phase 8 — Extended Provider Support ✅ Complete

Added ChatCompletions API providers (Groq, OpenRouter) for broader model access.

**Key deliverables:**

* `ChatCompletionsProvider` — shared client for providers using the `/v1/chat/completions` API format ✅
* Environment-variable-based configuration (API keys via `GROQ_API_KEY`, `OPENROUTER_API_KEY`) + `.env` auto-load ✅
* Provider factory (`create_provider()` in `src/harness/providers/__init__.py`) for centralized dispatch ✅
* Per-provider cost tracking with token-based pricing (`input_price_per_1m` / `output_price_per_1m`) ✅
* Retry logic with exponential backoff (429, 5xx, timeouts — configurable `max_retries`) ✅
