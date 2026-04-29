# Deferred Work

Findings surfaced during slice review that aren't this story's problem. Each entry names the slice/condition where it lands.

## From `spec-pflichtregeln-gate.md` review (2026-04-29)

- **D1 — NOW-78 fixture is self-fulfilling.** Six of eight `OratsCore` fields and two of five `OratsStrike` fields are tagged `inferred-plausible`. The "regression" test asserts the values picked to pass... pass. Acknowledged in spec Design Notes. **Lands with:** ORATS-client slice — replace fixture with the real `tests/cassettes/orats/cores_NOW.yaml` + `strikes_NOW.yaml` from 2026-04-24, recorded once with `pytest --record-mode=once`. PRD FR29 / NFR18 require this for CI gating.

- **D2 — Per-file 100% coverage gate not enforced in CI.** `pyproject.toml` `addopts` carries the 80% overall floor only (pytest honors a single `--cov-fail-under` value). The 100% `pflichtregeln.py` gate exists today only because someone runs `coverage report --include='src/csp/filters/pflichtregeln.py' --fail-under=100` separately. **Lands with:** CI/CD slice (when GitHub Actions / similar arrives) — add a second `coverage report --include=… --fail-under=100` step. Same applies to the future `lifecycle/state_machine.py` 100% gate.

- **D3 — `override=True` has no DB persistence stub.** ~~Per FR9, override decisions must be logged in DuckDB for monthly review.~~ **Closed 2026-04-29 via `spec-lifecycle-persistence.md` (slice 6).** `csp.log_idea(idea)` persists ANY idea (passing or override-bypassed) to the `ideas` table; `csp.list_ideas(overrides_only=True)` is the monthly-review query. Override-using callers must explicitly call `log_idea` — not auto-side-effected from `csp.idea`.

- **D4 — `mkt_cap_thousands` uses `float` at 9-figure scale.** Numerically fine at this magnitude (50B threshold has plenty of float headroom), but the field semantics ("thousands of USD" stored as float) invite rounding when ORATS surfaces integer thousands. **Lands with:** ORATS-client slice — type `mkt_cap_thousands: int` (matching the vendor) and consider `Decimal` (or scaled int) for the threshold setting.

- **D5 — Global NaN-input handling policy.** ~~Comparison-based rules silently fail with literal `"nan"` in messages.~~ **Closed 2026-04-29 via slice 9.** `_require_finite` helper in `src/csp/models/core.py` plus `@field_validator` on every numeric field of `MacroSnapshot`/`OratsCore`/`OratsStrike` rejects NaN/±Inf at the vendor boundary with a clear "nicht finite" message. Sort/comparison logic in `csp.scan` and Pflichtregeln are now transitively safe.

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

- **D12 — `Idea.format_fbg_mail()` not implemented.** ~~FR15 says ideas render in the brief §7.1 FBG-mail format with German number locale.~~ **Closed 2026-04-29 via `spec-daily-brief.md` (slice 7).** `Idea.format_fbg_mail()` renders the §7.1 layout against `csp.ui.formatters` (German-locale USD / Prozent / Datum). Default reasoning is synthesized from IVR + OTM% + DTE; caller can override via `reasoning=...`. Override + Pflichtregel-Fail-Pfade markieren den Header zusätzlich.

- **D13 — `vix_close` is static in `[macro]` settings until FMP-client slice.** ~~Today the slice reads `Settings.macro.vix_close` from `config/settings.toml`; live VIX requires FMP.~~ **Closed 2026-04-29 via `spec-fmp-client.md` (slice 5).** `csp.macro_snapshot()` now returns live VIX when `FMP_KEY` is set; `idea` and `scan` upgrade transparently. Settings fallback retained as the "no key" path so existing tests + zero-config dev still work.

- **D14 — Override DuckDB persistence stub.** ~~Spec inherits the FR9 obligation~~ **Closed 2026-04-29 via slice 6 (same path as D3).** `log_idea` persists override-bypassed Ideas with `bypassed_count > 0`; the loguru WARN from slice 3 still fires alongside.

- **D15 — `sector_exposure_delta_pct` requires position sizing.** FR16 says `Idea` exposes "sector-exposure delta vs current portfolio" — i.e., how much a hypothetical fill would shift the sector share. Computing the delta needs notional-per-trade, which lives in the lifecycle slice (positions + cash-secured amount). Today: `Idea.current_sector_share_pct` carries the *existing* share only. **Lands with:** lifecycle slice — add `sector_exposure_delta_pct` once `csp.log_trade` knows position sizing.

## From `spec-idea-singleticker.md` review (2026-04-29)

- **D16 — `Idea.pflichtregeln_passed=True` when `override=True` is a downstream-filter landmine.** With override active and rules failed, the boolean is `True` but `bypassed_rules` carries the violations. A naive `filter(lambda i: i.pflichtregeln_passed, ideas)` would silently surface override-bypassed candidates. The naming is per-spec (Slice 3 §Always) but ergonomically risky. **Lands with:** rename slice — split into `surfaced: bool` + `rules_originally_passed: bool`, or add a stronger `actionable` invariant; only justify the churn if a downstream consumer actually trips on this.

- **D17 — `Idea.data_freshness="live"` covers macro implicitly.** ~~The flag tracks the ORATS data segment; the VIX-close used for Pflichtregel 1 comes from static `[macro]` settings (D13).~~ **Partially closed 2026-04-29 via `spec-fmp-client.md` (slice 5).** When `FMP_KEY` is set, `Idea.data_freshness="live"` is now honest about the macro segment too. **Residual gap (still active):** when FMP errors and we fall back to static settings, `data_freshness` still says "live". **Lands with:** a small follow-up — promote `data_freshness` to per-segment (`vendor_data`, `macro`), or add a `macro_source: Literal["fmp_live", "fmp_eod", "settings_fallback"]` field on `Idea`.

- **D18 — Call→put delta conversion at `OratsClient.strikes` lacks defensive assertion.** `OratsClient` silently call-to-put converts via `delta - 1`. If ORATS ever surfaces real put-deltas (or renames the field), the conversion would double-negate or skew silently. `_select_strike` would then filter out everything (band requires negative delta) and raise `ORATSEmptyDataError` rather than fail loud. **Lands with:** vendor-schema-versioning slice (D8) — assert `all(d <= 0 for d in deltas)` post-conversion; fail loud on shape change.

- **D19 — `PortfolioSnapshot.sector_exposures` lookup is case-sensitive.** ORATS returns sector strings like `"Technology"`; a portfolio dict keyed `"technology"` would silently miss, Pflichtregel 8 would pass against an empty share, and Chris would see 0% sector exposure when reality says 30%. Today the model never carries real data (always empty in this slice). **Lands with:** `csp.log_trade` slice — normalize keys at `PortfolioSnapshot` construction (title-case or case-fold both sides) and add a unit test pinning case-insensitive equality.

- **D20 — Redacted URL builder uses manual `&`-join, not `urllib.parse.urlencode`.** `_async_idea` and `OratsClient._request_with_retry` build the redacted-URL string for error messages by hand. A ticker containing `&`/`=`/`#` (none in current curated universe) would produce ambiguous redaction. Low blast radius today; latent bug if universe expands. **Lands with:** vendor-schema slice OR first non-curated ticker — switch to `httpx.QueryParams` for the redacted URL too.

- **D21 — No NFR4 (≤5 s) timing benchmark for `csp.idea`.** Spec Always says ≤ 5 s wall-clock for US ticker. No benchmark pins this; tests run in milliseconds via respx. **Lands with:** future quality/perf slice — add a `pytest-benchmark` smoke (or a slow-marker integration) once a real cassette + warm cache pattern is in place.

---

## From `spec-scan-universe.md` (2026-04-29)

- **D22 — `scan` is US-only because the universe loader has no `region` column.** ~~PRD FR14 says "scan the entire universe (US + EU together)"~~ **Rejected 2026-04-29 — EU coverage removed from scope.** See PRD §"2026-04-29 Scope Amendment". `Settings.universe.allowed_tickers` stays a flat `list[str]`; all tickers are US.

- **D23 — No automated NFR1 (≤ 60 s for ~40 tickers) timing benchmark for `csp.scan`.** Spec Always says ≤ 60 s wall-clock. Tests run in milliseconds via respx; the real timing is unverified by CI. Mirrors D21 for the universe-level case. **Lands with:** the same future quality/perf slice — `pytest-benchmark` against a 40-ticker respx fixture (cheap) plus a slow-marker integration with real cassettes once they exist.

- **D24 — No `asyncio.Semaphore` concurrency cap on `_async_scan`.** All universe tickers fire concurrently via a single `asyncio.gather()`. Fine at 12 (today) and 40 (planned EU expansion) — well under ORATS's 1000 req/min headroom. Risk emerges if (a) the universe grows past ~100 tickers, (b) `scan` is invoked from a daemon making back-to-back calls, or (c) a vendor plan downgrade reduces the rate budget. **Lands with:** if/when any of those conditions trigger — introduce `asyncio.Semaphore(N)` with `N` from settings, default 16. Don't pre-build until the constraint is real.

- **D25 — Cassette smoke for `csp.scan(["NOW"])` not implemented; spec-promised but skipped.** Spec AC #6 promised a 1-ticker cassette smoke against `cores_NOW.yaml` + `strikes_NOW.yaml`. The live `strikes_NOW.yaml` doesn't exist (only `cores_NOW.yaml` and the historical `hist_*_NOW_20260424.yaml` pair were recorded in slices 2/3); stacking VCR cassettes is undefined behavior. The respx integration tests (rule-failer-filtered, all-fail, skip-and-continue, determinism) cover the same orchestration invariants; the manual `Verification` `python -c "import csp; print(csp.scan(max_results=5))"` covers real-cassette validation. **Lands with:** if/when a `strikes_NOW.yaml` is recorded as part of slice 2/3 cassette refresh, OR a future slice that records a multi-endpoint composite cassette — add a single `vcr_recorder.use_cassette(...)` smoke that asserts the consistency invariant `scan == [idea("NOW")]` if pass else `[]`.

- **D26 — `asyncio.gather(return_exceptions=False)` poison-pill cancellation.** `_async_scan` uses `gather(*tasks, return_exceptions=False)`. `_safe_fetch` catches `ORATSDataError` + `ORATSEmptyDataError`, but if a future code path leaks a different exception (e.g. an unwrapped `httpx.PoolTimeout`, `pydantic.ValidationError` from a malformed payload, an `OSError`), gather cancels every in-flight task and the whole scan dies — losing all completed work for one rogue payload. Today defended by `OratsClient`'s wrapping (`httpx.HTTPError` → `ORATSDataError`, transport → `ORATSDataError(status=-1)`). Adding `ValueError` back to the catch tuple is a different conversation (was deliberately removed in Patch P4). **Lands with:** the first naked-exception-leak observation in production — switch to `asyncio.TaskGroup` (Python 3.11+) so sibling-cancellation-on-error is explicit and graceful, OR broaden `_safe_fetch`'s except tuple with a deliberately-named `KNOWN_TICKER_FAULT_EXCEPTIONS` allow-list.

- **D27 — Sort key fragile against NaN / +Inf in `annualized_yield_pct`.** **Closed 2026-04-29 via slice 9 (transitive).** Now that `MacroSnapshot`/`OratsCore`/`OratsStrike` reject NaN/±Inf at construction, the inputs to `mid/strike × 365/dte × 100` are guaranteed finite, and `annualized_yield_pct` is too. `csp.scan`'s `sort(key=lambda i: (-i.annualized_yield_pct, i.ticker))` is now NFR20-safe.

- **D28 — `max_results` accepts `True`/`False` (bool ⊂ int) and has no upper bound.** `scan(True)` returns top-1 silently (Python's bool subclass of int + `True > 0`); `scan(False)` raises `ValueError("max_results muss > 0 sein, war False")` with confusing wording. `scan(sys.maxsize)` succeeds without complaint. Esoteric — Chris's universe is 12 tickers and Claude composes the call. **Lands with:** if/when the public surface widens (MCP server, cron-driven daily-brief, or third-party caller) — add `if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results <= 0 or max_results > 1000: raise ValueError(...)`.

## From `spec-fmp-client.md` (2026-04-29)

- **D29 — No real FMP cassette recorded yet.** ~~Slice-5 used respx synthesized payloads.~~ **Closed 2026-04-29 via slice 8b.** Real cassettes recorded at `tests/cassettes/fmp/quote_VIX.yaml` and `tests/cassettes/fmp/historical_VIX_20260424.yaml`. `TestCassettes` reads them in CI; `TestRecording` (opt-in via `-m recording`) re-records on demand. Discovery: real responses match the synthesized shapes (`price` field, list-shape — no `data` wrapper), confirming the slice-5 client logic. **Side effect**: also closes the FMP base-URL bug (slice-8b: `/api/stable/...` was legacy 403'd; correct is `/stable/...`).

- **D30 — IVolatility client slice blocked at tariff layer.** ~~Slice-8 probe found tariff block.~~ **Rejected 2026-04-29 — EU coverage removed from scope.** Probe trace preserved here for the record: auth works against `https://restapi.ivolatility.com`, but `/equities/eod/options-rawiv` returns 403 "You don't have the required tariff, access is denied" for ALV.DE / ALV / ALV.GR / NOW. `/equities/eod/single-stock-option*` accept the request but require a pre-known option ID. `/equities/eod/option-series` is "no such endpoint exists" today. If EU coverage is reactivated in the future, this trace tells the next implementer what NOT to spend hours debugging.

- **D31 — `csp.export_to_sheets()` not implemented.** ~~Last of the PRD's 10 public functions.~~ **Closed 2026-04-29 via slice 10.** Implemented against the `gws sheets` CLI via `subprocess.run` (no new Python deps; reuses Chris's already-authenticated `gws`-OAuth-token). 3-tab spreadsheet ("Ideas" / "Positions" / "Macro") created via `gws-sheets` skill — German column headers, bold + frozen header rows, append-only-per-day. Settings.google_sheet_id added. Live smoke verified: SMOKE-ticker idea + VIX 18.01 row appeared in real Sheet. **Deviation from NFR6:** function is sync (not fire-and-forget) — explicit caller invocation (`csp.daily_brief()` then `csp.export_to_sheets(brief)`) is cleaner than implicit threading; `daily_brief()` itself stays unblocked because the caller controls the order.

## From `spec-lifecycle-persistence.md` (2026-04-29)

- **D32 — Wheel-Lebenszyklus / Covered-Call-Folgegeschäfte.** MVP: `assigned` ist terminal, kein automatischer Übergang zu einem CC-Trade nach Aktien-Übernahme. Project-context.md MVP-Scope explizit: "Wheel covered-call lifecycle (`assigned → CC open`, net-credit-only roll mechanic) is **deferred to Growth**." **Lands with:** Growth-Phase, wenn Chris mit Wheel-Strategie starten will — neue `TradeStatus`-Werte (`CC_OPEN`, etc.), neue Übergänge in `VALID_TRANSITIONS`, separate Pflichtregeln-Pipeline für CC-Strikes.

- **D33 — Automated assignment detection.** MVP: User markiert Assignment manuell via `csp.close_trade(tid, new_status=ASSIGNED)`. PRD FR21-22 erwähnt automatische Erkennung über Broker-Feed nicht; project-context.md "no broker integration" hard rule. **Lands with:** wenn (und nur wenn) ein Read-only-Broker-Feed integriert wird (z. B. IBKR-FlexQuery-CSV-Import). Entry-Point: `csp.import_broker_csv(path)` — würde offene Trades vergleichen und automatisch ASSIGNED markieren.

- **D34 — `csp.log_trade(idea)` legt einen neuen `idea_id`-Record an, auch wenn `csp.log_idea(idea)` zuvor lief.** Idempotenz greift über `(ticker, open_date, contracts)`-Lookup in `trades`, NICHT über bereits existierende Idea-IDs. Folge: doppelte Idea-Rows mit gleichen Daten möglich, wenn jemand erst `log_idea` und dann `log_trade` für dieselbe Idea aufruft. Heute kein praktisches Problem (idea-Tabelle wird nur per `list_ideas` gelesen, dort sind Duplikate als unterschiedliche Snapshots interpretierbar). **Lands with:** wenn Idea-Deduplikation wichtig wird — ein UNIQUE-Constraint auf `(ticker, as_of, mid_premium, strike, dte, delta)` plus ein `INSERT … ON CONFLICT DO NOTHING RETURNING idea_id`-Pattern.

- **D35 — Sektor-Exposure-Delta noch immer nicht implementiert (D15 weiterhin offen).** Slice 6 hat `Trade.cash_secured`, also wäre die Berechnung jetzt prinzipiell möglich. Der `Idea.current_sector_share_pct` bleibt aber bewusst der EXISTIERENDE Sektor-Anteil; das Delta gegenüber einem hypothetischen Fill braucht 1) Aggregation aller offenen Trades nach Sektor, 2) Hinzufügen des potenziellen Trades, 3) Rückgabe der Differenz. **Lands with:** ein kleiner Folge-Slice — `Idea.compute_sector_exposure_delta(*, contracts) -> float` als reine Funktion, die `csp.list_open_positions()` ruft. Heute via `compute_in_caller`-Hilfsfunktion lösbar, in der Library wäre's sauberer.

- **D36 — `_row_to_trade` benutzt `# type: ignore`-Kommentare.** ~~Vier Annotationen.~~ **Closed 2026-04-29 via slice 9.** Ersetzt durch `typing.cast` (für `status` String) plus defensive `isinstance`-Checks an `contracts: int`, `open_date: date`, `close_date: date | None`, `inserted_at: datetime`, `updated_at: datetime`. Bei Schema-Drift fliegt jetzt eine klare `LifecycleError("Schema-Drift: trades.<col> ist <type>, erwartet <X>.")` statt einer kryptischen pydantic-Fehlermeldung. mypy --strict clean ohne `# type: ignore`.

- **D38 — `daily_brief()` lädt jeden offenen Trade einzeln zur Override-Prüfung.** `_compute_actions` ruft pro offener Position `get_idea(trade.trade_id)` auf — bei vielen offenen Trades macht das N DuckDB-Roundtrips. Heute kein Problem (≤ 5 offene Positionen erwartet). **Lands with:** wenn die offenen Positionen routinemäßig > 20 erreichen — Bulk-JOIN: `SELECT t.*, i.bypassed_count FROM trades t JOIN ideas i ON t.idea_id = i.idea_id WHERE t.status IN ('open', 'take_profit_pending')`.

- **D39 — `DailyBrief.to_markdown()` ist statisch; keine Templates / Lokalisierung.** Heute ASCII-Tabellen mit Pipe-Syntax. Falls man später Sheets oder PDF-Export anschließen will, müssten `Idea.format_fbg_mail` und `to_markdown` ein gemeinsames Render-Trait bekommen. **Lands with:** wenn Sheets / PDF tatsächlich gebraucht werden — z. B. durch Trennung `Idea` ⇒ `IdeaView` (View-Modell) oder `jinja2`-Templates in `ui/templates/`.

- **D40 — `format_fbg_mail` Felder unvollständig vs. Brief §7.1.** ~~Brief zeigte `IV aktuell 56,1 %`.~~ **Rejected 2026-04-29 — IVR ist heute der primäre Pflichtregel-1-Treiber, IV-aktuell wäre nur kosmetische Anreicherung und der Brief ist archived.** Wenn ATM-IV je gebraucht wird, kommt sie aus ORATS `/cores` (Feld noch zu identifizieren).

- **D37 — Migration-Parser ist naiv (split on `;`).** Heutige Migrationen sind reine DDL ohne Literale, daher safe. Eine zukünftige Migration mit einem `INSERT INTO config VALUES ('Hello; World')` würde das aufteilen. **Lands with:** wenn die erste DML-Migration ansteht — entweder zu `sqlglot`/`sqlparse` wechseln oder die SQL-Datei in einzelne `*.sql`-Files pro Statement splitten.

---

## How to clear an entry

When a slice closes one of these items: edit this file, move the entry from "active" to a `## Closed` section with a `closed: <date> via <commit-or-spec>` tag, and reference back in that slice's Spec Change Log.
