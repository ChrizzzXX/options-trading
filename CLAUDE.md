# CLAUDE.md — options-trading (csp-flywheel-terminal)

Python research library for German Cash-Secured-Put options trading. Solo project. Library-first — Claude Code in the terminal is the user surface.

## Read these first (in this order)

1. **PRD** — `_bmad-output/planning-artifacts/prd.md` — authoritative product spec (42 FRs, 39 NFRs, 740 lines).
2. **Project Context** — `_bmad-output/project-context.md` — 178 implementation rules (tech stack, conventions, vendor gotchas, the 9 Pflichtregeln). Load before writing code.
3. **Active spec(s)** — `_bmad-output/implementation-artifacts/spec-*.md` — current work in flight.
4. **Legacy brief (archived)** — `docs/archive/Projekt-Brief-2026-04-27.md` — superseded by PRD; reference only.

When PRD, project-context, and a spec disagree: **PRD wins, then project-context, then spec.** Surface the conflict to Chris before proceeding.

## State as of 2026-04-29 (after slice 9 — hardening)

Nine slices shipped on `origin/main` (`https://github.com/ChrizzzXX/options-trading.git`, **private repo**). All commits pushed; tree clean.

- **Slice 1-3** — Pflichtregeln gate, ORATS client (with NOW cassette), `csp.idea(...)`. Closed D1.
- **Slice 4** — `csp.scan(...)` universe scan (`bfceb53`). FR14/FR17/NFR5/NFR20.
- **Slice 5** — FMP client + `csp.macro_snapshot()` (`e4ffd1e`). Closes D13, partially D17.
- **Slice 6** — DuckDB lifecycle: `log_trade`, `close_trade`, `list_open_positions`, `get_idea`, `list_ideas`, `log_idea` + state machine (`35113f6`). Closes D3, D14.
- **Slice 7** — `csp.daily_brief()` + `Idea.format_fbg_mail()` + `csp.ui.formatters` (`94cd4e2`). Closes D12.
- **Slice 8** — IVolatility integration **REJECTED** (`7da5b5e` scope amendment). Probe established Chris's IV plan-tier doesn't include `/equities/eod/options-rawiv` (the only chain endpoint). EU coverage out of scope (MVP and Growth). D22, D30, D40 marked rejected. Forward-compat fields (`region`, `data_freshness`) stay on models.
- **Slice 8b** — FMP base-URL bugfix + real cassettes (`06dc456`). Slice 5 had `https://financialmodelingprep.com/api/stable/...` which is now legacy 403'd; correct is `https://financialmodelingprep.com/stable/...`. Real `^VIX = 18.01` (live) and `18.71` (2026-04-24) cassettes recorded, scrubbed, played back. Closes D29.
- **Slice 9** — Hardening pass (`6fb0a26`). Finite validators (`math.isfinite`) on every numeric field of `MacroSnapshot`/`OratsCore`/`OratsStrike` reject NaN/±Inf at the vendor boundary. `_row_to_trade` typing tightened: four `# type: ignore` comments replaced by defensive `isinstance` checks; schema drift raises a clear `LifecycleError` instead of a cryptic pydantic message. Closes D5, D27, D36.

Tests: **363 default + 5 opt-in `recording`**. Overall coverage 98.82 %. ruff + ruff-format + mypy --strict + pytest all clean.

PRD has 10 public library functions; **9 done**: `passes_csp_filters`, `idea`, `scan`, `macro_snapshot`, `log_trade`, `close_trade`, `list_open_positions`, `get_idea`, `list_ideas`, `daily_brief`. **1 to go**: `export_to_sheets` (D31 — Chris confirmed full Google Drive access is set up; needs implementation).

**Reconciliation truth:** `pytest -k now_regression` (PRD FR29 / NFR18) asserts real NOW-78 on 2026-04-24 **fails 3 of 9 rules** (DTE 56, earnings same day, spread 0.15 USD). Chris confirmed: `override=True` is routine practice. Slice 3 pinned the override-pathway design: rules 1, 3-9 are bypass-able via `override=True`; **Rule 2 (delta band) is structurally unbypassable** because `_select_strike` pre-filters by the band — to take a Rule-2-violating idea, relax `delta_min`/`delta_max` in `settings.toml` for that run.

## Next slice (recommended)

The MVP is feature-complete except for `csp.export_to_sheets`. Two reasonable directions:

**A) `csp.export_to_sheets()` — last of the 10 PRD functions (closes D31).** Chris confirmed full Google Drive + Sheets access is set up. Implement against `gws-sheets` skills (preferred) or `gspread` + `google-auth` directly. Single tab "Ideas" per PRD §5.2 (US-only after the EU scope amendment). NFR6: fire-and-forget, must not block daily-brief. Settings additions: `google_sheet_id` (env var), `google_sa_path` (default `~/.config/csp/sa.json`).

**B) Continue hardening.** Active deferred items still worth doing:
- D21, D23 — `pytest-benchmark` smoke for NFR1/NFR4 (≤ 60 s scan, ≤ 5 s idea).
- D26 — `gather` poison-pill (defer until first leak).
- D37 — SQL parser robustness (defer until first DML migration).
- D38 — `daily_brief` N+1 (defer until > 20 open positions).
- D39 — markdown templates (defer until Sheets/PDF needed).

To start: run `/bmad-quick-dev` in a fresh session and reference this CLAUDE.md plus PRD §5.2 (Sheets) or `deferred-work.md`. **Active D-numbers:** D2, D4, D6–D11, D15–D17 (D17 partial), D18–D21, D23–D26, D28, D29 (closed), D31, D32–D35, D37–D39. **Closed:** D1, D3, D5, D12–D14, D22, D27, D29, D30, D36, D40.

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

`uv` · Python 3.12+ · `pydantic` v2 · `pydantic-settings` · `httpx` · `duckdb` · `loguru` · stdlib `zoneinfo` · `polars` (planned) · `pytest` + `pytest-vcr` + `hypothesis` + `respx` · `ruff` · `mypy --strict`

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

Coverage: ≥ 80 % overall; 100 % required for `src/csp/filters/pflichtregeln.py`, `src/csp/strategies/csp.py`, `src/csp/idea.py`, `src/csp/scan.py`, `src/csp/lifecycle/state_machine.py`, `src/csp/models/idea.py`, `src/csp/models/trade.py`, `src/csp/ui/formatters.py`. Today: 99.25 % overall.

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
