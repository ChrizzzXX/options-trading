---
title: 'csp lifecycle persistence — log_trade, close_trade, list_open_positions, get_idea, list_ideas (slice 6)'
type: 'feature'
created: '2026-04-29'
status: 'done'
baseline_commit: 'e4ffd1e'
context:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/project-context.md'
  - '_bmad-output/implementation-artifacts/spec-idea-singleticker.md'
  - '_bmad-output/implementation-artifacts/spec-scan-universe.md'
---

<frozen-after-approval reason="YOLO batch — Chris waived approval">

## Intent

**Problem:** PRD's 10-function public surface still has 7 of 10 unbuilt. The next biggest cluster is lifecycle/persistence: `log_trade`, `close_trade`, `list_open_positions`, `get_idea`, `list_ideas`. These all share DuckDB infrastructure (schema, migrations, connection management) plus a `TradeStatus` state machine. Until they exist, deferred items D3 (override DB persistence), D14 (override stub), D15 (sector-exposure delta), and D19 (sector-key case-sensitivity) cannot land.

**Approach:** New `src/csp/persistence/` package with `db.py` (DuckDB connection + numbered migrations), `ideas.py` (ideas-table CRUD), `trades.py` (trades-table CRUD). New `src/csp/lifecycle/state_machine.py` with `TradeStatus` enum and a `valid_transition(from, to) -> bool` predicate (MVP scope: manual entry only, `assigned`/`closed_*`/`emergency_close` terminal). New `src/csp/lifecycle_api.py` orchestrates the 5 public functions plus `csp.log_idea` (FR9 override-persistence hook). All inserts are idempotent (`INSERT OR REPLACE` keyed on UUID). All money in `Decimal`, all dates `datetime.date`, all timestamps UTC.

## Boundaries & Constraints

**Always:**
- Public surface: `csp.log_trade`, `csp.close_trade`, `csp.list_open_positions`, `csp.get_idea`, `csp.list_ideas`, `csp.log_idea`, `csp.Trade`, `csp.TradeStatus`, `csp.LifecycleError`, `csp.IdempotencyError`. No new internal abstractions beyond what's needed.
- DuckDB file path from `Settings.duckdb_path` (default `data/trades.duckdb`). Tests use `tmp_path / "test.duckdb"` per-test, never the real file.
- Schema migrations in `src/csp/persistence/migrations/NNN_<name>.sql`, applied in numeric order at first connection. Migration tracking table `_migrations(version INTEGER PRIMARY KEY, name TEXT, applied_at TIMESTAMP)`.
- All inserts use `INSERT OR REPLACE` (NFR12, NFR13: same-day reruns idempotent).
- Money fields stored as `DECIMAL(18,4)`; ratios as `DOUBLE`; dates as `DATE`; timestamps as `TIMESTAMP` (UTC).
- `Idea` snapshots persisted as a `JSON`-typed column (`idea_json`) plus denormalized columns for filtering (`ticker`, `as_of`, `pflichtregeln_passed`, `bypassed_count`).
- State-machine `valid_transition` is the only place that knows transitions. `close_trade` calls it; on invalid transition it raises `LifecycleError` BEFORE touching DuckDB.
- 100% coverage required on `lifecycle/state_machine.py` (project-context.md gate).
- Trade UUIDs and Idea UUIDs are version-4 UUIDs from stdlib `uuid`; trade.idea_id FK-links into ideas.
- All public functions are sync (mirror `idea`/`scan`/`macro_snapshot`).

**Ask First:** N/A — YOLO batch.

**Never:**
- No automated state transitions (project-context.md MVP scope: "manual position entry only, no wheel state machine"). `take_profit_pending` is the only intermediate state.
- No `csp.idea(..., override=True)` auto-persistence. `csp.log_idea(idea)` is explicit; consumers opt in. (D14 closed via the helper, not via hidden side effects.)
- No DuckDB connection caching across function calls — open/close per call (sync, short-lived). DuckDB is in-process and cheap.
- No raw SQL string interpolation — every query uses parameterized `con.execute(sql, [params])`.
- No `pandas` — DuckDB returns `polars.DataFrame` or rows tuples directly; we convert to lists of Pydantic models.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Log idea (passes) | `log_idea(passing_idea)` | `idea_id: str` (UUID); row in `ideas` | N/A |
| Log idea (override) | `log_idea(bypassed_idea)` | `idea_id: str`; `bypassed_count > 0` queryable | N/A |
| Log trade from idea | `log_trade(idea, contracts=2)` | `Trade(status=OPEN, contracts=2, idea_id=...)`; row in `trades` AND `ideas` if not already there | N/A |
| Log trade idempotent rerun | same idea + contracts | same `trade_id` re-emitted; no duplicate row | N/A |
| Close trade — valid transition | `close_trade(tid, status=CLOSED_PROFIT, close_premium=Decimal("0.50"))` | updated `Trade` (status, close_date, close_premium, pnl computed) | N/A |
| Close trade — invalid transition | open → assigned (allowed) but assigned → closed_profit | — | `LifecycleError("invalid transition assigned → closed_profit")` BEFORE DB write |
| Close trade — unknown trade_id | `close_trade("does-not-exist", ...)` | — | `LifecycleError("trade not found: ...")` |
| List open positions | mix of open + closed in DB | only the OPEN + TAKE_PROFIT_PENDING ones, sorted by `open_date` ASC then `ticker` ASC | N/A |
| List open positions (empty DB) | no rows | `[]` | N/A |
| Get idea by trade_id | trade exists | the `Idea` snapshot as it was when logged (`Idea.model_validate_json(row.idea_json)`) | N/A |
| Get idea — unknown trade | `get_idea("does-not-exist")` | — | `LifecycleError("trade not found: ...")` |
| List ideas | `list_ideas(since=..., overrides_only=False)` | sorted DESC by `as_of`, then `ticker` ASC; ALL ideas, not just trade-linked | N/A |
| List ideas (overrides only) | `overrides_only=True` | only ideas with `bypassed_count > 0` | N/A |
| Migration on fresh DB | first connection, empty file | `001_initial.sql` runs, `_migrations` populated | N/A |
| Migration rerun | same DB, same code version | no re-application; `_migrations.version=1` already present → skip | N/A |

</frozen-after-approval>

## Code Map

- `src/csp/lifecycle/__init__.py` — package init.
- `src/csp/lifecycle/state_machine.py` — `TradeStatus` enum, `VALID_TRANSITIONS`, `valid_transition(from, to)`. 100% coverage gate.
- `src/csp/persistence/__init__.py` — package init.
- `src/csp/persistence/db.py` — `connection(settings) -> Iterator[duckdb.Connection]` context manager + `_apply_migrations(con)`.
- `src/csp/persistence/migrations/001_initial.sql` — `_migrations`, `ideas`, `trades` tables.
- `src/csp/persistence/ideas.py` — `insert_idea(con, idea) -> str`, `get_idea(con, idea_id) -> Idea | None`, `list_ideas(con, *, since, overrides_only) -> list[Idea]`.
- `src/csp/persistence/trades.py` — `insert_trade(con, trade) -> Trade`, `get_trade(con, trade_id) -> Trade | None`, `update_trade(con, trade) -> Trade`, `list_open(con) -> list[Trade]`, `get_idea_for_trade(con, trade_id) -> Idea | None`.
- `src/csp/models/trade.py` — `Trade` Pydantic model (frozen, money-Decimal/ratio-float).
- `src/csp/lifecycle_api.py` — public surface: `log_idea`, `log_trade`, `close_trade`, `list_open_positions`, `get_idea`, `list_ideas`.
- `src/csp/exceptions.py` — add `LifecycleError`, `IdempotencyError`.
- `src/csp/config.py` — add `Settings.duckdb_path: Path = Path("data/trades.duckdb")`.
- `src/csp/__init__.py` — re-exports.
- `tests/test_state_machine.py` — full transition matrix.
- `tests/test_persistence.py` — migration runs once, ideas + trades CRUD round-trip, idempotency.
- `tests/test_lifecycle_api.py` — happy paths + invalid transitions + unknown IDs + list filters.

## Tasks & Acceptance

**Acceptance:**
- `csp.TradeStatus.OPEN` initial; `valid_transition(OPEN, CLOSED_PROFIT)` is True; `valid_transition(ASSIGNED, CLOSED_PROFIT)` is False; `valid_transition(CLOSED_PROFIT, OPEN)` is False.
- `con.execute("SELECT version FROM _migrations").fetchall() == [(1,)]` after fresh init; running connection again does NOT re-apply.
- `log_trade` round-trip: returns `Trade` with `status=OPEN`, persists row, idempotent rerun returns same `trade_id`.
- `close_trade(tid, status=CLOSED_PROFIT, close_premium=Decimal("0.50"))`: PnL computed correctly = `(open_premium - close_premium) × contracts × 100`.
- `close_trade` with invalid transition raises `LifecycleError` BEFORE any DB write (verifiable: row's `status` unchanged afterwards).
- `list_open_positions()` returns only `OPEN` + `TAKE_PROFIT_PENDING` rows, sorted (date ASC, ticker ASC).
- `get_idea(trade_id)` returns the original `Idea` byte-equivalent to what was logged.
- `list_ideas(overrides_only=True)` filters to `bypassed_count > 0`.
- Pre-commit gates clean. Coverage ≥ 80% overall, **100% on `lifecycle/state_machine.py`**.
- New deferred D# entries for everything that's NOT in this slice (e.g., wheel-state extension, Hormuz special-rules, automated assignment detection).
