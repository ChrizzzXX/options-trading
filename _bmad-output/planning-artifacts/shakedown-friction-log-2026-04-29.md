---
title: 'Shakedown friction log — 2026-04-29'
status: 'complete'
track: 'A (single-session simulation, all 8 sessions + 6 probes)'
session_started: '2026-04-29 ~19:50 Berlin'
session_ended: '2026-04-29 ~22:00 Berlin'
post_slice_12: true
slice_12_commit: 'f8d2276'
---

# Shakedown friction log — 2026-04-29

Live shakedown of the csp-flywheel-terminal MVP using the protocol in
`shakedown-plan-2026-04-29.md`. This file is the input to slice 13+.

Severity tiers:
- **blocker** — workflow cannot complete; library crashes or returns visibly wrong data.
- **major** — workflow completes but the user-visible output misleads the decision.
- **minor** — workflow completes correctly, but ergonomically annoying.
- **cosmetic** — string formatting, locale nits.

## Status as of run

- **Slice-12 shipped during the shakedown.** Earnings sentinel detection
  added when Session 1.A surfaced 8/12 universe tickers returning the
  ORATS sentinel `nextErn = '0000-00-00'` simultaneously. Commit `f8d2276`
  on `origin/main`. Track A then restarted from 1.A.
- All gates green at restart (397 tests, 98.78% coverage).

## Findings

| # | Date | Track | Step | Severity | Observation | Hypothesis / suggested fix |
|---|------|-------|------|----------|-------------|----------------------------|
| F1 | 2026-04-29 | A | 1.A (initial) | **blocker → fixed in slice 12** | 8/12 universe tickers returned `daysToNextErn=0`, library treated as "earnings today" and rejected on Pflichtregel 5. Real cause: ORATS sentinel `nextErn='0000-00-00'`. | Detect sentinel; map to None (or derive from `wksNextErn`). Distinct German Rule-5 reason. **Done — slice 12.** |
| F2 | 2026-04-29 | A | 1.A | **major** | When `ranked_ideas` is empty, the daily-brief markdown just says `_keine Pflichtregeln-bestandenen Kandidaten_` with no signal as to *which rule(s) gated the universe*. User cannot distinguish "market is wrong today" from "data quality is wrong today". | `daily_brief.to_markdown()` should append a per-rule rejection histogram when ranked_ideas is empty and any tickers were screened. Format: "12 Tickers geprüft, davon 5 × Pflichtregel 5 (Vendor-Datum), 4 × Pflichtregel 6 (Liquidität), 3 × Rule 4 (OTM)." Direct slice-13 candidate. |
| F3 | 2026-04-29 | A | 1.A | **minor** | `csp.scan` has no diagnostic / `include_failures` flag — caller cannot see why universe was empty at the API level either. | Add `csp.scan(..., include_failures=True)` returning the failed Idea objects too (with `pflichtregeln_passed=False` and the German reasons). Pairs with F2. |
| F4 | 2026-04-29 | A | 1.A | **cosmetic** | `daily_brief.to_markdown()` renders VIX as `18,51 %`. VIX is conventionally quoted unitless (`18.51`). Same issue in Sheets Macro tab (`18,01 %` from slice-10 smoke). Numerical value identical, but the `%` sign is wrong by convention. | Update `csp.ui.formatters` / DailyBrief markdown VIX rendering: use `format_num` not `format_pct`. Sheets export already correct? Re-verify in 1.H. |
| F5 | 2026-04-29 | A | 1.A | **minor** | `MacroSnapshot` has no `as_of` / timestamp field. Caller cannot distinguish "live VIX from FMP" vs "Settings.macro fallback" vs stale data. The brief renders `VIX: 18,49 %` with no temporal context. | Add `MacroSnapshot.as_of: date` and `data_freshness: Literal["live", "fallback"]` (mirrors `Idea` model). Render as part of markdown header. |
| F6 | 2026-04-29 | A | 1.A | **cosmetic** | `to_markdown()` shows portfolio state nowhere — even when 0 positions, the user has no quick "Sektor-Verteilung" / "freie Quote" context. Slice 11 reconstructs portfolio from open trades; that data could surface here. | Optional `## Portfolio` section in markdown (skipped at 0 positions). Defer until > 3 open positions makes it actually useful. |
| F7 | 2026-04-29 | A | 1.A | **major** | Slice-12 fix renames the failure mode but doesn't unblock the daily flow — workflow still produces 0 candidates today even after correctly distinguishing data-gap from earnings-event. NOW would still need override=True for Rule 6 (Spread). | Slice-12 was scoped to correctness, not workflow recovery. F2 (empty-brief diagnostics) is the workflow-recovery move. Track this as the next priority. |
| F8 | 2026-04-29 | A | 1.B | **minor** | `format_fbg_mail()` Begründung is a generic 3-clause template ("IVR X % attraktiv; Strike Y % OTM bietet Sicherheitspuffer; Z DTE im Theta-Beschleunigungsfenster"). Same shape for every idea. | Synthesize from richer signals: highlight the standout metric ("IVR im 95.-Perzentil"), reference rule context ("Override Rule N akzeptiert weil ..."), or accept the user-supplied `reasoning` arg as the primary path. |
| F9 | 2026-04-29 | A | 1.B | **minor** | Calling `csp.idea(..., override=True)` after `csp.idea(...)` issues a fresh ORATS call — wasted network + risk of strike/quote drift between two calls (in this run spread jittered 0,15 → 0,25 USD between runs). The first idea object already has the data; the override is just a gate-flip. | Add `Idea.with_override()` (or `.reevaluate(override=True)`) that re-runs the Pflichtregeln gate in-process without a new ORATS round-trip. |
| F10 | 2026-04-29 | A | 1.B | **cosmetic** | Real-time spread jitter between consecutive calls (0,15 → 0,25 → 0,15 USD) is normal live-market behavior, but the user has no way to see "this is a quote that moved." Slice-7 omits a quote-timestamp field. | Could surface `as_of` precision (date today; later seconds in `data_freshness="live"`). Defer until quote drift causes a real decision miss. |
| F11 | 2026-04-29 | A | 1.C+1.D | **major** | `csp.log_idea(idea)` followed by `csp.log_trade(idea)` creates **two duplicate idea rows** in DuckDB. The trade FK links to the auto-created idea (from log_trade), not the one explicitly logged (from log_idea). Result: `csp.list_ideas(overrides_only=True)` returns 2 identical entries for one decision. **Breaks FR9 monthly override review** — counts are doubled. | Either (a) `log_trade` checks for an existing idea matching `idea` and reuses its idea_id, or (b) `log_idea` is removed and `log_trade` is the single persistence entry-point (with `persist_idea=True` default). Option (b) matches Chris's "log_idea separately is error-prone" earlier note. Slice-13 candidate. |
| F12 | 2026-04-29 | A | 1.D | **minor** | `Trade` model doesn't carry `strike` (only `idea_id` FK). To render a position with strike (or any other research-time metric), caller must `get_idea(trade.trade_id)` per trade — N+1 calls. `daily_brief` solves this internally; direct `list_open_positions()` users hit it. | Add either (a) read-only `Trade.strike` (denormalised from idea at log_trade time), or (b) `csp.list_open_positions(with_idea=True)` returning `(Trade, Idea)` tuples. Same N+1 risk surfaces in slice-7 daily_brief — D38 deferred work tracks this. |
| F13 | 2026-04-29 | A | 1.E | — | **Slice-11 bug 1 fix verified live.** Lowering `total_csp_capital_usd` to 12,000 produced Tech share 63.33%; all 4 Tech tickers (NOW, AAPL, MSFT, NVDA) failed Rule 8 with the German Sektor-Cap reason. Non-Tech tickers correctly silent on Rule 8. **Pass.** | n/a — works as designed. |
| F14 | 2026-04-29 | A | 1.F | — | **Slice-11 bug 2 fix verified live.** Opening a CF position (real `daysToNextErn=7`) triggered the German emergency-close warning in `daily_brief.actions`. NOW (84d via slice-12 sentinel resolution) correctly did *not* trigger. **Pass.** | n/a |
| F15 | 2026-04-29 | A | 1.F | — | **Vendor-fail resilience verified.** Bad ORATS_TOKEN: all 12 tickers 403, daily_brief still completes; emergency-close calls fail silently (WARN only); existing positions retained; tokens correctly redacted in WARN logs (`token=<REDACTED>`). **Pass.** | n/a |
| F16 | 2026-04-29 | A | 1.G | — | **Lifecycle state machine verified.** open → TAKE_PROFIT_PENDING (no PnL) → CLOSED_PROFIT (PnL = (2.225 − 0.50) × 1 × 100 = 172.50, exact). Invalid transitions (closed → closed_loss, closed → open) raise `LifecycleError("ungültiger Übergang ...")`. **Pass.** | n/a |
| F17 | 2026-04-29 | A | 1.H | **minor** | Sheets export only persists ranked ideas (filtered by Pflichtregeln). When `ranked_ideas == 0` (today's reality before override), no row is written. Result: no audit trail of "I screened the universe and found nothing actionable." | Either (a) write a placeholder row "29.04.2026 — keine Kandidaten — N geprüft" when scan returns empty, or (b) accept that the Macro row alone serves as the daily heartbeat. |
| F18 | 2026-04-29 | A | 1.H | **minor** | Closed trades are never persisted to the Positions tab (only `open` status). Once a trade closes, it disappears from the sheet. **No week-end PnL track.** Forces user to query DuckDB directly. | Add a "Closed-Trades" tab (or expand Positions to include closed states) so the Sheet captures the full history. FR23/FR24 implications. |
| F19 | 2026-04-29 | A | 1.H | **cosmetic** | F4 confirmed: VIX still rendered as `18,46 %` in Macro tab (slice-10 row had `18,01 %`). Same `%`-vs-unitless issue. Both rows have identical date `29.04.2026` with no time component → can't tell which is newer in the sheet. | (a) Drop `%` from VIX rendering. (b) Append a time/seconds column or include in the Datum cell. Pairs with F5 (MacroSnapshot.as_of). |

## Pre-flight residual

- Slice-10 smoke rows still in Sheet (1 SMOKE in Ideas, 1 row 29.04.2026 18,01 % in Macro). Will verify append-only behavior in 1.H.

## Live universe state (Session 1.A re-run, post-slice-12)

```
TICKER  PASS   IVR     EARN    DTE   PREM     REASONS
NOW     False  95.0    84      51    2.17     Rule 6 — Spread 0,15 USD
AAPL    False  53.0    None    51    3.95     Rule 4 + Rule 5 (Datum nicht verfügbar)
MSFT    False  93.0    None    51    6.30     Rule 5 (Datum nicht verfügbar) + Rule 6
GOOG    False  54.0    None    51    5.38     Rule 5 (Datum nicht verfügbar) + Rule 6
META    False  62.0    None    51    12.90    Rule 5 (Datum nicht verfügbar) + Rule 6
AMZN    False  50.0    None    51    4.55     Rule 5 (Datum nicht verfügbar) + Rule 6
NVDA    False  50.0    21      51    4.58     Rule 6 — Spread 0,15 USD
WMB     ERR    —       —       —     —       Kein passender Strike (low option volume)
KMI     False  60.0    77      51    0.35     Rule 6 — Volume 15369 + Spread 0,18 USD
LNG     ERR    —       —       —     —       Kein passender Strike
CF      False  92.0    7       51    3.35     Rule 5 (real, 7 < 8) + Rule 6
NTR     False  90.0    7       51    1.35     Rule 5 (real, 7 < 8) + Rule 6
```

NOW is the strongest candidate for Session 1.C override drill-down (only fails
Rule 6 with a 0,15 USD spread — easy to override consciously).

---

## Severity-grouped summary

### Blockers (1 — fixed in slice 12)
- **F1** — ORATS earnings sentinel (`nextErn='0000-00-00'`) silently invalidating the daily flow.

### Majors (3 — slice-13 candidates)
- **F2** — Empty-brief diagnostics: when `ranked_ideas == []`, no signal as to which rule(s) gated the universe. Most important UX recovery move now that F1 is closed.
- **F7** — Workflow not unblocked by slice-12 alone — distinguishes data-gap from earnings-event but still produces 0 candidates; F2 is the actual unblocker.
- **F11** — `log_idea` + `log_trade` duplicate-row pattern poisons FR9 monthly override review (3 audit rows for 2 decisions in this run).

### Minors (5 — defer to slice-14+ unless they accumulate)
- **F3** — `csp.scan(include_failures=True)` diagnostic mode (pairs with F2).
- **F8** — `format_fbg_mail` Begründung is generic 3-clause template.
- **F9** — `Idea.with_override()` to avoid second ORATS round-trip after gate decision.
- **F12** — `Trade.strike` denormalised vs N+1 `get_idea` calls.
- **F17** — Empty-scan days produce no Ideas-tab heartbeat row.
- **F18** — Closed trades never persist to Sheets.

### Cosmetic (3 — batch into a polish slice)
- **F4** — VIX rendered with `%` sign (markdown + Sheets); should be unitless.
- **F5** — `MacroSnapshot.as_of` missing → no temporal context for the VIX number.
- **F6** — `daily_brief.to_markdown()` no portfolio section even with positions.
- **F10** — Real-time quote drift, no quote-timestamp visible.
- **F19** — Macro tab has identical date strings, no time component to disambiguate same-day rows.

### Verified-passing (no friction logged)
- F13 — Slice-11 bug 1 (Pflichtregel 8 sector cap) ✓
- F14 — Slice-11 bug 2 (earnings emergency-close) ✓
- F15 — Vendor-fail resilience + token redaction ✓
- F16 — Lifecycle state machine + PnL math ✓

## Recommendation

**Slice 13 should be the empty-brief diagnostics (F2) + duplicate-idea fix (F11)**:

1. **F2 (major)** — `daily_brief.to_markdown()` appends per-rule rejection histogram when `ranked_ideas` is empty: "12 Tickers geprüft — 5 × Pflichtregel 5, 4 × Pflichtregel 6, 3 × Pflichtregel 4." Makes the daily flow self-debugging.
2. **F11 (major)** — `log_trade` should reuse an existing matching idea row (or `log_idea` should be folded into `log_trade(persist_idea=True)`). Choose one model. Audit trail must have 1 row per decision.
3. **F3 (minor)** — pairs naturally with F2; `csp.scan(include_failures=True)` is the API-level analog.

Cosmetic batch (F4 + F5 + F19) → polish slice once 5+ accumulate.

If F2/F11 are clean, declare MVP **production-ready** and move to Growth-phase
scope (Wheel, Iron Condor, scheduled cron, Hormuz special-rules).

## Files touched during this session

- `src/csp/models/core.py` — slice-12 sentinel detection
- `src/csp/models/idea.py` — Optional `earnings_distance_days`, format_fbg_mail handling
- `src/csp/filters/pflichtregeln.py` — Rule 5 None case
- `src/csp/daily_brief.py` — Optional propagation through emergency-close logic
- 5 test files updated/extended (+11 tests)
- `_bmad-output/planning-artifacts/shakedown-friction-log-2026-04-29.md` — this file
- `config/settings.toml` — temporarily 12k → 100k for P1, restored

## Sheet state at end of session

- Ideas: 1 SMOKE row (slice-10 baseline) + 0 ideas added today (no candidates passed without override)
- Positions: 1 row — CF (Trade-ID 604e37f0…, opened today)
- Macro: 3 rows total — slice-10 baseline `18,01 %`, plus 2 same-day rows from this session (`18,46 %`, …)
