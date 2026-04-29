---
title: 'csp.idea(ticker) — single-ticker CSP idea (slice 3)'
type: 'feature'
created: '2026-04-29'
status: 'done'
baseline_commit: '32e951b758808ec67e1511f57c1384f33127aa9c'
context:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/project-context.md'
  - '_bmad-output/implementation-artifacts/spec-pflichtregeln-gate.md'
  - '_bmad-output/implementation-artifacts/spec-orats-client.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** PRD's 10-function public surface has only `passes_csp_filters` shipped (slice 1) and `OratsClient` ready (slice 2). The next user-visible composition is `csp.idea(ticker)` — single-ticker, ORATS-fetched, Pflichtregeln-gated CSP candidate. Until this exists, Chris cannot move from "rule engine works" to "here is an idea I would trade".

**Approach:** Compose `OratsClient` (slice 2) and `passes_csp_filters` (slice 1) into a sync public function `csp.idea(...)`. Always returns a populated `Idea` model carrying `pflichtregeln_passed: bool`, `reasons: list[str]`, and `bypassed_rules: list[str]` — the override-pathway annotation. This amends PRD FR13 (was `Idea | None`) so Claude always sees "would-pass-with-override + which rules were bypassed" in one call. US-only this slice; EU dispatch awaits the IVolatility-client slice.

## Boundaries & Constraints

**Always:**
- Public signature: `csp.idea(ticker: str, dte: int = 45, target_delta: float = -0.20, *, as_of: date | None = None, override: bool = False) -> Idea`. Sync (wraps async via `asyncio.run`); ≤ 5 s wall-clock for US ticker (NFR4).
- Strike selection: pick the chain's expiration with DTE nearest `dte`; within it, pick the strike whose put-delta is nearest `target_delta` AND inside Pflichtregel #2 band `[delta_min, delta_max]`. Tie-break: lower strike (higher OTM%).
- All thresholds via `Settings`; no hardcoded magic. New `[macro] vix_close` block in `settings.toml` until FMP-client slice replaces it with a live fetch.
- `Idea` is frozen. Money (strike, premium) → `Decimal`; ratios (delta, IVR, yield_pct) → `float`. Annualized yield = `mid_premium / strike × 365 / dte × 100`.
- When `override=False` and rules fail → `Idea.pflichtregeln_passed = False`, `reasons` populated, `bypassed_rules = []`. When `override=True` → `pflichtregeln_passed = True`, `reasons = []`, `bypassed_rules` carries the German strings that were ignored, plus a `loguru` WARN. The two states never overlap.
- `as_of=None` → live `/cores` + `/strikes`; `as_of=<date>` → `/hist/cores` + `/hist/strikes`.

**Ask First:**
- Any change to the amended FR13 signature beyond what is specified here.
- Adding a 4th vendor, an `Idea.format_fbg_mail()` body, or DuckDB writes — all out of slice.

**Never:**
- No `Idea.format_fbg_mail()` (FR15) — deferred to a formatter slice.
- No DuckDB persistence of overrides (D3) or rejected ideas (FR10) — lifecycle slice.
- No EU/IVolatility dispatch — the IVolatility client doesn't exist; the universe currently has no `region` column, so all in-universe tickers are US by construction.
- No FMP-live macro lookup — `vix_close` reads from settings.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Happy path (live) | `idea("NOW")`, all 9 rules pass | `Idea(pflichtregeln_passed=True, reasons=[], bypassed_rules=[])` populated | N/A |
| Rule failure, no override | `idea("NOW", as_of=date(2026,4,24))` (3 rules fail) | `Idea(pflichtregeln_passed=False, reasons=[3 German strings], bypassed_rules=[])` | N/A |
| Rule failure, with override | same + `override=True` | `Idea(pflichtregeln_passed=True, reasons=[], bypassed_rules=[same 3 strings])` + WARN log | N/A |
| Ticker not in universe | `idea("AVGO")` | `Idea(pflichtregeln_passed=False, reasons=[…"Pflichtregel 9 — Ticker AVGO nicht im Universum"…])` | N/A |
| ORATS 4xx | bad token | — | `ORATSDataError` propagates verbatim |
| ORATS empty `/cores` | unknown ticker | — | `ORATSEmptyDataError` propagates |
| No strike matches delta band | chain has no put-delta in `[delta_min, delta_max]` near target | — | `ORATSEmptyDataError(status=200, body="kein passender Strike für target_delta=…")` |

</frozen-after-approval>

## Code Map

- `src/csp/models/idea.py` — new — `Idea` Pydantic model (frozen, German docstring).
- `src/csp/strategies/csp.py` — new — pure `_select_strike(strikes, target_delta, dte, settings) -> OratsStrike` and `build_idea(core, strike, macro, portfolio, settings, *, as_of, data_freshness, region, override) -> Idea`.
- `src/csp/idea.py` — new — async `_async_idea(...)` orchestrates ORATS fetch + selection + Idea construction; public `idea(...)` wraps `asyncio.run`.
- `src/csp/__init__.py` — re-export `idea` and `Idea`.
- `src/csp/config.py` — add `MacroConfig(vix_close: float)` and `Settings.macro: MacroConfig`.
- `config/settings.toml` — add `[macro] vix_close = 18.7` (placeholder until FMP-client slice).
- `tests/test_idea.py` — unit (`_select_strike` edge cases, `build_idea` happy + override + 3-fail) + integration (NOW-78 historical via `as_of=date(2026,4,24)` cassette; happy-path live via `cores_NOW.yaml`).
- `_bmad-output/planning-artifacts/prd.md` — amend FR13 line 572, Public API row 403, README example lines 439–444; add a section-header revision note.
- `_bmad-output/implementation-artifacts/deferred-work.md` — append D12–D15 (see Design Notes).

## Tasks & Acceptance

**Execution:**
- [x] `src/csp/models/idea.py` — `Idea` with fields: `ticker: str`, `strike: Decimal`, `dte: int`, `delta: float`, `put_bid: Decimal`, `put_ask: Decimal`, `mid_premium: Decimal`, `annualized_yield_pct: float`, `otm_pct: float`, `earnings_distance_days: int`, `current_sector_share_pct: float`, `pflichtregeln_passed: bool`, `reasons: list[str]`, `bypassed_rules: list[str]`, `as_of: date`, `data_freshness: Literal["live","eod","stale","unavailable"]`, `region: Literal["US","EU"]`. `model_config = ConfigDict(frozen=True)`. Module + class docstrings German.
- [x] `src/csp/strategies/csp.py` — `_select_strike` (1) groups strikes by `dte`; (2) picks expiration with smallest `|dte − requested|`; (3) within it filters strikes whose `delta ∈ [settings.rules.delta_min, settings.rules.delta_max]`; (4) returns the strike with smallest `|delta − target_delta|`; tie → lower `strike`. Empty result → raise `ORATSEmptyDataError(status=200, body="kein passender Strike …")`. `build_idea` calls `passes_csp_filters` and assembles all `Idea` fields per the override semantics in **Always**.
- [x] `src/csp/idea.py` — `_async_idea` opens `httpx.AsyncClient`, instantiates `OratsClient` from `Settings.load()`, fetches cores + strikes (live or `as_of`), calls `_select_strike` + `build_idea`. Public `idea(...)` is sync via `asyncio.run`. Empty `MacroSnapshot` from `Settings.macro.vix_close`; empty `PortfolioSnapshot` (lifecycle slice will replace). `data_freshness="live"` when `as_of is None` else `"eod"`.
- [x] `src/csp/config.py` — add `MacroConfig(BaseModel, ConfigDict(extra="forbid"))` with `vix_close: float` (≥ 0); `Settings.macro: MacroConfig`. Validator on TOML load.
- [x] `config/settings.toml` — append `[macro]\nvix_close = 18.7`.
- [x] `src/csp/__init__.py` — re-export `idea`, `Idea`.
- [x] `tests/test_idea.py` — unit: `_select_strike` (DTE-nearest, delta-nearest, band-filter, tie-break, no-match raises). Integration: historical NOW-78 via `as_of=date(2026,4,24)` against the existing `hist_*_NOW_20260424.yaml` cassettes — asserts `pflichtregeln_passed is False`, `len(reasons) == 3`, reasons start with `"Pflichtregel 3"`, `"Pflichtregel 5"`, `"Pflichtregel 6"`. Override path: same call with `override=True` → `pflichtregeln_passed is True`, `bypassed_rules == reasons_from_no_override`, WARN captured via `loguru` `caplog`. Happy path: live `cores_NOW.yaml` + a synthesized strikes payload (or recorded `strikes_NOW.yaml` if ORATS returns one in current slice cassette set; else respx-mocked).
- [x] `_bmad-output/planning-artifacts/prd.md` — edit FR13 (line 572), Public API row (line 403), README example (lines 439–444). Add `**Revision 2026-04-29:** FR13 return shape amended from `Idea | None` to `Idea` (always populated); see spec-idea-singleticker.md §Design Notes.` near the section header.
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` — append D12 (`Idea.format_fbg_mail()` — formatter slice), D13 (FMP-live VIX replaces `[macro] vix_close` — FMP-client slice), D14 (override DuckDB persistence — lifecycle slice; inherits D3 scope), D15 (`sector_exposure_delta_pct` — needs position sizing; today the model exposes `current_sector_share_pct` only).

**Acceptance Criteria:**
- Given the NOW-78-2026-04-24 cassettes and default settings, when `idea("NOW", dte=55, target_delta=-0.20, as_of=date(2026,4,24))` is called, then `Idea.pflichtregeln_passed is False` AND `len(Idea.reasons) == 3` AND reasons begin with `"Pflichtregel 3"`, `"Pflichtregel 5"`, `"Pflichtregel 6"` AND `Idea.bypassed_rules == []`.
- Given the same call with `override=True`, when invoked, then `Idea.pflichtregeln_passed is True` AND `Idea.bypassed_rules` equals the 3 reasons from the no-override case AND `Idea.reasons == []` AND a `loguru` WARN naming `NOW` was emitted.
- Given a chain with no put-delta in `[delta_min, delta_max]` near `target_delta`, when invoked, then `ORATSEmptyDataError` raises with body containing `"kein passender Strike"`.
- Given pre-commit gates, when run, then `ruff check`, `ruff format --check`, `mypy --strict`, `pytest -q` all pass in ≤ 30 s; overall coverage ≥ 80%; `src/csp/strategies/csp.py` and `src/csp/idea.py` ≥ 95%.

## Spec Change Log

### 2026-04-29 — Review iteration 1 (3-reviewer pass)

12 patches applied; 6 entries deferred (D16–D21); 5 nits rejected. No intent_gap, no bad_spec — all findings code-level or doc-level.

- **Triggered by:** Edge-case-hunter E2 (Pflichtregel 2 unbypassable via `override=True` due to delta-band pre-filter in `_select_strike`).
- **Amended:** Design Notes — added explicit "Rule 2 unbypassable" addendum. `_select_strike` docstring now states the consequence directly.
- **Known-bad state avoided:** silently dropping override-with-Rule-2-violation requests at the selector layer without telling the caller why; or sneaking a different selector behavior in the override path that breaks symmetry with `passes_csp_filters`'s 9-rule loop.
- **KEEP:** the band-pre-filter in `_select_strike` (originally specified in §Always). Removing it would let strikes with extreme deltas through, then the gate would reject them — but the *Idea* model would carry confusing data ("nearest delta is -0.05" with `bypassed_rules=["Pflichtregel 2 — Delta -0,05 außerhalb …"]`). Pre-filtering is the right behavior; the documentation gap was the real finding.

- **Triggered by:** Acceptance-auditor A5/A6 (`date.today()` violates project hard rule "TZ-aware datetimes only").
- **Amended:** none in spec; **fixed in code** via `datetime.now(ZoneInfo("Europe/Berlin")).date()`. No new dependency (stdlib `zoneinfo`); satisfies the project rule and locks Berlin as the reference clock for `as_of` resolution.
- **Known-bad state avoided:** mid-day boundary drift between UTC server clock and Chris's local Berlin clock — could shift `Idea.as_of` by a day near 22:00–00:00 UTC.
- **KEEP:** `as_of: date` field type on `Idea` (no `datetime`); only the resolution path needed TZ awareness.

- **Triggered by:** Edge-case-hunter E5 (`OratsStrike.dte=0` not rejected, would cause `ZeroDivisionError` in yield formula).
- **Amended:** none in spec; **fixed in slice 1's model** — `OratsStrike.dte: int = Field(gt=0)`. Tightening at the model boundary covers all current and future callers.
- **KEEP:** the yield formula (`mid/strike × 365/dte × 100`) — model-level guard is the right place for this.

- **Triggered by:** multiple (B3/E1, B4/A7, B9, B10/E10/A8, E3, E4/E8, E6, E7, E11, B5).
- **Amended:** none in spec; **12 code patches** in `idea.py`, `strategies/csp.py`, `models/core.py`, `config.py`, `tests/test_idea.py`. See review classification at `/tmp/slice3-review-classification.md` (transient).

## Design Notes

**Override-pathway annotation:** PRD-binding FR13 was `Idea | None`. Amended to always-`Idea` because when rules fail and Chris needs to decide "do I override here?", having to re-call with `override=True` to inspect bypassed reasons is friction. One call, all info — `pflichtregeln_passed=False` + `reasons` is default rejection; `pflichtregeln_passed=True` + `bypassed_rules` is explicit override; the two states never overlap (per **Always**).

**Rule 2 (Delta band) is structurally unbypassable** — added 2026-04-29 after review. `_select_strike` pre-filters strikes by `[delta_min, delta_max]` *before* `passes_csp_filters` ever sees them. Consequence: `override=True` cannot surface a Rule-2 violation in `bypassed_rules` (the strike never makes it that far). Pflichtregeln 1, 3-9 remain regularly bypass-able. If Chris needs a Rule-2-violating idea for a one-off, the path is to relax `delta_min`/`delta_max` in `settings.toml` for that run — not to flip `override`. Documenting this loud here so future reviewers don't re-flag it.

**Strike selection rationale:** DTE-nearest matches Chris's "the expiration closest to my target window" mental model. Delta-nearest *within* Pflichtregel #2 band avoids returning a strike that would auto-fail rule 2 — the gate would still catch it, but pre-filtering keeps the rejection signal honest (a strike that *did* qualify but failed for a different reason is more informative than "no strike ever could"). Lower-strike tie-break is more conservative (higher OTM%).

**Macro source decision:** This slice reads `vix_close` from `settings.toml [macro]` rather than mocking a `vix_close` parameter onto `csp.idea`. Reasoning: keeps the public signature aligned with PRD's `(ticker, dte, target_delta, override)` shape (plus `as_of`); when FMP-client slice lands, the internal swap to live VIX is invisible to callers.

**`as_of` parameter:** unblocks `pytest -k now_regression` invoking the public surface (not just `OratsClient` + `passes_csp_filters` directly), tightening the regression contract to what Chris actually calls.

## Verification

**Commands:**
- `uv run ruff check src tests` — expected: clean.
- `uv run ruff format --check src tests` — expected: no diffs.
- `uv run mypy --strict src` — expected: success.
- `uv run pytest -q` — expected: all 140+N tests pass; ≤ 30 s.
- `uv run pytest -k now_regression -v` — expected: invocation through `csp.idea("NOW", dte=55, target_delta=-0.20, as_of=date(2026,4,24))` reproduces the 3-rule failure deterministically.
- `uv run pytest --cov=csp --cov-fail-under=80` — expected: ≥ 80% overall; `coverage report --include='src/csp/strategies/csp.py','src/csp/idea.py' --fail-under=95` clean.
- `uv run python -c "import csp; print(csp.idea('NOW'))"` — manual smoke (requires live `.env` ORATS_TOKEN).

## Suggested Review Order

**Public surface & override-pathway design**

- Sync entry point — start here. Ticker normalization (P1) + future-`as_of` guard (P6) at the boundary.
  [`idea.py:81`](../../src/csp/idea.py#L81)

- 3-state override mapping — pass / fail-no-override / fail-with-override never overlap.
  [`csp.py:108`](../../src/csp/strategies/csp.py#L108)

- `Idea` Pydantic model — frozen, money-Decimal/ratio-float, the `pflichtregeln_passed` + `reasons` + `bypassed_rules` triplet.
  [`idea.py:26`](../../src/csp/models/idea.py#L26)

**Strike selection algorithm**

- DTE-nearest → band-and-positivity-filter → delta-nearest → multi-tier tie-break. Docstring states Rule 2 unbypassable consequence.
  [`csp.py:25`](../../src/csp/strategies/csp.py#L25)

- ORATS hist dispatch on `cores()` (slice 3 extension; matches slice-2 `strikes()` pattern).
  [`orats.py:121`](../../src/csp/clients/orats.py#L121)

**Spec, PRD, deferred work**

- Spec Change Log records the 12 review patches and Rule-2 design rationale.
  [`spec-idea-singleticker.md`](spec-idea-singleticker.md)

- PRD FR13 amendment (always-`Idea`).
  [`prd.md:572`](../planning-artifacts/prd.md#L572)

- D12–D21 — what this slice intentionally left for future slices.
  [`deferred-work.md:35`](deferred-work.md#L35)

**Settings & data freshness**

- `MacroConfig.vix_close` bounded `(0, 200]` — typo-protected (P7).
  [`config.py:97`](../../src/csp/config.py#L97)

- `OratsStrike.dte > 0` — kills 0DTE / ZeroDivision risk at the model boundary (P3).
  [`core.py:78`](../../src/csp/models/core.py#L78)

- `as_of` resolved via Berlin TZ — replaces naive `date.today()` (P11).
  [`idea.py:34`](../../src/csp/idea.py#L34)

- `[macro]` settings block — placeholder until FMP-client slice (D13/D17).
  [`settings.toml`](../../config/settings.toml)

**Tests & regression contract**

- NOW-78 historical: 3-rule-fail + `tradeDate` query-param assertion (P4) — pins the regression contract through the public surface.
  [`test_idea.py:421`](../../tests/test_idea.py#L421)

- Override-WARN test simplified + tightened on actual German emitted phrase (P5).
  [`test_idea.py:328`](../../tests/test_idea.py#L328)

- Live happy path with `delta == -0.20` and `strike == Decimal("81")` pinning (P10) + Berlin-TZ `as_of` assertion (P11).
  [`test_idea.py:466`](../../tests/test_idea.py#L466)

- `as_of`-in-future raises `ValueError` (P6 coverage).
  [`test_idea.py:555`](../../tests/test_idea.py#L555)
