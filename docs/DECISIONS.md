# Architecture Decision Records

This document records significant architectural decisions made during the project.

---

## ADR-001: Phase Ordering

- **Date:** 2026-06-24
- **Status:** Accepted

### Context

The initial PLAN.md defined Phase 2 as Multi-Model Comparison and Phase 3 as RAG Evaluation. The project lead's expertise in QA Architecture and AI Engineering aligns more closely with RAG evaluation, and RAG capabilities deliver higher immediate production value.

### Decision

Swap the phase ordering:

- Phase 2 → RAG Evaluation (was Phase 3)
- Phase 3 → Multi-Model Comparison (was Phase 2)

### Rationale

- RAG evaluation addresses immediate production needs (hallucination, faithfulness)
- DeepEval provides first-class RAG metrics that match the lead's QA Arch background
- Multi-model comparison is a benchmarking feature, not a quality-validation feature
- RAG pipeline understanding feeds naturally into Agent evaluation (Phase 4)

### Consequences

- RAG evaluation will be designed earlier in the architecture lifecycle
- Multi-model comparison will benefit from a more mature metric system
- PLAN.md and ROADMAP.md updated to reflect new ordering

---

## ADR-002: DeepEval as RAG Evaluation Framework

- **Date:** 2026-06-24
- **Status:** Accepted

### Context

RAG evaluation requires specialized metrics (faithfulness, answer relevancy, context precision, context recall) that general LLM evaluation frameworks may not provide out of the box. Two candidates were considered: DeepEval and RAGAS.

### Decision

Adopt DeepEval as the RAG evaluation framework.

### Rationale

- DeepEval provides built-in RAG metrics with minimal configuration
- DeepEval's metric design aligns with the project's evaluation principles (repeatable, explainable)
- DeepEval supports custom metric extension when built-in metrics are insufficient
- DeepEval's output format integrates naturally with the planned reporting layer

### Consequences

- RAG evaluation implementation accelerated by using DeepEval primitives
- Future migration path remains open if requirements outgrow DeepEval
- DeepEval dependency must be managed as an optional integration (not a hard requirement)

---

## ADR-003: Provider Abstraction via Common Interface

- **Date:** 2026-06-24
- **Status:** Accepted

### Context

The architecture defines support for multiple LLM providers (Ollama, OpenAI, Anthropic, Gemini, etc.). Each provider has a different API, authentication method, and response format.

### Decision

All providers must implement a common abstract interface. The provider interface defines:

- `generate(prompt, config) → Response`
- `stream(prompt, config) → AsyncIterable[Chunk]`
- Provider metadata (model list, capabilities, cost)

### Rationale

- Enables provider swapping without evaluation pipeline changes
- Simplifies multi-model comparison in Phase 3
- Local-first (Ollama) can be the reference implementation
- New providers can be added without modifying core evaluation logic

### Consequences

- Provider-specific code is isolated behind the interface
- Testing can use mock providers without real API calls
- Provider configuration becomes a first-class concern

---

## ADR-004: Dataset Specification — Input, Expected Output, Metadata

- **Date:** 2026-06-24
- **Status:** Accepted

### Context

A standardized dataset format is required to ensure repeatable evaluations across different use cases and providers.

### Decision

Every dataset entry must include:

- `id` — Unique identifier
- `input` — The prompt or query to evaluate
- `expected_output` — The reference/golden answer

Optional fields:

- `category` — Functional area or domain
- `difficulty` — Complexity level
- `tags` — Free-form labels
- `metadata` — Extensible key-value store

### Rationale

- Minimal required fields reduce barrier to entry
- Optional fields enable richer analysis without mandating complexity
- Extensible metadata supports future use cases (RAG context, agent trajectories)

### Consequences

- Dataset loaders must validate required fields
- Dataset format must be versioned to support schema evolution
- RAG datasets will extend this base schema with context documents

---

## ADR-005: Observability via TraceObserver, TimeSeriesStore, AlertEngine, DashboardGenerator

- **Date:** 2026-06-26
- **Status:** Accepted

### Context

As the evaluation harness grew to support prompt, RAG, and agent evaluations, teams needed visibility into evaluation results over time. Without observability, regressions could go unnoticed across evaluation runs.

### Decision

Phase 5 introduces four components for observability and monitoring:

1. **TraceObserver** — A concrete implementation of the existing `Observer` interface that collects `ObservableEvent`s in memory, groups them by trace ID, and persists to NdJSON files. Each evaluation command (eval, rag-eval, agent-eval) creates trace events (evaluation_start, evaluation_end, entry_start, entry_end) with timing data.

2. **TimeSeriesStore** — An append-only NdJSON store that records `MetricSnapshot` entries (metric_name, score, passed, threshold, timestamp, evaluation_id, config_snapshot) every time an evaluation runs. This enables trend analysis across evaluation runs.

3. **AlertEngine** — A rule evaluation engine that checks threshold-based `AlertRule` definitions against the latest metric snapshots. Supports operators: gt, lt, gte, lte, eq. Ships with three default rules (Low Pass Rate, Score Drop, Tool Selection Degradation).

4. **DashboardGenerator** — Generates a self-contained static HTML page with summary cards, an alert results table, and a metric history table with trend indicators.

### Rationale

- **TraceObserver** reuses the existing `Observer` interface without modifications
- **TimeSeriesStore** uses NdJSON (newline-delimited JSON) for append-only writes — no database dependency
- **AlertEngine** is rule-driven and extensible; users can define custom rules via JSON files
- **DashboardGenerator** produces a zero-dependency HTML file — no server or build step required
- All four components are isolated behind the CLI `harness monitor` subcommand

### Consequences

- Evaluation commands now automatically record time series data and traces
- `.harness/` directory stores runtime artifacts (gitignored)
- Custom alert rules can be provided via JSON file (`harness monitor alerts --rules my_rules.json`)
- Dashboard is a static snapshot, not real-time

---

## ADR-006: CORE Governance Integration

- **Date:** 2026-07-11
- **Status:** Accepted

### Context

The AI Evaluation Harness had become a capable execution engine for prompt, RAG, and agent evaluations with observability, but lacked the governance methodology needed to make risk-aware quality decisions. The AI QA Core Framework defines a governance model with risk classification, escalation procedures, prompt regression testing, red team security evaluation, override management, and continuous scheduling — all of which were absent from the harness.

### Decision

Integrate the AI QA Core Framework governance methodology across six workstreams (Phases A through G), adding new modules while keeping backward compatibility with all existing evaluation flows:

1. **Risk-Based Prioritization** — `RiskClassifier` with 7 `ChangeType` values (bugfix, feature, refactor, config, dependency, prompt, emergency), composite risk formula `risk = severity × (likelihood + impact) / 2`, and `--risk` / `--risk-threshold` CLI flags on eval/rag-eval/agent-eval.

2. **Failure Escalation** — `EscalationEngine` with severity gate map (none/warning/error/critical/blocker), 11 `FailureCode` values (from `unknown` to `data_loss`), and `--gate` flag on all eval commands that blocks or warns based on the configured severity threshold.

3. **Prompt Regression Testing** — `PromptRegistry` (JSON-backed baseline storage with versioning), `PromptRegressionMetric` (F1-based comparison against baseline), and `harness prompt-regress` CLI command.

4. **Red Team Security Evaluation** — `RedTeamExecutor` with 3 default attack tests (jailbreak, prompt injection, role-play extraction), Attack Success Rate (ASR) tracking, and `harness red-team` CLI command.

5. **Operations Tooling** — `harness override request/list/approve/reject` CLI stubs for emergency overrides, and `docs/rollback_checklist.md` for operational rollback procedures.

6. **Continuous Scheduling** — `SchedulerEngine` with JSON-backed schedule registry, interval-based execution, and `harness scheduler add/list/run` CLI commands.

### Rationale

- All governance modules are opt-in via CLI flags — existing evaluation commands continue to work without modification
- Risk and gate flags are integrated directly into the existing eval/rag-eval/agent-eval commands rather than requiring separate workflow definitions
- Contracts (`risk.py`, `security.py`) follow the existing dataclass pattern in `src/harness/contracts/`
- Default values (risk tolerance 1.0, gate "none") preserve backward compatibility
- Each workstream was committed as a standalone phase for audit trail clarity
- The CORE framework directory (`CORE/`) is gitignored to avoid duplicating source-of-truth content

### Consequences

- All existing 147 tests pass with zero regressions (7 pre-existing failures in DeepEval RAG metrics are unrelated)
- New contracts (`risk.py`, `security.py`) added to `src/harness/contracts/`
- New modules added: `risk/`, `red_team/`, `escalation.py`, `prompt_regression.py`, `scheduler.py`
- CLI now supports 6 new subcommands: `prompt-regress`, `red-team`, `override`, `scheduler`
- Existing eval commands accept 3 new optional flags: `--risk`, `--risk-threshold`, `--gate`
- `docs/rollback_checklist.md` created for operational procedures

---

## ADR-007: CI/CD Integration via GitHub Actions

- **Date:** 2026-07-11
- **Status:** Accepted

### Context

The AI Evaluation Harness had all the building blocks for CI integration — non-interactive CLI, configurable output paths, exit codes for pass/fail gating — but no actual CI/CD workflows. Teams had to manually run evaluations locally and interpret results. Without automated CI pipelines, regression detection was reactive rather than proactive.

### Decision

Add a CI/CD layer with four GitHub Actions workflows and one new CLI module:

1. **`.github/workflows/harness-eval.yml`** — Triggered on push/PR, runs 5 parallel jobs:
   - `test`: unit tests with pytest, uploads test results
   - `evaluate` (matrix: eval, rag-eval, agent-eval): smoke tests with --gate warning, generates dashboard, uploads artifacts
   - `regress`: prompt regression against baseline, uploads artifacts
   - `security`: red team security scan, uploads artifacts
   - `report`: aggregates all artifacts, posts a PR comment via `actions/github-script@v7` with a per-job status table

2. **`.github/workflows/harness-scheduled.yml`** — Triggered by cron (Monday/Thursday 06:00 UTC) and `workflow_dispatch`:
   - Runs a full evaluation with `--risk major --gate warning`
   - Generates dashboard and status badge
   - Uploads all artifacts for historical tracking

3. **`BadgeGenerator`** (`src/harness/ci.py`) — Generates a shields.io-compatible SVG badge from the latest MetricSnapshot in the time series store. Exposed via `harness ci badge --store .harness/timeseries.ndjson -o badge.svg`.

### Rationale

- GitHub Actions is the de-facto CI platform for open-source projects on GitHub — no additional service dependency
- Workflows are defined as YAML in `.github/workflows/` — no infrastructure to manage
- Parallel job execution minimizes pipeline wall-clock time
- Matrix strategy covers all evaluation types without duplicating step definitions
- `actions/github-script@v7` provides PR comment posting without external dependencies
- `actions/upload-artifact@v4` persists results without a database
- SVG badge is self-contained, cacheable on gh-pages or raw asset hosting
- CLI tool (`harness ci badge`) means badge generation works locally and in CI identically

### Consequences

- `.github/workflows/harness-eval.yml` created — runs on every push/PR to main and phase branches
- `.github/workflows/harness-scheduled.yml` created — runs twice weekly and on manual dispatch
- `src/harness/ci.py` added — contains `BadgeGenerator` class
- `harness ci badge` CLI command added — generates `badge.svg` from time series data
- `.gitignore` updated — `badge.svg` and `reports/` are ignored as run artifacts
- All 5 CORE prerequisite conditions were already satisfied (non-interactive CLI, exit codes, configurable paths)
