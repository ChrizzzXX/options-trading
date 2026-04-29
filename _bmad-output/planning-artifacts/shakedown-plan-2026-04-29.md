---
title: 'Shakedown plan — csp-flywheel-terminal MVP'
created: '2026-04-29'
status: 'ready-to-run'
intended_session: 'fresh / next session after slice 11'
---

# Shakedown plan — csp-flywheel-terminal MVP

**Goal:** validate the library through realistic Claude Code conversations, not just unit-test pass/fail. The 10 public functions all work in isolation; this plan stress-tests the *flow* — whether the daily decision loop is fast enough, the German user-facing strings are readable, the FBG-mail format is paste-ready, and the action-strings in `daily_brief` are actionable rather than spam.

The shakedown comes in two tracks. **Track A** is a 1-2 hour single-session simulation that fast-forwards through synthesized scenarios; **Track B** is a 1-2 week real-world routine. Pick one or run both. After either, work through the targeted probes.

This plan was authored at the close of slice 11. The library is at commit `dcbbff0` on `origin/main`, MVP-feature-complete + 2 silent bugs fixed.

---

## 0. Pre-flight checklist (≤10 min)

Before the shakedown begins, verify these exist:

- [ ] **Fresh git pull.** `git pull origin main` — should land on `dcbbff0` or later.
- [ ] **`.env` in place** with `ORATS_TOKEN`, `FMP_KEY`, `GOOGLE_SHEET_ID` (IVolatility key tolerated but unused). Verify with one-liner:
  `uv run python -c "from csp.config import Settings; s = Settings.load(); print('orats:', bool(s.orats_token.get_secret_value())); print('fmp:', bool(s.fmp_key.get_secret_value())); print('sheet:', bool(s.google_sheet_id))"`
  — all three should be `True`.
- [ ] **Fresh DuckDB.** `rm -f data/trades.duckdb` — start with zero open positions.
- [ ] **Spreadsheet reachable.** Open the URL from `GOOGLE_SHEET_ID` in a browser, confirm 3 tabs (Ideas / Positions / Macro) and the test rows from slice-10 smoke. Optionally clear those rows by hand for a clean run.
- [ ] **Setting sanity:**
  - `[portfolio] total_csp_capital_usd` in `config/settings.toml` reflects your real allocation. Default 100k USD — adjust if Pflichtregel #8 should fire at a different concentration.
  - `[universe] allowed_tickers` is the universe you actually want to scan today.
- [ ] **Live market context.** Glance at the real VIX (e.g. `tradingview.com`) so you can sanity-check `csp.macro_snapshot()` against reality.
- [ ] **Pre-commit gates clean** locally — `uv run pytest -q && uv run ruff check src tests && uv run mypy --strict src`. Don't shake down a broken tree.

If any check fails, fix it before starting. The shakedown isn't useful with a half-configured environment.

---

## Track A — Quick simulation (1-2 hours, single session)

A focused walk through every workflow path, fast-forwarding through real-time concerns by injecting synthesized state where needed.

### Session 1.A — Cold-start daily brief

**Persona:** Monday 9:00 AM Berlin. Fresh DuckDB. Ask Claude: *"Was ist heute los am Markt? Was sind die Top-Kandidaten?"*

**Claude should run, in order:**
1. `csp.macro_snapshot()` — returns `MacroSnapshot(vix_close=…)`.
2. `csp.daily_brief(max_ideas=5)` — returns `DailyBrief`.
3. Print `brief.to_markdown()` for human review.

**Verify (success looks like):**
- VIX value matches reality within ±0.5 (live FMP fetch, not the static fallback).
- `daily_brief.ranked_ideas` is non-empty (universe of 12 tickers; today should produce ≥ 1 candidate unless markets are extreme).
- Each idea's reasons / bypassed_rules is German and human-readable.
- The action-strings are *useful*, not template noise.

**Friction signals to log:**
- Ranked list is empty when you'd expect candidates (Pflichtregel #1 IVR-leg too restrictive?).
- Action-string says something obvious you'd ignore ("⚠ X: Sektor-Anteil 0% — Cap fast erreicht" would be a bug surfaced by an empty portfolio).
- Output takes longer than ~30 s (NFR2 violation).
- Any English string user-facing where German was promised.

### Session 1.B — Drill down on one candidate

**Persona:** *"Erzähl mir mehr über Idee #1 — sollte ich die nehmen?"*

**Claude should run:**
1. `csp.idea(ticker, dte=45, target_delta=-0.20)` for the top-ranked ticker.
2. Render `idea.format_fbg_mail()` — full §7.1 layout.
3. Annotate with the reasoning (annualized yield, rule details).

**Verify:**
- The FBG-mail string is paste-ready into a real broker order email. Read it as if you were sending it to your bank's order desk — does anything look wrong?
- All numbers in German locale (1.234,56 USD, 13,3 %, 27.04.2026).
- "Verfall" date is `as_of + dte` calendar days.
- "Begründung" is auto-synthesized but plausible.

**Friction signals:**
- Field missing or wrong (e.g., delta sign flipped, IVR misformatted).
- Reasoning string is generic when you'd want specifics.
- Cash-Bedarf computation off ((strike × contracts × 100) should be exact).

### Session 1.C — Override path

**Persona:** *"Die NOW-Idee ist gerade durchgefallen wegen DTE 56 — aber ich will sie trotzdem nehmen. Override."*

**Claude should run:**
1. `csp.idea("NOW", dte=55, target_delta=-0.20, override=True)` (or pick a real-failing case).
2. `csp.log_idea(idea)` — persist override decision (FR9 audit trail).
3. `idea.format_fbg_mail()` — should show `(Override aktiv)` in the header AND list `Bypassed (Override):` block.

**Verify:**
- Loguru emits a WARN containing "override" + ticker + bypassed-rule count.
- `csp.list_ideas(overrides_only=True)` returns this idea.
- `idea.pflichtregeln_passed is True`, `idea.bypassed_rules` non-empty, `idea.reasons == []` (per slice-3 invariants).

**Friction signals:**
- Workflow requires you to remember to call `log_idea` separately. If that feels error-prone, slice-12 might add an opt-in `csp.idea(..., persist=True)`.

### Session 1.D — Open a position

**Persona:** *"OK, ich nehm die Idee — 1 Kontrakt."*

**Claude should run:**
1. `csp.log_trade(idea, contracts=1, notes="Slice-11 shakedown trade")`.
2. Confirm the returned `Trade` (status=OPEN, cash_secured = strike × 100).

**Verify:**
- Same call run twice returns the same `trade_id` (idempotency on `(ticker, open_date, contracts)`).
- `csp.list_open_positions()` includes it.
- DuckDB: `data/trades.duckdb` exists and contains 1 trade row + 1 idea row.

### Session 1.E — Same-day re-scan (the bug 1 test)

**Persona:** *"Mach den Scan nochmal — sollte ja jetzt etwas anders aussehen, weil ich eine Tech-Position habe."*

**Claude should run:**
1. `csp.scan(max_results=10)` — second run after step 1.D.

**Verify (slice-11 bug 1 fix in action):**
- The scan now sees the open position. With default `total_csp_capital_usd = 100_000` and 1 NOW contract (~$8,800 cash-secured), Tech is at ~8.8 % — well below the 55 % cap; all Tech tickers still pass.
- Edit `[portfolio] total_csp_capital_usd = 12_000` in `settings.toml` and re-scan. Tech is now at ~73 % > 55 % cap. Every Tech idea should now fail with `Pflichtregel 8 — Sektor Technology bereits 73,3 % > 55,0 %` in `reasons`.
- Restore the setting after the test.

**This is the single most important verification in the whole shakedown.** Pre-slice-11 this test would have shown all Tech tickers passing regardless. If the German error string above appears, the fix works in practice.

### Session 1.F — Earnings emergency (the bug 2 test)

Bug 2 needs a real ticker with `daysToNextErn ≤ 7`. You can't simulate this purely in-process — `daily_brief` calls live ORATS for each open ticker.

**Two options:**
- **Option 1 — Wait for it.** If your open NOW position survives until ORATS reports `daysToNextErn ≤ 7`, the next `daily_brief()` will surface the German emergency-close warning.
- **Option 2 — Force it now.** Manually edit a row in DuckDB to fake `open_date` further in the past, OR open a position on a ticker whose earnings are imminent (check ORATS via `csp.idea(...).earnings_distance_days`). Cleanest: pick a ticker on the earnings calendar this week, log a position, run `daily_brief()`, watch the warning fire.

**Verify:**
- `daily_brief().actions` contains `⚠ <ticker> (offen): Earnings in N Tagen — emergency-close vor Earnings erwägen.` for `N ≤ 7`.
- For positions with `N > 7`, no such warning.
- Vendor-fail: temporarily remove `ORATS_TOKEN` from env, run `daily_brief()` — earnings-warning silently dropped (logged WARN), brief still completes.

### Session 1.G — Take-profit pending → close

**Persona:** Tuesday — *"Die NOW-Position ist schon bei +50 %. Mark-as-TP-pending."*

**Claude should run:**
1. `csp.close_trade(trade_id, new_status=TradeStatus.TAKE_PROFIT_PENDING)`.
2. Verify status, no `pnl` yet.
3. Wednesday — *"OK, das Limit ist gefüllt, schließ es."*: `csp.close_trade(trade_id, new_status=TradeStatus.CLOSED_PROFIT, close_premium=Decimal("0.50"))`.
4. Verify final status + `pnl` computation: `(open_premium - 0.50) * contracts * 100`.

**Verify:**
- Invalid transition raises `LifecycleError` *before* DB write. Try `csp.close_trade(tid, new_status=TradeStatus.OPEN)` on a closed trade — should error, status unchanged.
- `csp.list_open_positions()` shows correct membership at each step.

### Session 1.H — Sheets export

**Persona:** *"Sync den heutigen Brief ins Sheet."*

**Claude should run:**
1. `csp.export_to_sheets(csp.daily_brief())` — returns the Sheet URL.

**Verify:**
- Open the URL. Today's row appears in **Macro** with date + VIX.
- Today's ranked ideas appear in **Ideas** (1 row per idea).
- Today's open positions appear in **Positions**.
- All values in German locale (`27.04.2026`, `1.234,56 USD`, `13,3 %`).
- No leaked tokens — search the row for `apikey`, `A4I6B9`, `82326868` (cassette scrubber smoke).
- Append-only: re-run `export_to_sheets` and verify the previous rows are still there + new rows added.

**Friction signals:**
- Column ordering misaligned (header expectations vs. row values).
- Sheets parses USD as plain string (not localized number) — minor but noticeable.

---

## Track B — Real-world shakedown (1-2 weeks)

Use the library every weekday morning at 9:00 AM Berlin (US pre-market). 5-10 min per day. Each session:

1. **Daily brief** — *"Was ist heute los?"* — Claude runs `csp.daily_brief()`.
2. **Decision** — Claude proposes 0-1 trades. You decide.
3. **Position management** — for each open trade, Claude checks status, suggests action, executes if you agree.
4. **Sheets sync** — *"Sync"* — Claude runs `csp.export_to_sheets`.

**Track per session:**
- Wall-clock time from "open Claude" to "decision made".
- Number of times you had to override Claude's interpretation.
- Number of times the German strings felt clunky / robotic.
- Anything that surprised you (good or bad).

**Track over the week:**
- Did Pflichtregel #8 ever fire for real?
- Did the earnings-emergency warning ever fire (and was it actionable)?
- How many overrides did you take? Are they queryable via `csp.list_ideas(overrides_only=True)`?
- Does the Sheet history tell you anything useful at week-end?
- Cron-style timing — do you find yourself wanting `daily_brief` to auto-run?

---

## Targeted probes (run after Track A or B)

### Probe P1 — Pflichtregel #8 explicit stress test

Force the sector-cap rule to fire by either lowering `total_csp_capital_usd` or stacking trades.

**Steps:**
1. Set `[portfolio] total_csp_capital_usd = 20_000` in `settings.toml`.
2. Log 2 NOW contracts (~$17,600 cash-secured = 88 % Tech).
3. `csp.scan()` — every Tech ticker should fail with the Sector-cap reason.
4. `csp.idea("WMB")` — Energy ticker, should still pass (different sector).

**Verify:** the rule fires deterministically, error strings name the actual percentages in German.

### Probe P2 — Pflichtregel #1 IVR-leg

VIX is around 18 today (live). Pflichtregel #1 needs `VIX ≥ 20` OR `IVR ≥ 40`. With VIX < 20, every passing idea passes via the IVR-leg.

**Steps:**
1. `csp.scan()` and inspect the surviving ideas — confirm IVR ≥ 40 on each.
2. Edit `[rules] ivr_min = 95.0` to make IVR very strict.
3. `csp.scan()` — most ideas should now fail Rule 1 (only NOW-like high-IVR names survive).
4. Restore `ivr_min = 40.0`.

### Probe P3 — Override audit trail

Run a session with 2-3 deliberate `override=True` calls + `log_idea` for each. Then:

**Steps:**
1. `csp.list_ideas(overrides_only=True)` — should return the 2-3 overrides.
2. `csp.list_ideas()` — returns those plus all non-override ideas.
3. `csp.list_ideas(since=date(2026, 4, 25))` — date-bounded query.

**Verify:** at month-end, this query is sufficient to satisfy the FR9 monthly review.

### Probe P4 — Settings tweaks deterministic

Change `[rules] dte_min = 50` and `dte_max = 60` to narrow the DTE band. Re-run `csp.scan()`. Result must be **deterministic** across two runs against the same cassettes (NFR20).

Read the rule changes back via `csp.passes_csp_filters(...)` directly to confirm thresholds were picked up.

### Probe P5 — DuckDB invariants

**Steps:**
1. Open a position. Confirm it's in DuckDB.
2. Try `csp.close_trade(tid, new_status=TradeStatus.OPEN)` — should fail (LifecycleError, no DB write).
3. `csp.close_trade(tid, new_status=TradeStatus.CLOSED_PROFIT, close_premium=Decimal("0.50"))` — succeeds.
4. Try `csp.close_trade(tid, new_status=TradeStatus.CLOSED_LOSS)` again — should fail (terminal state).
5. `csp.log_trade(idea, contracts=1)` twice with same idea + contracts — should return the same trade (idempotent).

**Verify:** DuckDB stays clean — no orphan idea rows, no double trades.

### Probe P6 — Vendor-failure resilience

Temporarily corrupt `.env` `ORATS_TOKEN` to a known-bad value. Run `csp.daily_brief()`. Expected: scan returns `[]` (every ticker fails 401), `daily_brief` completes with `ranked_ideas=[]` and macro from FMP fallback if FMP key still works. No crash.

Restore the token. Re-run; behavior returns to normal.

---

## Friction log template

Keep a running log during the shakedown. One Markdown line per friction.

```
| date | track | step | severity | observation | hypothesis |
|------|-------|------|----------|-------------|------------|
| 2026-04-30 | A | 1.B | minor | "Begründung" string is generic — same for every idea | want richer auto-reasoning from rule context |
| 2026-04-30 | A | 1.D | major | log_trade requires me to remember to call log_idea first if override — easy to forget | add csp.log_trade(..., persist_idea=True) default-true |
| 2026-04-30 | P1 | — | minor | Sektor-Anteil rounded to 73 % but real value was 73.3 % — close to threshold cases? | ensure rounding policy is consistent (Decimal vs float) |
```

Severity tiers:
- **blocker** — workflow cannot complete; library crashes or returns visibly wrong data.
- **major** — workflow completes but the user-visible output misleads the decision.
- **minor** — workflow completes correctly, but ergonomically annoying.
- **cosmetic** — string formatting, locale nits.

---

## Success criteria

The shakedown is "done" when **all** of these are true:

- [ ] All Track-A steps completed without a blocker.
- [ ] At least one full Track-B day completed.
- [ ] Probes P1-P6 all run with documented outcomes.
- [ ] Friction log has ≥ 0 entries (zero is ideal, low single digits is normal).
- [ ] No real ORATS / FMP / Google credentials leaked into any tracked file (`rg -i "(token|api[_-]?key|secret|bearer)\s*[:=]" --glob '!_bmad/**' --glob '!.claude/**'`).

The shakedown is "successful" (versus merely complete) when:

- [ ] Time from "open Claude" to "actionable decision" is consistently ≤ 90 s warm cache (NFR3).
- [ ] You'd actually use the library next Monday without me asking.
- [ ] The Sheet's week-of-data tells you something you didn't already know.

---

## After the shakedown

The friction log is the input to the next slice. Group entries by severity:

- **Blockers** → top of slice 12 backlog. Fix immediately.
- **Majors** → slice 12 candidates. Decide priority.
- **Minors** → slice 13+ or deferred-work D-numbers.
- **Cosmetic** → batch into a future "polish slice" once 5+ have accumulated.

If no blockers and ≤ 2 majors: declare MVP **production-ready** and move to Growth-phase scope (Wheel, Iron Condor, scheduled cron, …).

---

## To start the next session

1. Open Claude Code in this repo.
2. Reference this plan: *"We're starting the shakedown. Read `_bmad-output/planning-artifacts/shakedown-plan-2026-04-29.md` and run me through Track A."*
3. Claude follows the plan step-by-step, runs the relevant `csp.*` calls via Bash, surfaces results, asks for your decision at each branch point.

The library is at commit `dcbbff0`. If you've added more commits since, the plan still applies — verify with the pre-flight checklist.
