# CLAUDE.md — options-trading (csp-flywheel-terminal)

Python research library for German Cash-Secured-Put options trading. Solo project. Library-first — Claude Code in the terminal is the user surface.

## Read these first (in this order)

1. **PRD** — `_bmad-output/planning-artifacts/prd.md` — authoritative product spec (42 FRs, 39 NFRs, 740 lines).
2. **Project Context** — `_bmad-output/project-context.md` — 178 implementation rules (tech stack, conventions, vendor gotchas, the 9 Pflichtregeln). Load before writing code.
3. **Active spec(s)** — `_bmad-output/implementation-artifacts/spec-*.md` — current work in flight.
4. **Legacy brief (archived)** — `docs/archive/Projekt-Brief-2026-04-27.md` — superseded by PRD; reference only.

When PRD, project-context, and a spec disagree: **PRD wins, then project-context, then spec.** Surface the conflict to Chris before proceeding.

## State as of 2026-04-29 (after slice 7)

Seven slices shipped on `main` (`https://github.com/ChrizzzXX/options-trading.git`, **private repo**). Slices 4-7 not pushed at the time of this handoff (most recent commit `94cd4e2`).

- **Slice 1 — Pflichtregeln gate + bootstrap** (`spec-pflichtregeln-gate.md`, `done`). Public surface: `csp.passes_csp_filters`, `Settings`, 4 models, exceptions. 100 % on `pflichtregeln.py`.
- **Slice 2 — ORATS client + NOW cassette** (`spec-orats-client.md`, `done`). Adds `csp.OratsClient`, `csp.orats_health_check`. 100 % on `clients/orats.py`. Closed D1.
- **Slice 3 — `csp.idea(...)` single-ticker** (`spec-idea-singleticker.md`, `done`). Adds `csp.idea`, `csp.Idea`. **Amended PRD FR13** to always-`Idea` (override-pathway on the model). 100 % on slice files.
- **Slice 4 — `csp.scan(...)` universe scan** (`spec-scan-universe.md`, `done`, `bfceb53`). Adds `csp.scan(max_results=10, *, dte=45, target_delta=-0.20, as_of=None) -> list[Idea]`. Single shared `httpx.AsyncClient` + `OratsClient`, `asyncio.gather()` (NFR5), per-ticker skip-and-WARN, dedupe, ranked yield-DESC + ticker-ASC (NFR20). No `strategy` / `override` params.
- **Slice 5 — FMP client + live macro** (`spec-fmp-client.md`, `done`, `e4ffd1e`). Adds `csp.FmpClient`, `csp.fmp_health_check`, `csp.macro_snapshot`, `FMPDataError` / `FMPEmptyDataError`. `csp.idea` + `csp.scan` upgrade transparently to live VIX when `FMP_KEY` is set; settings fallback otherwise. Closes D13, partially D17.
- **Slice 6 — DuckDB lifecycle persistence** (`spec-lifecycle-persistence.md`, `done`, `35113f6`). Adds `csp.log_trade`, `csp.close_trade`, `csp.list_open_positions`, `csp.get_idea`, `csp.list_ideas`, `csp.log_idea`, `csp.Trade`, `csp.TradeStatus`, `csp.LifecycleError`. New `lifecycle/state_machine.py` (100 % coverage gate, MVP scope: manual entry only, `take_profit_pending` sole intermediate, `assigned`/`closed_*`/`emergency_close` terminal). Numbered SQL migrations in `persistence/migrations/`. Idempotent `INSERT OR REPLACE`. Closes D3, D14.
- **Slice 7 — `csp.daily_brief()` + `Idea.format_fbg_mail()`** (`spec-daily-brief.md`, `done`, `94cd4e2`). Composes `macro_snapshot + scan + list_open_positions` plus deutsche action-strings (Earnings ≤ 8d, Sektor-Anteil > 50 %, Override-Trade-Audit). New `csp.ui.formatters` (German-locale `format_usd` / `format_pct` / `format_date_de`). `Idea` extended with `under_price` + `iv_rank_1y_pct`. `DailyBrief.to_markdown()` renders §7.2 sketch as ASCII pipe-tables. Closes D12.

Tests: **321 default + 3 opt-in `recording`**. Overall coverage 99.25 %. ruff + ruff-format + mypy --strict + pytest all clean.

PRD has 10 public library functions; **9 done**: `passes_csp_filters`, `idea`, `scan`, `macro_snapshot`, `log_trade`, `close_trade`, `list_open_positions`, `get_idea`, `list_ideas`, `daily_brief`. **1 to go**: `export_to_sheets` (deferred via D31 — needs Google service account at `~/.config/csp/sa.json`).

**Reconciliation truth:** `pytest -k now_regression` (PRD FR29 / NFR18) asserts real NOW-78 on 2026-04-24 **fails 3 of 9 rules** (DTE 56, earnings same day, spread 0.15 USD). Chris confirmed: `override=True` is routine practice. Slice 3 pinned the override-pathway design: rules 1, 3-9 are bypass-able via `override=True`; **Rule 2 (delta band) is structurally unbypassable** because `_select_strike` pre-filters by the band — to take a Rule-2-violating idea, relax `delta_min`/`delta_max` in `settings.toml` for that run.

## Next slice (recommended)

The MVP is essentially feature-complete. Three reasonable directions:

**A) `csp.export_to_sheets()` (closes D31; last of the 10 PRD functions).** Needs Google service-account JSON at `~/.config/csp/sa.json` and `Settings.google_sheet_id` + `Settings.google_sa_path`. Implement against `gspread` + `google-auth`; NFR6 fire-and-forget, must not block daily-brief. Without real credentials end-to-end testing is shallow — synthesize `gspread` mocks for `respx`-equivalent verification.

**B) IVolatility client slice (closes D22, D30).** Activates EU dispatch on `csp.scan`. Project-context.md forbids docs-only Pydantic models — first step must be a recording cassette via `csp.iv_health_check("ALV.DE")` against the real API. Requires `IVOLATILITY_API_KEY` in `.env`. Reshape universe loader to `list[UniverseEntry(ticker, region, vendor_symbol)]`.

**C) Hardening / review pass.** No new features; instead ramp coverage strictness, write a `pytest-benchmark` for NFR1/NFR4 (closes D21, D23), record the FMP cassette (closes D29), tighten the `_row_to_trade` typing (D36), add `validate_finite` validators on `MacroSnapshot`/`OratsCore`/`OratsStrike` (D5, D27).

To start: run `/bmad-quick-dev` in a fresh session and reference this CLAUDE.md, the PRD (FR-NFR6 for Sheets; FR2 + NFR9 for IVolatility), and `_bmad-output/implementation-artifacts/deferred-work.md`. Active D-numbers: D2, D4–D11, D15–D24, D25–D40 (D1, D3, D12, D13, D14 closed).

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
