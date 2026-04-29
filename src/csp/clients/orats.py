"""ORATS Data API-Client (asynchron, mit Retry-Policy und Token-Redaktion).

Konstruktor erhält einen `httpx.AsyncClient` per Dependency-Injection — der Client
wird nicht intern instanziiert, damit Tests ihn per `respx` ersetzen oder per
`pytest-vcr` aufzeichnen können.

Retry-Policy (PRD FR4 / project-context.md "httpx (API clients)"):
- 3 Versuche, exponentielles Backoff 1 s / 2 s / 4 s, für 5xx und 429.
- 4xx löst sofort `ORATSDataError` aus (kein Retry, da idempotent kaputt).
- Token in der URL wird in jeder Exception-Message und jedem Log durch `<REDACTED>`
  ersetzt; dazu greift zusätzlich VCR `filter_query_parameters=["token", "apikey"]`
  an der Cassette-Grenze.
"""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

import httpx
from loguru import logger

from csp.exceptions import ORATSDataError
from csp.models.core import OratsCore, OratsStrike

RATE_LIMIT_PER_MIN = 1_000
"""ORATS-Plan-Tier-Limit (project-context.md). Throttling folgt im Universe-Scan-Slice."""

_MAX_ATTEMPTS = 3
_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
_REDACTED = "<REDACTED>"


def _redact_url(url: str, token: str) -> str:
    """Ersetzt das Token im URL-String durch `<REDACTED>`.

    Wird vor jeder Aufnahme in `ORATSDataError`-Messages und Loguru-Logs angewandt.
    Cassette-Schutz greift zusätzlich über VCR `filter_query_parameters`.
    """
    if not token:
        return url
    return url.replace(token, _REDACTED)


def _put_delta_from_call_delta(call_delta: float) -> float:
    """ORATS `/hist/strikes` liefert nur das Call-Delta; Put-Delta = call - 1.

    Put-Delta ist immer ≤ 0; das Pydantic-Modell erzwingt `delta ∈ [-1, 0]`.
    """
    return call_delta - 1.0


class OratsClient:
    """Async-Client für ORATS Data API (`/cores`, `/strikes`, `/hist/strikes`, …).

    Methoden geben Pydantic-Modelle zurück — kein Caller arbeitet auf rohen Dicts.

    Args:
        client: Vorbereiteter `httpx.AsyncClient` (i. d. R. via `async with`).
        base_url: ORATS-Datav2-Basis-URL (`https://api.orats.io/datav2`).
        token: API-Token aus `.env` / `Settings`. Wird nie geloggt.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        token: str,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._token = token

    async def cores(self, ticker: str) -> OratsCore:
        """Aktueller `/cores`-Snapshot für einen Ticker."""
        data = await self._request_with_retry("GET", "/cores", {"ticker": ticker})
        items = data.get("data", [])
        if not items:
            raise ORATSDataError(
                status=200,
                body=f"leere data-Liste für ticker={ticker}",
                url_redacted=f"{self._base_url}/cores?ticker={ticker}&token={_REDACTED}",
            )
        return OratsCore.model_validate(items[0])

    async def strikes(self, ticker: str, *, trade_date: date | None = None) -> list[OratsStrike]:
        """Strikes-Kette für einen Ticker — aktuell oder historisch.

        - Ohne `trade_date`: `/strikes` (live).
        - Mit `trade_date`: `/hist/strikes?tradeDate=YYYYMMDD` (historisch).

        Liefert ausschließlich Strikes, deren Put-Quotes vorhanden sind
        (`putBidPrice` und `putAskPrice` nicht None) — die Pflichtregeln
        operieren immer auf der Put-Seite.
        """
        params: dict[str, str] = {"ticker": ticker}
        if trade_date is not None:
            path = "/hist/strikes"
            params["tradeDate"] = trade_date.strftime("%Y%m%d")
        else:
            path = "/strikes"
        data = await self._request_with_retry("GET", path, params)
        result: list[OratsStrike] = []
        for item in data.get("data", []):
            if item.get("putBidPrice") is None or item.get("putAskPrice") is None:
                continue
            call_delta = item.get("delta")
            if call_delta is None:
                continue
            put_delta = _put_delta_from_call_delta(float(call_delta))
            payload = dict(item)
            payload["delta"] = put_delta
            result.append(OratsStrike.model_validate(payload))
        return result

    async def ivrank(self, ticker: str) -> dict[str, Any]:
        """`/ivrank`-Endpunkt — rohe Daten (Modell folgt mit Universe-Scan-Slice)."""
        data = await self._request_with_retry("GET", "/ivrank", {"ticker": ticker})
        items = data.get("data", [])
        return items[0] if items else {}

    async def summaries(self, ticker: str) -> dict[str, Any]:
        """`/summaries`-Endpunkt — rohe Daten (Modell folgt mit Universe-Scan-Slice)."""
        data = await self._request_with_retry("GET", "/summaries", {"ticker": ticker})
        items = data.get("data", [])
        return items[0] if items else {}

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: dict[str, str],
    ) -> dict[str, Any]:
        """Issues a request with exponential backoff on 5xx/429; raises immediately on 4xx.

        Token wird als Query-Parameter angehängt; in jedem Log/Exception-Pfad redigiert.
        """
        url = f"{self._base_url}{path}"
        full_params = {**params, "token": self._token}
        last_exc: ORATSDataError | None = None

        for attempt in range(_MAX_ATTEMPTS):
            response = await self._client.request(method, url, params=full_params)
            status = response.status_code
            if 200 <= status < 300:
                payload: dict[str, Any] = response.json()
                return payload

            body = response.text
            redacted_url = _redact_url(str(response.request.url), self._token)

            if status in _RETRY_STATUSES:
                last_exc = ORATSDataError(status=status, body=body, url_redacted=redacted_url)
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = float(2**attempt)
                    logger.warning(
                        "ORATS {status} bei {url} — Versuch {n}/{total}, Backoff {s}s",
                        status=status,
                        url=redacted_url,
                        n=attempt + 1,
                        total=_MAX_ATTEMPTS,
                        s=delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise last_exc

            # 4xx (außer 429) — sofort fehlschlagen, kein Retry.
            raise ORATSDataError(status=status, body=body, url_redacted=redacted_url)

        # Alle Retries erschöpft — sollte durch obige `raise` schon abgefangen sein.
        assert last_exc is not None  # pragma: no cover
        raise last_exc  # pragma: no cover
