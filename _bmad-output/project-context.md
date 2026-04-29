---
project_name: 'options-trading (csp-flywheel-terminal)'
user_name: 'Chris'
date: '2026-04-27'
last_updated: '2026-04-27'
sections_completed:
  ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
status: 'complete'
rule_count: 178
optimized_for_llm: true
source_of_truth: '_bmad-output/planning-artifacts/prd.md'
source_brief_archived: 'docs/archive/Projekt-Brief-2026-04-27.md'
note: 'Brief is archived (superseded by PRD). PRD is now authoritative for scope/FRs/NFRs. This file distills implementation rules; in any conflict, PRD wins.'
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## 🛠 2026-04-29 Scope Amendment — EU coverage removed

**EU equity options via IVolatility is OUT OF SCOPE.** Probe established that the user's IVolatility plan tier does not include the options-chain endpoint (`/equities/eod/options-rawiv` → 403 "required tariff"). All references below to IVolatility, EU dispatch, EU candidates, `region="EU"`, `ALV.DE`, and the `vendor_symbol` universe column are **historical / superseded**. No new code should target EU coverage.

**What stays:** `region: Literal["US", "EU"]` field on `Idea` (forward-compat; today always `"US"`); `data_freshness: Literal["live", "eod", "stale", "unavailable"]` (general use, no region branch).

See `_bmad-output/planning-artifacts/prd.md` § "2026-04-29 Scope Amendment" for the binding wording.

---

## Technology Stack & Versions

**Runtime:** Python 3.12+

**Core stack (mandatory):**
- Package mgmt: `uv` (poetry as fallback)
- Public surface: Python library (`import csp`); Claude Code in the terminal is the user interface (no `typer` CLI in MVP — pivoted out 2026-04-27)
- HTTP: `httpx` (async-capable; never `requests`)
- Models & config: `pydantic` v2, `pydantic-settings`
- Tables: `polars` (primary), `pandas` (only for ecosystem compatibility)
- Persistence: `duckdb` + Parquet snapshots
- Logging: `loguru`
- Dates: `pendulum` or `whenever` (TZ-aware, never naive `datetime`)
- Testing: `pytest` + `pytest-vcr` + `hypothesis`
- Lint/format: `ruff` (single tool, no black/flake8/isort)
- Type-check: `mypy --strict` or `pyright`
- Sheets: `gspread` + `google-auth`

**Optional:** `plotly` (HTML export only, no live dashboards)

**Excluded by design** (do not add):
- `requests` → use `httpx`
- Any web UI framework (React/Vue/Streamlit/FastAPI dashboards) — Claude Code in the terminal is the user surface; the library is the product
- Any broker SDK — tool is research-only, no order routing
- Crypto-options libraries — out of scope

## Critical Implementation Rules

### Language-Specific Rules (Python)

**Type discipline:**
- All public functions/methods require explicit type hints; `mypy --strict` (or `pyright` strict) must pass
- No `Any` — use `unknown`-equivalent narrowing or `TypedDict`/`pydantic.BaseModel`
- Prefer `StrEnum`/`IntEnum` over string literals for state (see `TradeStatus` in brief §5.2)

**Async-first I/O:**
- All API clients (ORATS, FMP, IVolatility, Sheets) use `httpx.AsyncClient`
- No mixing of sync and async — `daily_brief()` parallelizes universe scans across tickers
- Public library functions (`csp.daily_brief()`, `csp.scan()`, `csp.idea()`) wrap async via `asyncio.run()` so callers (Claude Code via `uv run python -c "..."`, or future MCP server) don't manage event loops

**Pydantic v2 conventions:**
- API response models map JSON `camelCase` → Python `snake_case` via `Field(alias="camelCase")`
- Use `model_config = ConfigDict(populate_by_name=True)` so both names work
- Never parse raw JSON dicts in business logic — always go through a Pydantic model first
- For settings: `pydantic-settings` reads `.env` + TOML; never `os.environ` directly

**Dates & time zones:**
- Never use naive `datetime.datetime`; use `pendulum`/`whenever` with explicit TZ
- Trade dates stored as `date` (no time component); timestamps stored UTC
- US market hours referenced in `America/New_York`; Chris's local in `Europe/Berlin`
- DTE arithmetic: calendar days, not trading days (matches ORATS field semantics)

**Idioms to use:**
- `pathlib.Path` for all paths (never string concatenation)
- f-strings with `=` for debug logs: `logger.debug(f"{ticker=} {strike=}")`
- Dataclass-style returns or `NamedTuple` for multi-value returns; never bare tuples
- Context managers for DuckDB connections, file handles, HTTP clients

**Anti-patterns (rejected in review):**
- Bare `except:` — always catch specific exception types
- Mutable default args (`def f(x=[])`)
- `from module import *`
- `requests.get(...)` — use `httpx.AsyncClient`
- `pandas` as primary table type — use `polars` and only convert to `pandas` at the boundary if a dependency requires it
- Raw SQL string formatting — use DuckDB parameterized queries

**Code & log language:**
- All inline comments, docstrings, log messages, and user-facing strings the library returns (Pflichtregel-failure reasons, `Idea.format_fbg_mail()` output, Sheets cell text): **German**
- Identifiers (variable/function/class names): English (Python convention)
- Exception: this `project-context.md` file is English (BMad workflow context)

### Framework-Specific Rules

**Library API (replaces former typer + rich CLI rules):**
- Public surface is a flat top-level module: `import csp`, then call `csp.daily_brief()`, `csp.scan()`, `csp.idea()`, `csp.list_open_positions()`, `csp.log_trade()`, `csp.close_trade()`, `csp.get_idea()`, `csp.list_ideas()`, `csp.passes_csp_filters()`, `csp.export_to_sheets()`. These 10 functions are the binding MVP contract.
- **Never `print()`** in library code — return Pydantic models or typed primitives. Claude Code (the user surface) renders markdown from model fields.
- Each public function has a complete docstring (purpose, parameters, return shape with named fields, failure modes/exceptions). Claude reads docstrings to compose calls.
- No `typer`, no `rich.Table`, no `src/csp/ui/` — those were cut on the 2026-04-27 architectural pivot. A thin CLI wrapper may return in the Growth phase **only** if cron/automation requires it.
- Errors raise typed exceptions Claude can catch and explain: `ORATSDataError`, `FMPDataError`, `IVolatilityDataError`, `PflichtregelError`, `IdempotencyError`, `ConfigError`.

**httpx (API clients):**
- One client class per vendor: `OratsClient` (US options), `FmpClient` (macro), `IVolatilityClient` (EU options EOD), `SheetsClient` — all in `src/csp/clients/`
- Constructor accepts `httpx.AsyncClient` for testability; never instantiate inside methods
- Retry policy: 3 attempts with exponential backoff (1s, 2s, 4s) for 5xx + 429; 4xx raises immediately with response body in exception message
- Rate-limit awareness: ORATS = 1000 req/min; FMP = per-plan; IVolatility = plan-tier TBD (record on first request, surface as constants in `clients/ivolatility.py`)
- Always pass token via header or query param as the vendor expects — never URL-encode in path

**pydantic v2 (models):**
- One model file per concept (`models/option.py`, `models/core.py`, `models/trade.py` …)
- API response models live alongside their client; domain models live in `models/`
- Validators (`@field_validator`, `@model_validator`) for sanity checks (e.g., `delta` must be in `[-1, 1]`)
- Use `Decimal` for monetary fields where rounding matters (premium, P/L); `float` for ratios/percentages

**duckdb (persistence):**
- Single DB file: `data/trades.duckdb` (path from settings, override via `DUCKDB_PATH`)
- Schema migrations as numbered SQL files in `src/csp/persistence/migrations/`; applied at startup
- Snapshots write Parquet to `data/snapshots/YYYY-MM-DD/{ticker}.parquet` — DuckDB queries via `read_parquet()`
- All inserts use `INSERT OR REPLACE` (idempotent same-day reruns) — never plain `INSERT`
- Reads use parameterized queries: `con.execute("... WHERE ticker = ?", [ticker])`

**loguru (logging):**
- Configure once in `src/csp/__init__.py` via env (`LOG_LEVEL`, `LOG_FILE`)
- Rotation: 10 MB per file, retention 30 days, compression `zip`
- Structured fields via `logger.bind(...)` for ticker/trade_id correlation
- Never log secrets (token, service-account contents) — `loguru` filter strips known keys

**pydantic-settings (config):**
- Single `Settings` class in `src/csp/config.py`, loaded once at module import
- Reads `.env` (secrets) + `config/settings.toml` (rules) — TOML wins for explicit fields, env for secrets
- All threshold constants (`vix_min`, `delta_min`, etc.) come from settings, never hardcoded

**Strategy plugins (deferred to Growth):**
- MVP has only CSP. The `AbstractStrategy` base class is **not** built in MVP — no premature abstraction.
- When Iron Condor / Strangle / Put Credit Spread arrive in Growth: each strategy is a class inheriting `AbstractStrategy` (`src/csp/strategies/base.py`); required methods `scan(universe, macro, portfolio) -> list[Idea]` and `validate(idea) -> tuple[bool, list[str]]`; new strategies registered in `STRATEGIES` dict and dispatched via the `strategy="..."` argument to `csp.scan()`.

### Testing Rules

**Layer split:**
- **Unit:** every Pflichtregel filter in isolation, every formula (annualized_yield, OTM%, sector exposure)
- **Integration:** end-to-end client calls via `pytest-vcr` cassettes (no live API in test runs)
- **Property-based:** `hypothesis` for `annualized_yield()` and lifecycle state-machine transitions
- **Regression anchor:** the NOW-78-strike idea from 2026-04-24 (Strike 78, 55 DTE, Premium 4.30, IVR 94) must reproduce exactly from the recorded cassette

**Test layout:**
- All tests in `tests/`, mirror source tree (`tests/test_strategies_csp.py` ↔ `src/csp/strategies/csp.py`)
- Cassettes in `tests/cassettes/{vendor}/{endpoint}_{ticker}.yaml`
- Shared fixtures in `tests/conftest.py` (sample `OratsCore`, `MacroSnapshot`, `PortfolioSnapshot`)

**pytest-vcr discipline:**
- New cassettes recorded **once** with real tokens (`pytest --record-mode=once`)
- Cassettes committed to repo; tokens scrubbed via VCR `filter_query_parameters=["token", "apikey"]`
- Re-recording requires explicit reason in commit message — cassettes are the regression contract
- No test may set `record_mode=new_episodes` in the codebase (only on the developer CLI when intentional)

**Mocking rules:**
- Mock only at the HTTP boundary (VCR) — never mock pydantic models or filter functions
- Never mock `datetime.now()` directly; use `freezegun` or inject a clock parameter
- DuckDB tests use `:memory:` connection, not the real file

**Coverage gates:**
- ≥ 80% line coverage overall (matches Acceptance §13)
- 100% coverage required for `filters/pflichtregeln.py` and `lifecycle/state_machine.py`
- `pytest --cov=csp --cov-fail-under=80` in CI

**Test naming:**
- Use plain English: `test_csp_filter_rejects_when_delta_below_minimum`
- Group related tests in classes only when sharing nontrivial setup
- Arrange-Act-Assert with comments when the structure isn't obvious

**Forbidden in tests:**
- Live HTTP calls (CI must work offline once cassettes exist)
- `time.sleep()` (use `freezegun`/`hypothesis.settings(deadline=…)`)
- Tests that depend on test ordering
- Tests that touch `~/.config/csp/` or any path outside the repo

### Code Quality & Style Rules

**Linting & formatting (single tool: ruff):**
- `ruff check` + `ruff format` are the only tools — no black, flake8, isort, pylint
- Line length: 100 chars (override ruff default 88 for finance-domain readability)
- Enabled rule sets: `E`, `F`, `W`, `I` (imports), `N` (naming), `UP` (pyupgrade), `B` (bugbear), `SIM` (simplify), `RUF`
- `# noqa` requires a rule code AND a reason: `# noqa: E501 — long URL string`

**Repo & module structure (post-pivot, do not reorganize):**

```
src/csp/
├── __init__.py         # public API surface — re-exports the 10 public functions
├── config.py           # pydantic-settings
├── clients/            # orats.py, fmp.py, ivolatility.py, sheets.py
├── models/             # core.py, option.py, trade.py, portfolio.py, macro.py
├── strategies/         # csp.py only in MVP (base.py + others deferred to Growth)
├── filters/            # pflichtregeln.py, liquidity.py, sector_caps.py
├── ranking/            # annualized_yield.py (kelly.py, score.py deferred to Growth)
├── lifecycle/          # state_machine.py (alerts.py, roll_engine.py deferred)
├── persistence/        # db.py, snapshots.py, trades.py, migrations/
└── reporting/          # sheets.py, md_export.py
```

Removed from brief §5.1 by the architectural pivots:
- ❌ `cli.py` — no typer CLI in MVP
- ❌ `ui/` — Claude renders markdown directly; German-locale formatting only for Sheets export and `Idea.format_fbg_mail()`
- ❌ `reporting/tax.py` — tax export removed entirely from project scope (not deferred — deleted)

Added since brief §5.1:
- ✅ `clients/ivolatility.py` — EU options EOD vendor (added 2026-04-27)

New modules need a justification — prefer extending an existing one.
- Cross-module imports go through `__init__.py` re-exports for stable public API

**Naming conventions:**
- Files & modules: `snake_case.py`
- Classes: `PascalCase` (`OratsClient`, `CSPTrade`)
- Functions, methods, variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`, defined at module top
- Strategy classes named after the strategy: `class CashSecuredPut(AbstractStrategy)`
- Public library functions: `snake_case` (`daily_brief`, `list_open_positions`, `get_idea`)

**Function size & complexity:**
- Default target: ≤ 30 lines per function
- Filter functions return `tuple[bool, list[str]]` (passed, reasons) — never raise for filter failures
- Cyclomatic complexity ≤ 10 (ruff `C901`); split if exceeded

**Documentation patterns:**
- Module docstring: 1-2 lines stating purpose (German)
- Public functions: docstring required only when behavior isn't obvious from signature + name
- No "what" comments (`# increment counter`); only "why" comments (hidden constraint, vendor quirk)
- Vendor field semantics documented inline when surprising (e.g., ORATS `mktCap` is in thousands USD)

**Numeric output formatting (`ui/formatters.py` is the single source of truth):**
- USD prices: `1.234,56 USD` (German locale: thousand `.`, decimal `,`)
- Percentages: `13,3 %` (one decimal, space before `%`)
- DTE / counts: integer
- Dates in user-facing output (Sheets cells, `Idea.format_fbg_mail()` strings, anything Claude relays verbatim): `27.04.2026`; dates in DB/JSON: ISO `2026-04-27`

**Money & precision:**
- Premiums, P/L, cash-secured amounts: `Decimal` end-to-end (not `float`)
- Percentages, deltas, IV, IVR: `float`
- Conversion at the boundary only (when serializing to JSON or writing to DuckDB)

### Development Workflow Rules

**Repository & branches:**
- Default branch: `main` (protected once CI is set up)
- Feature work on `feature/<short-description>`; fixes on `fix/<short-description>`; chores on `chore/<short-description>`
- Branches are short-lived (days, not weeks); rebase on `main` before merge

**Commit messages (conventional-commits style, English):**
- Format: `<type>(<scope>): <imperative subject>`
- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`
- Scope = top-level module: `clients`, `strategies`, `filters`, `lifecycle`, `persistence`, `reporting`, `models`, `ranking`
- Subject ≤ 50 chars, imperative ("add", not "added")
- Body explains WHY (German OK if it captures domain reasoning more precisely); reference brief sections when relevant: `Closes brief §6.1`

**Pre-commit gates (must pass before commit):**
1. `ruff check src tests`
2. `ruff format --check src tests`
3. `mypy --strict src` (or `pyright`)
4. `pytest -q` (full suite, ≤ 30 s on cassettes)

Run via `uv run pre-commit run --all-files` if pre-commit hooks are installed.

**PR / review checklist:**
- [ ] All Pflichtregeln still pass (`pytest tests/test_pflichtregeln.py -v`)
- [ ] NOW-78-strike regression cassette still reproduces (`pytest -k now_regression`)
- [ ] No new dependencies without note in PR description (justify each)
- [ ] No live API calls in tests
- [ ] No secrets in diff (token, sheet IDs, service-account paths, IVolatility key)
- [ ] Coverage ≥ 80%; 100% for `filters/` and `lifecycle/`
- [ ] All public-API docstrings still complete (purpose, parameters, return shape, exceptions) — Claude reads these to compose calls

**Dependency management (`uv`):**
- Add deps via `uv add <pkg>` (writes `pyproject.toml` + `uv.lock`)
- `uv lock` committed; never edit `pyproject.toml` deps by hand without re-locking
- Pin Python version in `pyproject.toml`: `requires-python = ">=3.12"`
- No optional/extra dep groups for runtime; only `dev` (tests, linters) and `plot` (plotly)

**Files that MUST be gitignored (security-critical):**
- `.env` and any `.env.*` (contains ORATS_TOKEN, FMP_KEY, IVOLATILITY_API_KEY, GOOGLE_SHEET_ID)
- `~/.config/csp/sa.json` is outside repo by definition
- `data/trades.duckdb` and `data/snapshots/**` (regeneratable, may contain trade history)
- `logs/**`
- `.coverage`, `htmlcov/`, `__pycache__/`, `.mypy_cache/`, `.ruff_cache/`

**Daily run / cron (deferred to Growth):**
- MVP has no cron / systemd-timer. The user invokes the daily routine manually via Claude Code conversation.
- When cron arrives in Growth: `python -m csp.daily_brief` will be the entry point (a thin CLI wrapper). Cron must succeed even if Sheets is unreachable — Sheets push is best-effort; DuckDB write is mandatory. Exit non-zero only on data-source errors (ORATS/FMP/IVolatility), not on filter results returning empty.

### Critical Don't-Miss Rules

**Pflichtregeln are inviolable (PRD § Functional Requirements FR8):**
A CSP idea must pass ALL nine filters before being surfaced. Any agent generating ideas must:
- Run the full filter pipeline; never short-circuit
- Return `tuple[bool, list[str]]` with explicit failure reasons (German strings for user-visible)
- Never relax thresholds without explicit `override=True` argument to the library function (and even then, log a WARN and persist the override decision in DuckDB for monthly review)
- Plus a 10th implicit gate: `data_freshness` must be `"live"` for US candidates or `"eod"` (≤ 1 day old) for EU candidates — `"stale"` and `"unavailable"` block new ideas regardless of Pflichtregeln

The nine rules:
1. `VIX ≥ 20` OR `IVR (ivPctile1y) ≥ 40`
2. `delta ∈ [-0.25, -0.18]`
3. `dte ∈ [30, 55]` (preferred 35–45)
4. Strike OTM ≥ 8% from spot
5. Earnings (`daysToNextErn`) ≥ 8 days away
6. Liquidity: `avgOptVolu20d ≥ 50_000` AND `(putAskPrice − putBidPrice) ≤ 0.05`
7. `mktCap ≥ 50_000_000` (note: ORATS gives this in **thousands** USD, so this means 50 B USD)
8. Sector cap: new sector exposure ≤ 55% of CSP capital (single global cap in MVP — granular `[rules.sector_caps]` deferred to Growth)
9. Ticker is in `config.universe.allowed_tickers`

EU candidates use the **same 9 rules with the same thresholds** (no MVP relaxation). Pflichtregel #1 IVR-leg uses IVolatility-derived IVR; VIX-leg refers to US `^VIX` regardless of region.

**Hormuz Special-Regelwerk (deferred to Growth):**
The `[rules.hormuz_special]` configuration block (lower IVR threshold, looser spread, lower options-volume requirement, max 1 contract, manual-approval flag) is **not built in MVP**. Master-Investmentliste tickers (LNG, WMB, KMI, CF, NTR, etc.) either pass the standard 9 rules or are skipped — no special-case handling.

**Vendor gotchas:**
- **FMP options endpoints are dead** (deprecated 2025-08-31) — never call `/api/v3/options/...`; always use ORATS for US options data and IVolatility for EU options data
- **ORATS endpoints — empirically verified status (2026-04-29 plan-tier probe):**
  - ✅ Reachable on current plan (HTTP 200): `/datav2/cores`, `/datav2/strikes`, `/datav2/hist/strikes`, `/datav2/hist/cores`, `/datav2/ivrank`, `/datav2/summaries` — used by `OratsClient` (slice 2). The spec doc previously flagged `/datav2/hist/dailyPrice` (and the `/datav2/hist/...` family generically) as unauthorized — that note was stale; `/hist/strikes` and `/hist/cores` are reachable. Other `/hist/*` endpoints not yet probed — verify before assuming reachable.
  - ❌ Still unauthorized on current plan (untested 2026-04-29): `/datav2/hist/hv`, `/datav2/history/dailyPrice`, `/datav2/volatility` — do not call them; if HV is needed, derive from FMP daily prices.
  - **Rule of thumb:** before adding a new endpoint, run a one-off probe (`curl -sI 'https://api.orats.io/datav2/<path>?token=...&ticker=NOW'`) and update this list with the date.
- **ORATS field semantics:**
  - `mktCap` is in thousands USD (96.524 = 96.5 B USD market cap, NOT 96.5 M)
  - `ivPctile1y` is the **IVR** (1-year IV percentile), not 1-month
  - `daysToNextErn = 0` may mean "today is earnings day" — treat as ≥ 8d failure
- **FMP namespace:** prefer `/stable/...`; `/api/v3/...` and `/api/v4/...` are legacy and partly deprecated
- **IVolatility (added 2026-04-27):**
  - **EOD only** — never assume intraday. EU candidates gate on `data_freshness="eod"` and snapshot ≤ 1 day old.
  - **Response shape NOT yet verified** — first task during client implementation: run `csp.iv_health_check("ALV.DE")` to record a real cassette and inspect actual field names. **Do not write Pydantic models from docs alone.**
  - **EU symbol convention TBD** — `ALV.DE` for Allianz on Eurex is the assumed format; verify on first cassette. Universe loader maps each ticker via `region` and `vendor_symbol` columns.
  - **Auth scheme TBD** — query parameter vs. `X-API-Key` header. VCR scrubbing config in NFR9 confirmed once verified.
  - **Plan tier and rate limit TBD** — surface as constants in `clients/ivolatility.py` once known.
  - Endpoint reference: <https://www.ivolatility.com/api/docs#tag/End-of-Day-(EOD)-Equity-Options>

**Idempotency (PRD NFR12, NFR13):**
- Same-day reruns must not double-insert: snapshots use `INSERT OR REPLACE` keyed on `(ticker, snapshot_date)`
- Trade lifecycle transitions are idempotent: `take_profit_pending → closed_profit` runs at most once per day per `trade_id`

**State-machine invariants (MVP-scope subset):**
- MVP supports manual position entry (`csp.log_trade`, `csp.close_trade`) only — no automated transitions, no wheel state machine.
- `closed_loss` is only entered via Stop-Loss (200% of original premium) — not on assignment
- `emergency_close` fires when `daysToNextErn ∈ [0, 7]` AND position is open, regardless of P/L (flagged by `csp.daily_brief()` action recommendations)
- Wheel covered-call lifecycle (`assigned → CC open`, net-credit-only roll mechanic) is **deferred to Growth**. In MVP, `assigned` is a terminal manual-entry state; the user decides next action outside the tool.

**Security & secrets (PRD NFR7–NFR11):**
- API tokens NEVER in code or commits — only `.env` (gitignored)
- Service-account JSON path: `~/.config/csp/sa.json` — never copy into repo
- `loguru` filter strips `token`, `apikey`, `api-key`, `Authorization`, `IVOLATILITY_API_KEY` substrings from log output
- No automatic order routing — every order eyeballed by Chris before placement; library functions may return a copy-pasteable order summary in the `Idea.format_fbg_mail()` string but never call a broker API
- Library raises `ConfigError` at startup if `IVOLATILITY_API_KEY` is missing AND any universe ticker has region `EU`

**Out-of-scope (do NOT build):**
- Order execution / broker integration of any kind
- Web UI / dashboard / Streamlit / FastAPI HTTP server
- Crypto-options support
- A backtest framework from scratch (later: ORATS Backtest API only)
- **Tax export** (Anlage KAP / GmbH-Buchhaltung) — entirely removed from project scope, not deferred. Brief §10.1 `csp tax-report` and brief §5.1 `reporting/tax.py` are superseded.
- **`typer` CLI** in MVP — pivoted to library-first 2026-04-27. May return as a thin wrapper for cron in Growth.
- **MCP server** — wrap the library only if Bash invocation friction becomes real (Growth).

**Performance gates (PRD NFR1–NFR4):**
- `csp.daily_brief()` Python execution ≤ 30 s on warm cache (parallelize vendor calls per ticker via `asyncio.gather`)
- Universe scan over ~40 tickers (US + EU) ≤ 60 s
- Single `csp.idea(ticker)` ≤ 5 s for US ticker; ≤ 7 s for EU ticker (one ORATS or IVolatility round trip + Pflichtregeln evaluation)
- End-to-end daily-brief conversation in Claude Code (Python work + Claude reasoning) ≤ 90 s on warm cache
- Sheets push is async fire-and-forget — must not block library function return paths

**Regression anchor (brief §8.2):**
The NOW idea from 2026-04-24 (Strike 78, DTE 55, Premium 4.30, IVR 94) is the canonical reproduction case. If a refactor breaks `pytest -k now_regression`, stop and investigate before proceeding.

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code in this project
- Follow ALL rules exactly as documented; when in doubt, choose the more restrictive option
- The Pflichtregeln in "Critical Don't-Miss Rules" are inviolable — never relax thresholds
- The PRD at `_bmad-output/planning-artifacts/prd.md` is the authoritative spec — references to "PRD § …" point there. The legacy brief is archived at `docs/archive/Projekt-Brief-2026-04-27.md` and is **superseded** in any conflict.
- If a rule conflicts with what the user is asking, surface the conflict before proceeding
- Update this file via `/bmad-generate-project-context` if a new pattern emerges that future agents would also miss

**For humans:**
- Keep this file lean — every rule should prevent a real mistake an agent would otherwise make
- Update when the technology stack, vendor plan (ORATS/FMP/IVolatility), or Pflichtregeln change
- Re-check vendor gotchas (FMP namespace, ORATS unauthorized list, IVolatility response shape) on plan upgrades or when first cassette is recorded
- Review quarterly; remove rules that become obvious once the codebase makes them self-evident
- **Source of truth:** `_bmad-output/planning-artifacts/prd.md`. This file distills the PRD's implementation rules; the brief is archived (`docs/archive/Projekt-Brief-2026-04-27.md`) and retains historical-reference value only.

Last Updated: 2026-04-27 (post-PRD reconciliation: archived brief, removed CLI/UI/tax-export rules, added IVolatility vendor gotchas, deferred Wheel state-machine and Hormuz special-rules to Growth)
