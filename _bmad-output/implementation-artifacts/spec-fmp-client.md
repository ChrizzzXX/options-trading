---
title: 'csp.FmpClient + csp.macro_snapshot — live VIX (slice 5)'
type: 'feature'
created: '2026-04-29'
status: 'done'
baseline_commit: '51a4005'
context:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/project-context.md'
  - '_bmad-output/implementation-artifacts/spec-orats-client.md'
---

<frozen-after-approval reason="YOLO batch — Chris waived approval">

## Intent

**Problem:** `[macro] vix_close = 18.7` in `settings.toml` is a static placeholder that lies if the real VIX moves. Pflichtregel #1 (`VIX ≥ 20` OR IVR-leg) silently passes/fails wrong-headedly. Deferred items D13 + D17 explicitly land with this slice.

**Approach:** Mirror slice-2's `OratsClient` pattern. New `FmpClient` against FMP `/stable/...` namespace. Add `csp.macro_snapshot(*, as_of=None)` public helper that prefers a live FMP fetch but falls back to `settings.macro.vix_close` if `FMP_KEY` is unset OR FMP errors. `idea` + `scan` continue working without FMP_KEY (today's behavior); when key is set, both internally upgrade to live macro.

## Boundaries & Constraints

**Always:**
- Public surface: `csp.FmpClient`, `csp.fmp_health_check`, `csp.macro_snapshot`, `csp.FMPDataError`, `csp.FMPEmptyDataError`. Sync `macro_snapshot(*, as_of: date | None = None) -> MacroSnapshot`.
- Endpoints: `/stable/quote?symbol=^VIX` (live), `/stable/historical-price-eod/light?symbol=^VIX&from=YYYY-MM-DD&to=YYYY-MM-DD` (historical). Both respond with `[{"symbol": "^VIX", "price": 18.7, ...}]` or `[{"date": "2026-04-24", "close": 18.7, ...}]` shape.
- Auth via `apikey` query param.
- Retry policy mirrors `OratsClient` (3 attempts, exp backoff, retry on 5xx/429/transport, 4xx immediate).
- `_redact_text` covers `apikey=`, already wired in `clients/orats.py`. New `_async_scan` / `_async_idea` macro-fetch path uses the SAME shared `httpx.AsyncClient`.
- Fallback chain: `FMP_KEY` set → live fetch → on `FMPDataError`/`FMPEmptyDataError` → WARN log + return `MacroSnapshot.from_settings(settings)`. `FMP_KEY` unset → return `MacroSnapshot.from_settings(settings)` immediately, no HTTP.
- All thresholds via Settings; no hardcoded magic.

**Ask First:** N/A — YOLO batch.

**Never:**
- No FMP options endpoints — they're dead (project-context.md: "FMP options endpoints are dead, deprecated 2025-08-31").
- No `/api/v3/` or `/api/v4/` calls — `/stable/` namespace only.
- No live HTTP in tests — respx-mocked. (Real cassette deferred until `FMP_KEY` is recorded.)
- No `pandas` — return `float` for `vix_close`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Live happy | `FMP_KEY` set, `/stable/quote` → 200, list with one entry | `MacroSnapshot(vix_close=<live>)` | N/A |
| Historical happy | `as_of=date(2026,4,24)`, `/stable/historical-price-eod/light` → 200, list with one row | `MacroSnapshot(vix_close=<row.close>)` | N/A |
| FMP 4xx | bad key | — | `FMPDataError` raised inside client; `macro_snapshot` catches → fallback + WARN |
| FMP 5xx (3×) | vendor outage | — | `FMPDataError(status=5xx)` after retries; fallback + WARN |
| FMP empty data | `data: []` | — | `FMPEmptyDataError`; fallback + WARN |
| No FMP_KEY | settings.fmp_key empty | `MacroSnapshot.from_settings(settings)` | no HTTP, no WARN |
| Future `as_of` | `as_of > today` | — | `ValueError` at `macro_snapshot` boundary (mirror `idea`/`scan`) |

</frozen-after-approval>

## Code Map

- `src/csp/clients/fmp.py` — new — `FmpClient` (mirror `OratsClient`).
- `src/csp/exceptions.py` — add `FMPDataError`, `FMPEmptyDataError`.
- `src/csp/health.py` — add `fmp_health_check`.
- `src/csp/macro.py` — new — `csp.macro_snapshot(*, as_of=None)` + async `_fetch_macro(...)` helper used by `idea`/`scan` internals.
- `src/csp/idea.py` + `src/csp/scan.py` — replace direct `MacroSnapshot(vix_close=settings.macro.vix_close)` with `await _fetch_macro(...)` using the shared `httpx.AsyncClient`.
- `src/csp/config.py` — add `Settings.fmp_key: SecretStr`, `Settings.fmp_base_url: str = "https://financialmodelingprep.com/api"`.
- `src/csp/__init__.py` — re-export new public symbols.
- `tests/test_fmp_client.py` — new — unit + respx integration.
- `tests/test_macro.py` — new — fallback chain, key-unset, live-success.

## Tasks & Acceptance

**Execution:** see Code Map. State machine: write code, run gates, commit.

**Acceptance:**
- `csp.macro_snapshot()` returns `MacroSnapshot(vix_close=18.7)` (settings fallback) when `FMP_KEY` unset; respx assertion: zero HTTP calls.
- `csp.macro_snapshot()` with `FMP_KEY` set + respx-mocked `/stable/quote` returning `[{"symbol":"^VIX","price":17.45,...}]` → `MacroSnapshot(vix_close=17.45)`.
- `csp.macro_snapshot(as_of=date(2026,4,24))` with respx-mocked `/stable/historical-price-eod/light` returning a row with `close=23.1` → `MacroSnapshot(vix_close=23.1)`.
- `csp.scan()` with `FMP_KEY` set + macro mocks: shared `httpx.AsyncClient` carries both ORATS and FMP traffic (single-client invariant from slice 4 preserved).
- Coverage: `src/csp/clients/fmp.py` + `src/csp/macro.py` ≥ 95 %; overall ≥ 80 %.
- Pre-commit gates clean (ruff, format, mypy --strict, pytest).
- D13, D17 closed in `deferred-work.md`; new D29 (real-FMP-cassette) opened.

## Verification

- `uv run pytest -q tests/test_fmp_client.py tests/test_macro.py` — passes.
- `uv run pytest -q` — full suite passes; coverage ≥ 80%.
- `uv run mypy --strict src` — clean.
- Manual smoke: `uv run python -c "import csp; print(csp.macro_snapshot())"` (with or without `FMP_KEY` in `.env`).
