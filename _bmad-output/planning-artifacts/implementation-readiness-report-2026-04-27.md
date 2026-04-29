---
stepsCompleted: ['step-01-document-discovery', 'step-02-prd-analysis', 'step-03-epic-coverage-validation', 'step-04-ux-alignment', 'step-05-epic-quality-review', 'step-06-final-assessment']
filesIncluded:
  prd: '_bmad-output/planning-artifacts/prd.md'
  architecture: null
  epics: null
  ux: null
status: complete
date: '2026-04-27'
project_name: 'csp-flywheel-terminal (options-trading)'
sparseAssessmentReason: 'Only PRD authored; architecture and epics not yet created. Running readiness check against PRD only at user request.'
overallReadiness: NOT_READY
overallReadinessReason: 'PRD is complete and high-quality, but architecture and epics+stories are missing. Phase 4 implementation cannot start without them.'
---

# Implementation Readiness Assessment Report

**Date:** 2026-04-27
**Project:** csp-flywheel-terminal (options-trading)

## Document Inventory

| Document | Status | Source |
|---|---|---|
| PRD | ✅ Found, complete | `_bmad-output/planning-artifacts/prd.md` (740 lines, status: complete) |
| Architecture | ❌ Not found | Not yet authored — `_bmad-create-architecture` skill not run |
| Epics & Stories | ❌ Not found | Not yet authored — `bmad-create-epics-and-stories` skill not run |
| UX Design | ⏭️ N/A by design | CLI/conversational tool; no GUI surface (PRD §Project-Type explicitly skips `visual_design`, `ux_principles`, `touch_interactions`) |

**Auxiliary context loaded as persistent fact:**
- `_bmad-output/project-context.md` — 178 implementation rules across 7 sections (technology stack, language, framework, testing, code quality, workflow, critical rules). Substitutes partially for architecture during this assessment.

**Brief reconciliation note (from PRD § Document Status & Open Items):**
- `docs/Projekt-Brief.md` §4.1 (CLI subcommands), §5.1 (`reporting/tax.py`), §3 (vendor endpoints), §10.3 (`.env` template), §12 (6-phase roadmap) are partially superseded by the PRD.

## Critical Issues at Discovery

- ⚠️ **Architecture document missing.** Phase-4 implementation typically requires a formal architecture spec. `project-context.md` covers ~80% of what an architecture would say (modules, tech stack, conventions) but lacks: data-flow diagrams, sequence diagrams for the daily-brief and idea-generation paths, deployment topology, and explicit dependency-injection seams.
- ⚠️ **Epics & stories missing.** No backlog exists. The PRD has 42 FRs and 39 NFRs that must be broken into ~8–12 epics and 30–50 stories before development can sprint.
- ✅ **UX absent and correctly so** — PRD justifies this explicitly.

## PRD Analysis

### Functional Requirements

42 FRs across 8 capability areas. Extracted verbatim from PRD § Functional Requirements.

**Data Acquisition & Freshness**
- **FR1:** The library can fetch ORATS `/cores`, `/strikes`, `/ivrank`, and `/summaries` data for any single US-region ticker.
- **FR2:** The library can fetch FMP `/stable/` macro endpoints (VIX history, Treasury rates, earnings calendar, sector performance) for daily-brief context.
- **FR3:** The library can run universe-wide vendor data fetches in parallel for all watchlist tickers, respecting per-vendor rate limits (ORATS 1000 req/min; IVolatility plan-tier TBD).
- **FR4:** The library can retry failed vendor calls up to 3 times with exponential backoff for 5xx and 429 errors; 4xx errors raise immediately.
- **FR5:** The library can persist every successful vendor response as a snapshot tagged with ticker, region, and trade date, enabling later replay.
- **FR6:** The library can detect when live data fetch fails and fall back to the most recent persisted snapshot, flagging the result as `data_freshness="stale"`.
- **FR7:** The library applies a region-aware data-freshness gate before generating new trade ideas: US candidates require `data_freshness="live"`; EU candidates require `data_freshness="eod"` AND snapshot ≤ 1 day old. Other states (`stale`, `unavailable`) block new-idea generation regardless of Pflichtregeln pass/fail.

**Pflichtregeln Rule Enforcement**
- **FR8:** Evaluate the 9 Pflichtregeln (VIX/IVR, delta, DTE, OTM%, earnings proximity, liquidity, market-cap, sector-cap, universe membership), return `(passed: bool, reasons: list[str])` with German reasons.
- **FR9:** Accept `override=True` argument that bypasses Pflichtregeln gating, log WARN, persist override decision in DuckDB.
- **FR10:** Persist "considered-but-rejected" candidate evaluations with which Pflichtregeln failed and German reasons.
- **FR11:** Direct callable `csp.passes_csp_filters(...)` to test a hypothetical strike against the current rule set.
- **FR12:** Read all Pflichtregeln thresholds from `config/settings.toml`; no thresholds hardcoded.

**Idea Generation & Ranking**
- **FR13:** Generate single-ticker CSP idea given `(ticker, dte, target_delta)`; return `Idea | None` with German `reasons` on Pflichtregel failure. Region dispatch internal.
- **FR14:** Scan entire universe (US + EU together) and return up to N candidates ranked by annualized yield, Pflichtregeln-passing only.
- **FR15:** Render idea in brief §7.1 FBG-mail format (German number locale) via `Idea.format_fbg_mail()`. EU candidates include EU-native option symbol.
- **FR16:** Compute and expose annualized yield, OTM%, sector-exposure delta vs current portfolio, Earnings-distance-days as `Idea` fields.
- **FR17:** Deterministically tie-break ranked output (alphabetical by ticker on equal annualized yield).

**Daily-Brief Composition**
- **FR18:** Compose `DailyBrief` with macro snapshot + open positions + top-3 Pflichtregeln-passing candidates + Earnings warnings (next 8 days).
- **FR19:** Flag open positions with `action ∈ {take_profit, dte_21_exit, emergency_close, stop_loss, hold}`.
- **FR20:** Attach `data_freshness ∈ {live, eod, stale, unavailable}` flag per data segment in every `DailyBrief`.

**Trade Lifecycle Management**
- **FR21:** `csp.log_trade(ticker, strike, premium, dte, open_date, sector, region, ...)` opens a Position with status `"open"` and a unique `trade_id`. `region` required.
- **FR22:** `csp.close_trade(trade_id, close_premium, close_date, status)` with `status ∈ {closed_profit, closed_neutral, closed_loss, assigned, expired_otm}`.
- **FR23:** Compute live P/L for each open position; US uses ORATS live, EU uses IVolatility EOD (D-1).
- **FR24:** Trade-status transitions are idempotent; repeated same-day calls produce identical final state.

**Persistence & Historical Audit Trail**
- **FR25:** Persist every generated idea with raw vendor JSON in `raw_json` column + `source_vendor` discriminator.
- **FR26:** `csp.get_idea(trade_id)` retrieves historical idea including raw_json and source vendor.
- **FR27:** `csp.list_ideas(ticker=None, region=None, from_date=None, to_date=None, status=None, pflichtregeln_passed=None, limit=10)` for historical search.
- **FR28:** Idempotent same-day reruns; snapshots use `INSERT OR REPLACE` keyed on `(ticker, snapshot_date)`.
- **FR29:** NOW-78-Strike from 2026-04-24 reproduces from VCR cassette via `pytest -k now_regression` as CI gate.

**External Reporting (Google Sheets)**
- **FR30:** Push current Pflichtregeln-passing ideas (US + EU combined) to single Google Sheets tab `Ideas` via `csp.export_to_sheets()`. Includes `Region` column.
- **FR31:** Render Sheets values in German number locale (`1.234,56 USD`, `13,3 %`, dates `27.04.2026`); EU prices in `EUR` if vendor data is in EUR, otherwise USD.
- **FR32:** Sheets export is best-effort, fire-and-forget; failure must not raise; logs WARN; daily-brief still completes.

**Library API & Documentation**
- **FR33:** Each public library function has complete docstring (purpose, parameters, return shape, failure modes/exceptions).
- **FR34:** Flat top-level module `import csp`; the 10 public functions are MVP binding contract.
- **FR35:** `README.md` with function-by-function reference, "Claude, read this first" header on determinism/narration boundary, three-vendor section, working compile-as-written code example.
- **FR36:** `docs/CLAUDE_USAGE.md` with daily-brief workflow worked example, including EU-candidate handling.
- **FR37:** Library raises typed exceptions (`ORATSDataError`, `FMPDataError`, `IVolatilityDataError`, `PflichtregelError`, `IdempotencyError`, `ConfigError`).

**EU Options Data (IVolatility) — Region-Aware**
- **FR38:** Fetch IVolatility EOD equity options data for any EU-region ticker via `IVolatilityClient`; map ticker via universe `region` and `vendor_symbol` metadata.
- **FR39:** Universe loader recognizes `region ∈ {"US", "EU"}` column and dispatches each ticker to appropriate vendor. Missing `region` raises `ConfigError` at startup.
- **FR40:** Pflichtregeln engine evaluates EU candidates using same 9 rules with same thresholds (no MVP relaxation). Pflichtregel #1 IVR-leg uses IVolatility-derived IVR; VIX-leg refers to US `^VIX` regardless of region.
- **FR41:** Diagnostic `csp.iv_health_check()` fetches one well-known EU ticker (default `ALV.DE`), reports IVolatility connectivity, response shape, and field-mapping mismatches.
- **FR42:** Live cassettes for IVolatility under `tests/cassettes/ivolatility/`; API key scrubbed via VCR `filter_query_parameters` and `filter_headers` (final filter list confirmed once auth scheme verified).

**Total FRs: 42**

### Non-Functional Requirements

39 NFRs across 8 categories. Extracted verbatim from PRD § Non-Functional Requirements.

**Performance**
- **NFR1:** Full universe scan (~40 tickers US + EU) completes in ≤ 60 s of Python wall-clock time on warm cache.
- **NFR2:** `csp.daily_brief()` Python execution ≤ 30 s on warm cache.
- **NFR3:** End-to-end daily-brief conversation in Claude Code ≤ 90 s on warm cache.
- **NFR4:** Single `csp.idea(ticker)` ≤ 5 s for US ticker; ≤ 7 s for EU ticker.
- **NFR5:** Vendor calls parallelized via `asyncio.gather()`; sequential cross-ticker calls forbidden.
- **NFR6:** `csp.export_to_sheets()` async fire-and-forget; doesn't block return path.

**Security & Secrets**
- **NFR7:** No tokens or service-account material in repository. `.env` gitignored. Service-account JSON at `~/.config/csp/sa.json` outside repo.
- **NFR8:** `loguru` filter strips `token`, `apikey`, `api-key`, `Authorization`, `IVOLATILITY_API_KEY`, service-account email substrings.
- **NFR9:** VCR cassettes scrub vendor authentication. CI grep-checks every cassette + log artifact for known token prefixes (`82326868-`, `A4I6B9`, `eLlVI`); fails build on hit.
- **NFR10:** No automatic order routing, no broker SDK, no Authorization to anywhere except ORATS/FMP/IVolatility/Sheets. New outbound destinations need PR-review.
- **NFR11:** IVolatility key is user's responsibility; library raises `ConfigError` at startup if `IVOLATILITY_API_KEY` missing AND any universe ticker has region `EU`.

**Reliability & Idempotency**
- **NFR12:** Same-day reruns of `csp.daily_brief()` and `csp.scan()` are idempotent.
- **NFR13:** Trade-lifecycle transitions at-most-once per day per `trade_id`.
- **NFR14:** Vendor outages don't crash; surface via `data_freshness` flag.
- **NFR15:** Sheets export failures are best-effort; log WARN, don't raise, don't prevent DuckDB persistence.
- **NFR16:** Daily-brief completes before 15:00 CEST on ≥ 95 % of US trading days.

**Reproducibility & Audit**
- **NFR17:** Every generated idea persists full raw vendor JSON in `raw_json`; historical retrieval 6 months later returns identical data.
- **NFR18:** NOW-78-Strike reproduces from `tests/cassettes/orats/cores_NOW.yaml` and `strikes_NOW.yaml`. `pytest -k now_regression` as CI gate.
- **NFR19:** VCR cassettes committed to repo. Re-recording requires explicit reason in commit message. CI's `--record-mode=none` blocks accidental re-records.
- **NFR20:** `csp.scan()` produces fully deterministic output given identical input data; tie-break by ticker alphabetical; byte-identical result on rerun.
- **NFR21:** Every Pflichtregel evaluation produces audit-trail row (ticker, timestamp, pass/fail, German reasons, override-flag) for monthly review.

**Maintainability**
- **NFR22:** ≥ 80 % overall line coverage; 100 % for `filters/pflichtregeln.py` and `lifecycle/state_machine.py`. `pytest --cov=csp --cov-fail-under=80` as CI gate.
- **NFR23:** `mypy --strict src/` zero errors. `ruff check` and `ruff format --check` zero diagnostics.
- **NFR24:** Cyclomatic complexity ≤ 10 per function. Functions ≤ 30 lines. Modules > 200 lines need docstring justification.
- **NFR25:** No `Any` type. `# type: ignore` and `# noqa` require inline reason.
- **NFR26:** Dependencies pinned via `uv.lock` (committed). `pyproject.toml` declares `requires-python = ">=3.12"`. New runtime dep needs PR justification.

**Observability**
- **NFR27:** Long-running commands (≥ 2 s) log start+end with elapsed-time and function-name via `loguru.bind(...)`.
- **NFR28:** Log rotation: max 10 MB/file, 30-day retention, zip compression. Logs at `logs/csp.log` (gitignored).
- **NFR29:** Structured fields enable post-hoc query: `trade_id`, `ticker`, `region`, `data_freshness`, `pflichtregeln_outcome`. `loguru.bind(...)` is mechanism, not f-string.
- **NFR30:** Vendor errors at ERROR level with HTTP status, response body (secrets stripped), in-flight ticker context. Pflichtregel failures INFO; overrides WARN.

**Integration Resilience**
- **NFR31:** Each vendor client implements retry+backoff: 3 attempts, exponential delay (1s, 2s, 4s), only for 5xx and 429. 4xx raises immediately.
- **NFR32:** Vendor rate-limit awareness — `OratsClient` 1000/min; `IVolatilityClient` plan-tier limit (TBD on first request).
- **NFR33:** Each public library function call results in at most one logical "transaction" against vendors (parallel allowed; nested re-entry forbidden).
- **NFR34:** Single ticker's vendor failure during universe scan logs and excludes that ticker; doesn't fail the whole scan.

**Data Integrity**
- **NFR35:** Currency precision: premiums, P/L, cash-secured use `Decimal` end-to-end. Conversion to `float` only at JSON serialization boundary.
- **NFR36:** Date discipline: never naive `datetime`; trade dates `date`-only; UTC timestamps; `America/New_York` for US market hours; `Europe/Berlin` for user-local; DTE = calendar days (ORATS-equivalent for IVolatility TBD).
- **NFR37:** Pydantic `model_config = ConfigDict(populate_by_name=True)` on every API response model. Vendor field aliases (`Field(alias="camelCase")`) explicit.
- **NFR38:** DuckDB schema migrations as numbered SQL files in `src/csp/persistence/migrations/`; applied at startup. No ALTER TABLE drift between versions.
- **NFR39:** Inserts use parameterized queries (`con.execute("... WHERE ticker = ?", [ticker])`); no string formatting of SQL.

**Total NFRs: 39**

### Additional Requirements & Constraints

**Constraints embedded in PRD that are not labeled FR/NFR but bind implementation:**

- The 10 public library functions in PRD § Library + Claude Code Specific Requirements are the **binding API contract** for MVP. New public functions require PR-review against this contract.
- Module structure (`src/csp/{clients,models,strategies,filters,ranking,lifecycle,persistence,reporting}/`) preserved from brief §5.1, minus the deleted `ui/` directory and the deleted `reporting/tax.py`.
- Determinism / narration split is the **single intentional innovation**: Python owns facts and rules; Claude owns reasoning and narration; Claude cannot bypass `passes_csp_filters()`.
- Pre-commit gates (mandatory pass-before-commit): `ruff check`, `ruff format --check`, `mypy --strict`, `pytest -q`.
- 6-state Pflichtregeln list (PRD FR8) — VIX/IVR, delta, DTE, OTM%, earnings, liquidity, market-cap, sector-cap, universe — are **inviolable**. Override mechanic exists but is logged WARN and tracked monthly.

**Integration requirements:**
- 3 vendor APIs (ORATS, FMP, IVolatility) + 1 Google Workspace integration (Sheets via service-account JSON).
- No broker SDK, no third-party order-routing API, no MCP server in MVP.

**Open items (PRD § Document Status & Open Items):**
- IVolatility plan-tier and rate-limit TBD on first request.
- IVolatility response shape TBD; first task records cassette for `ALV.DE` and inspects fields before writing Pydantic models.
- IVolatility auth scheme (query param vs. header) TBD.
- EU vendor-symbol convention TBD with first cassette.
- EU regression anchor TBD; no historical reference trade exists yet.
- Pflichtregel #1 calm-VIX lock-out — empirical question for week 1.
- EU options liquidity vs. Pflichtregel #6 — empirical question for week 1.

### PRD Completeness Assessment

**Strengths:**
- ✅ All 9 BMAD-required sections present (Executive Summary, Success Criteria, Product Scope, User Journeys, Domain Requirements, Innovation, Project-Type Requirements, Functional Requirements, Non-Functional Requirements).
- ✅ FRs are testable, implementation-agnostic (mostly — see weaknesses), comprehensive coverage of MVP scope.
- ✅ NFRs are SMART: each has specific metric, measurement method, target value.
- ✅ Traceability chain validated in PRD self-validation: Vision → Success Criteria → Journeys → FRs → NFRs.
- ✅ Scope discipline excellent — explicit non-goals list (typer CLI, tax export, Wheel state machine, multi-strategy, Hormuz overlay, broker SDK, etc.).
- ✅ Risk register populated with technical, portfolio, resource risks plus mitigations.
- ✅ Innovation analysis honest — flags the determinism/narration split as the single innovation, names what's NOT innovation.

**Weaknesses / Concerns:**
- ⚠️ Some FRs leak implementation detail more than they should (e.g., FR21 names `csp.log_trade(ticker, strike, premium, dte, open_date, sector, region, ...)` — that's the function signature, not a capability statement). This is intentional given the library-as-public-surface design, but a strict reviewer would flag it. Acceptable for this project type.
- ⚠️ Open Items section identifies 7 deliberately unresolved items. These are honest but mean the PRD is **not 100 % locked** — week-1 cassette recording will close some, but the IVolatility-side rate limit, auth scheme, response shape, vendor-symbol convention, and EU regression anchor remain open.
- ⚠️ Brief partially superseded — the brief's CLI-subcommand pattern (§4.1) and `reporting/tax.py` module (§5.1) are explicitly out. A future agent reading the brief literally without this PRD would build the wrong product. Mitigated by `_bmad-output/project-context.md` updates and PRD's "Brief reconciliation" subsection.
- ⚠️ No epics or stories yet. PRD is upstream of those; readiness check at this stage cannot validate alignment.

**Overall:** PRD is **complete and dense for an MVP-stage spec on a single-developer project**. It is **not ready for hand-off to a multi-team enterprise architecture pass** without resolving the IVolatility open items, but that is acceptable given the MVP-first phasing.

## Epic Coverage Validation

**Result: Cannot validate — no epics document exists.**

### Coverage Matrix

All 42 PRD FRs are uncovered by epics because no epics file (`*epic*.md`) exists in `_bmad-output/planning-artifacts/`. A full per-FR matrix would just list every row as `Epic Coverage: NOT FOUND ❌ MISSING` — non-informative.

### Missing Requirements

**100 % of FRs (42 of 42) are uncovered by epics.** Equivalent for NFRs: NFRs are typically not 1-to-1 mapped to epics but are validated by stories' definition-of-done; with no epics or stories, NFRs are unvalidated as well.

### Recommended Epic Decomposition

Since this readiness check is being run before epic creation, here is the **recommended epic breakdown** that the next-step `bmad-create-epics-and-stories` workflow should produce. Capability-area-aligned, ~8 epics for MVP:

| Epic | Capability Area | FRs Covered | Estimated Stories | MVP Priority |
|---|---|---|---|---|
| **Epic 1: Project Skeleton & Tooling** | scaffolding, `pyproject.toml`, `uv` setup, `.env` template, `loguru` config, `pre-commit` gates | (constraints from PRD § Project-Type, NFR22–NFR26, NFR27–NFR30) | ~4 | P0 (must precede all others) |
| **Epic 2: Vendor Clients (ORATS + FMP + IVolatility)** | API clients, retry+backoff, rate-limit, typed exceptions, VCR cassettes | FR1, FR2, FR4, FR37, FR38, FR41, FR42, NFR8, NFR9, NFR31, NFR32, NFR34 | ~6–8 | P0 |
| **Epic 3: Persistence Layer (DuckDB + Parquet)** | schema, migrations, snapshots, raw_json column, idempotent inserts | FR5, FR25, FR28, NFR12, NFR17, NFR38, NFR39 | ~4–5 | P0 |
| **Epic 4: Pflichtregeln Engine** | 9 rules + freshness gate, German reasons, override mechanic, considered-rejected log, settings-driven thresholds | FR7, FR8, FR9, FR10, FR11, FR12, FR40, NFR21 | ~5–6 | P0 |
| **Epic 5: Idea Generation & Ranking** | `csp.idea`, `csp.scan`, ranking by annualized yield, brief §7.1 rendering, deterministic tie-break | FR13, FR14, FR15, FR16, FR17, NFR20 | ~4–5 | P0 |
| **Epic 6: Daily Brief Composition** | macro snapshot, open-position action flags, top-3 candidates, Earnings warnings, region-aware freshness | FR3, FR6, FR18, FR19, FR20, FR39 | ~4 | P0 |
| **Epic 7: Trade Lifecycle Management** | `csp.log_trade`, `csp.close_trade`, P/L computation, idempotent state transitions, get_idea, list_ideas | FR21, FR22, FR23, FR24, FR26, FR27, NFR13 | ~4–5 | P0 |
| **Epic 8: Reporting (Sheets + Library Docs)** | Sheets export with German locale, README, CLAUDE_USAGE.md, regression test for NOW-78 | FR29, FR30, FR31, FR32, FR33, FR34, FR35, FR36, NFR15, NFR18, NFR19 | ~4 | P1 (can ship MVP without if Sheets blocked) |

**Estimated total stories for MVP:** ~35–40 stories.
**Cross-cutting NFRs** (NFR1–NFR6 performance, NFR7–NFR11 security, NFR16 reliability, NFR22–NFR26 maintainability, NFR27–NFR30 observability, NFR33 integration discipline, NFR35–NFR37 data integrity) ride as Definition-of-Done criteria across stories rather than dedicated epics.

### Coverage Statistics

| Metric | Value |
|---|---|
| Total PRD FRs | 42 |
| FRs currently covered by epics | **0** |
| Coverage percentage | **0 %** |
| Reason | No epics document authored yet |
| Recommended epic count for full MVP coverage | 8 |
| Recommended story count | ~35–40 |

### Critical Gap

The single most critical gap surfaced by this step: **no epics document means no implementation backlog.** Until epics + stories exist:
- No sprint can be planned
- No story-level acceptance criteria can validate FRs
- No traceability from PRD → implementation tasks
- The `bmad-create-architecture` and `bmad-create-epics-and-stories` skills must run before development begins

**Recommendation surfaced for the final report:** Phase 4 (implementation) is **not yet ready to start**. Authoring epics + architecture is the next required step.

## UX Alignment Assessment

### UX Document Status

**Not found — and that's correct by design.**

### Justification (no warning issued)

The PRD explicitly excludes UX/UI surfaces in three places:
- **PRD § Project Classification** — "Project Type: Python library + Claude Code as primary interface. No `typer` CLI in MVP."
- **PRD § Library + Claude Code Specific Requirements → Skipped Sections** — explicitly skips `visual_design`, `ux_principles`, `touch_interactions`, `store_compliance` per the project-types CSV.
- **PRD § Innovation → What's NOT Innovation** — Library + Claude Code pattern, not a UI surface.

The user-facing surface is **Claude Code in the terminal**. Claude renders markdown directly from Pydantic model fields. No web UI, no mobile, no desktop GUI, no CLI subcommand polish, no store-compliance surface. The single non-conversational surface is the **Google Sheets export** (read-only dashboard) — and that has formatting requirements baked into FR31 (German number locale: `1.234,56 USD`, `13,3 %`, dates `27.04.2026`), which is sufficient.

### UX-like Considerations Already Captured

Three things that *could* be considered "UX" in a broader sense are already addressed in the PRD without a UX document:
1. **Conversational quality** — PRD § Success Criteria § User Success names "Claude's pushback is *useful*, not noise" and "trust threshold after 30 days" as testable conditions.
2. **Output formatting** — FR15 (`Idea.format_fbg_mail()` follows brief §7.1 with German locale), FR31 (Sheets German locale) cover the only format-quality surfaces.
3. **Claude-readable docs** — FR33–FR36 (docstrings, README, CLAUDE_USAGE.md) are the "UX" for the LLM consumer of the library.

### Alignment Issues

**None to flag.** No UX document means no misalignment between UX ↔ PRD ↔ Architecture (and architecture doesn't exist either, but that's the Step 5 issue).

### Warnings

**No UX-related warnings.** This is a deliberately UX-less product, and the PRD justifies that decision.

## Epic Quality Review

**Result: Cannot validate — no epics document exists.**

### Why we still record findings here

The skill is designed to find quality defects in *existing* epics (technical-milestone framing, forward dependencies, vague acceptance criteria, oversized stories). With zero epics, there are zero findings of this kind. Instead, this section captures the **best-practices guardrails** that the future `bmad-create-epics-and-stories` workflow must satisfy, so the gap is closed deliberately, not accidentally.

### Forward-Looking Quality Constraints (for the next workflow to enforce)

When epics are eventually authored, they must satisfy:

#### 🔴 Critical — Avoid technical-milestone framing

The recommended Epic 1 in Step 3 is named "Project Skeleton & Tooling" — that is a **technical-milestone label**, which the standard (per this step) flags as a red flag. The honest answer for a single-developer library project: **scaffolding epics are unavoidable** in the very first sprint because no user value can be delivered without `pyproject.toml`, `uv.lock`, `loguru` config, and the test harness existing first. The remediation is not to rename it to a fake user-value title ("As Chris, I want a project skeleton so that…") but to **flag this as known and intentional** in the epics document with an explicit note: *"Epic 1 is scaffolding-only by design; no user-facing value until Epic 2."* The standard's "user value per epic" rule applies cleanly to Epics 2–8.

#### 🔴 Critical — Independence rule

- Epic 1 (Skeleton) must function alone (it ships an importable empty `csp` package with passing tests, lint, type-check, no public functions yet).
- Epic 2 (Vendor Clients) needs Epic 1 only.
- Epic 3 (Persistence) needs Epic 1 only — and must not depend on Epic 2 (clients) being complete; persistence layer should be testable in isolation with mock vendor responses.
- Epic 4 (Pflichtregeln Engine) needs Epic 3 (persistence for considered-rejected logging) but does **not** need full Epic 2 — it can be tested with stubbed `OratsCore`/`OptionStrike` Pydantic instances.
- Epic 5 (Idea Generation) needs Epics 2, 3, 4.
- Epic 6 (Daily Brief) needs Epics 2, 3, 4, 5.
- Epic 7 (Trade Lifecycle) needs Epic 3.
- Epic 8 (Reporting) needs Epics 5, 6, 7 (it formats their outputs).

The future epics document **must call out** which prior epics each depends on (forward dependencies are forbidden but **backward** dependencies are fine and expected here).

#### 🟠 Major — Database/entity creation timing

Per the standard: tables are created **when first needed**, not all upfront. For this project: Epic 3 (Persistence) will need to ship the `snapshots` table first (Epic 2 depends on it) and `macro_snapshots` table soon after; the `trades` table can ship with Epic 7 (Trade Lifecycle) — not earlier. Future epics document must respect this: do not create one mega-Epic-3-Story-1 "Set up all DuckDB tables."

#### 🟠 Major — Acceptance criteria format

Each story's ACs must be **Given/When/Then BDD format** with testable, specific outcomes. Vague ACs like "user can scan" must be rejected at story authoring time.

Example of acceptable AC structure for an Epic 5 story ("Implement single-ticker idea generation"):
- **Given** a Pflichtregeln-passing strike for NOW with delta=-0.21, dte=52, IVR=96, **when** `csp.idea("NOW", dte=52, target_delta=-0.20)` is called against the 2026-04-24 cassette, **then** the function returns an `Idea` model whose `format_fbg_mail()` output exactly matches `tests/fixtures/now_2026_04_24_idea.txt`.
- **Given** a strike where Pflichtregel #5 fails (Earnings in 7 days), **when** `csp.idea(...)` is called, **then** the function returns `None` and the `reasons` list contains exactly the German string `"Earnings in 7 Tagen (< 8)"`.

#### 🟠 Major — Starter-template question

The standard asks whether the architecture specifies a starter template. **Not yet** — architecture is unwritten. The future architecture document should choose: *"Initialize from `uv init --lib` + custom additions"* vs. *"Clone from a separate repo template."* Likely the former for this project's simplicity. Whatever the decision, Epic 1 Story 1 will say *"Set up initial project from `uv init --lib` and add … "*.

#### 🟡 Minor — Greenfield indicators

This is a greenfield project. The future epics document should explicitly include:
- **Story 1.1** — Set up initial Python project from starter template (`uv init`, `pyproject.toml`, dev tooling).
- **Story 1.2** — Configure CI pipeline (lint + type-check + test gates from NFR22–NFR23).
- **Story 1.3** — Configure secrets discipline (`.env.example`, `.gitignore`, `loguru` filter for token substrings per NFR8).

These are non-negotiable for a greenfield project under this PRD's NFR rigor.

### Best-Practices Compliance Checklist (forward-looking, not yet checkable)

- [ ] Epic delivers user value (or, for Epic 1 only, is explicitly flagged scaffolding-only)
- [ ] Epic can function independently of later epics
- [ ] Stories appropriately sized (target 1–3 days each; 35–40 stories total per Step 3)
- [ ] No forward dependencies between stories
- [ ] Database tables created in the epic that first needs them
- [ ] Each AC in Given/When/Then with testable outcomes
- [ ] Each story traces back to ≥ 1 PRD FR (or, for cross-cutting NFRs, lives as Definition-of-Done criteria)
- [ ] Epic 1 includes `uv init`, CI pipeline, and secrets discipline as separate stories
- [ ] Reproducibility: NOW-78 regression test (FR29, NFR18) shipped no later than Epic 5 Story 1

### Quality Findings

**No findings of severity 🔴/🟠/🟡 — because there is nothing to review.** All future quality issues will be caught by re-running this readiness check after `bmad-create-epics-and-stories` completes.

## Summary and Recommendations

### Overall Readiness Status

**🚧 NOT READY for Phase 4 (Implementation).**

Reason: PRD is **complete and high-quality**, but **architecture is unwritten** and **no epics or stories exist**. Implementation cannot start without these two missing artifacts. This is a sequencing finding, not a defect of the existing PRD.

### Readiness Breakdown

| Artifact | Status | Quality |
|---|---|---|
| **PRD** | ✅ Complete | ✅ High — 42 FRs, 39 NFRs, traceability validated, scope discipline excellent, 1 acknowledged innovation, risk register populated |
| **Architecture** | ❌ Missing | N/A — must be authored |
| **Epics & Stories** | ❌ Missing | N/A — must be authored |
| **UX Design** | ⏭️ N/A by design | ✅ Justified absence (CLI/conversational tool) |

### Critical Issues Requiring Immediate Action

#### 🔴 Critical Issue 1 — Architecture missing

**Problem:** No formal architecture document exists. `_bmad-output/project-context.md` covers ~80 % of what an architecture would say (modules, tech stack, conventions, ~178 rules) but lacks: data-flow diagrams for the daily-brief and idea-generation paths, sequence diagrams for vendor-fetch-with-fallback, deployment topology (single-machine WSL2), and explicit module-boundary contracts (e.g., does `lifecycle/` know about `clients/`?).

**Impact:** Without architecture, epic decomposition is guesswork. The recommended 8-epic breakdown in this report (Step 3) is a placeholder, not a validated decomposition.

**Action:** Run `/bmad-create-architecture` (or `bmad-bmm-create-architecture`). Estimated time: 1–2 hours of conversation. Output: `_bmad-output/planning-artifacts/architecture.md` (or `architecture/` folder).

#### 🔴 Critical Issue 2 — Epics & stories missing

**Problem:** Zero epics, zero stories. PRD's 42 FRs have no implementation backlog.

**Impact:** No sprint can be planned. No story-level acceptance criteria can validate FR delivery. Direct PRD → code is possible (and `/bmad-quick-dev` would attempt it) but bypasses the disciplined story-by-story handoff that makes refactor and review tractable.

**Action:** Run `/bmad-create-epics-and-stories` after architecture is authored. Use the recommended 8-epic decomposition in this report (Step 3) as the starting input. Estimated time: 1–3 hours of conversation. Output: `_bmad-output/planning-artifacts/epics.md` (or `epics/` folder, sharded).

#### 🟠 Major Issue 3 — IVolatility integration unresolved

**Problem:** Seven open items related to IVolatility (PRD § Document Status & Open Items): plan tier, rate limit, response shape, auth scheme, EU vendor-symbol convention, EU regression anchor, EU options-liquidity empirical question.

**Impact:** Epic 2 (Vendor Clients) cannot ship the IVolatility client until at least one EU cassette is recorded against a real ticker (default `ALV.DE`). This is a development-time discovery, not a planning-time defect — but it bounds the earliest possible ship date.

**Action:** First task within Epic 2: implement `csp.iv_health_check()` (FR41) and run it once against `ALV.DE` to record a cassette. Inspect actual response fields before writing Pydantic models.

#### 🟡 Minor Issue 4 — Brief partial supersession

**Problem:** `docs/Projekt-Brief.md` §3, §4.1, §5.1, §10.3, §12 are partially superseded by this PRD (CLI cut, tax export removed, IVolatility added, 6-phase roadmap restructured).

**Impact:** A future agent or human reading the brief literally without the PRD could build the wrong thing (e.g., wire up `typer` and `reporting/tax.py`).

**Action:** Add a one-paragraph header to `docs/Projekt-Brief.md` noting "**Superseded sections** — see `_bmad-output/planning-artifacts/prd.md`. Brief retains value as background/rationale; PRD takes precedence in any conflict." This is a 5-minute manual edit by the user.

### Recommended Next Steps (in order)

1. **Run `/bmad-create-architecture`** (or `bmad-bmm-create-architecture`) — translate PRD FRs/NFRs into module boundaries, data-flow diagrams, sequence diagrams, and a starter-template decision. Time: ~1–2 hours.
2. **Run `/bmad-create-epics-and-stories`** (or `bmad-bmm-create-epics-and-stories`) — break MVP into ~8 epics and ~35–40 stories using the decomposition recommended in Step 3 of this report and the architecture from step 1. Time: ~1–3 hours.
3. **Re-run this readiness check** (`/bmad-check-implementation-readiness`) — with all four artifacts present, the check will produce a substantive coverage matrix and quality findings instead of "not yet authored" placeholders. Time: ~10 minutes.
4. **Manual: Add supersession header to `docs/Projekt-Brief.md`** — 5 minutes.
5. **Manual: Add `IVOLATILITY_API_KEY` to local `.env`** — 1 minute (the user has the key already).
6. **Begin implementation** — `/bmad-dev-story` per story. Time: weeks 1–2 per PRD MVP target.

### Alternative Path (lighter-weight)

If the user wants to skip formal architecture + epics and proceed directly to coding:

1. Run `/bmad-quick-dev` (or `bmad-bmm-quick-dev`) — implements directly from PRD. Suitable for solo-dev simplicity-first projects. Trade-off: less rigor in handoff between planning and code, but **the PRD is dense enough that this can work for a single developer**.
2. The recommended 8-epic decomposition in Step 3 still serves as a sequencing guide even without a formal epics document.

**My honest read:** for this specific project (single developer, 8–14 day MVP, Claude Code as primary surface), the lighter-weight path is **defensible**. The full architecture + epics + stories pipeline is designed for multi-developer team handoffs; you don't have a team. If you trust the PRD and want to ship quickly, `/bmad-quick-dev` plus the Step-3 epic sequencing guide may be enough.

### Final Note

This assessment identified **4 issues** across **3 categories** (artifact-completeness, integration-discovery, brief-supersession). **2 are critical blockers** to formal Phase 4 readiness; **1 is a development-time discovery item**; **1 is a 5-minute manual edit**.

The PRD itself is solid. The work remaining is downstream artifacts. Address the critical issues by running the next two BMAD workflows, or accept the lighter-weight path and proceed to `/bmad-quick-dev`.

---

**Assessment Date:** 2026-04-27
**Assessed By:** Claude Code (`bmad-check-implementation-readiness` skill)
**Next Review:** After `/bmad-create-architecture` and `/bmad-create-epics-and-stories` complete
