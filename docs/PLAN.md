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

- Risk-based prioritization (RiskClassifier, 7 change types, risk gates)
- Failure escalation (EscalationEngine, severity/failure codes, --gate flag)
- Prompt regression testing (PromptRegistry, F1 regression metric)
- Red team security evaluation (RedTeamExecutor, ASR tracking)
- Operations tooling (override CLI stubs, rollback checklist)
- Continuous scheduling (SchedulerEngine, interval-based auto-eval)

### Phase 7 — ✅ Complete

CI/CD Integration

Automated evaluation runs in CI/CD pipelines with GitHub Actions:

- `.github/workflows/harness-eval.yml` — CI workflow triggered on push/PR with 5 parallel jobs (test, evaluate matrix of 3, regress, security, report)
- `.github/workflows/harness-scheduled.yml` — Scheduled workflow (Mon/Thu) + manual dispatch with configurable dataset/model/limit
- PR Comment Reporting — `actions/github-script@v7` posts a status table per-pipeline-run
- Artifact Publishing — `actions/upload-artifact@v4` saves reports, dashboards, time series, and logs per job
- Status Badge — `BadgeGenerator` in `src/harness/ci.py` generates shields.io-compatible SVG badge; `harness ci badge` CLI command

All originally planned phases are complete. Additional phases are defined below and tracked in ROADMAP.md.

---

## Phase 8 — Extended Provider Support (Planned)

Add OpenAI-compatible providers (Groq, OpenRouter, OpenAI, Anthropic, etc.) for broader model access.

**Key deliverables:**

- OpenAI-compatible provider client (covers Groq, OpenRouter, OpenAI)
- Environment-variable-based configuration (API keys, base URLs)
- Per-provider cost tracking with token-based pricing
- Retry logic and rate-limit handling
