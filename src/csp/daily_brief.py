"""`csp.daily_brief()` — Tages-Zusammenfassung (Slice 7 + 11, PRD FR3 / FR15 / FR18).

Komponiert die bereits gebauten Slices:
- Makro: `csp.macro_snapshot()` (live-VIX falls FMP_KEY gesetzt — sonst Settings-Fallback).
- Top-Ideen: `csp.scan(max_results=N)` (Universe-Scan, FR14).
- Offene Positionen: `csp.list_open_positions()` (DuckDB, FR23).
- Aktionen: deutsche User-strings, abgeleitet aus den 3 Quellen oben.

Aktionen-Heuristiken:
- Earnings-Warnung auf ranked Ideas: redundant zu Pflichtregel 5 (sollte
  eigentlich gefiltert sein), aber defensive Backstop für Override-Pfade.
- Hoher Sektor-Anteil bei ranked Ideas: > 50 % → WARN.
- Override-Position offen: INFO "monatlicher Review".
- **Slice-11**: für jede offene Position einen frischen ORATS-`/cores`-Call,
  und WARN bei `daysToNextErn ≤ 7` (project-context.md: "emergency_close
  fires when daysToNextErn ∈ [0, 7] AND position is open"). Vorher gab es
  diese Heuristik nur für noch zu eröffnende Ideen — offene Positionen
  drifteten still in die Earnings-Zone.

Performance: NFR2 ≤ 30 s warm cache. Slice-11 fügt N extra ORATS-`/cores`-
Calls pro `daily_brief` hinzu, wobei N = Anzahl offener Positionen
(MVP: typisch ≤ 5; well unter NFR2-Budget).
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx
from loguru import logger

from csp.clients.orats import OratsClient
from csp.config import Settings
from csp.exceptions import ORATSDataError, ORATSEmptyDataError
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

    settings = Settings.load()
    today = datetime.now(_BERLIN).date()

    macro = macro_snapshot()
    ranked_ideas = scan(max_results=max_ideas)
    open_positions = list_open_positions()

    # Slice-11: frische Earnings-Daten pro offener Position holen.
    open_earnings_days = _fetch_earnings_days_for_opens(settings, open_positions)

    actions = _compute_actions(
        today=today,
        ideas=ranked_ideas,
        opens=open_positions,
        open_earnings_days=open_earnings_days,
    )

    return DailyBrief(
        as_of=today,
        macro=macro,
        open_positions=open_positions,
        ranked_ideas=ranked_ideas,
        actions=actions,
    )


def _fetch_earnings_days_for_opens(settings: Settings, opens: list[Trade]) -> dict[str, int | None]:
    """Lädt aktuellen `daysToNextErn` für jede offene Position aus ORATS.

    Returns:
        Mapping ticker → daysToNextErn. Tickers die ORATS gerade nicht
        liefert (4xx, leere Antwort, Transport) fehlen im Mapping —
        der Caller behandelt fehlende Keys als "unbekannt, keine WARN".

        Slice-12: der Wert kann ``None`` sein, wenn ORATS für den Ticker den
        Earnings-Sentinel zurückliefert. Der Caller behandelt ``None`` analog
        zu fehlendem Key (kein spurious emergency-close-WARN).
    """
    if not opens:
        return {}
    token = settings.orats_token.get_secret_value()
    if not token or not token.strip():
        # `csp.daily_brief` selber hat ORATS via `scan` schon zum Laufen
        # gebracht; falls hier kein Token mehr verfügbar ist, ist das ein
        # Programmierfehler. Defensiv: leere dict, kein WARN-Spam.
        return {}  # pragma: no cover

    unique_tickers = sorted({t.ticker for t in opens})

    async def _run() -> dict[str, int | None]:
        result: dict[str, int | None] = {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            orats = OratsClient(client, base_url=settings.orats_base_url, token=token)
            for ticker in unique_tickers:
                try:
                    core = await orats.cores(ticker)
                except (ORATSDataError, ORATSEmptyDataError) as exc:
                    logger.warning(
                        "daily_brief: konnte Earnings-Distance für offene Position "
                        "{ticker} nicht abrufen ({cls}: {msg})",
                        ticker=ticker,
                        cls=type(exc).__name__,
                        msg=str(exc),
                    )
                    continue
                result[ticker] = core.days_to_next_earn
        return result

    return asyncio.run(_run())


def _compute_actions(
    *,
    today: date,
    ideas: list[Idea],
    opens: list[Trade],
    open_earnings_days: dict[str, int | None],
) -> list[str]:
    """Leitet deutsche Action-Strings aus den vier Datenquellen ab.

    Defensiv — Pflichtregel 5 sollte alle ideas mit `earnings_distance_days <= 8`
    schon ausfiltern. Wir warnen trotzdem, falls eine Override-Idea durchrutscht.

    Slice-12: ``earnings_distance_days is None`` (Sentinel) wird hier still
    übergangen — Pflichtregel 5 hat den Daten-Lücken-Fall bereits in der
    deutschen Begründung sichtbar gemacht.
    """
    actions: list[str] = []

    for idea in ideas:
        if idea.earnings_distance_days is not None and idea.earnings_distance_days <= 8:
            actions.append(
                f"⚠ {idea.ticker}: Earnings in {idea.earnings_distance_days} "
                "Tagen — keine Position eröffnen."
            )
        if idea.current_sector_share_pct > 50.0:
            actions.append(
                f"⚠ {idea.ticker}: Sektor-Anteil "
                f"{idea.current_sector_share_pct:.0f} % — Cap fast erreicht."
            )

    for trade in opens:
        # Slice-11: Earnings-Warnung auf offene Positionen (project-context.md
        # "emergency_close fires when daysToNextErn ∈ [0, 7] AND position is open").
        days_left = open_earnings_days.get(trade.ticker)
        if days_left is not None and days_left <= 7:
            actions.append(
                f"⚠ {trade.ticker} (offen): Earnings in {days_left} Tagen — "
                f"emergency-close vor Earnings erwägen."
            )

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
