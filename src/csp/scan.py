"""`csp.scan(...)` — universumsweiter CSP-Scan (PRD FR14, FR17, NFR1, NFR5, NFR20).

Komponiert `csp.idea` über das gesamte konfigurierte Universum, parallelisiert
über `asyncio.gather()`, filtert auf Pflichtregeln-bestandene Kandidaten und
sortiert deterministisch nach annualisierter Yield (DESC) mit Ticker-ASC-Tie-Break.

Pro-Ticker-Resilienz (NFR14): `ORATSDataError` und `ORATSEmptyDataError` aus
`_fetch_and_build_idea` werden geschluckt, als WARN geloggt und der Ticker fällt
aus dem Resultat. `ConfigError`, `ValueError` und sonstige Exceptions
propagieren unverändert (Patch P4: zu breites `ValueError`-Catching entfernt;
Future-`as_of` wird jetzt am Public-Rand `scan(...)` validiert — Patch P2).

Ein einziger `httpx.AsyncClient` und ein einziger `OratsClient` werden geteilt —
spart Connection-Pool-Setup gegenüber einem Client pro Ticker und ist Voraussetzung
für die NFR1-Latenz (≤ 60 s über ~40 Ticker).
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx
from loguru import logger

from csp.clients.orats import OratsClient, _redact_text
from csp.config import Settings
from csp.exceptions import ConfigError, ORATSDataError, ORATSEmptyDataError
from csp.idea import _fetch_and_build_idea
from csp.models.idea import Idea

# Berlin-TZ für TZ-aware `as_of`-Auflösung am Public-Rand (Patch P1: ein einziger
# Datums-Stamp für alle Universe-Tasks → kein Mitternacht-Drift, NFR20).
_BERLIN = ZoneInfo("Europe/Berlin")


async def _safe_fetch(
    orats: OratsClient,
    ticker: str,
    *,
    dte: int,
    target_delta: float,
    as_of: date | None,
    effective_as_of: date,
    settings: Settings,
) -> Idea | None:
    """Wrappt `_fetch_and_build_idea` mit der Skip-und-WARN-Semantik.

    Erlaubte (geschluckte) Fehler:
    - `ORATSDataError` — 4xx oder erschöpfte Retry-Kette für 5xx/429/Transport.
    - `ORATSEmptyDataError` — leere `/cores`/`/strikes`-Antwort oder kein Strike
      im Delta-Band der gewählten Expiration.

    Patch P4: `ValueError` wird **nicht mehr** geschluckt — bevor `_async_scan`
    überhaupt startet, validiert `scan(...)` das `as_of`-Argument am Public-Rand.
    Damit kann ein `ValueError` aus dem Per-Ticker-Pfad nur noch ein echter
    Programmierfehler sein und soll laut zur Laufzeit fehlschlagen, statt still
    als "Skip"-WARN zu maskieren.

    Bei Fehler: WARN-Log mit `ticker`, Exception-Klasse und **redigierter**
    Exception-Message (Patch P5: `_redact_text` schützt vor Token-Echos);
    Rückgabe ``None``.
    """
    try:
        return await _fetch_and_build_idea(
            orats,
            ticker,
            dte=dte,
            target_delta=target_delta,
            as_of=as_of,
            effective_as_of=effective_as_of,
            override=False,
            settings=settings,
        )
    except (ORATSDataError, ORATSEmptyDataError) as exc:
        logger.warning(
            "scan: Ticker {ticker} übersprungen ({cls}: {msg})",
            ticker=ticker,
            cls=type(exc).__name__,
            msg=_redact_text(str(exc)),
        )
        return None


async def _async_scan(
    settings: Settings,
    *,
    dte: int,
    target_delta: float,
    as_of: date | None,
    effective_as_of: date,
    base_url: str,
    token: str,
    max_results: int,
) -> list[Idea]:
    """Async-Orchestrator: parallele Per-Ticker-Fetches → Filter → Sort → Truncate.

    Erzeugt EINEN `httpx.AsyncClient` (Timeout 30 s) und EINEN `OratsClient`,
    die alle Per-Ticker-Tasks teilen. `asyncio.gather(..., return_exceptions=False)`:
    da `_safe_fetch` `ORATSDataError`/`ORATSEmptyDataError` schon abfängt, können
    hier nur die propagierten (z. B. `ConfigError`) durchschlagen — und genau das
    ist gewünscht.
    """
    # Patch P11: Duplikate im Universum dedupieren — `dict.fromkeys` bewahrt
    # Insertion-Order, damit der Tie-Break stabil bleibt. Vermeidet doppelte
    # HTTP-Calls UND doppelte Ideen im Resultat.
    tickers = list(dict.fromkeys(settings.universe.allowed_tickers))
    async with httpx.AsyncClient(timeout=30.0) as client:
        orats = OratsClient(client, base_url=base_url, token=token)
        tasks = [
            _safe_fetch(
                orats,
                ticker,
                dte=dte,
                target_delta=target_delta,
                as_of=as_of,
                effective_as_of=effective_as_of,
                settings=settings,
            )
            for ticker in tickers
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

    # Filter: ``None`` (Per-Ticker-Fehler) und Regel-Failer ausblenden — FR14.
    surviving: list[Idea] = [i for i in results if i is not None and i.pflichtregeln_passed]

    # Sort: yield DESC, ticker ASC für deterministischen Tie-Break — FR17 / NFR20.
    surviving.sort(key=lambda i: (-i.annualized_yield_pct, i.ticker))

    # Truncate auf max_results.
    return surviving[:max_results]


def scan(
    max_results: int = 10,
    *,
    dte: int = 45,
    target_delta: float = -0.20,
    as_of: date | None = None,
) -> list[Idea]:
    """Universumsweiter CSP-Scan: Top-N Pflichtregeln-bestandene Ideen.

    Komponiert `csp.idea` über alle Ticker in `settings.universe.allowed_tickers`,
    parallelisiert über `asyncio.gather()` (NFR5). Pro Ticker fällt ORATS-Fehler
    aus dem Resultat (Skip-und-WARN, NFR14); ein leeres Universum oder global
    fehlende Token-Konfiguration löst dagegen aus.

    Args:
        max_results: Maximale Anzahl zurückgegebener Ideen (Default 10). Muss
            `> 0` sein — Validierung am Public-Rand vor jeglichem HTTP-Aufruf.
        dte: Wunsch-Tage bis Verfall pro Ticker (Default 45). Identische Semantik
            wie `csp.idea(dte=...)`.
        target_delta: Wunsch-Put-Delta pro Ticker (Default -0,20). Identische
            Semantik wie `csp.idea(target_delta=...)`.
        as_of: ``None`` ⇒ Live-Endpunkte für alle Ticker; Datum ⇒ historisch via
            `/hist/cores` + `/hist/strikes`. Alle Ticker teilen denselben `as_of`
            UND denselben `effective_as_of`-Stamp (Patch P1, NFR20).

    Returns:
        Pflichtregeln-bestandene `Idea`-Objekte, absteigend nach
        ``annualized_yield_pct``, bei Gleichstand alphabetisch nach Ticker
        (FR17 / NFR20). Niemals länger als `max_results`.

    Raises:
        ValueError: ``max_results <= 0`` ODER `as_of` liegt in der Zukunft
            (Patch P2: am Public-Rand validiert, mirror `csp.idea`).
        ConfigError: ``ORATS_TOKEN`` ist nicht in `.env` gesetzt ODER das
            Universum (`allowed_tickers`) ist leer (Patch P12: defense-in-depth,
            auch wenn `pydantic-settings` `min_length=1` heute schon prüft).

    Hinweis: Override-Pfad wird auf `scan` bewusst nicht angeboten — FR14
        verlangt "Pflichtregeln-bestanden". Wer einen einzelnen Kandidaten
        überstimmen will, ruft `csp.idea(ticker, override=True)` direkt.
    """
    if max_results <= 0:
        raise ValueError(f"max_results muss > 0 sein, war {max_results}")

    # Patch P2: `as_of` in der Zukunft → fail-fast am Public-Rand (mirror `idea()`).
    # Spec I/O matrix sagt zwar "ValueError propagates per-ticker", aber das ist
    # hier strenger: keine HTTP-Aufrufe gegen `/hist/*` mit ungültigem Datum.
    today = datetime.now(_BERLIN).date()
    if as_of is not None and as_of > today:
        raise ValueError(
            f"as_of {as_of.isoformat()} liegt in der Zukunft — historische "
            f"Reproduktion erfordert ein vergangenes Handelsdatum."
        )

    settings = Settings.load()
    token = settings.orats_token.get_secret_value()
    # Patch P6: Whitespace-only-Token zählt nicht als gesetzt.
    if not token or not token.strip():
        raise ConfigError("ORATS_TOKEN nicht in Umgebung/.env gesetzt")

    # Patch P12: leeres Universum → ConfigError (statt stiller `[]`-Rückgabe).
    if not settings.universe.allowed_tickers:
        raise ConfigError("settings.universe.allowed_tickers ist leer")

    # Patch P1: `effective_as_of` einmal hier auflösen, damit alle Universe-Tasks
    # denselben Stamp tragen — kein Drift bei Tasks, die Mitternacht Berlin
    # überschreiten.
    effective_as_of = as_of if as_of is not None else today

    return asyncio.run(
        _async_scan(
            settings,
            dte=dte,
            target_delta=target_delta,
            as_of=as_of,
            effective_as_of=effective_as_of,
            base_url=settings.orats_base_url,
            token=token,
            max_results=max_results,
        )
    )
