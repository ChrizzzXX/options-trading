"""`Idea` — vollständig populiertes Pydantic-Modell für eine einzelne CSP-Kandidatur.

Eine `Idea` ist immer populiert: ob die Pflichtregeln passieren oder nicht, ob ein
`override` aktiv war oder nicht — die Felder `pflichtregeln_passed`, `reasons` und
`bypassed_rules` tragen die Gate-Verdict-Annotation.

Semantik der drei Zustände (erschöpfend, paarweise disjunkt):
- Pass (Regeln gehalten):  ``pflichtregeln_passed=True,  reasons=[],          bypassed_rules=[]``.
- Fail ohne override:       ``pflichtregeln_passed=False, reasons=<n Regeln>,  bypassed_rules=[]``.
- Fail mit ``override``:    ``pflichtregeln_passed=True,  reasons=[],          bypassed_rules=<n>``.

Geld als ``Decimal`` (Strike, Bid/Ask, Mid-Premium); Verhältnisse als ``float``
(Delta, OTM%, annualisierte Yield). PRD FR13/FR15/FR16; Spec
``spec-idea-singleticker.md`` + ``spec-daily-brief.md``.
"""

from __future__ import annotations

from datetime import date, timedelta
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
    sector: str = Field(
        description=(
            "GICS-Sektor (ORATS sectorName, z. B. 'Technology'). Slice 11: "
            "wird vom Portfolio-Builder benutzt, um Pflichtregel-8-Sektor-Anteile "
            "aus offenen Trades zu rekonstruieren."
        )
    )
    under_price: float = Field(
        gt=0.0,
        description="Spotpreis des Underlyings beim Idea-Erzeugung (ORATS pxAtmIv).",
    )
    iv_rank_1y_pct: float = Field(
        ge=0.0,
        description="IVR (1-Jahres-IV-Perzentil) — ORATS ivPctile1y in %.",
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

    def format_fbg_mail(self, *, contracts: int = 1, reasoning: str | None = None) -> str:
        """Rendert die Idea im Standard-FBG-Mail-Format (Brief §7.1, FR15).

        Deutsche Locale: USD mit Tausender-Punkt + Dezimal-Komma, Prozente mit
        Komma-Dezimal und Leerzeichen vor `%`, Datum als `27.04.2026`.

        Slice-7-Stand: einige Felder aus dem Brief-Beispiel (`IV aktuell`,
        Verfall-Tagesgenauigkeit) sind aus `Idea` allein nicht herleitbar —
        wir näheren uns an mit den verfügbaren Feldern. Der Override-Fall
        wird via `(Override aktiv)`-Suffix in der Header-Zeile markiert.

        Args:
            contracts: Anzahl Kontrakte für die `Cash-Bedarf`-Zeile (Default 1).
            reasoning: optionale Freitext-Begründung (deutsch). Wenn ``None``,
                wird ein generischer Hinweis aus den verfügbaren Kennzahlen
                synthetisiert.

        Returns:
            Mehrzeiliger String, fertig zum Einfügen in eine FBG-Order-Mail.
        """
        # Lazy-Import vermeidet zirkuläre Abhängigkeit beim Modul-Laden.
        from csp.ui.formatters import format_date_de, format_pct, format_usd

        expiry = self.as_of + timedelta(days=self.dte)
        cash_demand = self.strike * Decimal(contracts) * Decimal(100)
        override_marker = "  (Override aktiv)" if self.bypassed_rules else ""
        if reasoning is None:
            reasoning = (
                f"IVR {format_pct(self.iv_rank_1y_pct, decimals=0)} attraktiv; "
                f"Strike {format_pct(self.otm_pct, decimals=1)} OTM bietet Sicherheitspuffer; "
                f"{self.dte} DTE im Theta-Beschleunigungsfenster."
            )

        lines: list[str] = [
            "---",
            f"CSP-IDEE | {self.ticker} | {format_date_de(self.as_of)}{override_marker}",
            "---",
            f"Kurs:              {format_usd(self.under_price)}",
            f"Strike:            {format_usd(self.strike)}",
            f"Abstand OTM:       {format_pct(self.otm_pct, decimals=1)}",
            f"Delta:             {self.delta:.2f}".replace(".", ","),
            f"Verfall:           {format_date_de(expiry)} ({self.dte} DTE)",
            f"IV-Rang 1y:        {format_pct(self.iv_rank_1y_pct, decimals=0)}",
            f"Prämie Bid/Ask:    {format_usd(self.put_bid)} / {format_usd(self.put_ask)}",
            f"Empf. Limit:       {format_usd(self.mid_premium, decimals=4)} (Mid-Point)",
            f"Cash-Bedarf:       {format_usd(cash_demand, decimals=0)} ({contracts} Kontrakt"
            f"{'e' if contracts != 1 else ''})",
            f"Ann. Rendite:      {format_pct(self.annualized_yield_pct, decimals=1)} p.a.",
            f"Nächste Earnings:  {self.earnings_distance_days} Tage Abstand",
        ]
        clean_pass = self.pflichtregeln_passed and not self.bypassed_rules
        lines.append(f"Pflichtregeln:     {'OK' if clean_pass else 'NICHT BESTANDEN'}")
        if self.reasons:
            lines.append("Verstöße:")
            lines.extend(f"  - {r}" for r in self.reasons)
        if self.bypassed_rules:
            lines.append("Bypassed (Override):")
            lines.extend(f"  - {r}" for r in self.bypassed_rules)
        lines.append(f"Begründung:        {reasoning}")
        lines.append("---")
        return "\n".join(lines)
