"""Minimale Pydantic-v2-Datenträger für den Pflichtregeln-Slice.

Diese Modelle sind absichtlich vendor-agnostisch — die ORATS-/IVolatility-spezifischen
Aliase (Field(alias=...)) folgen mit dem ORATS-Client-Slice.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OratsCore(BaseModel):
    """Per-Underlying-Kennzahlen, wie sie ORATS' /cores liefert (vendor-agnostisch lokal)."""

    model_config = ConfigDict(frozen=True)

    ticker: str
    under_price: float
    sector: str
    mkt_cap_thousands: float = Field(
        description="Marktkapitalisierung in Tausend USD (ORATS-Konvention)."
    )
    ivr: float = Field(description="1-Jahres-IV-Perzentil (entspricht ORATS ivPctile1y).")
    days_to_next_earn: int = Field(
        description="Tage bis zum nächsten Earnings; 0 = heute Earnings (Pflichtregel 5 Fail).",
    )
    avg_opt_volu_20d: int = Field(
        description="Durchschnittliches Optionsvolumen der letzten 20 Tage."
    )


class OratsStrike(BaseModel):
    """Per-Strike-Kennzahlen (ATM/OTM-Put), die für Pflichtregeln gebraucht werden."""

    model_config = ConfigDict(frozen=True)

    strike: float
    delta: float = Field(description="Put-Delta; muss in [-1, 0] liegen.")
    dte: int
    put_ask: float
    put_bid: float


class MacroSnapshot(BaseModel):
    """Makro-Kontext (heute nur VIX-Close — der einzige Wert für Pflichtregel 1)."""

    model_config = ConfigDict(frozen=True)

    vix_close: float


class PortfolioSnapshot(BaseModel):
    """Portfolio-Zustand für Sektorgewichtung (Pflichtregel 8)."""

    model_config = ConfigDict(frozen=True)

    sector_exposures: dict[str, float] = Field(
        default_factory=dict,
        description="Sektor → Anteil am CSP-Kapital (0..1).",
    )
