---
title: 'ORATS Client + Real NOW-78 Cassette'
type: 'feature'
created: '2026-04-29'
status: 'done'
implementation_commit: 'f7068e0'
baseline_commit: '1e7f126'
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/planning-artifacts/prd.md'
  - '{project-root}/_bmad-output/implementation-artifacts/spec-pflichtregeln-gate.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The Pflichtregeln gate works against synthetic fixtures. PRD FR29 / NFR18 require `pytest -k now_regression` to be a real determinism contract — `csp.scan()` must reproduce NOW-78 from a recorded ORATS cassette. The gate slice (1) explicitly deferred this (D1) until vendor I/O exists.

**Approach:** Build a single async ORATS client (`httpx.AsyncClient`, retry policy, typed exceptions); record real cassettes for `/cores` and `/hist/strikes` against ticker NOW on 2026-04-24 (the plan-tier probe today confirmed both endpoints return 200); replace the synthetic `NOW_CORE`/`NOW_STRIKE` fixtures with cassette-derived factory functions; expose `csp.orats_health_check("NOW")` as the public entry point that records the cassette and validates the parse + gate end-to-end.

## Boundaries & Constraints

**Always:**
- `OratsClient.__init__(client: httpx.AsyncClient, *, base_url: str, token: str)` — DI, never instantiates `httpx.AsyncClient` internally.
- Methods return parsed Pydantic models, not raw dicts: `cores(ticker) -> OratsCore`, `strikes(ticker, *, trade_date: date | None = None) -> list[OratsStrike]`, `ivrank(ticker)`, `summaries(ticker)`.
- Retry: 3 attempts, exponential backoff (1 s / 2 s / 4 s) for 5xx + 429; 4xx raises immediately as `ORATSDataError(status, body, url_redacted)` with no token in the message.
- Public surface: `from csp import OratsClient, ORATSDataError, orats_health_check`. `orats_health_check("NOW") -> OratsCore` is the cassette-recording entry; wraps async via `asyncio.run`.
- `OratsCore` and `OratsStrike` gain `Field(alias="camelCase")` for every API field, plus `model_config = ConfigDict(populate_by_name=True, extra="ignore")` (ORATS adds fields over time — `extra="ignore"` is the right policy for vendor responses).
- VCR cassettes scrub `token` and `apikey` query params via `filter_query_parameters=["token", "apikey"]`. No live HTTP in tests once cassette is recorded.
- mypy strict + ruff clean. Coverage: ≥ 90 % on `src/csp/clients/orats.py`, ≥ 80 % overall.
- `now_regression` test re-points to the cassette-derived NOW values; it now asserts whatever the real gate verdict is for NOW on 2026-04-24 (could be pass, could be fail — the assertion captures **the truth**, not aspiration).

**Ask First:**
- Any new dependency beyond `httpx`, `pytest-vcr`, `respx` (dev).
- Changing `OratsClient` constructor signature beyond the `Always` form.
- Re-recording an existing cassette (cassettes are the regression contract; re-recording requires explicit reason in the commit message per project-context.md).
- Touching FMP, IVolatility, Sheets clients (other slices).

**Never:**
- Live HTTP inside `pytest -q` runs. The one-time recording happens via `pytest --record-mode=once` on the developer machine, not in CI.
- `requests`, `urllib3.urlopen`, `aiohttp` — only `httpx`.
- Token / .env values in any tracked file. `.env` stays gitignored; cassette YAML stays scrubbed.
- Universe scan, `csp.idea(ticker)`, `csp.scan(...)`, daily-brief — those land in slice 3+.
- Actual rate-limiter implementation. Surface the 1 000 req/min constant and document; throttling lands with the universe-scan slice.

## I/O & Edge-Case Matrix

| Scenario | Input | Expected | Notes |
|---|---|---|---|
| Happy path: cores | `cores("NOW")` against cassette | `OratsCore` parsed from real 2026-04-28 snapshot | Aliases ingest camelCase JSON |
| Happy path: hist strikes | `strikes("NOW", trade_date=date(2026, 4, 24))` against cassette | `list[OratsStrike]` of all strikes that day | DTE-55 entry locatable for NOW-78 |
| 4xx raises immediately | `respx` mock returns 401 | `ORATSDataError` with status=401, body in message, **no token** in message | Inspect raised string |
| 5xx triggers retry then raises | `respx` returns 503 three times | Three attempts (verify call count), `ORATSDataError` with status=503 | Backoff sleeps mocked via `freezegun` or zeroed via `httpx.Timeout` injection |
| 429 triggers retry then succeeds | `respx` returns 429 then 200 | Returns parsed model on second attempt | |
| Token never in cassette | Recorded YAML contains `<REDACTED>` (or vcr scrub placeholder) wherever the URL had `token=…` | Cassette diff contains zero matches for the live token | grep assertion in test |
| `now_regression` real-data | Cassette-derived `OratsCore` + `OratsStrike` (NOW-78 row) into `passes_csp_filters` | Test asserts the **actual** verdict (pass or fail with specific reasons); fixture metadata records spot/delta/IVR/spread from the cassette | If gate fails, that's the real truth; spec change log captures it |
| Public re-export | `import csp; csp.OratsClient; csp.orats_health_check; csp.ORATSDataError` | All three resolve without error | |

</frozen-after-approval>

## Code Map

- `pyproject.toml` — add `httpx>=0.27` (runtime), `pytest-vcr>=1.0.2`, `respx>=0.20` (dev).
- `src/csp/exceptions.py` — add `ORATSDataError(Exception)` carrying `status: int`, `body: str`, `url_redacted: str`.
- `src/csp/clients/__init__.py` — new package marker; re-exports `OratsClient`.
- `src/csp/clients/orats.py` — `OratsClient` class; `RATE_LIMIT_PER_MIN = 1_000` module constant; private `_request_with_retry()` helper handling backoff and exception mapping; URL builder that places token in query string but a `_redact_url()` helper for exception messages.
- `src/csp/health.py` — `orats_health_check(ticker: str) -> OratsCore`; opens an `httpx.AsyncClient` via context manager, instantiates `OratsClient`, fetches `cores(ticker)`, returns the model.
- `src/csp/__init__.py` — extend re-exports: `OratsClient`, `orats_health_check`, `ORATSDataError`.
- `src/csp/models/core.py` — extend `OratsCore`/`OratsStrike` with `Field(alias=…)` for every camelCase field documented in project-context vendor-gotchas; add `model_config = ConfigDict(populate_by_name=True, extra="ignore")`. Existing test instantiations (`OratsCore(ticker=…, …)` keyword form) still work because Python field names are unchanged.
- `tests/conftest.py` — add VCR `vcr_config` fixture: `record_mode="none"` for normal runs, `filter_query_parameters=["token", "apikey"]`, `cassette_library_dir="tests/cassettes/orats"`. Add `recording` opt-in fixture for the one-time recording job.
- `tests/test_orats_client.py` — new file: unit tests with `respx` (retry on 5xx, retry on 429, immediate raise on 4xx, token redaction in exception message), integration tests with the cassette (cores parse, hist-strikes parse for 2026-04-24).
- `tests/cassettes/orats/cores_NOW.yaml`, `tests/cassettes/orats/hist_strikes_NOW_20260424.yaml` — recorded once via `uv run pytest --record-mode=once tests/test_orats_client.py::TestRecording`.
- `tests/fixtures/now_2026_04_24.py` — replace the hardcoded `NOW_CORE`/`NOW_STRIKE` with `_load_now_core_from_cassette()` / `_load_now_78_strike_from_cassette()` factory functions parsing the YAML at module import. Each factory's docstring records the cassette path + recording date.
- `tests/test_pflichtregeln.py` — `TestNowRegression.test_now_78_passes_all_rules` becomes `test_now_78_real_gate_verdict`: asserts the actual `(passed, reasons)` tuple based on the real cassette data. If real NOW-78 fails one or more rules, the assertion explicitly captures that — spec change log notes the reconciliation.
- `_bmad-output/project-context.md` — amend "Vendor gotchas / ORATS unauthorized endpoints" to remove `/datav2/hist/dailyPrice` from the unauthorized list (probe today returned 200 for `/hist/strikes` — verify the others empirically before unblocking them in the doc).

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml` — add `httpx`, `pytest-vcr`, `respx`; `uv lock`
- [x] `src/csp/exceptions.py` — `ORATSDataError`
- [x] `src/csp/models/core.py` — Field aliases + `populate_by_name=True` + `extra="ignore"` on `OratsCore` and `OratsStrike`
- [x] `src/csp/clients/__init__.py` + `src/csp/clients/orats.py` — `OratsClient` + `_request_with_retry` + `_redact_url`
- [x] `src/csp/health.py` — `orats_health_check`
- [x] `src/csp/__init__.py` — re-exports
- [x] `tests/conftest.py` — VCR config
- [x] `tests/test_orats_client.py` — unit tests (respx) + integration tests (cassette)
- [x] Record cassettes: `uv run pytest --vcr-record=once -k recording` (correct flag for pytest-vcr 1.0.2; not `--record-mode=once`)
- [x] `tests/fixtures/now_2026_04_24.py` — replace synthetic with cassette factory
- [x] `tests/test_pflichtregeln.py` — update `TestNowRegression` to assert the real gate verdict; spec-change-log the outcome
- [x] `_bmad-output/project-context.md` — vendor-gotchas amendment (hist endpoints reachable on this plan)
- [x] Single commit: `feat: ORATS client + real NOW cassette (closes D1)`

**Acceptance Criteria:**
- Given a fresh checkout (with the recorded cassettes committed), when `uv sync && uv run pytest`, then all tests pass and overall coverage stays ≥ 80 %; `src/csp/clients/orats.py` ≥ 90 %.
- Given a `respx` mock returning 503 three times, when `OratsClient.cores("NOW")` runs, then exactly 3 attempts are made and `ORATSDataError` is raised with `status=503`.
- Given a `respx` mock returning 401, when `OratsClient.cores("NOW")` runs, then exactly 1 attempt is made, `ORATSDataError` is raised, and the live token does **not** appear in the exception message or any captured log line.
- Given the cassette `cores_NOW.yaml`, when grepped, then the live token literal appears 0 times.
- Given the cassette `hist_strikes_NOW_20260424.yaml`, when parsed, then a strike with `dte` matching the NOW-78 candidate exists and its fields populate `OratsStrike` cleanly.
- Given `import csp`, when `csp.OratsClient`, `csp.orats_health_check`, `csp.ORATSDataError` are accessed, then all three resolve.
- `uv run ruff check src tests` and `uv run mypy --strict src` both exit 0.
- `pytest -k now_regression` runs against cassette-derived data and the assertion captures the real verdict (whatever it is — pass or fail-with-specific-reasons).

## Spec Change Log

- 2026-04-29 — Implementation complete. Live-probe today confirmed `/cores`, `/hist/cores` and `/hist/strikes` all return 200 on the current plan; the project-context.md note flagging `/hist/dailyPrice` (and the `/hist/*` family generically) as unauthorized was stale and has been amended.
- 2026-04-29 — **Reconciliation outcome — NOW-78 from 2026-04-24 fails 3 Pflichtregeln, not 0.** The synthetic fixture (Premium 4.30, DTE 55, daysToNextErn 30, Spread 0.04) was over-optimistic; the real ORATS data shows: putBid 2.70 / putAsk 2.85 (mid 2.775, **not** 4.30), DTE 56 (one day past dte_max 55), daysToNextErn 0 (earnings WAS 2026-04-24), and Spread 0.15 (3× the spread_max_usd of 0.05). The IVR (96 vs PRD's 94), spot (89.84), market cap (93.97 B USD), and put-delta (-0.221) all check out. `TestNowRegression` now asserts the exact list `["Pflichtregel 3 — DTE 56 außerhalb [30, 55]", "Pflichtregel 5 — Earnings in 0 Tagen (< 8)", "Pflichtregel 6 — Liquidität ungenügend: Spread 0,15 USD > 0,05 USD"]`. **This is the determinism contract going forward** — improving the regression anchor (e.g., picking a different historical date where NOW-78 actually passed) is a separate decision that should ride into a future spec, not a quiet fix.
- 2026-04-29 — Three cassettes are committed (Code Map listed two): `cores_NOW.yaml` (current snapshot for parse-shape testing), `hist_strikes_NOW_20260424.yaml` (historical strike chain for the regression), and a third — `hist_cores_NOW_20260424.yaml`. The spec listed only two but ORATS' `/cores` is current-only; for the regression to be temporally consistent, historical core data was needed. The `/hist/cores` endpoint is reachable on the current plan and was probed today. Each cassette is the regression contract for its respective endpoint.
- 2026-04-29 — `_core()`/`_strike()` test helpers in `tests/test_pflichtregeln.py` re-base from a synthetic `HAPPY_CORE`/`HAPPY_STRIKE` (defined inline) instead of the cassette-derived `NOW_CORE`/`NOW_STRIKE`. Reason: the real NOW values now break 3 rules; tests that need a "happy" baseline should not depend on a regression anchor that captures real-world failure. The cassette-derived `now_core`/`now_strike` fixtures are still consumed by `TestNowRegression` and `test_now_78_metadata_from_cassette`.
- 2026-04-29 — `OratsCore.avg_opt_volu_20d` widened from `int` to `float` because real ORATS responses return floats (e.g., `121174.45`). Rule 6's German message now `int(...)` -casts the value for clean output. Existing test `test_fails_on_low_volume_only` substring-asserts `"Volumen 10000"` which still matches `"Volumen 10000"` (the int cast).
- 2026-04-29 — `OratsCore.sector` aliases to ORATS' `sectorName` (GICS sector, e.g. "Technology") rather than `sector` (GICS sub-industry, e.g. "Application Software"). Pflichtregel 8's sector cap operates at the sector level; using the sub-industry would have produced a finer-grained partition than the cap intends.
- 2026-04-29 — `OratsStrike` has no alias for the `delta` field. ORATS `/hist/strikes` returns the **call** delta in the `delta` field; callers compute the put delta as `delta - 1` before validating the model (`OratsClient.strikes()` and the cassette factory both do this). This keeps `OratsStrike.delta` semantically the put delta everywhere it's consumed.
- 2026-04-29 — **Review-driven hardening (12 patches across 4 groups).** Group A (security/redaction): `_request_with_retry` now catches `httpx.RequestError` (Connect/Read/Timeout/Pool) with the same 1/2/4 s backoff and raises `ORATSDataError(status=-1, …)` after exhaustion; `_redact_url`/`_redact_text` replaced naive `str.replace` with regex per-query-param scrubbing (token/apikey/api_key/api-key) plus `Authorization: Bearer …`, and `ORATSDataError.__init__` runs the body through the scrubber before truncation — covers short tokens, URL-encoded tokens, and body-leak echoes. Group B (config discipline): `Settings` gained `orats_token: SecretStr` + `orats_base_url: str` from `.env` (no more `os.environ` in `health.py`); a global Loguru sink filter (`csp._logging.install_secret_redactor`) scrubs `token=…`, `apikey=…`, `Authorization: Bearer …`, and `IVOLATILITY_API_KEY=…` from every emitted record. Group C (hygiene/correctness): cassette-hygiene checks widened to URL-encoded tokens and Bearer headers, fail-loud when cassettes exist but `ORATS_TOKEN` unset; `_put_delta_from_call_delta` clamps to `[-1, 1]` first; `_decode_first_response_json` handles `Content-Encoding` as both `list[str]` and `str`; new `ORATSEmptyDataError(ORATSDataError)` for empty-data semantics. Group D (cosmetic): `pyproject.toml` description trimmed of slice-1 verbiage; `recording` marker excluded by default via `addopts = ["-m", "not recording"]`; `OratsCore`/`OratsStrike` migrated to `validate_by_name` + `validate_by_alias` (Pydantic v2.11+ idiom). Test count 114 → 140 (recording marker excluded by default; +3 recording opt-in selectable via `-m recording`). Coverage: orats.py 100 %, overall 99.73 %.

## Design Notes

**Token redaction.** Token lives in `.env`, loaded by `Settings` (slice 1) → passed into `OratsClient.__init__`. The client builds URLs as `f"{base_url}/cores?token={token}&ticker={ticker}"`; on exception, `_redact_url(url)` substitutes the token literal with `<REDACTED>` before placing the URL in the `ORATSDataError` message. Same redaction applies to any `loguru` debug log of the request URL. Cassettes use VCR's `filter_query_parameters` for double-defense.

**Cassettes vs `respx`.** Two test layers serve different purposes: `respx` mocks let unit tests pin retry / 4xx-vs-5xx / token-redaction logic without touching real bytes. Cassettes pin the actual ORATS response shape and let the gate run against real data. The `now_regression` test uses the cassette layer.

**Reconciliation outcome unknown until the cassette lands.** When `tests/test_pflichtregeln.py::TestNowRegression` runs against real cassette data, three outcomes are possible: (a) all 9 rules pass — synthetic was right and PRD FR29 is honest; (b) 1+ rules fail — the synthetic was over-optimistic and the real NOW-78 didn't actually pass; (c) field semantics differ subtly (e.g., `daysToNextErn` of 0 vs 8) and we discover a vendor-gotcha. **All three are captured in spec change log entries** — the test asserts the real verdict, no patching to "make it pass".

**Why `extra="ignore"` (not `forbid`) on vendor models.** Slice 1 set `extra="forbid"` on `RuleThresholds` and `UniverseConfig` to catch typos. Vendor responses are different — ORATS adds new JSON fields over time without notice; `forbid` would break parsing on upstream changes. `ignore` is the correct policy for the vendor boundary. Local domain models keep `forbid`.

## Verification

**Commands:**
- `uv sync` — lockfile updated with new deps
- `uv run ruff check src tests` — exit 0
- `uv run ruff format --check src tests` — exit 0
- `uv run mypy --strict src` — exit 0
- `uv run pytest -q` — all green
- `uv run coverage report --include='src/csp/clients/orats.py' --fail-under=90` — exit 0
- `uv run coverage report --fail-under=80` — exit 0
- `uv run pytest -k now_regression -v` — runs against real cassette
- `uv run python -c "import asyncio, csp; print(csp.orats_health_check('NOW'))"` — prints parsed `OratsCore` (live HTTP, sanity check; not part of CI)
- `! grep -r "${ORATS_TOKEN}" tests/cassettes/` — exits non-zero (no matches; token not leaked into recorded YAML)

## Suggested Review Order

**The vendor I/O & retry path (start here)**

- Public surface — slice 2 adds `OratsClient`, `orats_health_check`, `ORATSDataError`, `ORATSEmptyDataError` to `import csp`.
  [`__init__.py`](../../src/csp/__init__.py)

- DI'd async client; vendor methods return parsed Pydantic models, not raw dicts.
  [`orats.py:99`](../../src/csp/clients/orats.py#L99)

- Retry loop with transport-error coverage — `httpx.RequestError` retried with 1 / 2 / 4 s backoff (P1).
  [`orats.py:184`](../../src/csp/clients/orats.py#L184)

- Regex-based redaction for query params + Bearer headers, applied to URL **and** body (P2).
  [`orats.py:53`](../../src/csp/clients/orats.py#L53)

- Put-delta clamp `[-1, 1]` before `delta - 1` derivation (P6); D7 documents the dividend-yield approximation.
  [`orats.py:87`](../../src/csp/clients/orats.py#L87)

- Vendor methods: `cores()`, `strikes()` (live + `/hist/`), `ivrank()`, `summaries()`.
  [`orats.py:121`](../../src/csp/clients/orats.py#L121)

**Configuration discipline (FR12 + NFR8)**

- `Settings.orats_token: SecretStr` + `orats_base_url` sourced from `.env`; replaces `os.environ` access in `health.py` (P3).
  [`config.py:107`](../../src/csp/config.py#L107)

- Global Loguru filter scrubs `token=`, `apikey=`, `Authorization: Bearer …`, `IVOLATILITY_API_KEY=` from every emitted record (P4 / NFR8).
  [`_logging.py:43`](../../src/csp/_logging.py#L43)

- `orats_health_check("NOW") -> OratsCore` — the public sync wrapper; reads creds via `Settings.load()`.
  [`health.py:27`](../../src/csp/health.py#L27)

**Error types**

- `ORATSDataError(status, body, url_redacted)` plus the new `ORATSEmptyDataError` subclass for `data == []` semantics (P8).
  [`exceptions.py:14`](../../src/csp/exceptions.py#L14)

**Determinism contract (the keystone)**

- Real-data verdict — NOW-78 on 2026-04-24 fails rules 3, 5, 6 with the exact German messages. No patching to make it pass.
  [`test_pflichtregeln.py:514`](../../tests/test_pflichtregeln.py#L514)

- Cassette factory: parses YAML at module import, honours both list-and-string `Content-Encoding` (P7).
  [`now_2026_04_24.py:39`](../../tests/fixtures/now_2026_04_24.py#L39)

- Recorded cassettes — ground truth for what ORATS returns; reviewer's anchor for "is this parser realistic?".
  [`tests/cassettes/orats/`](../../tests/cassettes/orats/)

**Test surface (new)**

- Retry-policy unit tests via `respx`: 4xx immediate-raise, 5xx ×3 then raise, 429-then-200, transport-error retry, token never in messages.
  [`test_orats_client.py:168`](../../tests/test_orats_client.py#L168)

- Redaction unit tests: short tokens, URL-encoded tokens, Bearer-header scrubbing, body-leak path, put-delta clamp.
  [`test_orats_client.py:86`](../../tests/test_orats_client.py#L86)

- Cassette hygiene widened: URL-encoded tokens, Bearer headers, fail-loud when cassettes exist but env unset (P5).
  [`test_cassette_hygiene.py:69`](../../tests/test_cassette_hygiene.py#L69)

**Bootstrap & ergonomics**

- `addopts = ["-m", "not recording"]` excludes recording tests from `pytest -q`; description trimmed of slice-1 verbiage.
  [`pyproject.toml`](../../pyproject.toml)
