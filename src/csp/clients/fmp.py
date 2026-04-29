"""FMP-Client (Financial Modeling Prep, Stable-Namespace) — VIX-Schlusskurs.

Slice-5-Scope ist bewusst eng: Pflichtregel #1 braucht `vix_close`. Andere
Makro-Daten (Marktbreite, Earnings-Kalender) werden — falls jemals benötigt —
in einer späteren Slice ergänzt.

Endpunkte (FMP `/stable/...`):
- Live-Snapshot: `/stable/quote?symbol=^VIX&apikey=…` → Liste mit einem Quote-Eintrag
  (`price` als Schlusskurs / letzter Trade).
- Historischer EOD-Schlusskurs: `/stable/historical-price-eod/light?symbol=^VIX&
  from=YYYY-MM-DD&to=YYYY-MM-DD&apikey=…` → Liste mit einem oder mehreren Tagen.

Auth via `apikey`-Query-Param (kein Bearer-Header). Redaktion läuft über die in
`clients/orats.py` zentrale `_redact_text`-Regex, die auch `apikey=` erfasst.

Vendor-Caveat: FMP-Options-Endpunkte sind tot (deprecated 2025-08-31; siehe
project-context.md "FMP options endpoints are dead"). Dieser Client ruft NUR
`/stable/quote` und `/stable/historical-price-eod/light` an. Erweiterung um
weitere Endpunkte erfordert Vorab-Probe (`curl -sI` gegen den Pfad mit echtem
Key) und einen neuen deferred-work-Eintrag.
"""

from __future__ import annotations

import asyncio
from datetime import date, timedelta
from typing import Any

import httpx
from loguru import logger

from csp.clients.orats import _redact_text, _redact_url
from csp.exceptions import FMPDataError, FMPEmptyDataError

_MAX_ATTEMPTS = 3
_RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
_TRANSPORT_FAILURE_STATUS = -1


class FmpClient:
    """Async FMP-Client gegen den `/stable/...`-Namespace.

    Args:
        client: vorbereiteter `httpx.AsyncClient` (Dependency-Injection für Tests).
        base_url: FMP-API-Basis-URL (Default
            `https://financialmodelingprep.com/api`); ohne `/stable`-Suffix.
        api_key: FMP-API-Key aus `.env` / `Settings.fmp_key`. Wird nie geloggt.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        api_key: str,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    async def vix_close(self, *, trade_date: date | None = None) -> float:
        """Liefert den VIX-Schlusskurs (Cboe Volatility Index, Symbol `^VIX`).

        - Ohne ``trade_date``: `/stable/quote?symbol=^VIX` — letzter bekannter
          Quote (während Marktstunden = letzter Trade; nach Schluss = EOD-Close).
        - Mit ``trade_date``: `/stable/historical-price-eod/light?symbol=^VIX&from=…&to=…`
          — Wir ziehen ein 5-Tage-Fenster vor dem `trade_date`, um Wochenenden /
          Feiertage abzudecken, und nehmen den jüngsten Eintrag ≤ `trade_date`.
        """
        if trade_date is None:
            return await self._live_vix()
        return await self._historical_vix(trade_date)

    async def _live_vix(self) -> float:
        data = await self._request_with_retry(
            "GET",
            "/stable/quote",
            {"symbol": "^VIX"},
        )
        items = self._items_from_payload(data, endpoint="/stable/quote")
        first = items[0]
        # FMP /stable/quote liefert `price` (live oder letzter Trade). Defensiv
        # auf `close` zurückfallen — manche Endpunkte historisch unterschiedlich benannt.
        price = first.get("price", first.get("close"))
        if not isinstance(price, (int, float)) or price <= 0:
            raise FMPEmptyDataError(
                status=200,
                body=f"Quote für ^VIX hat ungültiges price-Feld: {first!r}",
                url_redacted=f"{self._base_url}/stable/quote?symbol=^VIX&apikey=<REDACTED>",
            )
        return float(price)

    async def _historical_vix(self, trade_date: date) -> float:
        # 5-Tage-Fenster nach hinten — Wochenenden / Feiertage.
        from_date = trade_date - timedelta(days=5)
        params = {
            "symbol": "^VIX",
            "from": from_date.strftime("%Y-%m-%d"),
            "to": trade_date.strftime("%Y-%m-%d"),
        }
        data = await self._request_with_retry(
            "GET",
            "/stable/historical-price-eod/light",
            params,
        )
        items = self._items_from_payload(data, endpoint="/stable/historical-price-eod/light")
        # Sortierung in der FMP-Antwort ist normalerweise descending nach `date`,
        # aber wir sortieren defensiv selbst. Wir nehmen den jüngsten Eintrag
        # mit `date <= trade_date`.
        candidates: list[tuple[str, float]] = []
        for row in items:
            row_date = row.get("date")
            row_price = row.get("price", row.get("close"))
            if not isinstance(row_date, str) or not isinstance(row_price, (int, float)):
                continue
            if row_date <= trade_date.strftime("%Y-%m-%d"):
                candidates.append((row_date, float(row_price)))
        if not candidates:
            raise FMPEmptyDataError(
                status=200,
                body=f"Keine VIX-Schlusskurse ≤ {trade_date.isoformat()} im 5-Tage-Fenster",
                url_redacted=(
                    f"{self._base_url}/stable/historical-price-eod/light?"
                    f"symbol=^VIX&from={from_date.isoformat()}"
                    f"&to={trade_date.isoformat()}&apikey=<REDACTED>"
                ),
            )
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        return candidates[0][1]

    def _items_from_payload(self, payload: object, *, endpoint: str) -> list[dict[str, Any]]:
        """FMP /stable liefert eine **flache Liste**, kein `{"data": [...]}`-Wrapper.

        Defensiv: `data`-Wrapper akzeptieren falls FMP das je angleicht.
        """
        if isinstance(payload, list):
            items: list[dict[str, Any]] = [x for x in payload if isinstance(x, dict)]
        elif isinstance(payload, dict):
            inner = payload.get("data") or payload.get("historical")
            items = [x for x in inner if isinstance(x, dict)] if isinstance(inner, list) else []
        else:
            items = []
        if not items:
            raise FMPEmptyDataError(
                status=200,
                body=f"Leere Antwort von {endpoint}",
                url_redacted=f"{self._base_url}{endpoint}?apikey=<REDACTED>",
            )
        return items

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: dict[str, str],
    ) -> Any:
        """3-Versuch-Retry mit 1/2/4 s Backoff für 5xx/429/Transport.

        4xx löst sofort aus. Mirror von `OratsClient._request_with_retry`.
        """
        url = f"{self._base_url}{path}"
        full_params = {**params, "apikey": self._api_key}
        last_exc: FMPDataError | None = None
        redacted_request_url = _redact_text(
            f"{url}?" + "&".join(f"{k}={v}" for k, v in full_params.items())
        )

        for attempt in range(_MAX_ATTEMPTS):
            try:
                response = await self._client.request(method, url, params=full_params)
            except httpx.RequestError as exc:
                msg = _redact_text(str(exc))
                last_exc = FMPDataError(
                    status=_TRANSPORT_FAILURE_STATUS,
                    body=f"Transport-Fehler: {msg}",
                    url_redacted=redacted_request_url,
                )
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = float(2**attempt)
                    logger.warning(
                        "FMP Transport-Fehler bei {url} — Versuch {n}/{total}, Backoff {s}s: {msg}",
                        url=redacted_request_url,
                        n=attempt + 1,
                        total=_MAX_ATTEMPTS,
                        s=delay,
                        msg=msg,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise last_exc from exc

            status = response.status_code
            if 200 <= status < 300:
                return response.json()

            body = response.text
            redacted_url = _redact_url(str(response.request.url), self._api_key)

            if status in _RETRY_STATUSES:
                last_exc = FMPDataError(status=status, body=body, url_redacted=redacted_url)
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = float(2**attempt)
                    logger.warning(
                        "FMP {status} bei {url} — Versuch {n}/{total}, Backoff {s}s",
                        status=status,
                        url=redacted_url,
                        n=attempt + 1,
                        total=_MAX_ATTEMPTS,
                        s=delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise last_exc

            # 4xx (außer 429) — sofort fehlschlagen.
            raise FMPDataError(status=status, body=body, url_redacted=redacted_url)

        # Defensiv: nicht erreichbar wegen `raise last_exc` oben in jedem Pfad.
        raise FMPDataError(  # pragma: no cover
            status=_TRANSPORT_FAILURE_STATUS,
            body="Retry-Schleife unerwartet beendet",
            url_redacted=redacted_request_url,
        )
