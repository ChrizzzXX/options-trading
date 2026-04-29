"""`trades`-Tabelle CRUD (Slice 6).

`insert_trade` ist `INSERT OR REPLACE` — idempotent. `update_trade` setzt nur
Status / `close_*` / `pnl` / `notes` / `updated_at`; `inserted_at` und alle
Open-Felder bleiben unangetastet.

Die `lifecycle_api`-Schicht orchestriert State-Machine-Validierung VOR DB-Calls;
diese Funktionen sind dumme Daten-Dippers und kennen keine Transition-Regeln.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import duckdb

from csp.lifecycle.state_machine import TradeStatus
from csp.models.trade import Trade


def insert_trade(con: duckdb.DuckDBPyConnection, trade: Trade) -> None:
    """`INSERT OR REPLACE` — idempotent."""
    con.execute(
        """
        INSERT OR REPLACE INTO trades (
            trade_id, idea_id, ticker, status, contracts,
            open_date, open_premium, cash_secured,
            close_date, close_premium, pnl, notes,
            inserted_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            trade.trade_id,
            trade.idea_id,
            trade.ticker,
            trade.status.value,
            trade.contracts,
            trade.open_date,
            trade.open_premium,
            trade.cash_secured,
            trade.close_date,
            trade.close_premium,
            trade.pnl,
            trade.notes,
            trade.inserted_at,
            trade.updated_at,
        ],
    )


def get_trade(con: duckdb.DuckDBPyConnection, trade_id: str) -> Trade | None:
    """Lädt einen `Trade` per UUID — ``None`` falls unbekannt."""
    row = con.execute(
        """
        SELECT trade_id, idea_id, ticker, status, contracts,
               open_date, open_premium, cash_secured,
               close_date, close_premium, pnl, notes,
               inserted_at, updated_at
        FROM trades WHERE trade_id = ?
        """,
        [trade_id],
    ).fetchone()
    if row is None:
        return None
    return _row_to_trade(row)


def list_open_trades(con: duckdb.DuckDBPyConnection) -> list[Trade]:
    """Alle Trades mit Status `OPEN` oder `TAKE_PROFIT_PENDING`.

    Sortiert: `open_date` ASC, dann `ticker` ASC — Älteste zuerst, deterministisch
    bei gleichem Tag.
    """
    rows = con.execute(
        """
        SELECT trade_id, idea_id, ticker, status, contracts,
               open_date, open_premium, cash_secured,
               close_date, close_premium, pnl, notes,
               inserted_at, updated_at
        FROM trades
        WHERE status IN (?, ?)
        ORDER BY open_date ASC, ticker ASC
        """,
        [TradeStatus.OPEN.value, TradeStatus.TAKE_PROFIT_PENDING.value],
    ).fetchall()
    return [_row_to_trade(row) for row in rows]


def update_trade(
    con: duckdb.DuckDBPyConnection,
    *,
    trade_id: str,
    new_status: TradeStatus,
    close_date: object | None,
    close_premium: Decimal | None,
    pnl: Decimal | None,
    notes: str | None,
) -> None:
    """Aktualisiert nur Status- + Close-Felder; ``updated_at`` neu gesetzt."""
    con.execute(
        """
        UPDATE trades SET
            status = ?,
            close_date = ?,
            close_premium = ?,
            pnl = ?,
            notes = COALESCE(?, notes),
            updated_at = ?
        WHERE trade_id = ?
        """,
        [
            new_status.value,
            close_date,
            close_premium,
            pnl,
            notes,
            datetime.now(UTC),
            trade_id,
        ],
    )


def find_open_trade_by_idea(
    con: duckdb.DuckDBPyConnection, idea_id: str, contracts: int
) -> Trade | None:
    """Sucht einen offenen Trade mit gleicher (idea_id, contracts).

    Wird von `csp.log_trade` für Idempotenz benutzt: zweimal `log_trade(idea, 1)`
    soll denselben Trade zurückliefern, nicht zwei.
    """
    row = con.execute(
        """
        SELECT trade_id, idea_id, ticker, status, contracts,
               open_date, open_premium, cash_secured,
               close_date, close_premium, pnl, notes,
               inserted_at, updated_at
        FROM trades
        WHERE idea_id = ? AND contracts = ? AND status = ?
        ORDER BY inserted_at ASC
        LIMIT 1
        """,
        [idea_id, contracts, TradeStatus.OPEN.value],
    ).fetchone()
    if row is None:
        return None
    return _row_to_trade(row)


def _row_to_trade(row: tuple[object, ...]) -> Trade:
    """DuckDB-Row → Pydantic-`Trade`. Decimal-Felder bleiben als Decimal erhalten."""
    # DuckDB-Rows sind statisch `tuple[object, ...]` — wir wissen aus dem
    # Schema, dass die Spalten passend sind. Pydantic-Validators an der
    # `Trade`-Modell-Konstruktion fangen jede Schema-Drift auf.
    return Trade(
        trade_id=str(row[0]),
        idea_id=str(row[1]),
        ticker=str(row[2]),
        status=TradeStatus(str(row[3])),
        contracts=int(row[4]),  # type: ignore[call-overload]  # DuckDB INT → int
        open_date=row[5],  # type: ignore[arg-type]
        open_premium=Decimal(str(row[6])),
        cash_secured=Decimal(str(row[7])),
        close_date=row[8],  # type: ignore[arg-type]
        close_premium=None if row[9] is None else Decimal(str(row[9])),
        pnl=None if row[10] is None else Decimal(str(row[10])),
        notes=None if row[11] is None else str(row[11]),
        inserted_at=row[12],  # type: ignore[arg-type]
        updated_at=row[13],  # type: ignore[arg-type]
    )
