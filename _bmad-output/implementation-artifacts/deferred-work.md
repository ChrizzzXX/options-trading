# Deferred Work

Findings surfaced during slice review that aren't this story's problem. Each entry names the slice/condition where it lands.

## From `spec-pflichtregeln-gate.md` review (2026-04-29)

- **D1 — NOW-78 fixture is self-fulfilling.** Six of eight `OratsCore` fields and two of five `OratsStrike` fields are tagged `inferred-plausible`. The "regression" test asserts the values picked to pass... pass. Acknowledged in spec Design Notes. **Lands with:** ORATS-client slice — replace fixture with the real `tests/cassettes/orats/cores_NOW.yaml` + `strikes_NOW.yaml` from 2026-04-24, recorded once with `pytest --record-mode=once`. PRD FR29 / NFR18 require this for CI gating.

- **D2 — Per-file 100% coverage gate not enforced in CI.** `pyproject.toml` `addopts` carries the 80% overall floor only (pytest honors a single `--cov-fail-under` value). The 100% `pflichtregeln.py` gate exists today only because someone runs `coverage report --include='src/csp/filters/pflichtregeln.py' --fail-under=100` separately. **Lands with:** CI/CD slice (when GitHub Actions / similar arrives) — add a second `coverage report --include=… --fail-under=100` step. Same applies to the future `lifecycle/state_machine.py` 100% gate.

- **D3 — `override=True` has no DB persistence stub.** Per FR9, override decisions must be logged in DuckDB for monthly review. Currently we emit a `loguru` WARN only. **Lands with:** lifecycle slice (DuckDB schema, `INSERT OR REPLACE` on overrides table). Spec Boundaries §Never explicitly defers this.

- **D4 — `mkt_cap_thousands` uses `float` at 9-figure scale.** Numerically fine at this magnitude (50B threshold has plenty of float headroom), but the field semantics ("thousands of USD" stored as float) invite rounding when ORATS surfaces integer thousands. **Lands with:** ORATS-client slice — type `mkt_cap_thousands: int` (matching the vendor) and consider `Decimal` (or scaled int) for the threshold setting.

- **D5 — Global NaN-input handling policy.** Comparison-based rules silently fail with literal `"nan"` in messages; no `math.isfinite` validators on `OratsCore` / `OratsStrike` / `MacroSnapshot`. **Lands with:** ORATS-client slice — Pydantic validators that scrub NaN/±inf at the vendor boundary, or a `validate_finite` decorator applied to all numeric fields. Cross-cutting; doesn't belong in the gate slice.

---

## From `spec-orats-client.md` review (2026-04-29)

- **D6 — `asyncio.run` deadlocks if `orats_health_check` is called inside an active event loop.** Documented limitation in the function's docstring; `RuntimeError: asyncio.run() cannot be called from a running event loop` if invoked from Jupyter / FastAPI / etc. **Lands with:** the first usage that hits this — detect with `asyncio.get_running_loop()` and fall back to `loop.run_until_complete` or document harder. Likely never bites this MVP since Claude Code calls via `uv run python -c`.

- **D7 — Put-delta is approximated as `call_delta - 1`** for dividend-paying tickers. Exact via put-call parity for non-dividend stocks (NOW); off by `dividend_yield × time_to_expiry` for AAPL / MSFT / META / AMZN / WMB / KMI / etc. — typically 0.5–2 % of delta at 60 DTE. **Lands with:** an ORATS plan-tier upgrade that exposes `putDelta` directly, OR a Black-Scholes-with-dividends slice that re-derives put delta locally from `pxAtmIv` + risk-free rate + dividend yield. Worth tracking which universe candidates this might shift across the rule-2 [-0.25, -0.18] band.

- **D8 — `extra="ignore"` on vendor models masks schema renames silently.** If ORATS deprecates `pxAtmIv` → `pxAtmIvNew`, Pydantic drops the new field; `under_price` falls back to default and rules pass against stale data. **Lands with:** vendor-schema-versioning slice — add canary assertions (e.g., `assert mktCap > 1_000_000` for known-large tickers in a daily smoke test) and/or a vendor schema-version field check.

- **D9 — Retry-on-POST/PUT without idempotency guard.** `_request_with_retry` retries on 5xx/429 unconditionally; only `GET` is used today, but a future write endpoint (override decision push? trade log?) could double-execute on 503-after-partial-commit. **Lands with:** the first non-GET endpoint introduction — assert `method == "GET"` or whitelist idempotent verbs.

- **D10 — Module-level cassette parsing → test-collection errors on corruption.** `tests/fixtures/now_2026_04_24.py` parses cassette YAML at import; a missing/truncated/malformed cassette breaks every test that imports `NOW_CORE`/`NOW_STRIKE`/`NOW_MACRO` with a confusing collection-time error. **Lands with:** if it ever bites — convert to lazy `@pytest.fixture` with a clear `pytest.fail("Cassette missing — re-record via …")` message.

- **D11 — `TestNowRegression` asserts exact German prose.** A whitespace or punctuation tweak in `pflichtregeln.py` German messages would break the regression test for the wrong reason. **Lands with:** if/when German-message format changes — tighten assertion to per-rule prefix (`"Pflichtregel 3"`, etc.) + key numeric tokens (`"56"`, `"0"`, `"0,15"`) instead of full-prose match.

---

## How to clear an entry

When a slice closes one of these items: edit this file, move the entry from "active" to a `## Closed` section with a `closed: <date> via <commit-or-spec>` tag, and reference back in that slice's Spec Change Log.
