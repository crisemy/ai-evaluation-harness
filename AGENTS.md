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
harness ci badge -o badge.svg                 # generate CI status badge
harness ci kpi -o kpi-report.json             # KPI baseline comparison
harness ci report -o release-report.json      # release quality report (Go/Conditional-Go/No-Go)
```

## Project Layout

- **`src/harness/`** — single package (no monorepo)
- **`harness.cli:main`** — entrypoint (registered in `pyproject.toml` scripts; also `python -m harness`)
- **Agents** use `create_autospec` from `unittest.mock` for isolated testing
- `.harness/`, `dashboard.html`, `report.json`, `*.ndjson` are gitignored run artifacts
- **CORE governance** modules: `risk/`, `red_team/`, `escalation.py`, `prompt_regression.py`, `scheduler.py`
- **CI/CD** workflows in `.github/workflows/`: `harness-eval.yml` (push/PR), `harness-scheduled.yml` (cron)
- **Badge generation + release reports**: `ci.py` — `BadgeGenerator`, `ReleaseReportGenerator`
- **KPI baseline comparison**: `kpi_baseline.py` — `BaselineComparator` with Green/Yellow/Red verdicts

## Documentation Rules (Mandatory)

You MUST update the following files whenever the corresponding change occurs. This is not optional.

| File | Update When | Always? |
| ------ | ------------- | --------- |
| **README.md** | User-facing behavior changes (CLI flags, new commands, features) | ❌ |
| **docs/ARCHITECTURE.md** | Module relationships, package structure, or data flow changes | ❌ |
| **docs/ROADMAP.md** | Phase status changes, milestone completion, or priority shifts | ❌ |
| **docs/PLAN.md** | Phase completion (move from Planned → Complete with deliverables) | ❌ |
| **docs/DECISIONS.md** | Every architectural decision — add an ADR entry | ✅ **always** |
| **docs/rollback_checklist.md** | Operational procedures change | ❌ |
| **CONTEXT.md** | Problem domain or scope expands | ❌ |
| **AGENTS.md** | Key commands, project layout, or rules change | ❌ |

**Hard rule**: When completing a **Phase** or **Milestone** (per docs/ROADMAP.md), you MUST review EVERY file in the table above and update those whose condition is met. Run `git diff --stat` before and after to confirm coverage.

**Recommendation**: After any code change that touches CLI commands, contracts, or modules, check the affected row above and update the corresponding doc in the same commit.

## Constraints

- No new dependencies without strong reason (see `requirements.txt`)
- Keep vendor-specific code isolated behind interfaces (`interfaces/`)
- All evaluations must be repeatable (deterministic or seeded)
