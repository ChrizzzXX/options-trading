"""Tests für `csp.FmpClient` und `csp.fmp_health_check` (Slice 5)."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Iterator
from datetime import date
from typing import Any

import httpx
import pytest
import respx
from pydantic import SecretStr

import csp
from csp import config as csp_config
from csp.clients.fmp import FmpClient
from csp.config import Settings
from csp.exceptions import ConfigError, FMPDataError, FMPEmptyDataError

BASE_URL = "https://financialmodelingprep.com/api"
FAKE_KEY = "fmp-test-key-not-real-67890"


def _run(coro: Any) -> Any:  # type: ignore[no-untyped-def]
    return asyncio.run(coro)


@pytest.fixture
def stub_fmp_settings(
    monkeypatch: pytest.MonkeyPatch, default_settings: Settings
) -> Iterator[Settings]:
    """Patcht `Settings.load` mit einem Fake-FMP-Key + Test-Base-URL."""
    patched = default_settings.model_copy(
        update={"fmp_key": SecretStr(FAKE_KEY), "fmp_base_url": BASE_URL}
    )
    monkeypatch.setattr(
        csp_config.Settings,
        "load",
        classmethod(lambda cls, *a, **kw: patched),
    )
    yield patched


# ---------------------------------------------------------------------------
# FmpClient — Live-VIX (`/stable/quote`)
# ---------------------------------------------------------------------------


class TestLiveVix:
    def test_quote_returns_price(self) -> None:
        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close()

        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(
                    200, json=[{"symbol": "^VIX", "name": "CBOE VIX", "price": 17.45}]
                )
            )
            assert _run(call()) == 17.45

    def test_quote_falls_back_to_close_field(self) -> None:
        """Defensive fallback wenn FMP `close` statt `price` liefert."""

        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close()

        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(200, json=[{"symbol": "^VIX", "close": 19.2}])
            )
            assert _run(call()) == 19.2

    def test_quote_invalid_price_raises_empty(self) -> None:
        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close()

        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(200, json=[{"symbol": "^VIX", "price": None}])
            )
            with pytest.raises(FMPEmptyDataError, match="ungültiges price-Feld"):
                _run(call())

    def test_quote_empty_list_raises_empty(self) -> None:
        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close()

        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(200, json=[])
            )
            with pytest.raises(FMPEmptyDataError, match="Leere Antwort"):
                _run(call())

    def test_quote_data_wrapper_accepted(self) -> None:
        """Falls FMP je auf `{"data": [...]}`-Wrapper umstellt — defensiv unterstützt."""

        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close()

        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(200, json={"data": [{"price": 22.0}]})
            )
            assert _run(call()) == 22.0

    def test_quote_4xx_raises_immediately(self) -> None:
        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close()

        with respx.mock(assert_all_called=True) as router:
            route = router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(401, text="Unauthorized")
            )
            with pytest.raises(FMPDataError) as exc_info:
                _run(call())
            # Genau 1 Versuch, kein Retry bei 4xx.
            assert route.call_count == 1
            assert exc_info.value.status == 401

    def test_quote_5xx_retries_then_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def _noop(_seconds: float) -> None:
            return None

        monkeypatch.setattr("csp.clients.fmp.asyncio.sleep", _noop)

        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close()

        with respx.mock(assert_all_called=True) as router:
            route = router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(503, text="upstream down")
            )
            with pytest.raises(FMPDataError) as exc_info:
                _run(call())
            assert route.call_count == 3  # 3 Versuche
            assert exc_info.value.status == 503

    def test_quote_transport_error_retries_then_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _noop(_seconds: float) -> None:
            return None

        monkeypatch.setattr("csp.clients.fmp.asyncio.sleep", _noop)

        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close()

        with respx.mock(assert_all_called=True) as router:
            route = router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                side_effect=httpx.ConnectError("boom")
            )
            with pytest.raises(FMPDataError) as exc_info:
                _run(call())
            assert route.call_count == 3
            assert exc_info.value.status == -1  # Sentinel für Transport-Fehler


# ---------------------------------------------------------------------------
# FmpClient — Historical-VIX (`/stable/historical-price-eod/light`)
# ---------------------------------------------------------------------------


class TestHistoricalVix:
    def test_historical_picks_latest_le_target(self) -> None:
        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close(trade_date=date(2026, 4, 24))

        with respx.mock(assert_all_called=True) as router:
            router.get(
                re.compile(rf"^{re.escape(BASE_URL)}/stable/historical-price-eod/light")
            ).mock(
                return_value=httpx.Response(
                    200,
                    json=[
                        {"date": "2026-04-22", "price": 21.0},
                        {"date": "2026-04-24", "price": 23.1},
                        {"date": "2026-04-23", "price": 22.0},
                    ],
                )
            )
            assert _run(call()) == 23.1

    def test_historical_skips_dates_after_target(self) -> None:
        """Falls FMP einen Eintrag nach `trade_date` ausliefert (sollte nicht im
        Fenster sein, aber defensive Filterung)."""

        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close(trade_date=date(2026, 4, 23))

        with respx.mock(assert_all_called=True) as router:
            router.get(
                re.compile(rf"^{re.escape(BASE_URL)}/stable/historical-price-eod/light")
            ).mock(
                return_value=httpx.Response(
                    200,
                    json=[
                        {"date": "2026-04-23", "price": 22.0},
                        {"date": "2026-04-24", "price": 23.1},  # zu jung
                    ],
                )
            )
            assert _run(call()) == 22.0

    def test_historical_empty_window_raises(self) -> None:
        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close(trade_date=date(2026, 4, 24))

        with respx.mock(assert_all_called=True) as router:
            router.get(
                re.compile(rf"^{re.escape(BASE_URL)}/stable/historical-price-eod/light")
            ).mock(return_value=httpx.Response(200, json=[]))
            with pytest.raises(FMPEmptyDataError, match="Leere Antwort"):
                _run(call())

    def test_historical_skips_malformed_rows(self) -> None:
        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close(trade_date=date(2026, 4, 24))

        with respx.mock(assert_all_called=True) as router:
            router.get(
                re.compile(rf"^{re.escape(BASE_URL)}/stable/historical-price-eod/light")
            ).mock(
                return_value=httpx.Response(
                    200,
                    json=[
                        {"date": "2026-04-22", "price": "not-a-float"},
                        {"price": 99.9},  # date fehlt
                        {"date": "2026-04-23", "price": 22.0},
                    ],
                )
            )
            assert _run(call()) == 22.0

    def test_historical_no_valid_rows_le_target(self) -> None:
        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close(trade_date=date(2026, 4, 22))

        with respx.mock(assert_all_called=True) as router:
            router.get(
                re.compile(rf"^{re.escape(BASE_URL)}/stable/historical-price-eod/light")
            ).mock(
                return_value=httpx.Response(
                    200,
                    json=[
                        {"date": "2026-04-23", "price": 22.0},
                        {"date": "2026-04-24", "price": 23.1},
                    ],
                )
            )
            with pytest.raises(FMPEmptyDataError, match="Keine VIX-Schlusskurse"):
                _run(call())


# ---------------------------------------------------------------------------
# Items extraction (defensive)
# ---------------------------------------------------------------------------


class TestPayloadShape:
    def test_dict_with_historical_key_accepted(self) -> None:
        """Legacy `{"historical": [...]}`-Shape akzeptieren (FMP v3 Format)."""

        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close(trade_date=date(2026, 4, 24))

        with respx.mock(assert_all_called=True) as router:
            router.get(
                re.compile(rf"^{re.escape(BASE_URL)}/stable/historical-price-eod/light")
            ).mock(
                return_value=httpx.Response(
                    200, json={"historical": [{"date": "2026-04-23", "close": 22.0}]}
                )
            )
            assert _run(call()) == 22.0

    def test_unexpected_payload_shape_raises(self) -> None:
        async def call() -> float:
            async with httpx.AsyncClient() as client:
                fmp = FmpClient(client, base_url=BASE_URL, api_key=FAKE_KEY)
                return await fmp.vix_close()

        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(200, json="garbage")
            )
            with pytest.raises(FMPEmptyDataError, match="Leere Antwort"):
                _run(call())


# ---------------------------------------------------------------------------
# fmp_health_check
# ---------------------------------------------------------------------------


class TestFmpHealthCheck:
    def test_health_check_returns_vix(self, stub_fmp_settings: Settings) -> None:
        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(200, json=[{"price": 18.7}])
            )
            assert csp.fmp_health_check() == 18.7

    def test_health_check_missing_key_raises(
        self, monkeypatch: pytest.MonkeyPatch, default_settings: Settings
    ) -> None:
        patched = default_settings.model_copy(update={"fmp_key": SecretStr("")})
        monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
        with pytest.raises(ConfigError, match="FMP_KEY"):
            csp.fmp_health_check()


class TestPublicSurface:
    def test_csp_fmp_exports_resolve(self) -> None:
        assert csp.FmpClient is FmpClient
        assert csp.FMPDataError is FMPDataError
        assert csp.FMPEmptyDataError is FMPEmptyDataError
        assert csp.fmp_health_check is not None
        for name in ("FmpClient", "FMPDataError", "FMPEmptyDataError", "fmp_health_check"):
            assert name in csp.__all__
