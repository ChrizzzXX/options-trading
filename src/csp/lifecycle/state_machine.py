"""Trade-State-Machine — `TradeStatus` plus erlaubte Übergänge (PRD FR21-FR24).

MVP-Scope (project-context.md "Critical Don't-Miss Rules → State-machine invariants"):
- Manuelle Positions-Pflege via `csp.log_trade` / `csp.close_trade` — keine
  automatischen Übergänge.
- `take_profit_pending` ist der einzige Zwischenzustand — der Tag, an dem Chris
  TP markiert hat, ohne dass der Broker schon abgewickelt hat.
- `assigned`, `closed_profit`, `closed_loss`, `emergency_close` sind terminal.
- Wheel-Lebenszyklus (Covered-Call-Folgegeschäfte nach Assignment) ist auf Growth
  verschoben; `assigned` bleibt im MVP final.

100%-Coverage-Gate (project-context.md): jeder erlaubte UND jeder verbotene
Übergang muss durch einen Test berührt werden.
"""

from __future__ import annotations

from enum import StrEnum


class TradeStatus(StrEnum):
    """Mögliche Status-Werte eines Trades.

    Werte sind Strings (StrEnum) — direkt persistierbar in DuckDB als TEXT,
    direkt serialisierbar in JSON, direkt vergleichbar mit String-Literalen.
    """

    OPEN = "open"
    TAKE_PROFIT_PENDING = "take_profit_pending"
    CLOSED_PROFIT = "closed_profit"
    CLOSED_LOSS = "closed_loss"
    ASSIGNED = "assigned"
    EMERGENCY_CLOSE = "emergency_close"


TERMINAL_STATES: frozenset[TradeStatus] = frozenset(
    {
        TradeStatus.CLOSED_PROFIT,
        TradeStatus.CLOSED_LOSS,
        TradeStatus.ASSIGNED,
        TradeStatus.EMERGENCY_CLOSE,
    }
)
"""Terminale Status — kein weiterer Übergang erlaubt."""


VALID_TRANSITIONS: dict[TradeStatus, frozenset[TradeStatus]] = {
    TradeStatus.OPEN: frozenset(
        {
            TradeStatus.CLOSED_PROFIT,
            TradeStatus.CLOSED_LOSS,
            TradeStatus.ASSIGNED,
            TradeStatus.EMERGENCY_CLOSE,
            TradeStatus.TAKE_PROFIT_PENDING,
        }
    ),
    TradeStatus.TAKE_PROFIT_PENDING: frozenset({TradeStatus.CLOSED_PROFIT}),
    # Terminale Status — keine Folge-Übergänge.
    TradeStatus.CLOSED_PROFIT: frozenset(),
    TradeStatus.CLOSED_LOSS: frozenset(),
    TradeStatus.ASSIGNED: frozenset(),
    TradeStatus.EMERGENCY_CLOSE: frozenset(),
}
"""Komplette Übergangstabelle. Jeder Eintrag ist explizit (auch leere Mengen),
damit `valid_transition` ohne KeyError arbeiten kann und neue Status-Werte
einen Compile-Time-Audit erzwingen (alle Cases im `match` müssen ergänzt werden).
"""


def valid_transition(from_status: TradeStatus, to_status: TradeStatus) -> bool:
    """Prüft, ob `from_status → to_status` ein erlaubter Übergang ist.

    Reine Funktion, kein I/O. `csp.close_trade` ruft sie BEVOR irgendetwas in
    DuckDB geschrieben wird — bei Verstoß wird `LifecycleError` geworfen, der
    DB-Zustand bleibt unverändert.

    Args:
        from_status: aktueller Status des Trades (aus DB gelesen).
        to_status: gewünschter neuer Status.

    Returns:
        ``True``, wenn der Übergang in `VALID_TRANSITIONS` enthalten ist;
        ``False`` sonst (inkl. selbst-Übergang `from == to`).
    """
    return to_status in VALID_TRANSITIONS[from_status]
