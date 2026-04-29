"""Pydantic-v2-Datenträger für ORATS-Vendor-Antworten und lokale Snapshots.

Die Aliase (`Field(alias="camelCase")`) bilden die JSON-Felder der ORATS-Endpunkte
`/cores`, `/hist/cores` und `/hist/strikes` direkt auf snake_case ab. ORATS fügt
Felder ohne Vorankündigung hinzu — daher `extra="ignore"` an der Vendor-Grenze
(im Gegensatz zu `extra="forbid"` auf Konfigurations-Modellen).

Vendor-Gotchas (siehe project-context.md):
- `mktCap` ist in **Tausend USD** (96524 = 96,5 Mio USD; 93302435 = 93,3 Mrd USD).
- `ivPctile1y` ist die IVR (1-Jahres-IV-Perzentil), nicht 1-Monat.
- `daysToNextErn = 0` bedeutet "heute Earnings" (Pflichtregel 5 Fail).
- ORATS hat zwei Sektor-Felder: `sector` (GICS-Subindustrie, z. B. "Application Software")
  und `sectorName` (GICS-Sektor, z. B. "Technology"). Pflichtregel 8 nutzt den Sektor
  (sectorName-Niveau), daher mappt unser `sector`-Feld auf `sectorName`.
- `pxAtmIv` ist der ATM-IV-Berechnungs-Spotpreis; `priorCls` ist der Vortagesschluss.
  Wir verwenden `pxAtmIv` als `under_price` (Spot zum Quotenzeitpunkt).
- `/hist/strikes` liefert die Felder `putBidPrice`/`putAskPrice` und `delta`
  (Call-Delta — Put-Delta = `delta - 1`); Aufrufer berechnet das Put-Delta
  vor der Modell-Konstruktion oder übergibt es explizit.

Slice-9-Härtung (D5 + D27): jedes numerische Feld bekommt einen
`@field_validator` mit ``math.isfinite`` — NaN und ±Inf scheitern an der
Vendor-Grenze. Folge: Pflichtregeln-Vergleiche und Sort-Schlüssel sehen
nie nicht-finite Floats; NFR20-Determinismus ist transitiv abgesichert.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _require_finite(value: float, *, field: str) -> float:
    """Pflichtregel-Härtung: NaN / ±Inf ablehnen, Wert sonst durchreichen.

    NaN-Vergleiche sind in Python nondeterministisch (jeder NaN-Vergleich = False),
    Inf bricht alle Top-N-Sortierungen. Beides darf nie aus der Vendor-Antwort
    in die Domain-Logik. Pydantic hat keinen built-in `assert_finite` — daher
    diese kleine Helper-Funktion, an jedem numerischen Feld als Validator.
    """
    if not math.isfinite(value):
        raise ValueError(f"{field}={value!r} ist nicht finite (NaN/Inf abgelehnt)")
    return value


class OratsCore(BaseModel):
    """Per-Underlying-Kennzahlen aus ORATS /cores oder /hist/cores."""

    model_config = ConfigDict(
        frozen=True, validate_by_name=True, validate_by_alias=True, extra="ignore"
    )

    ticker: str
    under_price: float = Field(
        alias="pxAtmIv",
        gt=0,
        description="Spotpreis des Underlyings (ORATS pxAtmIv); muss > 0 sein.",
    )
    sector: str = Field(
        alias="sectorName",
        description="GICS-Sektor (ORATS sectorName, nicht sector — Letzteres ist Subindustrie).",
    )
    mkt_cap_thousands: float = Field(
        alias="mktCap",
        description="Marktkapitalisierung in Tausend USD (ORATS-Konvention).",
    )
    ivr: float = Field(
        alias="ivPctile1y",
        description="1-Jahres-IV-Perzentil (entspricht ORATS ivPctile1y; ist die IVR).",
    )
    days_to_next_earn: int = Field(
        alias="daysToNextErn",
        ge=0,
        description="Tage bis zum nächsten Earnings; 0 = heute Earnings (Pflichtregel 5 Fail).",
    )
    avg_opt_volu_20d: float = Field(
        alias="avgOptVolu20d",
        description="Durchschnittliches Optionsvolumen der letzten 20 Tage (ORATS liefert float).",
    )

    @field_validator("ticker")
    @classmethod
    def _normalise_ticker(cls, value: str) -> str:
        """Ticker werden uppercase normalisiert, damit Pflichtregel 9 case-insensitiv prüft."""
        return value.upper()

    @field_validator("under_price", "mkt_cap_thousands", "ivr", "avg_opt_volu_20d")
    @classmethod
    def _finite(cls, value: float, info: object) -> float:
        # Slice-9-Härtung (D5/D27): NaN/±Inf am Vendor-Rand ablehnen.
        return _require_finite(value, field=getattr(info, "field_name", "<unknown>"))


class OratsStrike(BaseModel):
    """Per-Strike-Kennzahlen aus ORATS /strikes oder /hist/strikes (Put-Seite)."""

    model_config = ConfigDict(
        frozen=True, validate_by_name=True, validate_by_alias=True, extra="ignore"
    )

    strike: float
    delta: float = Field(ge=-1.0, le=0.0, description="Put-Delta; muss in [-1, 0] liegen.")
    dte: int = Field(
        gt=0,
        description="Tage bis Verfall; muss > 0 sein (0DTE-Strikes scheiden für CSP aus, "
        "und die Yield-Berechnung würde sonst durch 0 dividieren).",
    )
    put_ask: float = Field(alias="putAskPrice")
    put_bid: float = Field(alias="putBidPrice")

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

    @field_validator("strike", "delta", "put_ask", "put_bid")
    @classmethod
    def _finite(cls, value: float, info: object) -> float:
        # Slice-9-Härtung (D5/D27): NaN/±Inf am Vendor-Rand ablehnen.
        return _require_finite(value, field=getattr(info, "field_name", "<unknown>"))


class MacroSnapshot(BaseModel):
    """Makro-Kontext (heute nur VIX-Close — der einzige Wert für Pflichtregel 1)."""

    model_config = ConfigDict(frozen=True)

    vix_close: float

    @field_validator("vix_close")
    @classmethod
    def _finite(cls, value: float) -> float:
        # Slice-9-Härtung (D5/D27): NaN/±Inf am Macro-Rand ablehnen.
        return _require_finite(value, field="vix_close")


class PortfolioSnapshot(BaseModel):
    """Portfolio-Zustand für Sektorgewichtung (Pflichtregel 8)."""

    model_config = ConfigDict(frozen=True)

    sector_exposures: dict[str, float] = Field(
        default_factory=dict,
        description="Sektor → Anteil am CSP-Kapital (0..1).",
    )
