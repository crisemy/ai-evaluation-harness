# AGENTS

Instructions for AI agents working on this repository.

## Session Start

Read these files in order at session start for project context:

1. **CONTEXT.md** — problem domain, scope, terminology
2. **ARCHITECTURE.md** — module relationships, data flow
3. **README.md** — setup, usage, current status

## Key Commands

```powershell
.venv\Scripts\Activate.ps1      # activate venv
pytest tests/ -v                 # run all 147 tests
harness eval -d datasets/qa_kaggle.json -m phi3 --limit 5   # quick eval
harness monitor status           # check latest metrics
harness monitor dashboard -o dashboard.html   # generate dashboard
```

## Project Layout

- **`src/harness/`** — single package (no monorepo)
- **`harness.cli:main`** — entrypoint (registered in `pyproject.toml` scripts; also `python -m harness`)
- **Agents** use `create_autospec` from `unittest.mock` for isolated testing
- `.harness/`, `dashboard.html`, `report.json`, `*.ndjson` are gitignored run artifacts

## Documentation Rules

After any significant change, update:
- **README.md** — if user-facing behavior changes
- **ARCHITECTURE.md** — if module relationships change
- **ROADMAP.md** — if project priorities change
- **DECISIONS.md** — ADR when an architectural decision is made

When finishing a **Phase** or **Milestone** (per ROADMAP.md), review ALL of the above.

## Constraints

- No new dependencies without strong reason (see `requirements.txt`)
- Keep vendor-specific code isolated behind interfaces (`interfaces/`)
- All evaluations must be repeatable (deterministic or seeded)
