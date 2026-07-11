# AGENTS

Instructions for AI agents working on this repository.

## Session Start

Read these files in order at session start for project context:

1. **CONTEXT.md** — problem domain, scope, terminology
2. **docs/ARCHITECTURE.md** — module relationships, data flow
3. **README.md** — setup, usage, current status

## Key Commands

```powershell
.venv\Scripts\Activate.ps1      # activate venv
pytest tests/ -v                 # run all tests (138 pass, 7 pre-existing failures)
harness eval -d datasets/qa_kaggle.json -m phi3 --limit 5 --risk major --gate warning   # risk-gated eval
harness prompt-regress -d datasets/qa_kaggle.json -m phi3 --limit 10   # prompt regression
harness red-team -d datasets/qa_kaggle.json -m phi3 --limit 5           # red team security
harness scheduler list            # list scheduled evaluations
harness override list             # list override requests
harness monitor status            # check latest metrics
harness monitor dashboard -o dashboard.html   # generate dashboard
```

## Project Layout

- **`src/harness/`** — single package (no monorepo)
- **`harness.cli:main`** — entrypoint (registered in `pyproject.toml` scripts; also `python -m harness`)
- **Agents** use `create_autospec` from `unittest.mock` for isolated testing
- `.harness/`, `dashboard.html`, `report.json`, `*.ndjson` are gitignored run artifacts
- **CORE governance** modules: `risk/`, `red_team/`, `escalation.py`, `prompt_regression.py`, `scheduler.py`

## Documentation Rules

After any significant change, update:

- **README.md** — if user-facing behavior changes
- **docs/ARCHITECTURE.md** — if module relationships change
- **docs/ROADMAP.md** — if project priorities change
- **docs/DECISIONS.md** — ADR when an architectural decision is made
- **docs/rollback_checklist.md** — if operational procedures change

When finishing a **Phase** or **Milestone** (per docs/ROADMAP.md), review ALL of the above.

## Constraints

- No new dependencies without strong reason (see `requirements.txt`)
- Keep vendor-specific code isolated behind interfaces (`interfaces/`)
- All evaluations must be repeatable (deterministic or seeded)
