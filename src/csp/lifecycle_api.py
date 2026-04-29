"""Public lifecycle-API — `log_trade`, `close_trade`, `list_open_positions`,
`get_idea`, `list_ideas`, `log_idea` (Slice 6, PRD FR21-FR24, FR9).

Sync (mirror `csp.idea`/`csp.scan`/`csp.macro_snapshot`); jede Funktion öffnet
eine kurzlebige DuckDB-Connection via `persistence.db.connection(settings)` —
DuckDB ist in-Process, kostenlos zu öffnen, deshalb keine Pool-Verwaltung.

Zustands-Transitions werden vor jedem `UPDATE` über `valid_transition`
abgesichert; bei Verstoß wird `LifecycleError` geworfen, BEVOR die DB berührt
wird (deferred work D14: Override-Persistenz via `log_idea`; D3 dito).
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from loguru import logger

from csp.config import Settings
from csp.exceptions import LifecycleError
from csp.lifecycle.state_machine import TERMINAL_STATES, TradeStatus, valid_transition
from csp.models.idea import Idea
from csp.models.trade import Trade
from csp.persistence import connection
from csp.persistence.ideas import get_idea_by_id, insert_idea
from csp.persistence.ideas import list_ideas as _list_ideas_db
from csp.persistence.trades import (
    get_trade,
    insert_trade,
    list_open_trades,
    update_trade,
)


def _new_uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Ideas
# ---------------------------------------------------------------------------


def log_idea(idea: Idea) -> str:
    """Persistiert einen `Idea`-Snapshot und liefert die UUID zurück.

    Hauptzweck: FR9 Override-Audit-Trail (deferred-work D3, D14). Aufrufer, die
    `csp.idea(..., override=True)` benutzen, MÜSSEN diese Funktion aufrufen,
    um die Override-Entscheidung für den Monthly-Review-Query zu erhalten.
    Auch Pflichtregeln-bestandene Ideen können geloggt werden — `list_ideas`
    sortiert dann nach `as_of` DESC.

    Returns:
        Die UUID4 der Idea (als String). Wird auch in `trades.idea_id`
        verwendet, falls später `log_trade(idea)` ohne expliziten Re-Log
        aufgerufen wird.
    """
    settings = Settings.load()
    idea_id = _new_uuid()
    with connection(settings) as con:
        insert_idea(con, idea_id=idea_id, idea=idea)
    if idea.bypassed_rules:
        logger.warning(
            "log_idea: Override-Idea persistiert ({ticker}, idea_id={idea_id}, "
            "bypassed={n_bypass} Regeln)",
            ticker=idea.ticker,
            idea_id=idea_id,
            n_bypass=len(idea.bypassed_rules),
        )
    return idea_id


def get_idea(trade_id: str) -> Idea:
    """Liefert die `Idea`, aus der `trade_id` entstand (FR-NFR17).

    Raises:
        LifecycleError: wenn `trade_id` unbekannt ist.
    """
    settings = Settings.load()
    with connection(settings) as con:
        trade = get_trade(con, trade_id)
        if trade is None:
            raise LifecycleError(f"trade nicht gefunden: {trade_id}")
        idea = get_idea_by_id(con, trade.idea_id)
        if idea is None:
            # Defensiv: Idea sollte über FK garantiert sein.
            raise LifecycleError(
                f"idea {trade.idea_id} fehlt für trade {trade_id} (FK-Inkonsistenz)"
            )
    return idea


def list_ideas(
    *,
    since: date | None = None,
    overrides_only: bool = False,
) -> list[Idea]:
    """Liefert alle gespeicherten Ideas, optional gefiltert.

    Args:
        since: nur Ideas mit `as_of >= since`. Default: kein Filter.
        overrides_only: nur Ideas mit `len(bypassed_rules) > 0`. Default False.

    Returns:
        Sortiert: `as_of` DESC, `ticker` ASC. Niemals ``None``.
    """
    settings = Settings.load()
    with connection(settings) as con:
        return _list_ideas_db(con, since=since, overrides_only=overrides_only)


# ---------------------------------------------------------------------------
# Trades
# ---------------------------------------------------------------------------


def log_trade(idea: Idea, *, contracts: int = 1, notes: str | None = None) -> Trade:
    """Eröffnet eine Position aus einem `Idea`-Snapshot.

    Verhalten:
    - Persistiert den `Idea`-Snapshot (über `log_idea`-Logik), wenn nicht schon
      via `idea_id` referenziert.
    - **Idempotenz:** ein zweiter Aufruf mit derselben `(idea, contracts)`-
      Kombination liefert den **bestehenden** Trade zurück, statt einen
      Duplikat-Insert auszulösen — egal ob bewusster Rerun oder Brodelfehler.
    - Status startet als `TradeStatus.OPEN`.
    - `cash_secured = contracts * strike * 100` (Decimal-präzise).

    Args:
        idea: `Idea` vom Pflichtregeln-Gate. Override-Ideen (`bypassed_rules`
            non-empty) sind erlaubt — die Persistenz ist explizit Audit-Pfad.
        contracts: Anzahl Kontrakte (>0). Default 1.
        notes: Freitext (z. B. "Override wegen NOW-Earnings overhang").

    Raises:
        LifecycleError: bei `contracts <= 0`.
    """
    if contracts <= 0:
        raise LifecycleError(f"contracts muss > 0 sein, war {contracts}")

    settings = Settings.load()
    now = datetime.now(UTC)

    with connection(settings) as con:
        # Idempotenz-Anker: existiert bereits ein offener Trade mit
        # (ticker, open_date, contracts) — z. B. nach versehentlichem Doppel-Lauf?
        # Wir checken VOR jeglichem `INSERT`, damit kein Orphan-`Idea`-Record
        # auf Rerun entsteht.
        same_day_open = con.execute(
            """
            SELECT trade_id
            FROM trades
            WHERE ticker = ? AND open_date = ? AND contracts = ? AND status = ?
            ORDER BY inserted_at ASC
            LIMIT 1
            """,
            [
                idea.ticker,
                idea.as_of,
                contracts,
                TradeStatus.OPEN.value,
            ],
        ).fetchone()
        if same_day_open is not None:
            existing_trade = get_trade(con, str(same_day_open[0]))
            if existing_trade is not None:
                return existing_trade

        # Erst-Insert: zuerst Idea, dann Trade mit FK darauf.
        idea_id = _new_uuid()
        insert_idea(con, idea_id=idea_id, idea=idea)

        cash_secured = idea.strike * Decimal(contracts) * Decimal(100)
        trade = Trade(
            trade_id=_new_uuid(),
            idea_id=idea_id,
            ticker=idea.ticker,
            status=TradeStatus.OPEN,
            contracts=contracts,
            open_date=idea.as_of,
            open_premium=idea.mid_premium,
            cash_secured=cash_secured,
            notes=notes,
            inserted_at=now,
            updated_at=now,
        )
        insert_trade(con, trade)
        return trade


def close_trade(
    trade_id: str,
    *,
    new_status: TradeStatus,
    close_premium: Decimal | None = None,
    close_date_value: date | None = None,
    notes: str | None = None,
) -> Trade:
    """Schließt einen Trade in den gewünschten Zielstatus.

    Args:
        trade_id: UUID des Trades.
        new_status: Zielstatus (`CLOSED_PROFIT`, `CLOSED_LOSS`, `ASSIGNED`,
            `EMERGENCY_CLOSE`, `TAKE_PROFIT_PENDING`).
        close_premium: Pro-Kontrakt-Schluss-Premium in USD (nötig für PnL-
            Berechnung außer bei `ASSIGNED`).
        close_date_value: Tag der Schließung; Default = heute UTC-Datum.
        notes: optionaler Freitext (überschreibt `notes` nicht falls None).

    Raises:
        LifecycleError: trade unbekannt; oder Übergang nicht erlaubt.
    """
    settings = Settings.load()
    today = datetime.now(UTC).date()
    effective_close_date = close_date_value or today

    with connection(settings) as con:
        trade = get_trade(con, trade_id)
        if trade is None:
            raise LifecycleError(f"trade nicht gefunden: {trade_id}")
        if not valid_transition(trade.status, new_status):
            raise LifecycleError(f"ungültiger Übergang {trade.status.value} → {new_status.value}")

        # PnL-Berechnung nur bei terminalen Status mit `close_premium`.
        pnl: Decimal | None
        if new_status in TERMINAL_STATES and new_status is not TradeStatus.ASSIGNED:
            if close_premium is None:
                raise LifecycleError(f"close_premium ist Pflicht für Status {new_status.value}")
            pnl = (trade.open_premium - close_premium) * Decimal(trade.contracts) * Decimal(100)
            stored_close_date: date | None = effective_close_date
            stored_close_premium: Decimal | None = close_premium
        elif new_status is TradeStatus.ASSIGNED:
            # Bei Assignment wird die Position abgewickelt; `close_premium` darf
            # `None` sein, PnL bleibt `None` (Aktien-Übernahme verändert die
            # Buchhaltung anderswo).
            pnl = None
            stored_close_date = effective_close_date
            stored_close_premium = close_premium
        else:
            # `take_profit_pending` ist Zwischenstatus — Close-Felder bleiben leer.
            pnl = None
            stored_close_date = None
            stored_close_premium = None

        update_trade(
            con,
            trade_id=trade_id,
            new_status=new_status,
            close_date=stored_close_date,
            close_premium=stored_close_premium,
            pnl=pnl,
            notes=notes,
        )
        updated = get_trade(con, trade_id)
        # Defensiv: SELECT direkt nach UPDATE muss eine Zeile zurückgeben.
        assert updated is not None, "trade verschwunden zwischen UPDATE und SELECT"
        return updated


def list_open_positions() -> list[Trade]:
    """Liefert alle offenen Trades (Status `OPEN` oder `TAKE_PROFIT_PENDING`).

    Sortiert: `open_date` ASC, dann `ticker` ASC.
    """
    settings = Settings.load()
    with connection(settings) as con:
        return list_open_trades(con)
