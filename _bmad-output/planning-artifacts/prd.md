---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
status: complete
completedAt: '2026-04-27'
releaseMode: phased
visionInsights:
  oneLineVision: 'A local terminal cockpit that turns your daily 10 minutes of options research into reproducible, rule-checked trade ideas — and remembers every position so nothing slips through the cracks.'
  differentiator: 'Broker-agnostic, CLI-only, 9 inviolable Pflichtregeln machine-checked, reproducible JSON snapshot per idea, single-user discipline tool — not a multi-tenant dashboard.'
  coreInsight: 'The hard part of CSP-Flywheel is discipline and reproducibility, not the math. The tool makes discipline cheap and forgetting impossible.'
  workingAssumptions:
    - 'Suggest = opinionated ranking by annualized yield (no Kelly/composite scoring in MVP)'
    - 'Track = passive ledger (manual trade entry, exit-flagging in daily-brief; defer wheel state machine)'
    - 'Scope = options only in MVP (direct-stock ideas from Hormuz overlay deferred)'
inputDocuments:
  - docs/Projekt-Brief.md
  - docs/CSP-Strategie.md
  - docs/CSP-Flywheel-Strategie: Deep-Dive-Analyse.md
  - docs/Hormuz-Makro-Overlay.md
  - docs/Optionsstrategien-Kompendium.md
  - docs/MakroÖkonomischer Kontext.md
  - docs/portfolio übersicht.md
  - docs/Portfolio-Uebersicht.csv
  - docs/CSP-Watchlist.csv
  - _bmad-output/project-context.md
documentCounts:
  briefCount: 1
  researchCount: 0
  brainstormingCount: 0
  projectDocsCount: 8
classification:
  projectType: 'python_library + Claude Code as primary interface'
  projectTypePivot: '2026-04-27 — pivoted away from cli_tool. The codebase is a Python library; Claude Code in the terminal is the daily user-facing surface. Typer CLI deferred indefinitely.'
  domain: fintech
  domainSubFlavor: 'options-trading research/decision-support (no execution)'
  complexity: medium
  complexityNotes: 'Was high-by-default for fintech; reduced to medium per user steer — single-user research tool, no PCI/KYC/AML, no order execution. High-rigor pockets remain: Pflichtregeln engine, idempotency, regression anchor.'
  projectContext: greenfield-with-prebaked-spec
  scopingPrinciple: 'Research, suggest, track option trade ideas. Nothing more. Cut everything else from MVP.'
  reproducibilityModel: 'Python is deterministic (Pflichtregeln, snapshots, rankings, persistence). Claude Code is non-deterministic (narration, explanation, conversational pushback). Claude cannot override a Pflichtregel-fail.'
workflowType: 'prd'
project_name: 'csp-flywheel-terminal (options-trading)'
user_name: 'Chris'
date: '2026-04-27'
---

# Product Requirements Document - csp-flywheel-terminal (options-trading)

**Author:** Chris
**Date:** 2026-04-27

## Executive Summary

`csp-flywheel-terminal` is a single-user, conversation-driven research and tracking tool for German-tax-aware options-trading decisions. The user-facing surface is **Claude Code in the terminal**, not a typer CLI. The Python codebase is a **library** of deterministic functions — vendor-data fetching, the nine Pflichtregeln, ranking, persistence, Sheets export — that Claude calls during a daily 10-minute pre-market conversation. Data sources are ORATS (US options, 15-min delayed), FMP (macro context), and IVolatility (EU options, EOD). The tool prepares ideas with explicit reasoning; order entry stays manual at the user's broker. No CLI subcommand polish, no web UI, no execution layer, no multi-user concept — by design.

The problem is not options theory; it is **discipline under time pressure plus the cost of explanation**. A retail or family-office trader running 5–7 simultaneous CSPs forgets exits, drifts past Earnings windows, lets sector-caps creep, and — critically — cannot reconstruct *why* a past trade looked attractive. A pure CLI catches the discipline failures but doesn't explain anything. A pure conversation explains beautifully but invents facts. This tool's split: **Python owns facts and rules (deterministic, regression-tested); Claude owns reasoning and narration (conversational, contextual).** Claude cannot override a Pflichtregel-fail; the rules engine is inviolable.

### What Makes This Special

- **Conversation-first, not CLI-first.** Daily routine is "talk to Claude in the project terminal" — natural language requests like *"what's today's pick?"*, *"why did NOW pass when AVGO didn't?"*, *"show me the 6-week-old idea from the Friday Earnings crash"*. No subcommand taxonomy to memorize. Library functions exposed via Bash + `uv run python -c "..."` (or MCP later).
- **Pflichtregeln as code, not guidance.** Nine filters (VIX/IVR, delta, DTE, OTM%, earnings proximity, liquidity, market-cap, sector-cap, universe) gate every idea inside Python. Failures return explicit German reasons; relaxing any threshold requires an explicit `override=True` argument with logged WARN. Claude can argue but cannot bypass.
- **Determinism / narration split.** All facts (data fetch, rule pass/fail, candidate ranking, snapshot persistence) live in Python and are regression-tested. Claude provides ranking explanation, macro context, and conversational pushback. The NOW-78-Strike from 2026-04-24 reproduces from the VCR cassette regardless of which Claude session calls it.
- **Reproducibility over recommendation polish.** Every idea is persisted with the ORATS/FMP raw response of that moment. The conversation transcript itself is auto-archived in Claude Code history; the *facts* are in DuckDB.
- **Broker-agnostic by deletion, not abstraction.** No broker SDK, no "future plugin point" — just a copy-pasteable order summary the user types into IBKR/FBG manually.
- **Opinionated within the rules.** Candidates ranked by annualized yield (Premium/Strike × 365/DTE × 100). The top result is *the* recommendation, with Claude explaining why. Outside the rule-set there is no opinion.

## Project Classification

- **Project Type:** Python library + Claude Code as primary interface. Public surface is functions (`scan()`, `get_idea(ticker)`, `log_trade(...)`, `list_open_positions()`), not commands. No `typer` CLI in MVP.
- **Domain:** Fintech — options-trading research/decision-support; explicitly **not** order execution. Compliance lens is German-specific (§8b KStG GmbH treatment, JStG 2024 Verlustverrechnung, Anlage KAP) — none of the typical fintech load (PCI/KYC/AML).
- **Complexity:** Medium. High-rigor pockets remain in the Pflichtregeln engine, idempotency guarantees, and the regression anchor; standard rigor everywhere else.
- **Project Context:** Greenfield code (no `src/` exists yet) on top of brownfield-grade pre-existing planning — `docs/Projekt-Brief.md` (~900 lines), `_bmad-output/project-context.md` (178 rules across 7 sections — note: the CLI-specific rules in §"Framework-Specific Rules → typer + rich" need updating to reflect the library pivot), strategy regulations, watchlist, portfolio. The PRD's job is to convert that intent into testable FRs/NFRs and lock down MVP scope.
- **Scoping principle:** Research, suggest, track option trade ideas. Nothing more. Default-deferred: Wheel state machine, multi-strategy plugin abstraction, Hormuz special-rules, Telegram, cron, GmbH/private capital toggle, advanced ranking (Kelly/composite scores), and the typer CLI itself.
- **Architectural pivot (2026-04-27):** Cut typer CLI from MVP. Cost neutral (Chris on Claude Max subscription). Reproducibility model: Python = deterministic facts; Claude = narration + explanation. Pflichtregeln remain inviolable; Claude cannot override.

## Success Criteria

### User Success

The daily 10-minute pre-market routine is a **conversation in Claude Code**, not a sequence of CLI invocations. Success is when the user feels:

- "Worth opening the terminal" because Claude either surfaces an opportunity faster than manual research would have, or flags a discipline trap (Earnings 7 days out, sector-cap creep, thin-liquidity strike) before it becomes an order.
- **Conversational quality:** Claude's pushback ("are you sure NOW is the right pick when AVGO has lower beta?") is *useful*, not noise. Claude doesn't invent facts (because facts come from Python) but does explore tradeoffs.
- **Reproducibility win:** "Show me the NOW idea from 6 weeks ago" surfaces the persisted ORATS snapshot and the Pflichtregeln pass/fail trail, regardless of which Claude session created it.
- **Discipline catch:** Claude refuses to draft an idea that fails a Pflichtregel — even if asked nicely. The rules engine returns the German failure reason; Claude relays it.
- **Exit catch:** Daily-brief conversation flags a 50%-take-pending position the user would have otherwise let drift past 21-DTE.
- **Trust threshold:** After 30 days, the user trusts the top-1 candidate enough to send to FBG without double-checking on Marketchameleon.

### Portfolio / Risk Outcomes (in lieu of "business success")

Single-user tool, no revenue, no growth metric. Honest stand-in is **portfolio-level discipline**, measured against brief §18:

| Metric | 3-month target |
|---|---|
| Ideas surfaced by tool (Pflichtregeln-passing) | ≥ 120 |
| Executed trades documented | ≥ 30 |
| Earnings-window violations | **0** |
| Sector-cap violations | **0** |
| 50%-Profit-Take rate on closed trades | ≥ 50 % |
| Days the daily-brief conversation completed before 15:00 CEST | ≥ 95 % of trading days |
| Pflichtregeln passed-but-overridden via `override=True` | tracked & reviewed monthly |

### Technical Success

- **Performance:** Full universe scan (~40 tickers) ≤ 60 s of Python execution; daily-brief conversation end-to-end ≤ 90 s on warm cache.
- **Reliability:** Same-day reruns are idempotent. Snapshots use `INSERT OR REPLACE` on `(ticker, snapshot_date)`.
- **Reproducibility:** The NOW-78-Strike from 2026-04-24 (Strike 78, DTE 55, Premium 4.30, IVR 94) reproduces exactly from VCR cassette via Python `scan()`. `pytest -k now_regression` is the contract.
- **Test rigor:** ≥ 80 % overall line coverage; **100 %** for `filters/pflichtregeln.py` and `lifecycle/state_machine.py`. All nine Pflichtregeln have isolated unit tests.
- **No live HTTP in CI.** All API responses replayed from VCR cassettes; tokens scrubbed.
- **Library-API quality:** every public function has a complete docstring (Claude reads them to know how to call it), explicit type hints, Pydantic-or-`dict[str, Any]` returns — never raw `print()`. Errors raise typed exceptions.
- **Secrets discipline:** `.env` and `~/.config/csp/sa.json` never in repo; `loguru` filter strips `token`, `apikey`, `Authorization`.
- **Determinism boundary:** Claude can call any library function but cannot bypass `passes_csp_filters()`. There is no Claude-callable `force_idea()` escape hatch.

### Measurable Outcomes

- **Week 2:** MVP acceptance criteria pass — Claude Code runs the full daily-brief workflow conversationally; library handles all facts.
- **Month 1:** 30+ ideas in DuckDB, every one with reproducible ORATS snapshot. Zero Earnings/Sector-Cap violations.
- **Month 3:** 120 ideas, 30 trades, 50 % Profit-Take rate.

## Product Scope

### 🛠 2026-04-29 Scope Amendment — EU coverage removed

**Removed from MVP and Growth scope (binding):** EU equity options coverage via IVolatility. Reason: probe of `IVOLATILITY_API_KEY` against the documented `/equities/eod/options-rawiv` endpoint returned **HTTP 403 "required tariff, access denied"** on Chris's plan tier (verified 2026-04-29 against ALV.DE, ALV, ALV.GR, NOW). The single accessible endpoints (`/equities/eod/single-stock-option`, `…-raw-iv`) require a pre-known option ID and are useless for discovery. Plan upgrade or vendor switch is a future Growth-phase decision, not an open MVP debt.

**What this removes from this PRD:**
- IVolatility integration (FR3 mention, FR7 EU branch, FR13 region-dispatch, FR14 "US + EU together", FR15 "EU candidates", FR18 mixed top-3, FR20 EU-D-1 framing, FR23 EU live P/L) — all read US-only.
- EU ticker support in the universe loader (`region`/`vendor_symbol` columns).
- `IVolatilityClient`, `IVolatilityDataError`, `iv_health_check`.

**What stays:** the `data_freshness` enum (`"live"`, `"eod"`, `"stale"`, `"unavailable"`) — useful generally; just no `region="EU"` paths today. `region: Literal["US", "EU"]` on `Idea` is kept for forward-compat — every Idea has `region="US"` until/unless EU is reactivated.

This amendment supersedes the 2026-04-27 IVolatility addition described in §"Project Scoping & Phased Development". `D22` and `D30` in `deferred-work.md` are now **rejected** (out of scope), not deferred.

### MVP — Minimum Viable Product (Weeks 1–2)

**In scope:**

1. **Public Python library surface** — `import csp`, then call:
   - `csp.daily_brief(date=None) -> DailyBrief` — VIX/Treasury/Sector-Performance + open positions + top-3 candidates + Earnings warnings (next 8 days)
   - `csp.scan(strategy="csp", max_results=10) -> list[Idea]` — full universe run, ranked by annualized yield
   - `csp.idea(ticker: str, dte: int = 45, target_delta: float = -0.20) -> Idea | None` — single-ticker CSP idea (returns None with German reason if any Pflichtregel fails)
   - `csp.list_open_positions() -> list[Position]` — open trades with computed DTE, P/L vs theoretical, exit-action recommendation
   - `csp.log_trade(ticker, strike, premium, dte, open_date, ...) -> Trade` — manual trade-lifecycle entry
   - `csp.close_trade(trade_id, close_premium, close_date, status) -> Trade` — close at 50%-take, 21-DTE-exit, assignment, or expired
   - `csp.passes_csp_filters(...) -> tuple[bool, list[str]]` — the deterministic rules engine, callable directly for diagnostics

   Each function has a complete docstring. Claude reads docstrings to compose calls; users never call them by hand.

2. **Pflichtregeln engine** — all 9 rules, German failure reasons, `override=True` parameter with WARN log. Claude can argue but cannot bypass.

3. **Data layer:** ORATS client (`/cores`, `/strikes`, `/ivrank`, `/summaries`), FMP client (VIX, Treasury, Earnings, Sector-Performance). Pydantic v2 response models. `pytest-vcr` cassettes.

4. **Persistence:** DuckDB with `trades`, `snapshots`, `macro_snapshots` tables. Parquet snapshots per day. `INSERT OR REPLACE`.

5. **Sheets export:** `csp.export_to_sheets()` — one tab (Ideas), updated by direct call. German number locale applied (sheet is for human eyes outside the conversation).

6. **Regression anchor:** `pytest -k now_regression` reproduces NOW-78-Strike from cassette.

7. **Library-usage docs in `README.md`** — short, function-by-function. Aimed at Claude Code (which reads it on first session).

**Explicit non-goals for MVP:**
- ❌ **No `typer` CLI.** No `csp daily-brief` shell command. (Pivoted out 2026-04-27.)
- ❌ No MCP server wrapping the library.
- ❌ No `src/csp/ui/` module. Claude renders markdown directly. German-locale formatting only for Sheets export.
- ❌ No Wheel state machine. Manual position entry only.
- ❌ No Iron Condor, Strangle, Put Credit Spread strategies. CSP only.
- ❌ No Hormuz special-rules engine. Single 55 % sector-cap.
- ❌ **No tax export — entirely out of project scope** (not deferred, removed). Brief §10.1 `csp tax-report` and the `reporting/tax.py` module in brief §5.1 are superseded.
- ❌ No Telegram, no cron, no systemd-timer. Manual conversational invocation only.
- ❌ No GmbH/private capital-mode toggle. One configuration.
- ❌ No Kelly sizing or composite scoring. Annualized yield is the only ranker.
- ❌ No multi-tab Sheets dashboard. Just Ideas.
- ❌ No backtest framework.

### Growth Features (Post-MVP)

In priority order:

1. **Wheel covered-call lifecycle** — state machine for assigned positions, CC scan, `csp.wheel_status(ticker)`.
2. **Hormuz special-rules engine** — `[rules.hormuz_special]`, granular `[rules.sector_caps]`, `csp.makro_status()`.
3. **Multi-strategy scanners** — Iron Condor, Strangle, Put Credit Spread (one per release).
4. **Multi-tab Sheets** — Positions, History, Macro tabs.
5. **Thin CLI wrapper for cron only** — `python -m csp.daily_brief` writes to Sheets, exits non-zero on data-source error. Brought back **only** when scheduled automation is actually needed.
6. **MCP server** — wrap the library if Bash invocation friction becomes real.

### Vision (Future)

- ORATS Backtest API integration for historical strategy validation.
- Telegram alerts for Earnings warnings and exit-pending positions.
- Optional read-only Streamlit view (Claude Code remains the primary surface).

## User Journeys

**Persona (one):** Chris, Family Office Hamburg. Python-affine, terminal-native, runs WSL2, Claude Max subscription. Manages ~16 M EUR liquid + ~5 M EUR FBG anleihen. ~14 % of portfolio (~2.2 M EUR) sits in the active CSP pool. Daily 10-min pre-market routine before US market open. Order entry happens later by mail to FBG advisor or directly in IBKR — the tool never touches it.

This is a single-user tool with no admin, no support staff, no API consumers, no team. The journeys below cover one persona across six **situational** entry points, not multiple roles.

### Journey 1 — Happy Monday Morning (the 80 % case)

**Opening:** 14:25 CEST, coffee, terminal open, Claude Code in `~/dev/projects/options-trading`. Chris types: *"Daily brief."*

**Rising action:** Claude calls `csp.daily_brief()`. Python fetches VIX (FMP) + Treasury curve + sector performance + ORATS `/cores` for all 41 watchlist tickers in parallel. Pflichtregeln engine filters the universe. Top 3 candidates returned with annualized yield, IVR, DTE, sector exposure delta. Claude renders the result as a markdown summary with a one-sentence "today's pick" verdict.

**Climax:** Chris asks *"send the NOW idea in the FBG mail format."* Claude calls `csp.idea("NOW")`, gets the brief §7.1 format with strike, premium bid/ask, mid-point limit, cash-bedarf, ann. yield, next-Earnings check, German rationale. Claude pastes it into the chat.

**Resolution:** Chris copies it into a mail to FBG advisor. Total elapsed: 4 minutes. Sheets-Ideas tab updates in the background via `csp.export_to_sheets()`.

**Capabilities revealed:** parallel ORATS fetch, Pflichtregeln engine, ranking by ann. yield, idea-format generator (German number locale + brief §7.1 layout), Sheets export side-effect.

### Journey 2 — Discipline Catch (the rule actually saves you)

**Opening:** Wednesday, VIX spiked to 24, Chris is excited about volatility. Asks *"AVGO at 200, give me an idea."*

**Rising action:** Claude calls `csp.idea("AVGO", target_delta=-0.20)`. The library checks ORATS `/cores`: `daysToNextErn = 7`. Pflichtregel #5 fails. The function returns `None` with reason list `["Earnings in 7 Tagen (< 8)"]`.

**Climax:** Chris pushes back: *"VIX 24, IVR 65, can we just override?"* Claude has the override option visible (`override=True`) but explains: this is the rule that prevents Earnings-IV-collapse losses; the brief §6.1 logged WARN if used; in the last 12 months no override has been justified after the fact. Suggests the post-Earnings entry instead — *"AVGO Earnings is May 6, let's revisit on May 7 at IVR > 80."*

**Resolution:** Chris says no, doesn't override. The rejection is logged in DuckDB as a "considered, rejected, reason" row (so it shows up in the monthly review). Lesson: the value moment is *not* surfacing the idea, it's blocking it.

**Capabilities revealed:** Pflichtregeln return `(False, [German reasons])`, override mechanic with WARN log, Claude's role as rule-explainer not rule-bypasser, "considered-but-rejected" logging in DuckDB.

### Journey 3 — Post-Earnings IV-Crush Opportunism (the NOW-24.04 setup)

**Opening:** Friday 16:00 CEST, NOW just dropped 17 % after Earnings beat. Chris remembers the 2026-04-24 trade and asks *"is this a setup like 24.04 again?"*

**Rising action:** Claude calls `csp.idea("NOW", dte=55, target_delta=-0.20)` to mirror the historical structure. Library returns: IVR 92, strike $X (8 % OTM), premium yield ~30 % p.a., next Earnings 86 days out (passes), all Pflichtregeln green. Claude pulls the historical 2026-04-24 NOW idea from DuckDB (`csp.list_ideas(ticker="NOW", limit=10)`) and shows side-by-side: same setup, different date, similar metrics.

**Climax:** Chris asks *"what's different?"* Claude flags: VIX is 16 today vs. 22 then (Pflichtregel #1 only passes via IVR-leg, not VIX-leg); sector exposure is 47 % Tech today vs. 38 % then (closer to 55 % cap, less headroom for assignment).

**Resolution:** Chris decides to take a smaller position than 04-24. Logs the trade. The historical comparison is what unlocks confidence.

**Capabilities revealed:** historical idea retrieval from DuckDB (`csp.list_ideas` with filters), portfolio-state-aware ranking (sector exposure delta), the regression-anchor cassette is *also* a daily-use comparison source.

### Journey 4 — Lifecycle Event Mid-Day (50 %-take pending)

**Opening:** Wednesday, Chris opens daily-brief. MSFT $380 strike from 4 weeks ago — premium has fallen from $1.80 to $0.85 (53 % gain).

**Rising action:** `csp.daily_brief()` returns `open_positions` with `MSFT` flagged `action="take_profit"` (50 %-take threshold crossed). Claude surfaces it first in the brief.

**Climax:** Chris asks *"close it at mid-point."* Claude calls `csp.close_trade(trade_id="msft-380-2026-03-30", close_premium=0.85, close_date="2026-04-29", status="closed_profit")`. DuckDB updated. Cash freed up = $38,000.

**Resolution:** Claude proposes *"with that cash, the next Pflichtregeln-passing candidate is JPM at $215, 44 DTE, 9.4 % ann. yield. Open it?"* Chris reviews, sends to FBG.

**Capabilities revealed:** lifecycle state-machine entry/exit (50 %-take, 21-DTE, assignment), `csp.close_trade()` mutation, idempotent re-entry suggestion when capital is freed.

### Journey 5 — Reproducibility 6 Weeks Later (the audit trail)

**Opening:** It's now 2026-06-15. Chris is reviewing closed trades and asks *"why did I open NOW at $78 back in April? what was the setup?"*

**Rising action:** Claude calls `csp.get_idea(trade_id="now-78-2026-04-24")`. DuckDB returns the row including the `raw_json` snapshot column — the entire ORATS `/cores` and `/strikes` response from that exact moment. Claude renders the original idea-format (§7.1) plus the macro context of that date (VIX 22.4, IVR 96, post-Earnings day 0).

**Climax:** Chris asks *"could I have known the assignment risk?"* Claude pulls `correlSpy1y`, `beta1y`, sector-exposure-at-the-time from the snapshot. Walks through the rationale.

**Resolution:** The historical record is intact regardless of which Claude session is asking. If a refactor broke `pytest -k now_regression`, this conversation would be impossible — the regression test *is* this journey's contract.

**Capabilities revealed:** raw-JSON snapshot persistence in DuckDB, idea retrieval by trade_id, the regression test as a user-facing reproducibility guarantee.

### Journey 6 — Data Source Failure (the unhappy path)

**Opening:** 14:30 CEST, Chris asks *"daily brief."* ORATS API returns HTTP 503 (provider outage). FMP also slow.

**Rising action:** `csp.daily_brief()` raises `ORATSDataError("503 — provider unavailable")` after 3 retries. The library has graceful degradation: it falls back to **yesterday's snapshot** from DuckDB and clearly marks every value as `[STALE 2026-04-28]`. Returns a `DailyBrief` object with `data_freshness="stale"` flag.

**Climax:** Claude does NOT pretend things are fresh. Renders the brief with a prominent *"⚠ ORATS is down. The numbers below are from yesterday's close. Do not open new positions on this data."* The Pflichtregeln engine refuses to greenlight any new idea when `data_freshness != "live"` — this is itself a rule, the 10th implicit rule.

**Resolution:** Chris closes the terminal, retries in 30 minutes. Or accepts the stale-data-only-for-status-checking mode (open positions, exit checks).

**Capabilities revealed:** typed exceptions (`ORATSDataError`, `FMPDataError`), graceful-degradation fallback to last good snapshot, freshness flag on `DailyBrief`, Pflichtregeln awareness of data freshness.

### Journey Requirements Summary

The six situational journeys reveal the following capability buckets that the FRs (Step 9) must cover:

1. **Data fetch & cache** — parallel async ORATS+FMP, retry+backoff, typed exceptions, fallback to last DuckDB snapshot, `data_freshness` flag.
2. **Pflichtregeln engine** — 9 rules + 1 implicit (data-freshness gate), German reasons, `override=True` with WARN log, "considered-but-rejected" logging.
3. **Idea generation** — `csp.idea()` returns Idea-or-None, formatted per brief §7.1, with German number locale.
4. **Universe scan + ranking** — `csp.scan()` returns top-N by annualized yield.
5. **Daily-brief composition** — VIX/Treasury/Sector + open positions with action flags + top-3 candidates + Earnings warnings.
6. **Trade lifecycle** — `csp.log_trade()`, `csp.close_trade()`, state-machine transitions (50%-take, 21-DTE, assignment, expired, stop-loss). Snapshot per trade.
7. **Persistence** — DuckDB schema with raw-JSON snapshot, idempotent inserts, historical retrieval (`csp.get_idea`, `csp.list_ideas`).
8. **Sheets export** — best-effort, async, German number locale on the Sheet itself.
9. **Reproducibility** — VCR cassettes, regression test (`pytest -k now_regression`), historical idea retrieval works regardless of session.

## Domain-Specific Requirements

Typical fintech compliance load (KYC/AML, PCI-DSS, payment processing, regional banking regs) does **not** apply — this is a single-user research tool with no money flow, no third-party customer data, no payment surface. The real domain-specific constraints are below.

### Compliance & Regulatory

- **No MiFID II / WpHG investment-advice burden.** The tool generates ideas for the user's *own* trades; it never advises a third party. Order entry stays manual at FBG/IBKR. Inviolable: any feature crossing into "automated routing" or "advice for another person" changes the regulatory posture entirely.
- **No PII, no KYC/AML, no PCI.** No customer data, no payment data, no identity data. Portfolio/trade data is the user's own, stored locally only.
- **GDPR is N/A in practice** — single-user local tool, no controller/processor distinction. If logs or DuckDB ever leave the local machine (e.g., future cloud sync), revisit.
- **German tax context is reference, not feature.** `docs/CSP-Strategie §8` and `docs/CSP-Flywheel-Strategie §12` explain §8b KStG / Anlage KAP / JStG 2024 for the user's understanding of CSP economics. The tool produces no tax artifacts (entirely out of scope).

### Vendor-Data Licensing & Terms

- **ORATS data is paid-license** (subscription). Snapshots stored in DuckDB are for personal use. The Sheets export is a *personal* dashboard — sharing the Sheet with third parties would breach terms.
- **FMP** "Ultimate Annual" plan; same personal-use posture.
- **IVolatility** (added 2026-04-27) — paid-license for EU equity options EOD data. Same personal-use posture; same gitignored-secret discipline. Plan tier and rate-limit TBD on first request and surfaced in `clients/ivolatility.py` constants.
- **Tokens never in repo.** `.env` gitignored, `~/.config/csp/sa.json` outside repo. `loguru` filter strips `token`, `apikey`, `Authorization`, and `IVOLATILITY_API_KEY` substrings.
- **Public-redistribution risk:** if the project goes open-source, all verified-working tokens currently in `docs/Projekt-Brief.md §3` (ORATS, FMP) need to be scrubbed; IVolatility key is only in local `.env`, never in `docs/`.

### Vendor-Data Semantics (the gotchas that bite)

- **ORATS `mktCap` is in thousands USD.** A value of `96524` means $96.5 B, **not** $96.5 M. Pflichtregel #7 (`mktCap ≥ 50_000_000` = ≥ 50 B) depends on this.
- **ORATS `ivPctile1y` is the IVR** (1-year IV percentile), not 1-month.
- **ORATS `daysToNextErn = 0`** may mean "today is earnings day" — treat as Pflichtregel #5 fail (< 8d), not "no upcoming earnings".
- **FMP options endpoints are dead** (deprecated 2025-08-31). Never call `/api/v3/options/*`. All options data goes through ORATS.
- **FMP namespace:** prefer `/stable/...`. `/api/v3/...` and `/api/v4/...` are legacy and partly deprecated.
- **ORATS unauthorized endpoints** under current plan: `/datav2/hist/hv`, `/datav2/history/dailyPrice`, `/datav2/volatility`. Don't call them. If HV is ever needed, derive from FMP daily prices.
- **IVolatility EOD-only.** The endpoint set documented at `https://www.ivolatility.com/api/docs#tag/End-of-Day-(EOD)-Equity-Options` provides EOD equity options data, not intraday. EU candidates are gated by the `eod` freshness state (≤ 1 day old) — never `live`. Do not assume IVolatility's response shape matches ORATS — record a real cassette first and inspect actual field names before writing Pydantic models.
- **EU symbol format** in IVolatility may differ from US conventions (e.g., `ALV.DE` for Allianz on Eurex). The universe loader maps each ticker to its vendor-specific symbol via the `region` column.

### Technical Constraints

- **Determinism boundary:** Pflichtregeln engine, candidate ranking, snapshot persistence are deterministic Python. Claude provides narration only and cannot bypass `passes_csp_filters()`. There is no Claude-callable `force_idea()` escape hatch.
- **Currency precision:** premiums, P/L, cash-secured amounts use `Decimal` end-to-end. Percentages, deltas, IV, IVR are `float`. Conversion only at serialization boundary.
- **Date discipline:** never naive `datetime`. Trade dates are `date` (no time component). Timestamps are UTC. US market hours referenced in `America/New_York`; user-local in `Europe/Berlin`. DTE = calendar days, matching ORATS field semantics.
- **Idempotency required:** same-day reruns must not double-insert. Snapshots use `INSERT OR REPLACE` on `(ticker, snapshot_date)`. Trade lifecycle transitions are at most once per day.
- **Audit trail:** every idea persists the `raw_json` ORATS+FMP response of that moment. Without this, reproducibility journeys fail.

### Integration Requirements

- **ORATS Data API** — primary US options data source. Async client, retry+backoff, rate-limit awareness (1000 req/min).
- **FMP `/stable/` namespace** — VIX, Treasury, Earnings calendar, sector performance.
- **IVolatility EOD Equity Options API** — EU options data source (added 2026-04-27). EOD only, region-dispatched per universe `region` column. Async client + Pydantic + retry+backoff like the others.
- **Google Sheets** — single tab "Ideas" (US + EU candidates in one sheet, distinguished by `region` column) via `gspread` + service-account JSON. Best-effort, fire-and-forget.
- **No broker integration.** Hard architectural constraint, not a "future plugin point."

### Risk Mitigations

| Risk | Mitigation |
|---|---|
| Vendor outage or rate-limit hit | Fall back to last DuckDB snapshot; mark `data_freshness="stale"`; Pflichtregeln gate refuses new ideas on stale data (Journey 6). |
| Token leakage in logs | `loguru` filter strips `token`, `apikey`, `Authorization`; CI grep-checks for these strings in any log artifact. |
| Misreading ORATS field semantics | Pydantic models with explicit `Field(alias=...)` mapping + inline comments where the field's meaning surprises. Regression test against NOW-78 catches arithmetic errors. |
| Refactor breaks reproducibility | `pytest -k now_regression` is a CI gate. Cassette committed to repo. Re-recording requires explicit reason in commit message. |
| Claude hallucinates a fact | Public functions return Pydantic-validated objects, not free text. Claude renders fields, not invents them. Pflichtregeln engine is single source of truth for pass/fail. |
| Pflichtregel `override=True` overused | Logged with WARN; monthly review of overrides; "considered, rejected" rows in DuckDB build the reference base. |
| Scope creep into tax/execution/automation | Memory file `project_scope_no_tax.md` + this PRD's explicit non-goals list. Push back at PR-review time. |

### What's Conspicuously Absent

Typical fintech sections that do **not** appear because they don't apply: KYC/AML, PCI-DSS, Open Banking / PSD2, multi-region data residency, regulatory audit-log retention (only personal `loguru` 30-day rotation), DR/RTO/RPO, SOC 2 / ISO 27001. If any becomes relevant (tool shared with an advisor, or runs as a service for a second user), the regulatory posture changes and this section needs a rewrite. For product-level non-goals (CLI, Wheel state machine, tax export, etc.) see the canonical list in **Product Scope → Explicit non-goals for MVP**.

## Innovation & Novel Patterns

This product is an **excellent execution of existing concepts, not a moonshot.** CSP-Flywheel mechanics are well-documented (CBOE PUT-Index since 1986, Tastylive's 1000+ backtests, Bondarenko 2014/2019). One architectural pattern is genuinely innovative; everything else is boring excellence — by design.

### Detected Innovation Areas

**The Determinism / Narration Split.** Most "AI-assisted trading" tooling falls into one of two camps:

| Camp | How it works | Failure mode |
|---|---|---|
| **LLM-as-suggester** | LLM generates trade ideas from prompt + market data dump | Hallucinations on facts; rules selectively applied; user can't tell when it's wrong |
| **Black-box engine** | Deterministic Python emits "BUY NOW $78" | No explanation; user can't sanity-check rationale; trust degrades over time |

This project's pattern: **Python owns facts and rules; Claude owns reasoning and narration. Claude cannot bypass the rules engine.**

- Every numeric value Claude shows the user comes from a Pydantic-validated Python return — never from Claude's own generation.
- Every Pflichtregel pass/fail is computed in Python, returns `(bool, list[str German reasons])`, and Claude relays it verbatim.
- Claude *can* argue, explore alternatives, and reason about macro context — but cannot override.
- The override mechanic (`override=True` parameter) is Claude-callable, but every use is logged WARN and surfaced in monthly review.

### Market Context & Competitive Landscape

The pattern is not unique to this domain — it's the right answer for any "AI co-pilot for high-stakes deterministic decisions" (medication dosing, financial trading, legal contract review). In retail/family-office options trading specifically, it's underused. Most retail tools are either pure-rule (TastyTrade screeners) or pure-LLM (the recent crop of "ChatGPT for stocks" plugins). The split — deterministic kernel + LLM narrator + inviolable rules engine — is what makes this tool trustworthy for €2.2 M of CSP capital. A formal competitive scan is deferred until post-MVP.

### Validation Approach

1. **Reproducibility test:** `pytest -k now_regression` — given the cassette of 2026-04-24, `csp.scan()` returns NOW-78 as top candidate. This is the contract that proves Python is deterministic.
2. **Override-rate metric:** track `override=True` usage monthly. If overrides exceed ~5 % of generated ideas, the rules engine is too strict (or Claude is being too pushy). If overrides go to zero, the override flag itself is theatrical and can be removed.
3. **Hallucination-spot test:** monthly, manually pick 3 random ideas from DuckDB and verify every numeric value Claude rendered matches the persisted `raw_json`. If any value is "narrated into existence", the architecture is leaking.
4. **Trust threshold (Journey 1 success criterion):** after 30 days, Chris sends top-1 candidate to FBG without double-checking on Marketchameleon.

### Risk Mitigation

| Innovation Risk | Mitigation |
|---|---|
| Claude finds creative ways to bypass Pflichtregeln (e.g., suggesting the user manually override) | Override flag is logged; "considered, rejected" rows in DuckDB; monthly review surfaces the pattern. |
| Library API surface grows in ways Claude exploits (a new function with looser checks) | All public functions go through the same `passes_csp_filters()` gate; new functions need explicit `@requires_pflichtregeln` decorator review. |
| Users mistake Claude's narration confidence for fact-confidence | Explicit "this came from Python" / "this is my reasoning" framing in every Claude response template. |
| Determinism breaks under refactor without anyone noticing | NOW-78 regression test fails CI; Pflichtregeln engine has 100% line coverage; cassette is the contract. |

### What's NOT Innovation

The CSP strategy itself, the Pflichtregeln content, the rules-as-code pattern, the library + Claude Code pattern, DuckDB/Parquet snapshots, Sheets integration, and vendor-API wiring are all **execution**, not innovation. The single innovation is the determinism/narration split.

## Library + Claude Code Specific Requirements

The standard `cli_tool` CSV row no longer applies (we pivoted out). Closest analog is `developer_tool` (library + package). This section merges the relevant questions and skips what doesn't fit. `_bmad-output/project-context.md` already locks ~178 rules — this section *summarizes and references*, not restates.

### Project-Type Overview

**Type:** Python library + Claude Code as primary interface. No CLI in MVP. Public surface is a flat module (`import csp` then call `csp.daily_brief()`, `csp.scan()`, etc.). Claude reads docstrings to compose calls. Bash + `uv run python -c "..."` is the invocation pattern; MCP server deferred.

**Language & runtime:**
- Python 3.12+ (locked, `pyproject.toml` `requires-python = ">=3.12"`)
- Linux / WSL2 primary; no Windows-native or macOS commitment
- Single user, single machine — no cross-host coordination

**Package & dependency management:**
- `uv` (primary) — `uv add <pkg>` writes `pyproject.toml` + `uv.lock`; lockfile committed.
- Poetry as fallback only.
- No optional/extra dep groups for runtime; only `dev` (tests, linters) and `plot` (plotly, deferred).

### Public API Surface (the contract Claude calls)

These are the **only** public symbols Claude is expected to call. Anything else is internal.

| Function | Returns | Purpose |
|---|---|---|
| `csp.daily_brief(date=None)` | `DailyBrief` | Composite: macro snapshot + open positions + top-3 candidates + Earnings warnings (next 8d). |
| `csp.scan(strategy="csp", max_results=10)` | `list[Idea]` | Full universe run, ranked by annualized yield. Pflichtregeln-passing only. |
| `csp.idea(ticker, dte=45, target_delta=-0.20, override=False)` | `Idea` | Single-ticker CSP idea. Always returns a populated Idea; `pflichtregeln_passed: bool` plus `reasons` / `bypassed_rules` carry the gate verdict. |
| `csp.list_open_positions()` | `list[Position]` | Open trades with computed DTE, P/L vs theoretical, exit-action recommendation. |
| `csp.log_trade(ticker, strike, premium, dte, open_date, ...)` | `Trade` | Manual trade-lifecycle entry — opens a Position. |
| `csp.close_trade(trade_id, close_premium, close_date, status)` | `Trade` | Close at 50%-take, 21-DTE-exit, assignment, expired, or stop-loss. |
| `csp.get_idea(trade_id)` | `Idea` | Historical retrieval — the audit-trail surface (Journey 5). |
| `csp.list_ideas(ticker=None, limit=10, ...)` | `list[Idea]` | Historical idea search with filters. |
| `csp.passes_csp_filters(core, strike, macro, portfolio)` | `tuple[bool, list[str]]` | The deterministic rules engine, callable directly for diagnostics. |
| `csp.export_to_sheets()` | `dict[str, Any]` | Push current Ideas to the single Sheets tab. Best-effort. |

**Return-type discipline:** every public function returns either a Pydantic model or a typed primitive. **Never `print()`. Never bare `str` "result text".** Claude reads model fields and renders markdown — Python doesn't format for humans.

**Error-type discipline:** typed exceptions Claude can catch and explain.
- `ORATSDataError` — vendor returned 5xx after retries, or 4xx (bad token, unauthorized endpoint).
- `FMPDataError` — same for FMP.
- `PflichtregelError` — Pflichtregeln engine code/data integrity error (a normal "rule failed" returns `(False, [reasons])`, not this).
- `IdempotencyError` — same-day rerun would create a duplicate that `INSERT OR REPLACE` can't reconcile.
- `ConfigError` — settings.toml or .env missing/invalid.

### Documentation Strategy (Claude is the primary reader)

1. **Docstrings on every public function** — purpose (1 line), parameter semantics (especially non-obvious ones), return-shape with named fields, failure modes (which exceptions when), one-line usage example.
2. **`README.md` — function-by-function reference** — short, structured. First paragraph tells Claude: *"This is a library for German-tax-aware CSP options-trading research. The Pflichtregeln engine is inviolable — Claude cannot bypass `passes_csp_filters()`. Here are the 10 functions you can call."* One section per function.
3. **`docs/CLAUDE_USAGE.md`** — daily-brief workflow as a 30-line worked example, written as Claude-talking-to-Claude.
4. **No Sphinx, no MkDocs, no auto-generated HTML.** Markdown only.

### Code Examples (Claude's bootstrap pattern)

The README's first usage example must compile and run as written:

```python
from csp import daily_brief, idea, log_trade

brief = daily_brief()
# DailyBrief(date=2026-04-27, macro=MacroSnapshot(vix_close=18.7, ...),
#            open_positions=[...], top_candidates=[...], earnings_warnings=[...])

now_idea = idea("NOW", dte=55, target_delta=-0.20)
if not now_idea.pflichtregeln_passed:
    print("No idea — Pflichtregel failures:", now_idea.reasons)
else:
    print(now_idea.format_fbg_mail())  # available once formatter slice ships
```

### Configuration

- `pydantic-settings` reads `.env` (secrets) + `config/settings.toml` (Pflichtregeln thresholds, universe, sector caps).
- Settings instantiated once at module import, available as `csp.settings`.
- All thresholds come from settings — never hardcoded. `override=True` paths respect the same threshold semantics.
- Universe loaded from `config/universe.csv` at startup; portfolio from `config/portfolio.csv`. Both required for Pflichtregeln #8 and #9.

### Output Formats

- **In-process / Claude-facing:** Pydantic models. Claude renders markdown from fields.
- **Persisted (DuckDB):** primitive columns + `raw_json` text column carrying original ORATS/FMP response. `INSERT OR REPLACE` for idempotency.
- **Snapshots (Parquet):** `data/snapshots/YYYY-MM-DD/{ticker}.parquet`.
- **External (Google Sheets):** German number locale (`1.234,56 USD`, `13,3 %`). Single tab "Ideas".
- **Logs (`logs/csp.log`):** `loguru`-structured, German messages, secrets stripped, 30-day rotation.

### Skipped Sections (per CSV)

- ❌ `visual_design` — no GUI.
- ❌ `ux_principles` — Claude renders markdown; no UX surface.
- ❌ `touch_interactions` — N/A.
- ❌ `store_compliance` — not distributed via package registries.

### Implementation Considerations

- **Module structure** stays as in brief §5.1 (`src/csp/{clients,models,strategies,filters,ranking,lifecycle,persistence,reporting}/`) — minus the deleted `ui/` directory and the deleted `reporting/tax.py`.
- **Async-first I/O:** all API clients use `httpx.AsyncClient`. Public library functions (`scan`, `idea`, `daily_brief`) wrap async via `asyncio.run()` so Claude calling them via `uv run python -c "..."` doesn't manage event loops.
- **Strategy plugin abstraction** deferred until Iron Condor is actually built (Growth phase). MVP has only CSP; no premature `AbstractStrategy` base class.
- **Pre-commit gates:** `ruff check`, `ruff format --check`, `mypy --strict`, `pytest -q`. All four must pass before commit.

## Project Scoping & Phased Development

The Product Scope section above defines MVP / Growth / Vision in detail. This section adds the **strategic MVP rationale**, **risk analysis**, and the **single-page strategic summary** that the scope section doesn't cover.

### MVP Strategy & Philosophy

**MVP type:** **Problem-solving MVP** (vs. experience / platform / revenue MVP).

The problem is "discipline under time pressure plus the cost of explanation." The MVP succeeds when:
- The Pflichtregeln engine + ranking + persistence work well enough that Chris's daily 10-minute routine produces a reproducible, gated CSP candidate.
- The conversation-driven surface (Claude Code calling library functions) feels natural enough that Chris doesn't reach for the old manual workflow on Marketchameleon.
- The NOW-78 regression test reproduces from cassette — proving determinism is intact.

We are **not** trying for an experience MVP (no UX polish required — Claude renders markdown), a platform MVP (single-user, no plugin marketplace), or a revenue MVP (no monetization). Just: solve the discipline problem for one user, well.

**Resource requirements (honest estimate):**
- 1 developer (Chris himself, with Claude Code as pair) — no team.
- Approximate effort: 8–12 working days for MVP, per the brief's "Weeks 1–2" target (Phase 1 in brief §12).
- Dependencies: ORATS + FMP API access (provisioned), Google service-account JSON for Sheets (provisioned), `uv` toolchain (standard).

**Delivery mode:** **Phased.** Brief §12 explicitly defined 6 phases. The current PRD respects that as MVP / Growth / Vision. Frontmatter `releaseMode: phased`.

### Scope Reductions — Audit Trail

The MVP / Growth / Vision breakdown is canonical in the **Product Scope** section above. All scope reductions in that section were either the user's explicit request (tax export removal, CLI pivot away from typer, simplicity steer) or recommendations confirmed by the user (Wheel state machine, multi-strategy abstraction, Hormuz special-rules deferred to Growth). Nothing was silently de-scoped. The IVolatility integration (added 2026-04-27) was the only scope **addition** during PRD authoring.

### Risk Analysis

#### Technical Risks

| Risk | Probability | Mitigation |
|---|---|---|
| ORATS API behavior diverges from brief §3 documentation (endpoints removed, fields renamed, plan downgraded) | **Medium** — observable from FMP `/api/v3/options` deprecation pattern. | Async client with typed exceptions per-endpoint; Pydantic models with `populate_by_name=True`; each Pflichtregel-relevant field has a unit test that asserts the field exists. Cassettes pinned. |
| Claude rendering doesn't match brief §7.1 idea-format (German number locale wrong, layout drifts) | **Low–Medium** — Claude is good at format-following but needs explicit examples. | `docs/CLAUDE_USAGE.md` has the §7.1 worked example. `Idea.format_fbg_mail()` is a Python method (not Claude responsibility). |
| The 9 Pflichtregeln + region-aware freshness gate produce **zero candidates** under normal market conditions | **Low–Medium** — needs empirical check. | If zero-candidates becomes routine, threshold review (especially Pflichtregel #1 lock-out in calm-VIX periods). Override mechanic exists. Tracking override-rate is part of validation. |
| **EU options liquidity** is structurally thinner than US ADRs — Pflichtregel #6 (≥ 50 000 contracts/day) may produce **zero EU candidates** even on names that pass mkt-cap and earnings | **Medium–High** — known characteristic of EU options markets. | Empirical discovery in week 1. If zero EU candidates routinely, the EU integration is "available but unused" — acceptable for MVP. Growth-phase response would be an EU-tier rule (lower threshold ~10 000 contracts) similar to the deferred Hormuz overlay. Do **not** preemptively add the EU-tier in MVP. |
| IVolatility response shape diverges from assumed schema, breaking Pydantic models on day 1 | **Medium** — common with new vendor integration. | First implementation task: record one real cassette for `ALV.DE` (or whichever EU ticker the user picks first) via `csp.iv_health_check()` and **inspect actual field names before writing Pydantic models**. Don't write models from docs alone — verify against real data. |
| `pytest -k now_regression` becomes flaky (cassette drifts, library refactor breaks deterministic ordering) | **Medium** — VCR integration tests are infamous for this. | Cassette is the contract. If it breaks, fix the test or the code; never re-record without explicit reason in commit message. Sort-key stability for ranked output (tie-break on ticker alphabetical). |
| Claude session forgets the deterministic-vs-narration boundary and starts hallucinating numbers | **Low** — Claude is generally well-behaved with typed Pydantic returns. | `README.md` first paragraph hammers the rule. Monthly hallucination-spot test. Repeated drift triggers MCP-server upgrade where Claude is *forced* to call functions. |
| Library API surface grows organically and becomes inconsistent | **Medium** — happens to every library. | The 10 functions are the contract for MVP. New public functions require PR-review against this contract. |

#### Portfolio / Outcome Risks (in lieu of "market risks")

| Risk | Mitigation |
|---|---|
| Tool surfaces ideas Chris would have surfaced manually anyway — no real value-add | Track override-rate, "considered-but-rejected" log, and trust-threshold metric (Journey 1). If after 30 days Chris still double-checks every pick on Marketchameleon, the tool isn't earning its keep — re-evaluate. |
| Pflichtregeln are too strict and Chris stops using the tool because it always says "no" | Override mechanic is the safety valve. Monthly review tracks override-rate. If overrides exceed 5%, threshold-tuning is overdue. |
| Tool surfaces an idea that turns into a large loss (Stop-Loss triggered at 200%) | The Pflichtregeln don't promise zero losses — they promise *disciplined* losses (8% OTM, Stop-Loss at 200%, sector caps). Chris's risk framework is the safety net. |
| Macro regime shift (Hormuz de-escalation, sudden VIX collapse, sector rotation) makes the universe + Pflichtregeln + sector caps wrong | Hormuz overlay deferred to Growth — but even without it, monthly review of override-rate + portfolio outcomes is the human-in-the-loop check. The tool isn't autonomous. |

#### Resource Risks

| Risk | Mitigation |
|---|---|
| Solo developer gets blocked on a Pydantic-v2 migration quirk, an `uv` lock issue, or an ORATS auth failure | Claude Code is the pair. `pytest-vcr` cassettes mean development is offline-capable. All third-party tokens already provisioned and verified. |
| Effort exceeds 12 days because the brief underestimated some module | MVP scope explicitly excludes anything with hidden complexity. The 10 public functions are surgical. If a function takes >2 days, that's a signal to check the simplicity steer. |
| Chris's calendar time gets compressed by family-office work | Phased delivery means MVP can ship without Growth. Single-user tool, single-user timeline. |
| Tooling drift (Python 3.12 → 3.13, `httpx` major version, `pydantic` → v3) breaks the codebase between sessions | Locked Python version, `uv.lock` committed, `mypy --strict` and `pytest -q` as pre-commit gates catch incompatibilities at commit time. |

### Single-Page Strategic Summary

- **What we're building:** smallest disciplined CSP options-research tool, conversation-driven via Claude Code, library-shaped Python under the hood.
- **What we're NOT building (and why):** anything with hidden complexity (CLI polish, Wheel state machine, multi-strategy abstraction, tax export, automation). The simplicity steer is load-bearing.
- **What success looks like at week 2:** daily-brief conversation works end-to-end. NOW-78 regression test green. Sheets-Ideas tab updates. `pytest -q` passes with ≥80% coverage.
- **What success looks like at month 3:** brief §18 numbers (120 ideas, 30 trades, 50% Profit-Take rate, zero Earnings/Sector-Cap violations).
- **The single innovation:** determinism / narration split — Python facts, Claude reasoning, inviolable rules engine.
- **Biggest risk to watch:** Pflichtregeln producing zero candidates in calm-VIX periods (Pflichtregel #1 lock-out) **and** EU options liquidity producing zero EU candidates after Pflichtregel #6 (≥ 50 000 contracts/day). Track both empirically in week 1.

## Functional Requirements

This list is the binding capability contract — anything not listed will not exist in the final product unless explicitly added later. 42 FRs across 8 capability areas. IVolatility integration (added 2026-04-27) folded in.

Actors:
- **The user** (Chris) — initiates conversations and records lifecycle events.
- **Claude Code** — calls library functions on the user's behalf; relays results.
- **The library** — the Python module; deterministic.

### Data Acquisition & Freshness

- **FR1:** The library can fetch ORATS `/cores`, `/strikes`, `/ivrank`, and `/summaries` data for any single US-region ticker.
- **FR2:** The library can fetch FMP `/stable/` macro endpoints (VIX history, Treasury rates, earnings calendar, sector performance) for daily-brief context.
- **FR3:** The library can run universe-wide vendor data fetches in parallel for all watchlist tickers, respecting per-vendor rate limits (ORATS 1000 req/min; IVolatility plan-tier TBD).
- **FR4:** The library can retry failed vendor calls up to 3 times with exponential backoff for 5xx and 429 errors; 4xx errors raise immediately.
- **FR5:** The library can persist every successful vendor response as a snapshot tagged with ticker, region, and trade date, enabling later replay.
- **FR6:** The library can detect when live data fetch fails and fall back to the most recent persisted snapshot, flagging the result as `data_freshness="stale"`.
- **FR7:** The library applies a **region-aware** data-freshness gate before generating new trade ideas: US candidates require `data_freshness="live"`; EU candidates require `data_freshness="eod"` AND snapshot ≤ 1 day old. Other states (`stale`, `unavailable`) block new-idea generation regardless of Pflichtregeln pass/fail.

### Pflichtregeln Rule Enforcement

- **FR8:** The library can evaluate the 9 Pflichtregeln (VIX/IVR, delta, DTE, OTM%, earnings proximity, liquidity, market-cap, sector-cap, universe membership) against any candidate strike + macro snapshot + portfolio state, returning `(passed: bool, reasons: list[str])` where reasons are German.
- **FR9:** The library can accept an `override=True` argument that bypasses Pflichtregeln gating, log the override at WARN level, and persist the override decision in DuckDB for monthly review.
- **FR10:** The library can persist "considered-but-rejected" candidate evaluations — including which Pflichtregeln failed and the German reasons — so monthly review can quantify which rules trigger most often.
- **FR11:** The user (or Claude Code) can call `csp.passes_csp_filters(...)` directly to test a hypothetical strike against the current rule set without generating a full Idea.
- **FR12:** The library can read all Pflichtregeln thresholds (`vix_min`, `ivr_min`, `delta_min`, `delta_max`, `dte_min`, `dte_max`, `strike_otm_min_pct`, `earnings_min_days`, `options_volume_min`, `spread_max_usd`, `market_cap_min_billion`, `sector_cap_pct`) from `config/settings.toml` — no thresholds hardcoded.

### Idea Generation & Ranking

*Revision 2026-04-29:* FR13 return shape amended from `Idea | None` to always-`Idea` (override-pathway annotation lives on the model). See `_bmad-output/implementation-artifacts/spec-idea-singleticker.md` §Design Notes.

- **FR13:** The library can generate a single-ticker CSP idea given `(ticker, dte, target_delta, as_of=None, override=False)`, returning a populated `Idea` model whose `pflichtregeln_passed: bool` indicates rule-gate pass/fail; on failure `Idea.reasons` carries German rule descriptions. With `override=True`, the gate is bypassed: `pflichtregeln_passed=True`, `Idea.bypassed_rules` carries the German strings of the ignored rules, plus a loguru WARN. Region dispatch happens internally based on universe metadata (US-only in MVP slice 3; EU dispatch follows in the IVolatility-client slice).
- **FR14:** The library can scan the entire universe (US + EU together) and return up to N candidates ranked by annualized yield (`Premium/Strike × 365/DTE × 100`), filtered to Pflichtregeln-passing only.
- **FR15:** The library can render an idea in the brief §7.1 FBG-mail format (German number locale, every field per the §7.1 example) via `Idea.format_fbg_mail()`. EU candidates include the EU-native option symbol per IVolatility convention.
- **FR16:** The library can compute and expose annualized yield, OTM percentage, sector-exposure delta vs current portfolio, and Earnings-distance-days as `Idea` fields.
- **FR17:** The library can deterministically tie-break ranked output (e.g., alphabetical by ticker on equal annualized yield) so `scan()` is fully reproducible across runs.

### Daily-Brief Composition

- **FR18:** The library can compose a `DailyBrief` containing: today's macro snapshot (VIX close, VIX futures front-month, Treasury 10Y, S&P 500 close, sector performance), all open positions with computed action recommendations, top-3 Pflichtregeln-passing candidates (US + EU mixed, ranked by annualized yield), and Earnings warnings for the next 8 days.
- **FR19:** The library can flag open positions with one of `action="take_profit"` (50%-take threshold reached), `action="dte_21_exit"` (21-DTE threshold reached), `action="emergency_close"` (Earnings within 8 days), `action="stop_loss"` (premium ≥ 200% of original), or `action="hold"`.
- **FR20:** The library can attach a `data_freshness` flag (`"live"`, `"eod"`, `"stale"`, `"unavailable"`) per data segment in every `DailyBrief` so Claude Code can render appropriate warnings — including a clear "EU candidates are D-1 EOD" framing when the user asks about EU ideas during US trading hours.

### Trade Lifecycle Management

- **FR21:** The user can record a newly opened trade by calling `csp.log_trade(ticker, strike, premium, dte, open_date, sector, region, ...)`, which persists a `Trade` to DuckDB with status `"open"` and a unique `trade_id`. `region` is required for downstream P/L pricing dispatch.
- **FR22:** The user can close a trade by calling `csp.close_trade(trade_id, close_premium, close_date, status)` with one of: `"closed_profit"`, `"closed_neutral"`, `"closed_loss"`, `"assigned"`, `"expired_otm"`.
- **FR23:** The library can compute live P/L for each open position. For US positions this uses ORATS live data; for EU positions this uses IVolatility EOD data (D-1, marked as such in the output).
- **FR24:** The library can transition trade status idempotently — repeated same-day `close_trade` calls produce the same final state.

### Persistence & Historical Audit Trail

- **FR25:** The library can persist every generated idea with the raw vendor JSON response of that moment (ORATS for US, IVolatility for EU), stored in a `raw_json` column in DuckDB along with a `source_vendor` discriminator.
- **FR26:** The library can retrieve any historical idea by `trade_id` via `csp.get_idea(trade_id)`, including the raw JSON snapshot and source vendor.
- **FR27:** The library can search historical ideas via `csp.list_ideas(ticker=None, region=None, from_date=None, to_date=None, status=None, pflichtregeln_passed=None, limit=10)`.
- **FR28:** The library can guarantee idempotent same-day reruns — snapshots use `INSERT OR REPLACE` keyed on `(ticker, snapshot_date)`.
- **FR29:** The library can reproduce the NOW-78-Strike from 2026-04-24 (Strike 78, DTE 55, Premium 4.30, IVR 94) from the recorded ORATS VCR cassette, validated by `pytest -k now_regression` as a CI gate. (Once an EU regression anchor is established empirically, a parallel `eu_regression` test will be added — not in MVP because there is no historical reference trade yet.)

### External Reporting (Google Sheets)

- **FR30:** The library can push the current Pflichtregeln-passing ideas list (US + EU combined) to a single Google Sheets tab named `Ideas` via `csp.export_to_sheets()`. The sheet includes a `Region` column distinguishing US/EU.
- **FR31:** The library can render Sheets values in German number locale (`1.234,56 USD`, `13,3 %`, dates as `27.04.2026`). EU prices render in `EUR` if vendor data is in EUR, otherwise USD.
- **FR32:** The library can complete Sheets export as a best-effort, fire-and-forget operation — Sheets failure must not raise to the caller; failure is logged and the daily-brief still completes.

### Library API & Documentation

- **FR33:** Each public library function has a complete docstring stating purpose, parameter semantics (especially non-obvious ones), return shape with named fields, and failure modes (which exceptions raise when).
- **FR34:** The library exposes a flat top-level module (`import csp`); the 10 public functions defined in the Project-Type section are the binding contract for MVP.
- **FR35:** The repository contains a `README.md` with a function-by-function reference, a one-paragraph "Claude, read this first" header explaining the determinism/narration boundary, a section listing the three vendor integrations (ORATS, FMP, IVolatility) and which region each serves, and a working code example that compiles as written.
- **FR36:** The repository contains `docs/CLAUDE_USAGE.md` with the daily-brief workflow as a worked example written as Claude-talking-to-Claude, including a worked EU-candidate handling example.
- **FR37:** The library raises typed exceptions (`ORATSDataError`, `FMPDataError`, `IVolatilityDataError`, `PflichtregelError`, `IdempotencyError`, `ConfigError`) whose messages Claude can relay verbatim to the user.

### EU Options Data (IVolatility) — Region-Aware Capabilities

- **FR38:** The library can fetch IVolatility EOD equity options data for any EU-region ticker via `IVolatilityClient`, mapping the ticker to its vendor-specific symbol (e.g., `ALV.DE` for Allianz on Eurex) using the universe `region` and `vendor_symbol` metadata.
- **FR39:** The universe loader recognizes a `region ∈ {"US", "EU"}` column in `config/universe.csv` and dispatches each ticker to the appropriate vendor (ORATS for US, IVolatility for EU). Tickers without a `region` value fail loud, not silent — `ConfigError` raises at startup.
- **FR40:** The Pflichtregeln engine evaluates EU candidates using the **same 9 rules with the same thresholds** — no relaxation in MVP. Pflichtregel #1 (VIX/IVR) uses the candidate's IVR (computed from IVolatility data) for the IVR-leg; the VIX-leg refers to the US `^VIX` regardless of region (a single global volatility-regime signal is sensible).
- **FR41:** The library exposes a `csp.iv_health_check()` diagnostic that fetches one well-known EU ticker (default `ALV.DE`) and reports IVolatility connectivity, response shape, and any field-mapping mismatches — used during initial cassette recording and quarterly schema-drift checks.
- **FR42:** Live cassettes for IVolatility live under `tests/cassettes/ivolatility/`; the IVolatility API key is scrubbed from cassettes via VCR `filter_query_parameters=["apiKey", "api-key"]` and `filter_headers=[("X-API-Key", "REDACTED")]` (final filter list confirmed once the actual auth scheme is verified against the docs).

### Self-Validation

- ✅ Every MVP-scope item maps to at least one FR.
- ✅ Domain requirements covered (vendor freshness gate ↔ FR6/7/20; idempotency ↔ FR24/28; secret-handling at NFR layer).
- ✅ Innovation pattern covered (determinism / narration split ↔ FR33/34/37 emphasize Pydantic returns and typed exceptions; FR9 + FR10 enforce override-tracking).
- ✅ Each Journey traces to FRs:
  - Journey 1 (Happy Monday) → FR3, FR14, FR15, FR18, FR30
  - Journey 2 (Discipline Catch) → FR8, FR9, FR10, FR13
  - Journey 3 (Post-Earnings IV-Crush) → FR13, FR16, FR27
  - Journey 4 (Lifecycle Event) → FR19, FR22, FR23
  - Journey 5 (Reproducibility 6 weeks later) → FR25, FR26, FR29
  - Journey 6 (Data Source Failure) → FR4, FR5, FR6, FR7, FR20, FR37
- ✅ IVolatility integration covered (FR38–FR42 plus amended FR1/FR3/FR5/FR7/FR15/FR20/FR21/FR23/FR25/FR27/FR30/FR31/FR35/FR36/FR37).
- ✅ Each FR states *what* exists, not *how* it's implemented (multiple implementations possible).

**Conspicuously absent (by scope decision):** No FRs for tax export, CLI, Wheel state machine, multi-strategy, Hormuz special-rules, MCP server, automation/cron, broker integration, or EU-tier-relaxed Pflichtregeln. All correctly missing per the **Product Scope → Explicit non-goals for MVP** list.

## Non-Functional Requirements

Selective approach. Skipping categories that don't apply to a single-user local research tool: **Scalability** (single user, single machine), **Accessibility** (no GUI, no public audience), **Internationalization** (settled — German for output/comments, English for identifiers), **Multi-tenancy** (N/A), **Disaster recovery / RTO/RPO** (single-user local; user owns the risk).

### Performance

- **NFR1:** A full universe scan (~40 tickers across US + EU regions) completes in ≤ 60 s of Python wall-clock time on warm cache.
- **NFR2:** A `csp.daily_brief()` call completes Python execution in ≤ 30 s on warm cache (`live` ORATS data, `eod` IVolatility data D-1).
- **NFR3:** End-to-end daily-brief conversation in Claude Code (Python work + Claude reasoning) completes in ≤ 90 s on warm cache.
- **NFR4:** A single `csp.idea(ticker)` call completes in ≤ 5 s for a single US ticker (one ORATS round trip + Pflichtregeln evaluation), ≤ 7 s for a single EU ticker (IVolatility EOD + Pflichtregeln).
- **NFR5:** ORATS calls are parallelized across the universe via `asyncio.gather()`; IVolatility calls similarly. Sequential vendor calls within a single ticker are acceptable; sequential calls across tickers are not.
- **NFR6:** `csp.export_to_sheets()` is asynchronous and fire-and-forget; it must not block the daily-brief return path. Sheets latency does not contribute to NFR2 or NFR3.

### Security & Secrets

- **NFR7:** No API tokens or service-account material in the repository. `.env` (containing `ORATS_TOKEN`, `FMP_KEY`, `IVOLATILITY_API_KEY`, `GOOGLE_SHEET_ID`) is gitignored. The Google service-account JSON lives at `~/.config/csp/sa.json`, outside the repo by definition.
- **NFR8:** `loguru` is configured with a filter that strips the substrings `token`, `apikey`, `api-key`, `Authorization`, `IVOLATILITY_API_KEY`, and the Google service-account email from any log output.
- **NFR9:** `pytest-vcr` cassettes scrub vendor authentication (query params, headers) before being committed. CI grep-checks every cassette and every log artifact for known token prefixes (`82326868-`, `A4I6B9`, `eLlVI`) and fails the build on hit.
- **NFR10:** No automatic order routing, no broker SDK, no Authorization header to anything other than ORATS / FMP / IVolatility / Google Sheets. New outbound HTTP destinations require explicit PR-review.
- **NFR11:** The IVolatility key is the user's responsibility to provision in `.env`; the library raises `ConfigError` at startup if `IVOLATILITY_API_KEY` is missing AND any universe ticker has region `EU`.

### Reliability & Idempotency

- **NFR12:** Same-day reruns of `csp.daily_brief()` and `csp.scan()` are idempotent — DuckDB row counts do not grow on a second invocation; snapshots use `INSERT OR REPLACE` keyed on `(ticker, snapshot_date)`.
- **NFR13:** Trade-lifecycle transitions are at-most-once per day per `trade_id` — repeated `csp.close_trade()` calls with the same arguments produce the same final state.
- **NFR14:** Vendor outages do not crash the library — `ORATSDataError`, `FMPDataError`, `IVolatilityDataError` are caught and surfaced via the `data_freshness` flag (`"stale"` or `"unavailable"`); the daily-brief still completes with a clear warning.
- **NFR15:** Sheets export failures are best-effort — they log a WARN, do not raise to the caller, and do not prevent persistence to DuckDB (the system of record is local).
- **NFR16:** Daily-brief reliability target: completes successfully before 15:00 CEST on ≥ 95 % of US trading days.

### Reproducibility & Audit

- **NFR17:** Every generated idea persists the full raw vendor JSON response in DuckDB's `raw_json` column. A historical idea retrieved via `csp.get_idea(trade_id)` 6 months later contains exactly the data the original Pflichtregeln evaluation saw.
- **NFR18:** The NOW-78-Strike from 2026-04-24 reproduces from `tests/cassettes/orats/cores_NOW.yaml` and `strikes_NOW.yaml`. `pytest -k now_regression` is a CI gate; failure blocks merge.
- **NFR19:** VCR cassettes are committed to the repo. Re-recording a cassette requires an explicit reason in the commit message. CI's `--record-mode=none` (default) blocks accidental re-records.
- **NFR20:** `csp.scan()` produces fully deterministic output given identical input data — including tie-break by ticker alphabetical when annualized yields are equal. Run twice on the same cassettes, byte-identical result.
- **NFR21:** Every Pflichtregel evaluation produces an audit-trail row in DuckDB: ticker, timestamp, pass/fail, German reason list, override-flag-used (true/false). Monthly review querying this table is the override-rate metric source.

### Maintainability

- **NFR22:** ≥ 80 % overall line coverage; **100 %** for `filters/pflichtregeln.py` and `lifecycle/state_machine.py`. `pytest --cov=csp --cov-fail-under=80` is a CI gate.
- **NFR23:** `mypy --strict src/` (or `pyright` strict) passes with zero errors. `ruff check` and `ruff format --check` pass with zero diagnostics.
- **NFR24:** Cyclomatic complexity ≤ 10 per function (ruff `C901`). Functions ≤ 30 lines. Modules with > 200 lines require justification in a top-of-file docstring.
- **NFR25:** No `Any` type in production code. `# type: ignore` and `# noqa` require an inline reason comment (e.g., `# noqa: E501 — long URL string`).
- **NFR26:** Dependencies pinned via `uv.lock` (committed). `pyproject.toml` declares `requires-python = ">=3.12"`. Adding a new runtime dependency requires PR-review with a one-sentence justification.

### Observability

- **NFR27:** All long-running commands (≥ 2 s) log start and end events with elapsed-time and function-name fields via `loguru.bind(...)`. Daily-brief logs include the full call tree (which tickers, which vendors, which Pflichtregeln evaluated).
- **NFR28:** Log rotation: max 10 MB per file, 30-day retention, zip compression. Logs live at `logs/csp.log` (gitignored).
- **NFR29:** Structured log fields enable post-hoc query: every log row has `trade_id` (when applicable), `ticker`, `region`, `data_freshness`, `pflichtregeln_outcome`. `loguru.bind(...)` is the mechanism, not f-string interpolation.
- **NFR30:** Vendor errors are logged at ERROR level with the HTTP status, response body (with secrets stripped), and the in-flight ticker context. Pflichtregel failures are INFO; overrides are WARN.

### Integration Resilience

- **NFR31:** Each vendor client (`OratsClient`, `FmpClient`, `IVolatilityClient`) implements retry+backoff: 3 attempts, exponential delay (1s, 2s, 4s), only for 5xx and 429. 4xx raises immediately with the response body in the exception message.
- **NFR32:** Vendor rate-limit awareness — `OratsClient` tracks request count per minute and waits before exceeding 1000/min. `IVolatilityClient` enforces its plan-tier limit (TBD on first request, surfaced in client constants).
- **NFR33:** Each public library function call results in at most one logical "transaction" against vendors (parallel calls allowed, but no nested re-entry that could spike rate-limit usage unpredictably).
- **NFR34:** If a single ticker's vendor fetch fails during a universe-wide scan, the scan continues for remaining tickers; the failed ticker is logged and excluded from results, not allowed to fail the whole scan.

### Data Integrity

- **NFR35:** Currency precision: premiums, P/L, cash-secured amounts use `Decimal` end-to-end. Conversion to/from `float` only at the JSON serialization boundary (DuckDB `raw_json` column, Sheets cell write).
- **NFR36:** Date discipline: never naive `datetime`. Trade dates are `date` (no time). Timestamps are UTC. US market hours referenced in `America/New_York`; user-local in `Europe/Berlin`. DTE = calendar days, matching ORATS field semantics; verified-equivalent for IVolatility (TBD on first cassette).
- **NFR37:** Pydantic `model_config = ConfigDict(populate_by_name=True)` on every API response model. Vendor field aliases (`Field(alias="camelCase")`) make `mktCap → mkt_cap` explicit.
- **NFR38:** DuckDB schema migrations are numbered SQL files in `src/csp/persistence/migrations/`; applied at startup. No ALTER TABLE drift between code versions.
- **NFR39:** Inserts use parameterized queries (`con.execute("... WHERE ticker = ?", [ticker])`); no string formatting of SQL.

## Document Status & Open Items

This PRD is the authoritative spec for MVP scope. Several items are deliberately **not yet locked down** — they will be resolved during implementation, in week 1 of the build.

### Open vendor / integration items

- **IVolatility plan tier and rate limit** — TBD on first request. Will be surfaced as constants in `clients/ivolatility.py` once verified, and reflected in NFR32.
- **IVolatility response shape** — first task during client implementation: record one real cassette for an EU ticker (default `ALV.DE` for Allianz on Eurex) via `csp.iv_health_check()` and inspect actual field names. Pydantic models written **after** cassette inspection, never from docs alone.
- **IVolatility auth scheme** — query parameter vs. header (`X-API-Key`) vs. both. VCR scrubbing config in NFR9 confirmed once verified.
- **EU vendor-symbol convention** — exact format the IVolatility API expects (`ALV.DE`, `ALV` + `exchange=EUREX`, etc.) confirmed when the first cassette is recorded. The universe `vendor_symbol` column is populated only after this is known.
- **EU regression anchor** — no historical reference trade exists yet. A `pytest -k eu_regression` test parallel to NOW-78 will be added once the first real EU CSP idea is generated and persisted.

### Open empirical questions (resolve in week 1 of operation)

- **Pflichtregel #1 lock-out** — does the rule (`VIX ≥ 20 OR IVR ≥ 40`) produce zero candidates routinely in calm-VIX periods? Track empirically. Threshold review is a Growth-phase response, not MVP.
- **EU options liquidity** — does Pflichtregel #6 (≥ 50 000 contracts/day) zero out EU candidates? Likely yes for most EU names. EU integration is "available but rarely used" until Growth-phase EU-tier rules.
- **Override-rate baseline** — what fraction of generated ideas trigger `override=True`? Target ≤ 5 %; review monthly.

### Brief reconciliation

`docs/Projekt-Brief.md` is partially superseded by this PRD. Specifically:
- §4.1 (`csp` CLI subcommands) — superseded by the library API surface in **Library + Claude Code Specific Requirements**.
- §5.1 (`reporting/tax.py` module) — superseded by the explicit non-goal "no tax export."
- §3 (verified ORATS + FMP endpoints) — extended by IVolatility integration; brief `.env` template (§10.3) needs the `IVOLATILITY_API_KEY` line added by the user manually.
- §12 (6-phase roadmap) — restructured into MVP / Growth / Vision in **Product Scope**, with several phases deferred or removed.

The brief remains valuable as background context (data-vendor field semantics, Pflichtregeln rationale, German tax explanation for the user). It should not be silently auto-edited; this PRD takes precedence in any conflict.

### Traceability check (final)

| Layer | Source | Count | Verified |
|---|---|---|---|
| Vision → Success Criteria | Executive Summary → "Trust threshold" + brief §18 metrics | 7 metrics | ✅ |
| Success Criteria → User Journeys | Each metric maps to ≥ 1 journey | 6 journeys | ✅ |
| User Journeys → FRs | Journey-FR map in self-validation | 42 FRs | ✅ |
| FRs → NFRs | NFRs cover quality of FR delivery | 39 NFRs | ✅ |
| Domain → NFRs | Vendor-licensing + secrets + freshness | NFR7–NFR11, NFR14, NFR17 | ✅ |
| Innovation → FRs | Determinism/narration split → typed exceptions, Pydantic returns, override-tracking | FR9, FR10, FR33, FR34, FR37 | ✅ |
