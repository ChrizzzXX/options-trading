"""`trades`-Tabelle CRUD (Slice 6, Slice-9-Härtung).

`insert_trade` ist `INSERT OR REPLACE` — idempotent. `update_trade` setzt nur
Status / `close_*` / `pnl` / `notes` / `updated_at`; `inserted_at` und alle
Open-Felder bleiben unangetastet.

Die `lifecycle_api`-Schicht orchestriert State-Machine-Validierung VOR DB-Calls;
diese Funktionen sind dumme Daten-Dippers und kennen keine Transition-Regeln.

Slice-9-Härtung (D36): `_row_to_trade` benutzte vier `# type: ignore`-
Kommentare, weil `duckdb.DuckDBPyConnection.execute(...).fetchone()` als
`tuple[object, ...]` typisiert ist. Ersetzt durch `typing.cast` plus
defensive `isinstance`-Checks an den Boundary-Spalten — jeder fehlerhafte
Schema-Drift fällt jetzt mit einer klaren `LifecycleError` auf statt
mit einer pydantic-Fehlermeldung tief in der Modellkonstruktion.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import cast

import duckdb

from csp.exceptions import LifecycleError
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
    """DuckDB-Row → Pydantic-`Trade`. Decimal-Felder bleiben als Decimal erhalten.

    Defensive Schema-Boundary: jede Spalte mit nicht-trivialem Python-Typ
    (`int`, `date`, `datetime`) wird per `isinstance` gecheckt — bei Drift
    fliegt eine klare `LifecycleError` statt einer kryptischen pydantic-Message.

    Strings + Decimals gehen über `str(...)` durch (DuckDB liefert
    `decimal.Decimal` bereits direkt; `str(...)` ist idempotent für sie).
    """
    # Schema-Erwartungen aus 001_initial.sql:
    # 0 trade_id TEXT | 1 idea_id TEXT | 2 ticker TEXT | 3 status TEXT
    # 4 contracts INTEGER | 5 open_date DATE | 6 open_premium DECIMAL
    # 7 cash_secured DECIMAL | 8 close_date DATE NULL | 9 close_premium DECIMAL NULL
    # 10 pnl DECIMAL NULL | 11 notes TEXT NULL | 12 inserted_at TIMESTAMP
    # 13 updated_at TIMESTAMP
    contracts_raw = row[4]
    if not isinstance(contracts_raw, int):
        raise LifecycleError(
            f"Schema-Drift: trades.contracts ist {type(contracts_raw).__name__}, "
            f"erwartet `int`. Migration `001_initial.sql` aktuell?"
        )
    open_date_raw = row[5]
    if not isinstance(open_date_raw, date):
        raise LifecycleError(
            f"Schema-Drift: trades.open_date ist {type(open_date_raw).__name__}, "
            f"erwartet `datetime.date`."
        )
    inserted_at_raw = row[12]
    updated_at_raw = row[13]
    if not isinstance(inserted_at_raw, datetime):
        raise LifecycleError(
            f"Schema-Drift: trades.inserted_at ist {type(inserted_at_raw).__name__}, "
            f"erwartet `datetime`."
        )
    if not isinstance(updated_at_raw, datetime):
        raise LifecycleError(
            f"Schema-Drift: trades.updated_at ist {type(updated_at_raw).__name__}, "
            f"erwartet `datetime`."
        )
    close_date_raw = row[8]
    close_date_typed: date | None
    if close_date_raw is None:
        close_date_typed = None
    elif isinstance(close_date_raw, date):
        close_date_typed = close_date_raw
    else:
        raise LifecycleError(
            f"Schema-Drift: trades.close_date ist {type(close_date_raw).__name__}, "
            f"erwartet `datetime.date` oder NULL."
        )

    return Trade(
        trade_id=str(row[0]),
        idea_id=str(row[1]),
        ticker=str(row[2]),
        status=TradeStatus(cast(str, row[3])),
        contracts=contracts_raw,
        open_date=open_date_raw,
        open_premium=Decimal(str(row[6])),
        cash_secured=Decimal(str(row[7])),
        close_date=close_date_typed,
        close_premium=None if row[9] is None else Decimal(str(row[9])),
        pnl=None if row[10] is None else Decimal(str(row[10])),
        notes=None if row[11] is None else str(row[11]),
        inserted_at=inserted_at_raw,
        updated_at=updated_at_raw,
    )
