---
title: 'Pflichtregeln Gate (csp.passes_csp_filters) + Project Bootstrap'
type: 'feature'
created: '2026-04-29'
status: 'in-progress'
baseline_commit: 'NO_VCS'
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
| Sector cap | `portfolio.sector_exposures = {"Tech": 0.60}`, candidate sector "Tech" | `(False, ["Pflichtregel 8 — Sektor Tech bereits 60,0 % > 55 %"])` | Rule 8, dict input from caller |
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
