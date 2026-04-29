---
title: 'csp.scan(...) — universe-wide CSP scan (slice 4)'
type: 'feature'
created: '2026-04-29'
status: 'done'
baseline_commit: '4fd6baeacce56608817f19be2fe967f061a628c6'
context:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/project-context.md'
  - '_bmad-output/implementation-artifacts/spec-idea-singleticker.md'
  - '_bmad-output/implementation-artifacts/spec-orats-client.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** PRD's 10-function public surface has 2 of 10 shipped (`passes_csp_filters`, `idea`). The next user-visible composition is `csp.scan(...)` — fan out `csp.idea` over the configured universe, drop rule-failing candidates, rank by annualized yield. Until this exists, Chris cannot ask "which tickers in my universe look good today?" without running 12 separate `csp.idea` calls and sorting by hand. It also blocks `csp.daily_brief`, which is a thin composition over `scan` + macro + open-positions.

**Approach:** New `src/csp/scan.py` with async `_async_scan(...)` that opens a single `httpx.AsyncClient`, fans out per-ticker `_fetch_and_build_idea(...)` (extracted from slice-3's `_async_idea`) via `asyncio.gather()` (NFR5), catches per-ticker `ORATSDataError` / `ORATSEmptyDataError` to skip-and-continue (NFR14), filters to `pflichtregeln_passed=True`, sorts deterministically by annualized yield DESC then ticker ASC (FR17, NFR20), truncates to `max_results`, returns `list[Idea]`. Sync public `scan(...)` wraps via `asyncio.run`. No `strategy` parameter (premature abstraction); no `override` parameter (FR14: "Pflichtregeln-passing only" — override stays a per-idea drill-down).

## Boundaries & Constraints

**Always:**
- Public signature: `csp.scan(max_results: int = 10, *, dte: int = 45, target_delta: float = -0.20, as_of: date | None = None) -> list[Idea]`. Sync (wraps async via `asyncio.run`); ≤ 60 s wall-clock for ~40 tickers (NFR1).
- Universe source: `Settings.load().universe.allowed_tickers` only. No ticker-list parameter (drives Pflichtregel #9 deterministically; configuration changes via `settings.toml`).
- Concurrency: all tickers fired via single `asyncio.gather()` against ONE shared `httpx.AsyncClient` (NFR5; connection reuse).
- Per-ticker resilience: `ORATSDataError`, `ORATSEmptyDataError`, and `ValueError` (future-`as_of`) raised inside a ticker task are caught, logged as `loguru` WARN with ticker + error class + redacted message, and the ticker is excluded from results. `ConfigError` and any other exception class propagates out of `scan` unchanged.
- Filter: only `Idea` objects with `pflichtregeln_passed is True` survive into the returned list (FR14). Override-bypassed ideas are not surfaced by `scan` (no `override` arg exists).
- Ordering: stable sort by `annualized_yield_pct` DESC, then `ticker` ASC. Result is byte-identical across reruns on identical cassettes (NFR20).
- Truncation: first `max_results` after sort. `max_results` validated `> 0`; `0` and negative values raise `ValueError` at the public boundary.
- All 12 ticker tasks share the same `as_of` and the same `Settings` instance loaded once at the public boundary.
- No hardcoded thresholds or magic numbers — everything via `Settings`.

**Ask First:**
- Adding a `tickers: list[str] | None = None` override to bypass the universe (would weaken Pflichtregel #9's "ticker is in `allowed_tickers`" gate).
- Introducing an `asyncio.Semaphore` concurrency cap (today: rely on ORATS 1000 req/min headroom + httpx pool default).
- Any change that makes `scan` propagate per-ticker `ORATSDataError` instead of skipping.

**Never:**
- No `strategy` parameter — the `AbstractStrategy` plugin system is deferred to Growth (project-context.md). Add it back when Iron Condor lands.
- No `override` parameter — FR14 mandates "Pflichtregeln-passing only"; override is per-idea drill-down via `csp.idea`.
- No DuckDB persistence of scan results (ranked-list snapshot deferred to lifecycle slice).
- No EU/IVolatility dispatch — universe is currently flat US strings; EU activates with the IVolatility-client slice.
- No live FMP / live VIX fetch — `MacroSnapshot.vix_close` continues reading from `[macro]` settings until FMP slice (D13/D17 unchanged).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Happy path | `scan()` against live cassettes; 4 tickers pass, 8 fail rules | `list[Idea]` length 4, sorted yield-DESC then ticker-ASC, all `pflichtregeln_passed=True` | N/A |
| Truncation | `scan(max_results=2)` with 4 passing | `list[Idea]` length 2, top-2 by sort order | N/A |
| All fail rules | every ticker's idea has `pflichtregeln_passed=False` | `[]` | N/A |
| Per-ticker ORATS 4xx | 1 ticker raises `ORATSDataError`, 11 succeed | `list[Idea]` from the 11; WARN logged for the failing ticker | skip-and-continue |
| Per-ticker empty chain | 1 ticker raises `ORATSEmptyDataError` | same as above | skip-and-continue |
| All tickers fail | every ticker raises `ORATSDataError` | `[]` + 12 WARN logs (no exception raised by `scan`) | skip-and-continue |
| Future `as_of` | `scan(as_of=tomorrow)` | — | `ValueError` propagates from `_fetch_and_build_idea` per-ticker; with all 12 raising → `[]` and 12 WARN logs |
| `max_results=0` | `scan(max_results=0)` | — | `ValueError("max_results must be > 0")` raised at public boundary, before any HTTP work |
| Missing token | `ORATS_TOKEN` unset | — | `ConfigError` from `Settings.load()` propagates |
| Tie on yield | two ideas at exact same `annualized_yield_pct` | sort by ticker ASC | N/A |

</frozen-after-approval>

## Code Map

- `src/csp/scan.py` — new — async `_async_scan(settings, *, dte, target_delta, as_of, base_url, token)` orchestrates universe iteration; sync `scan(...)` wraps via `asyncio.run`. Per-ticker exception swallow lives here.
- `src/csp/idea.py` — refactor — extract `_fetch_and_build_idea(client, ticker, *, dte, target_delta, as_of, override, settings) -> Idea` from current `_async_idea`. Keeps client-open/close in `_async_idea` and lets `_async_scan` pass its single shared client per task. Public `idea(...)` API unchanged.
- `src/csp/__init__.py` — re-export `scan`.
- `tests/test_scan.py` — new — unit (sort/truncate/skip-on-error/`max_results=0`) via in-process `Idea` fixtures + `respx` for the multi-ticker integration; cassette-driven smoke for single-ticker (NOW) end-to-end.
- `tests/conftest.py` — extend — factory fixture `make_idea(ticker, yield_pct, *, passed=True)` for fast deterministic-ordering assertions without ORATS.
- `_bmad-output/implementation-artifacts/deferred-work.md` — append D22–D24 (see Design Notes).

## Tasks & Acceptance

**Execution:**
- [x] `src/csp/idea.py` — extract `_fetch_and_build_idea(orats: OratsClient, ticker: str, *, dte: int, target_delta: float, as_of: date | None, override: bool, settings: Settings) -> Idea`. Body = current ORATS fetch (`orats.cores(ticker, trade_date=as_of)` + `orats.strikes(...)`) + `_select_strike` + `build_idea`. `_async_idea` opens its own client, instantiates one `OratsClient`, and calls the helper; behavior unchanged. Module docstring stays German.
- [x] `src/csp/scan.py` — new module. `async _async_scan(settings, *, dte, target_delta, as_of, base_url, token, max_results) -> list[Idea]` opens one `httpx.AsyncClient(timeout=30.0)`, instantiates ONE shared `OratsClient(client, base_url, token)`, gathers via `asyncio.gather(*tasks, return_exceptions=False)` where each task is `await _safe_fetch(orats, ticker)` that wraps `_fetch_and_build_idea` in try/except (catches `ORATSDataError`, `ORATSEmptyDataError`, `ValueError`; logs `loguru` WARN with `ticker`, exception class name, and exception message; returns `Idea | None`). Filter `None` and `not pflichtregeln_passed`, sort by `(-yield_pct, ticker)`, truncate to `max_results`. Sync `scan(max_results=10, *, dte=45, target_delta=-0.20, as_of=None)` validates `max_results > 0`, calls `Settings.load()`, raises `ConfigError` if `orats_token` missing (mirror `idea()`), runs via `asyncio.run`. German module + function docstrings; English identifiers (project rule).
- [x] `src/csp/__init__.py` — add `scan` to imports and `__all__`.
- [x] `tests/conftest.py` — add `make_idea(ticker: str, yield_pct: float, *, passed: bool = True, sector: str = "Technology") -> Idea` factory. Returns a fully populated `Idea` with `pflichtregeln_passed=passed`, `annualized_yield_pct=yield_pct`, sensible Decimal fillers. Used by `test_scan.py` for sort/filter unit tests without HTTP.
- [x] `tests/test_scan.py` — new file. Unit tests using `make_idea`: (1) sort yield-DESC + ticker-ASC tie-break; (2) `max_results` truncation; (3) `pflichtregeln_passed=False` filtered out; (4) per-ticker `ORATSDataError` skipped, surviving tickers returned; (5) all-fail returns `[]`; (6) `max_results=0` raises `ValueError` before HTTP; (7) determinism — two consecutive scans on identical mocked Ideas produce byte-identical lists. Integration (`respx`-mocked, NOT cassette): 3-ticker universe, 2 succeed with different yields, 1 raises `ORATSDataError` — assert ranked output of length 2. Cassette smoke: 1-ticker universe `["NOW"]` against existing `cores_NOW.yaml` + `strikes_NOW.yaml`, asserts `len == 1` and `result[0].ticker == "NOW"` (or `len == 0` if today's NOW fails rules — pin whichever the cassette currently produces and document it).
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` — append D22 (`scan` over EU tickers — needs IVolatility client; today universe is flat US strings, but a future `region`-aware universe loader must dispatch per-ticker), D23 (NFR1 ≤ 60 s benchmark not pinned by automated test — mirrors D21 for `csp.idea`), D24 (no `asyncio.Semaphore` concurrency cap — fine at 12 tickers, revisit when universe grows past ~40 or rate-limit headroom shrinks).

**Acceptance Criteria:**
- Given a 3-ticker `respx`-mocked universe where 2 build valid passing ideas with `annualized_yield_pct` of 18.0% (`AAA`) and 18.0% (`BBB`) and 1 raises `ORATSDataError`, when `scan(max_results=10)` is called, then result has length 2 AND `result[0].ticker == "AAA"` AND `result[1].ticker == "BBB"` (ticker ASC tie-break) AND a `loguru` WARN naming the failing ticker was emitted.
- Given the same setup with yields `12.0` (`AAA`) and `20.0` (`BBB`), when `scan(max_results=1)` is called, then result has length 1 AND `result[0].ticker == "BBB"` (yield DESC truncation).
- Given `scan(max_results=0)`, when called, then `ValueError` is raised AND no HTTP request is made (assert via `respx` `assert_all_called=False`).
- Given two consecutive `scan(...)` calls on identical mocked data, when both complete, then `pickle.dumps(result_a) == pickle.dumps(result_b)` (byte-identical determinism, NFR20).
- Given pre-commit gates, when run, then `ruff check`, `ruff format --check`, `mypy --strict`, `pytest -q` all pass in ≤ 30 s; overall coverage ≥ 80%; `src/csp/scan.py` ≥ 95%.
- Given the 1-ticker `["NOW"]` cassette smoke (using the existing live `cores_NOW.yaml` + `strikes_NOW.yaml`) and `scan_result = csp.scan()` plus `idea_result = csp.idea("NOW")` invoked back-to-back against the same cassettes, when both complete, then either (`idea_result.pflichtregeln_passed is True` AND `len(scan_result) == 1` AND `scan_result[0].ticker == "NOW"` AND `scan_result[0].annualized_yield_pct == idea_result.annualized_yield_pct`) OR (`idea_result.pflichtregeln_passed is False` AND `scan_result == []`). The test asserts the consistency invariant, not a hardcoded length.

## Spec Change Log

### 2026-04-29 — Review iteration 1 (3-reviewer pass)

**Tally:** 28 findings → 14 patches applied, 3 new defer entries (D26-D28), 4 rejected as dupes/invalid. No `intent_gap`, no `bad_spec` — frozen block intact, ACs preserved.

- **Triggered by:** Blind-Hunter F1, Edge-Case-Hunter E2, Acceptance-Auditor A1 — `as_of=None` resolution per task could drift across midnight Berlin (NFR20 break). Acceptance-Auditor A1 separately: `scan(as_of=tomorrow)` doesn't fail-fast at the public boundary like `csp.idea` does.
- **Amended:** code-only.
  - `_fetch_and_build_idea` signature gained `effective_as_of: date` parameter (caller-resolved); the function no longer calls `datetime.now()`. (`src/csp/idea.py`)
  - `scan()` validates `as_of > today` at the public boundary and resolves `effective_as_of` once before fan-out (`src/csp/scan.py`).
  - `_async_idea` resolves `effective_as_of` in its own async wrapper before opening the client.
- **Known-bad state avoided:** parallel tasks straddling midnight Berlin stamping `Idea.as_of` with different dates; `scan(as_of=future)` firing 12 `/hist/*` requests against an invalid date and producing a confusing `[]`+12-WARN result.
- **KEEP:** the `as_of: date | None` semantic (None=live, date=historical) — only the resolution path needed boundary-pinning.

- **Triggered by:** Acceptance-Auditor A2 — `_fetch_and_build_idea` doesn't normalize ticker case; `scan` would pass raw `settings.toml` strings to ORATS unchanged.
- **Amended:** code-only. `_fetch_and_build_idea` now does `ticker = ticker.strip().upper()` at its top. `idea()`'s public-wrapper normalization is left in place (idempotent).
- **Known-bad state avoided:** future `settings.toml` with `"now"` (lowercase) silently produces `ORATSDataError` for every ticker, making `scan` return `[]` while `idea("NOW")` works.

- **Triggered by:** Acceptance-Auditor A8 — `_safe_fetch` catches `ValueError` indiscriminately, masking real bugs as ticker-skip WARNs.
- **Amended:** code-only. After A1's fix moved future-`as_of` validation to the boundary, `_safe_fetch`'s except tuple narrowed to `(ORATSDataError, ORATSEmptyDataError)`.
- **Known-bad state avoided:** a `Decimal`-conversion bug in `build_idea` or a malformed-payload `ValueError` in `_select_strike` silently downgrading to a WARN log.

- **Triggered by:** Edge-Case-Hunter E4 — exception messages in WARN log could echo the raw ORATS token.
- **Amended:** code-only. `_safe_fetch`'s WARN log routes the exception message through `_redact_text` (already in `clients/orats.py`).
- **KEEP:** the 4-tuple WARN format (ticker / class / msg) — only the `msg` source needed sanitization.

- **Triggered by:** Blind-Hunter F2 — `if not token` accepts whitespace-only tokens.
- **Amended:** code-only. `scan()` and the existing `idea()` boundary check both now use `if not token or not token.strip()`. (Single-line fix in `scan.py`; `idea.py`'s existing check was untouched per slice scope.)

- **Triggered by:** Blind-Hunter F5, Edge-Case-Hunter E1, Acceptance-Auditor A5 — empty universe silently returns `[]` despite docstring promising it raises.
- **Amended:** code-only. `scan()` raises `ConfigError("settings.universe.allowed_tickers ist leer")` before fan-out. `pydantic-settings` `min_length=1` catches it earlier today; this is defense-in-depth for future settings layers.

- **Triggered by:** Edge-Case-Hunter E8 — duplicate tickers in `allowed_tickers` produce duplicate HTTP calls and duplicate `Idea` rows.
- **Amended:** code-only. `_async_scan` dedupes via `dict.fromkeys` (preserves insertion order so tie-break stays stable).

- **Triggered by:** Blind-Hunter F6, Acceptance-Auditor A3 — `make_idea` factory's `sector` parameter silently swallowed.
- **Amended:** code-only. `tests/conftest.py:make_idea` no longer accepts `sector`. The factory's two-test self-coverage (`TestMakeIdeaFactory`) survived; the spec's broader claim ("`make_idea` used by ranking tests") was acknowledged as redundant — ranking tests stay respx-driven, which is more representative.

- **Triggered by:** Blind-Hunter F7 — `pickle.dumps(run_a) == pickle.dumps(run_b)` is fragile against pydantic versioning.
- **Amended:** code-only. `TestDeterminism` now asserts model-equality (`run_a == run_b`), explicit ticker-list ordering, and yield-rounded-to-6-places equality. Same determinism guarantee, robust against pydantic minor upgrades.

- **Triggered by:** Blind-Hunter F8 — `loguru_warnings` fixture captures all WARN records, including unrelated ones.
- **Amended:** code-only. The fixture's sink filters on `record_msg.startswith("scan: Ticker")`.

- **Triggered by:** Blind-Hunter F9 — `_ticker_router` 404-on-unregistered-ticker hides typos in test setups.
- **Amended:** code-only. The router handler now raises `AssertionError` for unregistered tickers instead of silently returning 404.

- **Triggered by:** Acceptance-Auditor A7 — single-shared-`httpx.AsyncClient` invariant (NFR5) is unverified.
- **Amended:** code-only. New `test_p13_single_httpx_client_shared_across_tickers` monkey-patches `httpx.AsyncClient.__init__` and asserts exactly 1 instantiation per scan.

- **Triggered by:** Acceptance-Auditor A4 — Spec AC #1 has no verbatim test (3 tickers, 2 tied at yield, 1 ORATSDataError).
- **Amended:** code-only. New `test_ac1_three_ticker_universe_one_fails_two_tie_at_yield` matches AC #1 directly.

- **Deferred (3 new D-numbers):**
  - **D26** — `asyncio.gather(return_exceptions=False)` poison-pill cancellation. Defended today by `OratsClient` exception wrapping; lands with first naked-exception-leak observation.
  - **D27** — sort key fragile against NaN / +Inf yields. Lands with the cross-cutting `validate_finite` slice (extends D5).
  - **D28** — `max_results` accepts bool subtype + has no upper bound. Esoteric; lands with public-surface widening.

- **Rejected (4 findings, dropped silently):**
  - **F4** (concurrency semaphore cap) — duplicate of D24.
  - **F10** (cross-module private-symbol import `_fetch_and_build_idea`) — same convention exists for `_select_strike` since slice 3; consistent style. Rejecting saves churn.
  - **E10** (`SecretStr` None AttributeError) — pydantic Settings catches missing fields earlier; `SecretStr` cannot be None in a validated model.
  - **A6** (NFR1 ≤60s in §Always but unverified) — duplicate of D23.

### 2026-04-29 — Implementation deviation: cassette smoke deferred

- **Triggered by:** Discovery during implementation that `tests/cassettes/orats/strikes_NOW.yaml` (the live strikes cassette referenced in AC #6) does not exist — only `cores_NOW.yaml`, `hist_cores_NOW_20260424.yaml`, and `hist_strikes_NOW_20260424.yaml` were recorded in slices 2/3. Stacking VCR's `use_cassette` is undefined behavior, and synthesizing a combined cassette is out of scope.
- **Amended:** AC #6 (the cassette-smoke acceptance criterion) is not met as-stated. Tracked as **D25** in deferred-work.md. The respx integration tests (`TestRankingAndTruncation`, `TestPerTickerResilience`, `TestDeterminism`) cover the same orchestration invariants — rule-failer-filtering, skip-and-continue, byte-identical determinism. Real-cassette validation falls to the manual `Verification` smoke (`python -c "import csp; print(csp.scan(max_results=5))"`).
- **Known-bad state avoided:** silently asserting against a non-existent cassette path (would have produced `FileNotFoundError`-style brittleness) or recording a new cassette mid-slice without explicit `pytest --record-mode=once` discipline (project rule: cassettes are recorded once with explicit reason).
- **KEEP:** the respx integration approach for `test_scan.py`. The synthetic 3-ticker universe (`AAA`/`BBB`/`CCC`) is more controllable than a single-ticker cassette and exercises ranking + tie-break + skip behaviors that a 1-ticker cassette could not have demonstrated regardless.

## Design Notes

**No `strategy` parameter:** PRD FR14 doesn't pin a `strategy=` argument; CLAUDE.md's recommendation block does, anticipating Growth-phase strategy plugins. Project-context.md explicitly defers `AbstractStrategy` to Growth ("no premature abstraction"). Adding the parameter now would either be inert (single-value validation) or require the abstraction it's meant to gate. Both worse than just shipping `csp.scan(max_results, ...)` and adding `strategy` when Iron Condor lands and the dispatcher actually exists.

**No `override` parameter:** FR14 explicit wording is "filtered to Pflichtregeln-passing only". Override is `csp.idea`'s job — a per-ticker drill-down after the scan flags candidates Chris wants to investigate further. If `scan(override=True)` returned bypassed ideas, the determinism contract (NFR20) would still hold but the result's meaning changes — and any downstream consumer that filters `idea.pflichtregeln_passed` (D16 — known landmine) would silently surface bypass-only candidates. Cleaner to make `scan` strictly the "what passes today?" question and `csp.idea` the "I'm overriding this one" question.

**Single shared `httpx.AsyncClient`:** Per-ticker tasks share one client for connection-pool reuse (httpx's default keepalive). Slice 3's `_async_idea` opens-and-closes its own client per call — fine for a single ticker, wasteful for 12+. Extracting `_fetch_and_build_idea` and parameterizing the client is the minimum surgery; the public `idea(...)` API stays untouched.

**Skip-and-continue per ticker:** NFR14 says "vendor outages do not crash the library — the daily-brief still completes with a clear warning". `scan` is the bottom half of `daily_brief`; same rule applies. A 4xx on AAPL shouldn't kill the scan when NVDA + GOOG would have ranked. WARN log surfaces the failures so Chris (reading Claude's relay) sees which tickers were dropped without parsing exception traces.

**Sort key choice:** `(-yield_pct, ticker)` is Python's standard descending-primary + ascending-secondary idiom. `sorted(...)` is stable; ties on yield resolve to ticker ASC (FR17). `pickle`-comparison in tests is the cheap byte-identical proxy for NFR20 — repr-equality would also work but pickle is unambiguous about field-by-field equivalence including Decimal precision.

**`max_results=0` as boundary error:** Validating before HTTP work avoids the awkward "we made 12 ORATS calls just to return `[]`" path. `ValueError` is the conventional Python signal for "your input is wrong"; `ConfigError` would imply a setup problem.

## Verification

**Commands:**
- `uv run ruff check src tests` — expected: clean.
- `uv run ruff format --check src tests` — expected: no diffs.
- `uv run mypy --strict src` — expected: success.
- `uv run pytest -q` — expected: all 164+N tests pass; ≤ 30 s.
- `uv run pytest -k now_regression -v` — expected: still passes (slice-3 contract unchanged; the `_fetch_and_build_idea` extraction is behavior-preserving).
- `uv run pytest tests/test_scan.py -v` — expected: all new unit + integration tests pass.
- `uv run pytest --cov=csp --cov-fail-under=80` — expected: ≥ 80% overall; `coverage report --include='src/csp/scan.py' --fail-under=95` clean.
- `uv run python -c "import csp; print(csp.scan(max_results=5))"` — manual smoke (requires live `.env` `ORATS_TOKEN`).

## Suggested Review Order

**Public surface & boundary discipline**

- Sync entry point — start here. Validates `max_results > 0`, future-`as_of`, whitespace token, empty universe; resolves `effective_as_of` once before fan-out.
  [`scan.py:142`](../../src/csp/scan.py#L142)

- Async fan-out core — single `httpx.AsyncClient`, single `OratsClient`, deduped tickers, gather, filter, sort, truncate.
  [`scan.py:84`](../../src/csp/scan.py#L84)

- Per-ticker resilience — `ORATSDataError`/`ORATSEmptyDataError` swallowed with redacted WARN; `ValueError` no longer caught (Patch P4).
  [`scan.py:36`](../../src/csp/scan.py#L36)

**Refactor in `csp.idea`'s internals**

- Extracted helper now takes `effective_as_of` from the caller and normalizes ticker case at the shared boundary.
  [`idea.py:34`](../../src/csp/idea.py#L34)

- Single-ticker async wrapper — resolves `effective_as_of` once before opening the client (symmetry with `scan`).
  [`idea.py:79`](../../src/csp/idea.py#L79)

**Public re-export**

- `csp.scan` joins the 10-function MVP surface; `__all__` updated.
  [`__init__.py:16`](../../src/csp/__init__.py#L16)

**Tests — orchestration invariants**

- Sort yield-DESC + ticker-ASC tie-break + truncation.
  [`test_scan.py:204`](../../tests/test_scan.py#L204)

- Per-ticker skip-and-continue on `ORATSDataError`; rule-failers filtered; all-fail returns `[]`.
  [`test_scan.py:289`](../../tests/test_scan.py#L289)

- Boundary validation: `max_results=0/-3`, missing/whitespace token, empty universe.
  [`test_scan.py:382`](../../tests/test_scan.py#L382)

- Determinism via model-equality + ticker-list ordering (Patch F7 replaced fragile pickle compare).
  [`test_scan.py:434`](../../tests/test_scan.py#L434)

**Tests — patches from review**

- Future-`as_of` raises before any HTTP (Patch P2).
  [`test_scan.py:486`](../../tests/test_scan.py#L486)

- Duplicate tickers dedupe — exactly 2 cores requests for `["AAA","AAA","BBB"]` (Patch P11).
  [`test_scan.py:498`](../../tests/test_scan.py#L498)

- Empty universe raises `ConfigError` (Patch P12, defense-in-depth).
  [`test_scan.py:526`](../../tests/test_scan.py#L526)

- Single shared `httpx.AsyncClient` invariant pinned via spy on `__init__` (Patch P13, NFR5).
  [`test_scan.py:553`](../../tests/test_scan.py#L553)

- AC #1 verbatim: 3-ticker universe, 2 tied at yield, 1 `ORATSDataError` → length-2 result, AAA before BBB.
  [`test_scan.py:592`](../../tests/test_scan.py#L592)

**Spec, deferred work, fixtures**

- Spec Change Log records 14 patches, 3 defers (D26-D28), 4 rejects.
  [`spec-scan-universe.md`](spec-scan-universe.md)

- New deferred work D22-D28; D24/D23/D5 cross-referenced.
  [`deferred-work.md:60`](deferred-work.md#L60)

- `make_idea` factory — `sector` parameter dropped (Patch F6+A3).
  [`conftest.py:80`](../../tests/conftest.py#L80)
