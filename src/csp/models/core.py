"""Minimale Pydantic-v2-Datenträger für den Pflichtregeln-Slice.

Diese Modelle sind absichtlich vendor-agnostisch — die ORATS-/IVolatility-spezifischen
Aliase (Field(alias=...)) folgen mit dem ORATS-Client-Slice.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OratsCore(BaseModel):
    """Per-Underlying-Kennzahlen, wie sie ORATS' /cores liefert (vendor-agnostisch lokal)."""

    model_config = ConfigDict(frozen=True)

    ticker: str
    under_price: float = Field(gt=0, description="Spotpreis des Underlyings; muss > 0 sein.")
    sector: str
    mkt_cap_thousands: float = Field(
        description="Marktkapitalisierung in Tausend USD (ORATS-Konvention)."
    )
    ivr: float = Field(description="1-Jahres-IV-Perzentil (entspricht ORATS ivPctile1y).")
    days_to_next_earn: int = Field(
        ge=0,
        description="Tage bis zum nächsten Earnings; 0 = heute Earnings (Pflichtregel 5 Fail).",
    )
    avg_opt_volu_20d: int = Field(
        description="Durchschnittliches Optionsvolumen der letzten 20 Tage."
    )

    @field_validator("ticker")
    @classmethod
    def _normalise_ticker(cls, value: str) -> str:
        """Ticker werden uppercase normalisiert, damit Pflichtregel 9 case-insensitiv prüft."""
        return value.upper()


class OratsStrike(BaseModel):
    """Per-Strike-Kennzahlen (ATM/OTM-Put), die für Pflichtregeln gebraucht werden."""

    model_config = ConfigDict(frozen=True)

    strike: float
    delta: float = Field(ge=-1.0, le=0.0, description="Put-Delta; muss in [-1, 0] liegen.")
    dte: int
    put_ask: float
    put_bid: float

    @model_validator(mode="after")
    def _validate_quotes(self) -> OratsStrike:
        """Lehnt überkreuzte oder negative Quotes ab: put_ask >= put_bid >= 0."""
        if self.put_bid < 0:
            raise ValueError(
                f"put_bid {self.put_bid} ist negativ; gültige Quotes erfordern put_bid >= 0"
            )
        if self.put_ask < self.put_bid:
            raise ValueError(
                f"put_ask {self.put_ask} < put_bid {self.put_bid} (überkreuzte Quotes)"
            )
        return self


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
