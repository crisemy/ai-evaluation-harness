# AGENTS

This repository is designed to be AI-agent friendly.

All agents contributing to this repository must follow the rules below.

## Session Start

Project context files are **pre-loaded as system instructions** via `opencode.json`:

- **CONTEXT.md** — Project overview, purpose, scope, and terminology.
- **ARCHITECTURE.md** — System design, module relationships, and data flow.
- **README.md** — User-facing documentation, setup, and usage instructions.

Their content is included in the system prompt at every session start, so you do not need to read them manually.

## Core Principles

* Documentation is part of the product.
* Architecture consistency is more important than implementation speed.
* Evaluation quality is more important than feature quantity.
* Simplicity is preferred over premature optimization.

## Required Documentation Updates

Whenever a significant change is introduced:

* Update README.md if user-facing behavior changes.
* Update CONTEXT.md if project scope changes.
* Update ARCHITECTURE.md if architectural decisions change.
* Update ROADMAP.md if project priorities change.
* Register a decision in DECISIONS.md when appropriate.

When finishing a **Phase** or **Milestone** (as defined in ROADMAP.md), ALL of the above documents must be reviewed and updated before moving to the next phase/milestone.

## Coding Guidelines

* Prioritize readability.
* Favor maintainability over cleverness.
* Avoid introducing unnecessary dependencies.
* Keep vendor-specific implementations isolated.

## Evaluation Guidelines

* Evaluations must be repeatable.
* Metrics must be observable.
* Results must be explainable.
* Human review should remain possible.

## Pull Request Expectations

Every contribution should include:

* Purpose of the change.
* Impacted architectural components.
* Documentation updates.
* Risks and limitations.
