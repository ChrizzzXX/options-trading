"""Makro-Snapshot (heute: VIX-Schlusskurs) — live FMP, mit Fallback auf Settings.

`csp.macro_snapshot(*, as_of=None)` ist die öffentliche Convenience-Funktion.
Intern teilen `csp.idea` und `csp.scan` den `_fetch_macro(...)`-Helper, sodass
**ein einziger** `httpx.AsyncClient` ORATS- UND FMP-Traffic trägt (NFR5,
Slice-4-Single-Client-Invariante).

Fallback-Kette:
1. ``settings.fmp_key`` leer → keine HTTP, ``MacroSnapshot(vix_close=settings.macro.vix_close)``.
2. ``settings.fmp_key`` gesetzt → FMP-Live-Fetch.
3. FMP-Fetch wirft ``FMPDataError`` / ``FMPEmptyDataError`` → WARN-Log + Fallback wie 1.

Slice-5 schließt damit deferred-work D13 (Live-VIX statt statisch) und D17 (Macro-
Daten-Frische): ``MacroSnapshot.vix_close`` ist live, sobald ein FMP-Key vorliegt.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx
from loguru import logger

from csp.clients.fmp import FmpClient
from csp.config import Settings
from csp.exceptions import FMPDataError, FMPEmptyDataError
from csp.models.core import MacroSnapshot

_BERLIN = ZoneInfo("Europe/Berlin")


async def _fetch_macro(
    *,
    settings: Settings,
    fmp_key: str,
    fmp_base_url: str,
    client: httpx.AsyncClient,
    as_of: date | None,
) -> MacroSnapshot:
    """Holt einen `MacroSnapshot` mit live-VIX falls FMP-Key gesetzt, sonst Fallback.

    Caller liefert den `httpx.AsyncClient` — `_fetch_macro` öffnet KEINEN eigenen.
    Damit teilen `idea` / `scan` einen Pool für ORATS- und FMP-Traffic.
    """
    if not fmp_key:
        return MacroSnapshot(vix_close=settings.macro.vix_close)
    fmp = FmpClient(client, base_url=fmp_base_url, api_key=fmp_key)
    try:
        vix = await fmp.vix_close(trade_date=as_of)
    except (FMPDataError, FMPEmptyDataError) as exc:
        logger.warning(
            "macro: FMP-Live-VIX-Fetch fehlgeschlagen, Fallback auf [macro] settings "
            "({cls}: {msg})",
            cls=type(exc).__name__,
            msg=str(exc),
        )
        return MacroSnapshot(vix_close=settings.macro.vix_close)
    return MacroSnapshot(vix_close=vix)


def macro_snapshot(*, as_of: date | None = None) -> MacroSnapshot:
    """Liefert einen aktuellen oder historischen Makro-Snapshot.

    Args:
        as_of: ``None`` → live-VIX via ``/stable/quote``; Datum → historischer
            EOD-Schlusskurs via ``/stable/historical-price-eod/light``. Ohne FMP-Key
            wird in beiden Fällen `[macro] vix_close` aus den Settings benutzt
            (kein HTTP-Aufruf).

    Returns:
        ``MacroSnapshot`` mit `vix_close`.

    Raises:
        ValueError: ``as_of`` liegt in der Zukunft.
        ConfigError: nur wenn `Settings.load()` selbst scheitert.
    """
    today = datetime.now(_BERLIN).date()
    if as_of is not None and as_of > today:
        raise ValueError(
            f"as_of {as_of.isoformat()} liegt in der Zukunft — historische "
            f"Makro-Reproduktion erfordert ein vergangenes Handelsdatum."
        )
    settings = Settings.load()
    fmp_key = settings.fmp_key.get_secret_value()
    if fmp_key and not fmp_key.strip():
        fmp_key = ""

    async def _run() -> MacroSnapshot:
        async with httpx.AsyncClient(timeout=30.0) as client:
            return await _fetch_macro(
                settings=settings,
                fmp_key=fmp_key,
                fmp_base_url=settings.fmp_base_url,
                client=client,
                as_of=as_of,
            )

    return asyncio.run(_run())
