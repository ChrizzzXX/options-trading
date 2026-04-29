---
title: 'Pflichtregeln Gate (csp.passes_csp_filters) + Project Bootstrap'
type: 'feature'
created: '2026-04-29'
status: 'done'
baseline_commit: 'EMPTY_TREE'
implementation_commit: '4c82a17'
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/planning-artifacts/prd.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** No code exists yet. The Pflichtregeln engine (PRD FR8/FR11/FR12) is the inviolable core — every CSP idea must pass it — and we need it functioning, fully tested, and re-exportable as `csp.passes_csp_filters(...)` before any vendor, persistence, or daily-brief work makes sense.

**Approach:** Bootstrap a minimal `uv`-managed Python 3.12 package, then ship the deterministic 9-rule gate as pure functions in `src/csp/filters/pflichtregeln.py`, fed by minimal Pydantic data carriers (`OratsCore`, `OratsStrike`, `MacroSnapshot`, `PortfolioSnapshot`) and a `pydantic-settings` `Settings` class reading `config/settings.toml`. NOW-78 (2026-04-24) is encoded as a hardcoded test fixture; the real ORATS cassette arrives with the ORATS-client slice.

## Boundaries & Constraints

**Always:**
- 9 rules, each isolated as `def rule_NN(...) -> tuple[bool, str | None]` returning `(passed, German reason on failure)`.
- `passes_csp_filters(core, strike, macro, portfolio, settings, *, override=False)` runs all 9, never short-circuits — collects every failure reason in rule order.
- All thresholds from `Settings` (FR12). No hardcoded numbers in `pflichtregeln.py`.
- German failure-reason strings; English identifiers.
- `mypy --strict` clean, `ruff check` clean, **100 % line coverage on `pflichtregeln.py`**, ≥ 80 % overall.
- Public re-export: `from csp import passes_csp_filters`.
- Init git repo (`main`); single commit for the slice.

**Ask First:**
- Any new dependency beyond `pydantic`, `pydantic-settings`, `loguru`, `pytest`, `pytest-cov`, `hypothesis`, `ruff`, `mypy`.
- Renaming any threshold key (FR12 fixes them: `vix_min`, `ivr_min`, `delta_min`, `delta_max`, `dte_min`, `dte_max`, `strike_otm_min_pct`, `earnings_min_days`, `options_volume_min`, `spread_max_usd`, `market_cap_min_billion`, `sector_cap_pct`).
- Changing the function signature beyond adding `settings` (PRD line 409 fixes `core, strike, macro, portfolio`).

**Never:**
- ORATS / FMP / IVolatility client code. `OratsCore` / `OratsStrike` here are minimal local Pydantic models, no `Field(alias=...)` mapping — vendor-shaped versions land with the ORATS-client slice.
- DuckDB, snapshots, trade lifecycle, ranking, daily-brief, Sheets.
- Override-flag DB persistence (FR9). `override=True` logs a `loguru` WARN only; persistence joins the lifecycle slice.
- `typer` / `rich` / web UI.
- Hardcoded thresholds anywhere except `config/settings.toml`.
- Live HTTP in tests.

## I/O & Edge-Case Matrix

| Scenario | Input | Expected | Notes |
|---|---|---|---|
| NOW-78 happy path | NOW fixture (Strike 78, DTE 55, IVR 94, delta -0.22…), VIX 18.7, empty portfolio | `(True, [])` | Regression anchor `@pytest.mark.now_regression` |
| Multi-rule fail (collect all) | Candidate failing rules 2, 3, 5 | `(False, [r2_msg, r3_msg, r5_msg])` in rule order | Never short-circuits |
| Rule 1 OR-gate | VIX 18 + IVR 35 → fail; VIX 18 + IVR 45 → pass | German reason names both values on fail | |
| Universe miss | `ticker="XXX"` not in `allowed_tickers` | `(False, ["Pflichtregel 9 — Ticker XXX nicht im Universum"])` | Rule 9 |
| Sector cap | `portfolio.sector_exposures = {"Tech": 0.60}`, candidate sector "Tech" | `(False, ["Pflichtregel 8 — Sektor Tech bereits 60,0 % > 55,0 %"])` | Rule 8, dict input from caller |
| Override flag | Failing candidate + `override=True` | `(True, [original reasons preserved])`; loguru WARN emitted | No DB write yet |
| Mkt-cap unit conversion | Setting `market_cap_min_billion = 50`; ORATS `mktCap` in **thousands** USD | Internally: `min_thousands = setting * 1_000_000`; tested at boundary in both directions | Rule 7 |

</frozen-after-approval>

## Code Map

- `pyproject.toml` — uv project; runtime deps `pydantic>=2`, `pydantic-settings`, `loguru`; dev deps `pytest`, `pytest-cov`, `hypothesis`, `ruff`, `mypy`. Tool configs: ruff line 100 + rules `E,F,W,I,N,UP,B,SIM,RUF`; mypy strict; pytest with `--cov=csp.filters.pflichtregeln --cov-fail-under=100 --cov=csp --cov-fail-under=80`.
- `.gitignore`, `.env.example` — security baseline (`.env`, `__pycache__/`, `.mypy_cache/`, `.ruff_cache/`, `htmlcov/`, `.coverage`, `data/`, `logs/`).
- `config/settings.toml` — 12 thresholds (defaults from project-context.md "9 rules") + `[universe] allowed_tickers` (seed list, ≥ NOW + a few PRD-mentioned tickers).
- `src/csp/__init__.py` — public re-exports: `passes_csp_filters`, `Settings`, the 4 models, exceptions.
- `src/csp/config.py` — `Settings(BaseSettings)` with nested `[rules]` and `[universe]` sections; raises `ConfigError` on load failure.
- `src/csp/exceptions.py` — `ConfigError`, `PflichtregelError`.
- `src/csp/models/core.py` — `OratsCore` (ticker, under_price, sector, mkt_cap_thousands, ivr, days_to_next_earn, avg_opt_volu_20d), `OratsStrike` (strike, delta, dte, put_ask, put_bid), `MacroSnapshot` (vix_close), `PortfolioSnapshot` (sector_exposures: dict[str, float]). Plain Pydantic v2.
- `src/csp/filters/__init__.py` — re-export `passes_csp_filters`.
- `src/csp/filters/pflichtregeln.py` — 9 `rule_NN(core, strike, macro, portfolio, settings)` functions + `passes_csp_filters` orchestrator + German reason constants.
- `tests/fixtures/now_2026_04_24.py` — NOW-78 frozen model instances; each field's docstring tag records `(value, source: PRD § / brief § / inferred-plausible)` so reconciliation with the real cassette is explicit.
- `tests/conftest.py` — `default_settings`, `empty_portfolio`, NOW fixtures, `macro_vix_18_7`.
- `tests/test_pflichtregeln.py` — one test class per rule + `TestPassesCspFilters` orchestrator + `TestNowRegression` (`@pytest.mark.now_regression`) + override + multi-failure ordering.
- `tests/test_settings.py` — load `config/settings.toml`, verify keys present, verify `ConfigError` on missing/malformed file (use `tmp_path`).
- `README.md` — minimal scaffold required by `hatchling` build backend; one-paragraph slice intro + install command.
- `tests/__init__.py`, `tests/fixtures/__init__.py` — package markers so `tests.fixtures.now_2026_04_24` is importable from `conftest.py`.
- `src/csp/models/__init__.py` — re-exports `OratsCore`, `OratsStrike`, `MacroSnapshot`, `PortfolioSnapshot`.

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml` — uv project skeleton + deps + tool configs
- [x] `.gitignore`, `.env.example` — security baseline
- [x] `config/settings.toml` — 12 thresholds + universe seed
- [x] `src/csp/exceptions.py` — `ConfigError`, `PflichtregelError`
- [x] `src/csp/config.py` — `Settings` class
- [x] `src/csp/models/core.py` — four minimal models
- [x] `src/csp/filters/pflichtregeln.py` — 9 rules + orchestrator + reason constants
- [x] `src/csp/__init__.py` + `src/csp/filters/__init__.py` — re-exports
- [x] `tests/fixtures/now_2026_04_24.py` — NOW-78 instances
- [x] `tests/conftest.py` — shared fixtures
- [x] `tests/test_pflichtregeln.py` — covers every I/O-matrix row + each rule individually
- [x] `tests/test_settings.py` — load + malformed-file `ConfigError`
- [x] `git init && git add -A && git commit -m "chore: bootstrap project + Pflichtregeln gate"`

**Acceptance Criteria:**
- Given a fresh checkout, when `uv sync && uv run pytest`, then all tests pass with `--cov-fail-under=100` for `csp.filters.pflichtregeln` and `--cov-fail-under=80` overall.
- Given the NOW-78 fixture and empty portfolio, when `passes_csp_filters(...)` runs, then result equals `(True, [])`.
- Given a candidate failing rules 2 and 5, when `passes_csp_filters(...)` runs, then `passed=False` and `reasons` lists rule 2's German message before rule 5's.
- Given `override=True` on a failing candidate, when `passes_csp_filters(...)` runs, then `passed=True`, reasons preserved unchanged, and a `loguru` WARN was emitted.
- Given `config/settings.toml` is missing, when `Settings()` is constructed, then `ConfigError` is raised naming the missing path.
- Given `import csp`, when `csp.passes_csp_filters` is referenced, then it resolves to the orchestrator (PRD FR11 public surface).
- `uv run ruff check src tests` and `uv run mypy --strict src` both exit 0.

## Spec Change Log

- 2026-04-29 — Implementation complete. `addopts` in `pyproject.toml` carries the 80 % overall gate; the 100 % `pflichtregeln.py` gate is enforced via a separate `coverage report --include='src/csp/filters/pflichtregeln.py' --fail-under=100` invocation (pytest only honors the last `--cov-fail-under` flag, so two simultaneous gates aren't expressible in pyproject `addopts`). Both gates pass at HEAD: `pflichtregeln.py` 100 % / overall 100 %.
- 2026-04-29 — Pre-review patch: initial commit (`6085731`) swept in 831 files / 131 717 LOC because `git add -A` ran without a `.gitignore` rule for tool-install folders (`.agents/`, `.claude/`, `_bmad/`). Code itself was correct (40 tests green, all gates passing). Fix: appended `_bmad/`, `.agents/`, `.claude/` to `.gitignore`; reset HEAD via `git update-ref -d HEAD` (initial commit, no parent); unstaged the three folders with `git rm -r --cached`; re-committed identical content scope to **35 files / 7 419 LOC** as `4c82a17`. KEEP: `_bmad-output/` (PRD, project-context.md, this spec) and `docs/` (Chris's pre-existing strategy/watchlist) remain tracked — they are user-authored source-of-truth, not tool installations. Future bootstraps must include the .gitignore tooling-folder rules before any `git add -A`.
- 2026-04-29 — Review-driven hardening (14 patches). **Group A (P2/P3/P5/P10/P14):** front-load data sanity at the Pydantic boundary — `OratsCore.under_price > 0`, `OratsStrike.delta ∈ [-1, 0]`, `OratsCore.days_to_next_earn ≥ 0`, `OratsStrike` rejects crossed/negative quotes (`put_ask ≥ put_bid ≥ 0`); the now-unreachable spot-guard branch in rule 4 is removed. **Group B (P1/P6/P7/P8/P9):** Settings hygiene — `RuleThresholds` enforces ordering & sign of all twelve thresholds via `model_validator`, both `RuleThresholds` and `UniverseConfig` set `extra="forbid"` to catch typos, `Settings.load` narrows its `except` to `(TomlDecodeError, ValidationError, OSError)` so `KeyboardInterrupt` propagates, `allowed_tickers` requires `min_length=1` and is uppercase-normalised, `OratsCore.ticker` likewise — case-insensitive Pflichtregel 9 falls out for free. **Group C (P4/P11/P12):** rule 8 sector-cap compares the raw share against `sector_cap_pct / 100` to side-step the `0.55 * 100 → 55.000…01` FP artefact (parametrised tests at 0.5499/0.5500/0.5501); `passes_csp_filters` only logs the override-WARN when `override=True AND reasons` (silent on zero-violation overrides); a parametrised rule 1 boundary test pins both legs at threshold-grazing values. **Group D (P13):** Row 5 of the I/O & Edge-Case Matrix realigned to the project formatter convention (`> 55,0 %`).

## Design Notes

**Signature deviation from PRD line 409.** PRD lists `passes_csp_filters(core, strike, macro, portfolio)`. We add `settings` as a 5th positional arg because (a) FR12 forbids hardcoded thresholds, (b) the function is the only public consumer of the rule thresholds, and (c) injecting `Settings` keeps the function pure (no module-level singleton import). Flagged here for human approval; documented in the function's docstring.

**Per-rule functions, not a config-driven rule loop.** Each Pflichtregel has different input requirements (rule 1 wants macro+core, rule 8 wants portfolio, rule 9 wants settings.universe). Nine named functions stay debuggable, individually testable, and produce named coverage entries.

**NOW-78 fixture vs. cassette.** The real ORATS cassette joins the ORATS-client slice. Until then, each fixture field carries a docstring tag `(value, source)` so the reconciliation point is explicit when the cassette arrives.

## Verification

**Commands:**
- `uv sync` — expected: lockfile + venv created
- `uv run ruff check src tests` — expected: exit 0
- `uv run ruff format --check src tests` — expected: exit 0
- `uv run mypy --strict src` — expected: exit 0
- `uv run pytest -q` — expected: all green, coverage gates hold
- `uv run pytest -k now_regression -v` — expected: NOW-78 passes
- `uv run python -c "import csp; print(csp.passes_csp_filters)"` — expected: prints function repr (public re-export verified)

## Suggested Review Order

**The deterministic gate (start here)**

- Public surface — `import csp` re-exports the orchestrator + 4 models + exceptions per PRD FR11.
  [`__init__.py:8`](../../src/csp/__init__.py#L8)

- Orchestrator: runs all 9 rules, collects every reason in rule order, never short-circuits.
  [`pflichtregeln.py:224`](../../src/csp/filters/pflichtregeln.py#L224)

- Override-silence guard — `override=True` only logs WARN when at least one rule actually failed.
  [`pflichtregeln.py:248`](../../src/csp/filters/pflichtregeln.py#L248)

- Rule 8 sector-cap with FP-safe boundary — compares raw share, not `share*100 vs cap_pct`.
  [`pflichtregeln.py:181`](../../src/csp/filters/pflichtregeln.py#L181)

- Rule 7 mkt-cap unit reconciliation — `min_thousands = setting * 1_000_000` (billions ↔ thousands).
  [`pflichtregeln.py:149`](../../src/csp/filters/pflichtregeln.py#L149)

**Input contracts (Pydantic data carriers)**

- `OratsStrike` rejects crossed/negative quotes at parse time — rule 6 doesn't have to defend against bad data.
  [`core.py:46`](../../src/csp/models/core.py#L46)

- Field constraints on `OratsCore` (under_price > 0, days_to_next_earn ≥ 0) and `OratsStrike.delta ∈ [-1, 0]`.
  [`core.py:1`](../../src/csp/models/core.py#L1)

**Settings & thresholds (FR12 compliance)**

- `RuleThresholds` model_validator — enforces `delta_min < delta_max ≤ 0`, dte/strike/cap orderings, sign checks.
  [`config.py:35`](../../src/csp/config.py#L35)

- `UniverseConfig` — `allowed_tickers` is non-empty and case-insensitive (uppercase on load + on `OratsCore.ticker`).
  [`config.py:74`](../../src/csp/config.py#L74)

- Single source of truth for the 12 thresholds + universe seed.
  [`settings.toml`](../../config/settings.toml)

**Determinism contract (tests)**

- NOW-78 regression — the canonical pass case (synthetic until ORATS-client slice records the real cassette).
  [`test_pflichtregeln.py:459`](../../tests/test_pflichtregeln.py#L459)

- Rule 8 FP-boundary parametrised at 0.5499 / 0.5500 / 0.5501 — locks down the floating-point fix.
  [`test_pflichtregeln.py:311`](../../tests/test_pflichtregeln.py#L311)

- Rule 1 OR-gate boundary — VIX-leg and IVR-leg threshold-grazing cases both tested.
  [`test_pflichtregeln.py:70`](../../tests/test_pflichtregeln.py#L70)

- Override silence — zero-violation overrides emit no WARN.
  [`test_pflichtregeln.py:426`](../../tests/test_pflichtregeln.py#L426)

- NOW-78 fixture with field-by-field source tags — reconciliation point when the real cassette arrives.
  [`now_2026_04_24.py:17`](../../tests/fixtures/now_2026_04_24.py#L17)

- Pydantic validator coverage — every Field constraint + every model_validator has a rejection test.
  [`test_models.py:1`](../../tests/test_models.py#L1)

**Bootstrap & ergonomics (peripherals)**

- uv project skeleton + ruff/mypy/pytest tool configs + per-file 100% coverage gate command.
  [`pyproject.toml`](../../pyproject.toml)

- Repo-wide hard rules (read first by future Claude/Codex sessions).
  [`CLAUDE.md`](../../CLAUDE.md)
