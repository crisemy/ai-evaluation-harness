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
