"""`csp.daily_brief()` — Tages-Zusammenfassung (Slice 7, PRD FR3 / FR15 / FR18).

Komponiert die bereits gebauten Slices:
- Makro: `csp.macro_snapshot()` (live-VIX falls FMP_KEY gesetzt — sonst Settings-Fallback).
- Top-Ideen: `csp.scan(max_results=N)` (Universe-Scan, FR14).
- Offene Positionen: `csp.list_open_positions()` (DuckDB, FR23).
- Aktionen: deutsche User-strings, abgeleitet aus den 3 Quellen oben.

Aktionen-Heuristiken (MVP):
- Earnings-Warnung: jede ranked Idea mit `earnings_distance_days <= 8` →
  WARN-String (sollte eigentlich Pflichtregel 5 schon abfangen — defensive doppelt).
- Hoher Sektor-Anteil: jede ranked Idea mit `current_sector_share_pct > 50` →
  WARN-String.
- Override-Position offen: jede offene Position deren ursprüngliche Idea
  bypassed_rules trägt → INFO-String "Override-Trade aktiv, monatlicher Review".

Performance: NFR2 ≤ 30 s warm cache. Slice-7 macht 1 macro-Fetch + 1 scan-Fan-Out
+ 1 DuckDB-SELECT. Auf 12 Tickern + warmer ORATS-Cache deutlich unter 30 s.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from csp.lifecycle_api import get_idea, list_open_positions
from csp.macro import macro_snapshot
from csp.models.daily_brief import DailyBrief
from csp.models.idea import Idea
from csp.models.trade import Trade
from csp.scan import scan

_BERLIN = ZoneInfo("Europe/Berlin")


def daily_brief(*, max_ideas: int = 10) -> DailyBrief:
    """Erzeugt den Tages-Brief aus Macro + Scan + Open-Positions + Actions.

    Args:
        max_ideas: Cap für `ranked_ideas` (entspricht `csp.scan(max_results=...)`).

    Returns:
        Frozenes `DailyBrief`-Modell. `to_markdown()` liefert die Claude-Code-
        Renderung.

    Raises:
        ConfigError: ``ORATS_TOKEN`` fehlt (über `csp.scan`).
        ValueError: ``max_ideas <= 0``.
    """
    if max_ideas <= 0:
        raise ValueError(f"max_ideas muss > 0 sein, war {max_ideas}")

    today = datetime.now(_BERLIN).date()

    macro = macro_snapshot()
    ranked_ideas = scan(max_results=max_ideas)
    open_positions = list_open_positions()

    actions = _compute_actions(today=today, ideas=ranked_ideas, opens=open_positions)

    return DailyBrief(
        as_of=today,
        macro=macro,
        open_positions=open_positions,
        ranked_ideas=ranked_ideas,
        actions=actions,
    )


def _compute_actions(*, today: date, ideas: list[Idea], opens: list[Trade]) -> list[str]:
    """Leitet deutsche Action-Strings aus den drei Datenquellen ab.

    Defensiv — Pflichtregel 5 sollte alle ideas mit `earnings_distance_days <= 8`
    schon ausfiltern. Wir loggen trotzdem, falls eine Override-Idea durchrutscht.
    """
    actions: list[str] = []

    for idea in ideas:
        if idea.earnings_distance_days <= 8:
            actions.append(
                f"⚠ {idea.ticker}: Earnings in {idea.earnings_distance_days} "
                "Tagen — keine Position eröffnen."
            )
        if idea.current_sector_share_pct > 50.0:
            actions.append(
                f"⚠ {idea.ticker}: Sektor-Anteil "
                f"{idea.current_sector_share_pct:.0f} % — Cap fast erreicht."
            )

    # Open-Position-Heuristiken: Override-Audit-Hinweis.
    for trade in opens:
        try:
            origin = get_idea(trade.trade_id)
        except Exception:  # pragma: no cover
            # Defensiv: get_idea propagiert LifecycleError nur bei FK-Inkonsistenz.
            continue
        if origin.bypassed_rules:
            plural = "e" if trade.contracts != 1 else ""
            actions.append(
                f"ℹ {trade.ticker} (offen, {trade.contracts} Kontrakt{plural}): "  # noqa: RUF001
                "Override-Trade — beim monatlichen Review prüfen."
            )

    del today  # Reserved für zukünftige Heuristiken (Timing-Fenster, Wochentag).
    return actions
