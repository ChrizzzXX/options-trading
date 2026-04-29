"""`Trade` — Pydantic-Modell für persistierte Positionen (Slice 6).

Money in `Decimal`, Datum in `date`, Status als `TradeStatus`-Enum. Frozen.

PnL-Konvention: Kurzer Put — Premium-Einnahme bei Open, Premium-Ausgabe bei Close.
``pnl = (open_premium - close_premium) * contracts * 100``. Ein bei `0.50` USD
geschlossener Trade, der bei `1.55` USD geöffnet wurde, mit 1 Kontrakt:
``(1.55 - 0.50) * 1 * 100 = 105.00`` USD Gewinn pro Kontrakt-Position.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from csp.lifecycle.state_machine import TradeStatus


class Trade(BaseModel):
    """Eine offene oder geschlossene CSP-Position.

    Frozen: nach Konstruktion unveränderlich. Status-Änderungen erzeugen ein
    NEUES `Trade`-Objekt mit aktualisierten `status` / `close_*`-Feldern.
    """

    model_config = ConfigDict(frozen=True)

    trade_id: str = Field(description="UUID4 — Primärschlüssel in DuckDB.")
    idea_id: str = Field(
        description="FK auf `ideas`. Liefert die `Idea`-Snapshot zum Zeitpunkt des Logs (FR-NFR17)."
    )
    ticker: str = Field(description="Ticker-Symbol (Großbuchstaben).")
    status: TradeStatus = Field(description="Aktueller Status; siehe `lifecycle.state_machine`.")
    contracts: int = Field(gt=0, description="Anzahl Kontrakte (immer > 0; Short-Put).")
    open_date: date = Field(description="Tag der Eröffnung.")
    open_premium: Decimal = Field(description="Pro-Kontrakt-Eröffnungsprämie in USD.")
    cash_secured: Decimal = Field(
        description="Cash-Secured-Betrag = `contracts * strike * 100` (Decimal)."
    )
    close_date: date | None = Field(
        default=None, description="Tag der Schließung; ``None`` solange offen."
    )
    close_premium: Decimal | None = Field(
        default=None,
        description="Pro-Kontrakt-Schluss-Premium; ``None`` solange offen / bei Assignment.",
    )
    pnl: Decimal | None = Field(
        default=None,
        description="Realisierter PnL = `(open_premium - close_premium) * contracts * 100`.",
    )
    notes: str | None = Field(default=None, description="Freitext-Anmerkung.")
    inserted_at: datetime = Field(description="UTC-Zeitstempel beim ersten Insert.")
    updated_at: datetime = Field(description="UTC-Zeitstempel beim letzten Update.")
