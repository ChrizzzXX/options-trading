"""`Idea` — vollständig populiertes Pydantic-Modell für eine einzelne CSP-Kandidatur.

Eine `Idea` ist immer populiert: ob die Pflichtregeln passieren oder nicht, ob ein
`override` aktiv war oder nicht — die Felder `pflichtregeln_passed`, `reasons` und
`bypassed_rules` tragen die Gate-Verdict-Annotation.

Semantik der drei Zustände (erschöpfend, paarweise disjunkt):
- Pass (Regeln gehalten):  ``pflichtregeln_passed=True,  reasons=[],          bypassed_rules=[]``.
- Fail ohne override:       ``pflichtregeln_passed=False, reasons=<n Regeln>,  bypassed_rules=[]``.
- Fail mit ``override``:    ``pflichtregeln_passed=True,  reasons=[],          bypassed_rules=<n>``.

Geld als ``Decimal`` (Strike, Bid/Ask, Mid-Premium); Verhältnisse als ``float``
(Delta, OTM%, annualisierte Yield). PRD FR13/FR16; Spec
``spec-idea-singleticker.md``.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Idea(BaseModel):
    """Eine CSP-Kandidatur — ORATS-Daten + Pflichtregeln-Verdict + Override-Pfad.

    Das Modell ist ``frozen=True``: nach Konstruktion unveränderlich. Spätere
    Slices (Lifecycle, FBG-Mail-Formatter) lesen die Felder; sie schreiben nicht.
    """

    model_config = ConfigDict(frozen=True)

    ticker: str = Field(description="Ticker-Symbol (immer Großbuchstaben).")
    strike: Decimal = Field(description="Strike-Preis in USD (Geld → Decimal).")
    dte: int = Field(description="Tage bis Verfall (Calendar-Days).")
    delta: float = Field(description="Put-Delta des gewählten Strikes (≤ 0).")
    put_bid: Decimal = Field(description="Bid des Put-Quotes in USD.")
    put_ask: Decimal = Field(description="Ask des Put-Quotes in USD.")
    mid_premium: Decimal = Field(
        description="Mid-Prämie = (put_bid + put_ask) / 2, auf 4 Nachkommastellen quantisiert."
    )
    annualized_yield_pct: float = Field(
        description="Annualisierte Yield = mid_premium / strike * 365 / dte * 100 (in %)."
    )
    otm_pct: float = Field(
        description="Out-of-the-Money-Distanz in % vom Spot ((spot - strike) / spot * 100)."
    )
    earnings_distance_days: int = Field(
        description="Tage bis zum nächsten Earnings (ORATS daysToNextErn)."
    )
    current_sector_share_pct: float = Field(
        description=(
            "Aktueller Anteil dieses Sektors am Portfolio in %. "
            "FR16 erwartet später zusätzlich `sector_exposure_delta_pct` "
            "(siehe deferred-work D15)."
        )
    )
    pflichtregeln_passed: bool = Field(
        description=(
            "True, wenn alle 9 Pflichtregeln passieren ODER `override=True` aktiv war. "
            "False nur bei reinem Regel-Fail ohne Override."
        )
    )
    reasons: list[str] = Field(
        default_factory=list,
        description=(
            "Deutsche Begründungen der durchgefallenen Regeln, leer wenn passed=True. "
            "Bei aktiviertem Override sind die Begründungen in `bypassed_rules` zu finden."
        ),
    )
    bypassed_rules: list[str] = Field(
        default_factory=list,
        description=(
            "Deutsche Begründungen der per `override=True` ignorierten Regeln. "
            "Leer im Pass-Fall und im Fail-ohne-Override-Fall."
        ),
    )
    as_of: date = Field(
        description=(
            "Datum, auf das sich die ORATS-Daten beziehen. "
            "`as_of=None` im Public-Aufruf → `data_freshness='live'` und `as_of` = heute."
        )
    )
    data_freshness: Literal["live", "eod", "stale", "unavailable"] = Field(
        description=(
            "Frische der zugrundeliegenden Vendor-Daten (NFR / FR7). "
            "MVP: 'live' für US-Live-Calls, 'eod' für historische Calls."
        )
    )
    region: Literal["US", "EU"] = Field(
        description=(
            "Vendor-Region: 'US' für ORATS, 'EU' für IVolatility. "
            "Slice 3: ausschließlich 'US' (EU folgt im IVolatility-Slice)."
        )
    )
