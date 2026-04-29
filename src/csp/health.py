"""Health-Checks für Vendor-Anbindungen (live HTTP — nicht Teil des CI-Pytest-Laufs).

`orats_health_check("NOW")` ist die kanonische Live-Sanity-Prüfung: öffnet einen
`httpx.AsyncClient`, instanziiert den `OratsClient` mit dem Token aus `Settings`,
ruft `/cores` ab und gibt das geparste Modell zurück. Dient außerdem als
Aufnahme-Entry für das `cores_NOW.yaml`-Cassette.
"""

from __future__ import annotations

import asyncio
import os

import httpx

from csp.clients.orats import OratsClient
from csp.models.core import OratsCore

DEFAULT_BASE_URL = "https://api.orats.io/datav2"


async def _async_orats_health_check(ticker: str, *, base_url: str, token: str) -> OratsCore:
    async with httpx.AsyncClient(timeout=30.0) as client:
        orats = OratsClient(client, base_url=base_url, token=token)
        return await orats.cores(ticker)


def orats_health_check(ticker: str = "NOW") -> OratsCore:
    """Live-`/cores`-Aufruf gegen ORATS — gibt das geparste `OratsCore` zurück.

    Token und Basis-URL kommen aus den Umgebungsvariablen `ORATS_TOKEN` und
    `ORATS_BASE_URL` (Letzteres optional; Default `https://api.orats.io/datav2`).
    Funktion ist sync — wickelt die async-Implementierung in `asyncio.run` ein,
    damit Claude Code-Aufrufe (`uv run python -c "..."`) keinen Event-Loop verwalten.

    Raises:
        ConfigError: wenn `ORATS_TOKEN` nicht gesetzt ist.
        ORATSDataError: bei 4xx oder 5xx/429 nach drei Retries.
    """
    from csp.exceptions import ConfigError

    token = os.environ.get("ORATS_TOKEN", "")
    if not token:
        raise ConfigError("ORATS_TOKEN nicht in Umgebung gesetzt")
    base_url = os.environ.get("ORATS_BASE_URL", DEFAULT_BASE_URL)
    return asyncio.run(_async_orats_health_check(ticker, base_url=base_url, token=token))
