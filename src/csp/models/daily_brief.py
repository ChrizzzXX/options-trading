"""`DailyBrief` — Pydantic-Modell für die Tages-Zusammenfassung (Slice 7).

Kombiniert Makro-Snapshot, ranked-Idea-Liste (aus `csp.scan`) und offene Trades
(aus `csp.list_open_positions`) plus eine Liste deutscher Action-Strings für
Earnings-Warnungen / TP-Empfehlungen.

`to_markdown()` liefert eine Brief-§7.2-Annäherung als Markdown — Claude Code
rendert das direkt im Terminal. Tabellen verwenden ASCII-Pipe-Syntax (kein
`rich`-Dependency) — die Original-Brief-Skizze nutzte Box-Zeichen, die in
verschiedenen Terminals unterschiedlich darstellbar sind.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from csp.models.core import MacroSnapshot
from csp.models.idea import Idea
from csp.models.trade import Trade


class DailyBrief(BaseModel):
    """Tages-Zusammenfassung: Makro + offene Positionen + Top-Ideen + Aktionen."""

    model_config = ConfigDict(frozen=True)

    as_of: date = Field(description="Tag der Zusammenfassung (Berlin-Datum).")
    macro: MacroSnapshot = Field(description="Makro-Snapshot (heute nur VIX-Close).")
    open_positions: list[Trade] = Field(
        default_factory=list,
        description=(
            "Offene Trades (Status OPEN oder TAKE_PROFIT_PENDING) aus `list_open_positions`."
        ),
    )
    ranked_ideas: list[Idea] = Field(
        default_factory=list,
        description=(
            "Pflichtregeln-bestandene Top-N-Ideen aus `csp.scan(...)`, sortiert "
            "nach annualisierter Yield DESC."
        ),
    )
    actions: list[str] = Field(
        default_factory=list,
        description=(
            "Deutsche User-strings: Earnings-Warnungen, TP-Empfehlungen, Emergency-Close-Hinweise."
        ),
    )

    def to_markdown(self) -> str:
        """Rendert den DailyBrief als Markdown — direkt von Claude Code anzeigbar."""
        from csp.ui.formatters import format_date_de, format_pct, format_usd

        lines: list[str] = [
            f"# CSP DAILY BRIEF — {format_date_de(self.as_of)}",
            "",
            "## Makro",
            f"- VIX: {format_pct(self.macro.vix_close, decimals=2)}",
            "",
        ]

        # Offene Positionen. Strike via cash_secured / (contracts * 100) abgeleitet.
        from decimal import Decimal

        lines.append(f"## Offene Positionen ({len(self.open_positions)})")
        if not self.open_positions:
            lines.append("_keine offenen Positionen_")
        else:
            lines.append("")
            lines.append("| Ticker | Strike | Open-Date | Status | Prämie offen |")
            lines.append("|---|---|---|---|---|")
            for t in self.open_positions:
                strike = t.cash_secured / Decimal(t.contracts) / Decimal(100)
                lines.append(
                    f"| {t.ticker} | {format_usd(strike)} | "
                    f"{format_date_de(t.open_date)} | {t.status.value} | "
                    f"{format_usd(t.open_premium)} |"
                )
        lines.append("")

        # Top-Ideen.
        lines.append(f"## Top-Ideen heute ({len(self.ranked_ideas)})")
        if not self.ranked_ideas:
            lines.append("_keine Pflichtregeln-bestandenen Kandidaten_")
        else:
            lines.append("")
            lines.append("| Ticker | IVR | DTE | Strike | Δ | Ann.Yield |")
            lines.append("|---|---|---|---|---|---|")
            for i in self.ranked_ideas:
                lines.append(
                    f"| {i.ticker} | {format_pct(i.iv_rank_1y_pct, decimals=0)} | "
                    f"{i.dte} | {format_usd(i.strike)} | "
                    f"{i.delta:.2f}".replace(".", ",")
                    + " | "
                    + format_pct(i.annualized_yield_pct, decimals=1)
                    + " |"
                )
        lines.append("")

        # Actions.
        if self.actions:
            lines.append("## Aktionen")
            lines.extend(f"- {a}" for a in self.actions)
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"
