"""`csp.idea(ticker)` — öffentliche Single-Ticker-CSP-Idee (PRD FR13).

Sync-Wrapper um den async-Orchestrator: lädt Settings, öffnet einen
`httpx.AsyncClient`, instanziiert `OratsClient`, holt Cores + Strikes
(live oder historisch via ``as_of``), wählt den am besten passenden Strike
und ruft den Pflichtregeln-Gate auf.

Liefert immer eine populierte `Idea` — der Override-Pfad ist im Modell selbst
annotiert (siehe ``Idea.pflichtregeln_passed`` / ``reasons`` / ``bypassed_rules``).
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from typing import Literal
from zoneinfo import ZoneInfo

import httpx

from csp.clients.orats import OratsClient
from csp.config import Settings
from csp.exceptions import ConfigError
from csp.models.core import MacroSnapshot, PortfolioSnapshot
from csp.models.idea import Idea
from csp.strategies.csp import _select_strike, build_idea

# Chris' lokale Zeitzone — bewusst stdlib `ZoneInfo` statt `pendulum`, damit kein
# neuer Dep nur für die Datums-Auflösung dazukommt. Der Projekt-Hard-Rule
# „TZ-aware datetimes only" wird über `datetime.now(_BERLIN).date()` eingehalten.
_BERLIN = ZoneInfo("Europe/Berlin")


async def _fetch_and_build_idea(
    orats: OratsClient,
    ticker: str,
    *,
    dte: int,
    target_delta: float,
    as_of: date | None,
    effective_as_of: date,
    override: bool,
    settings: Settings,
) -> Idea:
    """Pro-Ticker-Orchestrator: ORATS-Fetch → Strike-Selektion → Idea-Konstruktion.

    Nimmt einen vorbereiteten `OratsClient` entgegen — so kann sowohl der Single-
    Ticker-Aufruf (`_async_idea`) als auch die Universe-Variante (`_async_scan`)
    den HTTP-Client teilen, ohne dass diese Funktion etwas über das Lifecycle der
    `httpx.AsyncClient`-Verbindung wissen muss.

    Patch P3 (Slice 4 review): Ticker wird hier zentral normalisiert (strip + upper),
    damit beide öffentlichen Pfade (`csp.idea`, `csp.scan`) dieselbe Garantie
    erhalten. `effective_as_of` wird **nicht mehr** intern via `datetime.now(...)`
    aufgelöst — der Caller liefert das schon einmal aufgelöste Datum, damit alle
    Universe-Tasks denselben Stamp tragen (Patch P1: NFR20-Determinismus).
    """
    ticker = ticker.strip().upper()
    region: Literal["US", "EU"] = "US"
    data_freshness: Literal["live", "eod", "stale", "unavailable"] = (
        "live" if as_of is None else "eod"
    )

    core = await orats.cores(ticker, trade_date=as_of)
    strikes = await orats.strikes(ticker, trade_date=as_of)

    strike = _select_strike(strikes, target_delta=target_delta, dte=dte, settings=settings)
    macro = MacroSnapshot(vix_close=settings.macro.vix_close)
    portfolio = PortfolioSnapshot()

    return build_idea(
        core,
        strike,
        macro,
        portfolio,
        settings,
        as_of=effective_as_of,
        data_freshness=data_freshness,
        region=region,
        override=override,
    )


async def _async_idea(
    ticker: str,
    dte: int,
    target_delta: float,
    *,
    as_of: date | None,
    override: bool,
    settings: Settings,
    base_url: str,
    token: str,
) -> Idea:
    """Async-Wrapper für den Single-Ticker-Pfad.

    Öffnet einen kurzen `httpx.AsyncClient` (Timeout 30 s) und delegiert an den
    geteilten `_fetch_and_build_idea`. Der NFR4-Limit von 5 s pro US-Aufruf wird
    so in der Regel mit Sicherheitsmarge eingehalten.
    """
    # Effective-as_of einmal hier auflösen — single call, keine Drift möglich,
    # aber Symmetrie zur Universe-Variante (Patch P1) gewährleistet.
    effective_as_of = as_of if as_of is not None else datetime.now(_BERLIN).date()
    async with httpx.AsyncClient(timeout=30.0) as client:
        orats = OratsClient(client, base_url=base_url, token=token)
        return await _fetch_and_build_idea(
            orats,
            ticker,
            dte=dte,
            target_delta=target_delta,
            as_of=as_of,
            effective_as_of=effective_as_of,
            override=override,
            settings=settings,
        )


def idea(
    ticker: str,
    dte: int = 45,
    target_delta: float = -0.20,
    *,
    as_of: date | None = None,
    override: bool = False,
) -> Idea:
    """Erzeugt eine populierte CSP-`Idea` für einen einzelnen Ticker.

    Komponiert ORATS-Daten (`OratsClient.cores` + `strikes`) mit dem
    Pflichtregeln-Gate (`passes_csp_filters`) und dem Strike-Selektor.

    Args:
        ticker: Ticker-Symbol (case-insensitiv; wird intern uppercase normalisiert).
        dte: Wunsch-Tage bis Verfall (Default 45). Auswahl: nächstgelegene
            Expiration; Tie-Break niedrigerer DTE.
        target_delta: Wunsch-Put-Delta (Default -0,20). Auswahl: minimaler
            Abstand innerhalb des Pflichtregel-2-Delta-Bands; Tie-Break
            niedrigerer Strike.
        as_of: Wenn ``None``, Live-Endpunkte (`/cores`, `/strikes`,
            ``data_freshness='live'``). Sonst: historisch (`/hist/cores`,
            `/hist/strikes` mit ``tradeDate=YYYYMMDD``, ``data_freshness='eod'``).
        override: Wenn ``True``, werden alle Pflichtregeln-Verstöße im Modell
            als ``bypassed_rules`` annotiert (statt als Reject); ``passed=True``.
            Loguru-WARN wird emittiert. Persistenz folgt im Lifecycle-Slice.

    Returns:
        Eine immer populierte `Idea`. ``Idea.pflichtregeln_passed`` plus
        ``reasons`` / ``bypassed_rules`` tragen das Verdict.

    Raises:
        ConfigError: ``ORATS_TOKEN`` ist nicht in `.env` gesetzt.
        ORATSDataError: 4xx (sofort) oder 5xx/429/Transport (nach 3 Retries).
        ORATSEmptyDataError: Cores oder Strikes leer; oder kein Strike fällt
            ins Delta-Band der gewählten Expiration.
    """
    # P1: Ticker am öffentlichen Rand normalisieren — Docstring verspricht
    # case-insensitive Aufruf; ohne `.upper()`/`.strip()` ginge ein Whitespace-
    # oder Lowercase-Wert verbatim an ORATS und produzierte unklare 4xx/Empty.
    ticker = ticker.strip().upper()

    # P6: `as_of` darf nicht in der Zukunft liegen — der Vendor liefert leere
    # Daten und der Aufrufer bekäme einen generischen "leere data-Liste"-Fehler.
    if as_of is not None and as_of > datetime.now(_BERLIN).date():
        raise ValueError(
            f"as_of {as_of.isoformat()} liegt in der Zukunft — historische "
            f"Reproduktion erfordert ein vergangenes Handelsdatum."
        )

    settings = Settings.load()
    token = settings.orats_token.get_secret_value()
    if not token:
        raise ConfigError("ORATS_TOKEN nicht in Umgebung/.env gesetzt")
    return asyncio.run(
        _async_idea(
            ticker,
            dte,
            target_delta,
            as_of=as_of,
            override=override,
            settings=settings,
            base_url=settings.orats_base_url,
            token=token,
        )
    )
