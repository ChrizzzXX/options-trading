# CLAUDE.md — options-trading (csp-flywheel-terminal)

Python research library for German Cash-Secured-Put options trading. Solo project. Library-first — Claude Code in the terminal is the user surface.

## Read these first (in this order)

1. **PRD** — `_bmad-output/planning-artifacts/prd.md` — authoritative product spec (42 FRs, 39 NFRs, 740 lines).
2. **Project Context** — `_bmad-output/project-context.md` — 178 implementation rules (tech stack, conventions, vendor gotchas, the 9 Pflichtregeln). Load before writing code.
3. **Active spec(s)** — `_bmad-output/implementation-artifacts/spec-*.md` — current work in flight.
4. **Legacy brief (archived)** — `docs/archive/Projekt-Brief-2026-04-27.md` — superseded by PRD; reference only.

When PRD, project-context, and a spec disagree: **PRD wins, then project-context, then spec.** Surface the conflict to Chris before proceeding.

## State as of 2026-04-29 (after slice 3)

Three slices shipped on `main` and pushed to `origin` (`https://github.com/ChrizzzXX/options-trading.git`, **private repo**).

- **Slice 1 — Pflichtregeln gate + bootstrap** (`_bmad-output/implementation-artifacts/spec-pflichtregeln-gate.md`, status `done`). Public surface: `csp.passes_csp_filters`, `Settings`, 4 models, exceptions. 100 % coverage on `pflichtregeln.py`.
- **Slice 2 — ORATS client + real NOW cassette** (`_bmad-output/implementation-artifacts/spec-orats-client.md`, status `done`). Adds `csp.OratsClient`, `csp.orats_health_check`, `ORATSDataError`, `ORATSEmptyDataError`. 100 % coverage on `clients/orats.py`. Closed deferred D1.
- **Slice 3 — `csp.idea(...)` single-ticker idea** (`_bmad-output/implementation-artifacts/spec-idea-singleticker.md`, status `done`). Adds `csp.idea`, `csp.Idea`. **Amended PRD FR13**: return shape `Idea | None` → always-`Idea` (override-pathway annotation lives on the model: `pflichtregeln_passed: bool` + `reasons` + `bypassed_rules`). 100 % coverage on `idea.py`, `strategies/csp.py`, `models/idea.py`. Settings gained `[macro] vix_close` (placeholder until FMP-client slice — D13/D17).

Tests: **164 default + 3 opt-in `recording`** (gated by `-m recording`). Overall coverage 99.80 %. ruff + mypy strict clean.

PRD has 10 public library functions; **2 done** (`passes_csp_filters`, `idea`). 8 to go: `daily_brief`, `scan`, `list_open_positions`, `log_trade`, `close_trade`, `get_idea`, `list_ideas`, `export_to_sheets`.

**Reconciliation truth:** `pytest -k now_regression` (PRD FR29 / NFR18) asserts that real NOW-78 on 2026-04-24 **fails 3 of 9 rules** (DTE 56, earnings same day, spread 0.15 USD). The real verdict is the determinism contract. Chris confirmed: `override=True` is routine practice (see project memory `project_override_routine.md`). Slice 3 pinned the override-pathway design: rules 1, 3-9 are bypass-able via `override=True`; **Rule 2 (delta band) is structurally unbypassable** because `_select_strike` pre-filters by the band — to take a Rule-2-violating idea, relax `delta_min`/`delta_max` in `settings.toml` for that run.

## Next slice (recommended)

**`csp.scan(strategy="csp", max_results=10) -> list[Idea]`** — PRD FR14, FR17. Universe-wide scan composing `csp.idea` per ticker, parallelized via `asyncio.gather()`, ranked by annualized yield with deterministic tie-break (FR17). Why next: reuses slice-3 surface; doesn't require new persistence; closes the "discovery" half of daily-brief; `csp.daily_brief` then becomes a thin composition over `scan` + macro + open-positions.

Alternative if you want DuckDB earlier: jump to **`csp.log_trade` + `csp.close_trade`** to land persistence (closes D3, D14, D19), then `scan`/`daily_brief` can attach sector-exposure-delta (D15) and override-history.

To start: run `/bmad-quick-dev` in a fresh session and reference this CLAUDE.md, the PRD (FR14, FR17, FR18 if going for `daily_brief`; FR21–24 if going lifecycle-first), and `_bmad-output/implementation-artifacts/deferred-work.md` (D2-D5, D7-D11, D13-D21 active).

## Hard rules (don't violate without explicit human approval)

- **Pflichtregeln are inviolable** — all 9 rules pass before any CSP idea surfaces. No `force_idea()` escape hatch.
- **Library, not app** — no `typer` CLI in MVP, no web UI. Public surface = `import csp` + 10 named functions. Claude renders.
- **No tax export** — removed from scope, not deferred.
- **No broker integration** — research tool only.
- **German user-facing strings; English identifiers.** Pflichtregel reasons, `Idea.format_fbg_mail()` output, Sheets cells → German. Code → English.
- **No hardcoded thresholds** — all rule values from `config/settings.toml` (PRD FR12).
- **No live HTTP in tests** — `pytest-vcr` cassettes only.
- **Scan for secrets before any `git push` to a new remote** — grep tracked files (especially `docs/`, archives, the brief, anything from Perplexity/Claude exports) for token/api-key/Bearer patterns. April 2026: pushed a live ORATS token to GitHub by skipping this; the brief is committed and contained the secret. Token wasn't rotated (Chris's call) but the repo went private. Don't repeat — `rg -i "(token|api[_-]?key|secret|bearer)\s*[:=]" --glob '!_bmad/**' --glob '!.claude/**'` before any `git push -u origin <new-remote>`.
- **Async-first I/O** — vendor clients use `httpx.AsyncClient`. Public functions wrap with `asyncio.run()`.
- **`Decimal` for money, `float` for ratios.** Premium / P/L → `Decimal`. Delta / IV / IVR → `float`.
- **TZ-aware datetimes only** — never naive `datetime.now()` / `date.today()`. Slice 3 settled on stdlib `zoneinfo.ZoneInfo("Europe/Berlin")` (no new dep) for `as_of` resolution; `pendulum` / `whenever` remain options if a future slice needs richer date arithmetic.

## Stack (don't add deps without justification)

`uv` · Python 3.12+ · `pydantic` v2 · `pydantic-settings` · `httpx` · `polars` (planned) · `duckdb` (planned) · `loguru` · stdlib `zoneinfo` · `pytest` + `pytest-vcr` + `hypothesis` + `respx` · `ruff` · `mypy --strict`

Excluded by design: `requests`, web frameworks (React/Vue/Streamlit/FastAPI), broker SDKs, crypto-options libraries.

## Output layout

- Code: `src/csp/` (module map in `project-context.md`)
- Tests: `tests/` mirroring source tree
- Cassettes: `tests/cassettes/{vendor}/`
- Planning artifacts: `_bmad-output/planning-artifacts/`
- Implementation specs: `_bmad-output/implementation-artifacts/`
- Snapshots/DB: `data/` (gitignored)
- Logs: `logs/` (gitignored)
- Secrets: `.env` (gitignored); service account at `~/.config/csp/sa.json` (outside repo)

## Pre-commit gates (must pass)

1. `uv run ruff check src tests`
2. `uv run ruff format --check src tests`
3. `uv run mypy --strict src`
4. `uv run pytest -q` (cassettes only, ≤ 30 s)

Coverage: ≥ 80 % overall; 100 % required for `src/csp/filters/pflichtregeln.py`, `src/csp/strategies/csp.py`, `src/csp/idea.py`, `src/csp/models/idea.py`, and (future) `src/csp/lifecycle/state_machine.py`. Today: 99.80 % overall.

## Workflow

BMad-Method module is installed under `_bmad/`. Outputs land in `_bmad-output/`.

- Slice planning + implementation: `/bmad-quick-dev`
- Full backlog (when warranted): `/bmad-create-architecture` → `/bmad-create-epics-and-stories` → `/bmad-check-implementation-readiness`
- Adversarial review: `/bmad-code-review` (run after each implementation slice)
- Refresh implementation rules: `/bmad-generate-project-context` if a new pattern emerges

## Regression anchor

NOW-78-Strike from 2026-04-24 (Strike 78, DTE 55, Premium 4.30, IVR 94). `pytest -k now_regression` is the determinism contract — failing it blocks merge.

## House style

- Be direct. Surface problems before they ship.
- Drastic simplicity wins — push back on overengineering.
- No premature abstraction. The `AbstractStrategy` base class waits for Growth (when Iron Condor / Strangle land).
