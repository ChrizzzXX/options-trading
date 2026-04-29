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

## From `spec-idea-singleticker.md` (2026-04-29)

- **D12 — `Idea.format_fbg_mail()` not implemented.** FR15 says ideas render in the brief §7.1 FBG-mail format with German number locale. Today the `Idea` model exposes raw fields; Claude/Chris formats manually. **Lands with:** Idea-formatter slice — implement `format_fbg_mail()` against the brief §7.1 worked example, with `ui/formatters.py` for German-locale number/date/percentage helpers.

- **D13 — `vix_close` is static in `[macro]` settings until FMP-client slice.** Today the slice reads `Settings.macro.vix_close` from `config/settings.toml`; live VIX requires FMP. Risk: stale VIX silently passes/fails Pflichtregel 1. **Lands with:** FMP-client slice — replace internal `MacroSnapshot` construction with a live FMP fetch; preserve `csp.idea` public signature.

- **D14 — Override DuckDB persistence stub.** Spec inherits the FR9 obligation (override decisions persist for monthly review) but cannot implement it — DuckDB schema doesn't exist yet. Today: loguru WARN only (already wired in slice 1). **Lands with:** lifecycle slice — extends D3 (`override=True` has no DB persistence stub) by also persisting the `Idea` snapshot per `csp.idea(..., override=True)` invocation.

- **D15 — `sector_exposure_delta_pct` requires position sizing.** FR16 says `Idea` exposes "sector-exposure delta vs current portfolio" — i.e., how much a hypothetical fill would shift the sector share. Computing the delta needs notional-per-trade, which lives in the lifecycle slice (positions + cash-secured amount). Today: `Idea.current_sector_share_pct` carries the *existing* share only. **Lands with:** lifecycle slice — add `sector_exposure_delta_pct` once `csp.log_trade` knows position sizing.

## From `spec-idea-singleticker.md` review (2026-04-29)

- **D16 — `Idea.pflichtregeln_passed=True` when `override=True` is a downstream-filter landmine.** With override active and rules failed, the boolean is `True` but `bypassed_rules` carries the violations. A naive `filter(lambda i: i.pflichtregeln_passed, ideas)` would silently surface override-bypassed candidates. The naming is per-spec (Slice 3 §Always) but ergonomically risky. **Lands with:** rename slice — split into `surfaced: bool` + `rules_originally_passed: bool`, or add a stronger `actionable` invariant; only justify the churn if a downstream consumer actually trips on this.

- **D17 — `Idea.data_freshness="live"` covers macro implicitly.** The flag tracks the ORATS data segment; the VIX-close used for Pflichtregel 1 comes from static `[macro]` settings (D13). A user reading `data_freshness="live"` may assume VIX is live too. **Lands with:** FMP-client slice (extends D13) — promote `data_freshness` to per-segment (`vendor_data`, `macro`) once FMP delivers live VIX.

- **D18 — Call→put delta conversion at `OratsClient.strikes` lacks defensive assertion.** `OratsClient` silently call-to-put converts via `delta - 1`. If ORATS ever surfaces real put-deltas (or renames the field), the conversion would double-negate or skew silently. `_select_strike` would then filter out everything (band requires negative delta) and raise `ORATSEmptyDataError` rather than fail loud. **Lands with:** vendor-schema-versioning slice (D8) — assert `all(d <= 0 for d in deltas)` post-conversion; fail loud on shape change.

- **D19 — `PortfolioSnapshot.sector_exposures` lookup is case-sensitive.** ORATS returns sector strings like `"Technology"`; a portfolio dict keyed `"technology"` would silently miss, Pflichtregel 8 would pass against an empty share, and Chris would see 0% sector exposure when reality says 30%. Today the model never carries real data (always empty in this slice). **Lands with:** `csp.log_trade` slice — normalize keys at `PortfolioSnapshot` construction (title-case or case-fold both sides) and add a unit test pinning case-insensitive equality.

- **D20 — Redacted URL builder uses manual `&`-join, not `urllib.parse.urlencode`.** `_async_idea` and `OratsClient._request_with_retry` build the redacted-URL string for error messages by hand. A ticker containing `&`/`=`/`#` (none in current curated universe) would produce ambiguous redaction. Low blast radius today; latent bug if universe expands. **Lands with:** vendor-schema slice OR first non-curated ticker — switch to `httpx.QueryParams` for the redacted URL too.

- **D21 — No NFR4 (≤5 s) timing benchmark for `csp.idea`.** Spec Always says ≤ 5 s wall-clock for US ticker. No benchmark pins this; tests run in milliseconds via respx. **Lands with:** future quality/perf slice — add a `pytest-benchmark` smoke (or a slow-marker integration) once a real cassette + warm cache pattern is in place.

---

## How to clear an entry

When a slice closes one of these items: edit this file, move the entry from "active" to a `## Closed` section with a `closed: <date> via <commit-or-spec>` tag, and reference back in that slice's Spec Change Log.
