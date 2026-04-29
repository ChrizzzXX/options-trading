"""Tests für `csp.macro_snapshot` und den `_fetch_macro`-Helper (Slice 5)."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx
from pydantic import SecretStr

import csp
from csp import config as csp_config
from csp.config import Settings
from csp.macro import macro_snapshot
from csp.models.core import MacroSnapshot

BASE_URL = "https://financialmodelingprep.com"
FAKE_KEY = "fmp-test-key-not-real"


@pytest.fixture
def stub_with_key(
    monkeypatch: pytest.MonkeyPatch, default_settings: Settings
) -> Iterator[Settings]:
    patched = default_settings.model_copy(
        update={"fmp_key": SecretStr(FAKE_KEY), "fmp_base_url": BASE_URL}
    )
    monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
    yield patched


@pytest.fixture
def stub_without_key(
    monkeypatch: pytest.MonkeyPatch, default_settings: Settings
) -> Iterator[Settings]:
    patched = default_settings.model_copy(
        update={"fmp_key": SecretStr(""), "fmp_base_url": BASE_URL}
    )
    monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
    yield patched


# ---------------------------------------------------------------------------
# macro_snapshot — Public surface
# ---------------------------------------------------------------------------


class TestMacroSnapshot:
    def test_no_key_falls_back_to_settings(self, stub_without_key: Settings) -> None:
        """Ohne `FMP_KEY`: kein HTTP, Settings-Fallback (Slice-3-Verhalten erhalten)."""
        with respx.mock(assert_all_called=False) as router:
            quote_route = router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote"))
            result = macro_snapshot()
            assert quote_route.call_count == 0
        assert isinstance(result, MacroSnapshot)
        assert result.vix_close == stub_without_key.macro.vix_close

    def test_live_key_returns_fetched_vix(self, stub_with_key: Settings) -> None:
        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(200, json=[{"price": 17.45}])
            )
            result = macro_snapshot()
        assert result.vix_close == 17.45

    def test_historical_returns_fetched_vix(self, stub_with_key: Settings) -> None:
        with respx.mock(assert_all_called=True) as router:
            router.get(
                re.compile(rf"^{re.escape(BASE_URL)}/stable/historical-price-eod/light")
            ).mock(return_value=httpx.Response(200, json=[{"date": "2026-04-24", "price": 23.1}]))
            result = macro_snapshot(as_of=date(2026, 4, 24))
        assert result.vix_close == 23.1

    def test_fmp_4xx_falls_back_to_settings(self, stub_with_key: Settings) -> None:
        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(401, text="Unauthorized")
            )
            result = macro_snapshot()
        assert result.vix_close == stub_with_key.macro.vix_close

    def test_fmp_empty_falls_back_to_settings(self, stub_with_key: Settings) -> None:
        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(200, json=[])
            )
            result = macro_snapshot()
        assert result.vix_close == stub_with_key.macro.vix_close

    def test_future_as_of_raises(self, stub_with_key: Settings) -> None:
        future = datetime.now(ZoneInfo("Europe/Berlin")).date() + timedelta(days=1)
        with pytest.raises(ValueError, match="liegt in der Zukunft"):
            macro_snapshot(as_of=future)

    def test_whitespace_only_key_treated_as_missing(
        self, monkeypatch: pytest.MonkeyPatch, default_settings: Settings
    ) -> None:
        patched = default_settings.model_copy(
            update={"fmp_key": SecretStr("   "), "fmp_base_url": BASE_URL}
        )
        monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
        with respx.mock(assert_all_called=False) as router:
            quote_route = router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote"))
            result = macro_snapshot()
            assert quote_route.call_count == 0
        assert result.vix_close == default_settings.macro.vix_close


# ---------------------------------------------------------------------------
# csp.scan + csp.idea — wiring through _fetch_macro
# ---------------------------------------------------------------------------


def _passing_cores_payload(ticker: str) -> dict[str, Any]:
    return {
        "data": [
            {
                "ticker": ticker,
                "pxAtmIv": 100.0,
                "sectorName": "Technology",
                "mktCap": 100_000_000.0,
                "ivPctile1y": 80.0,
                "daysToNextErn": 30,
                "avgOptVolu20d": 120_000.0,
            }
        ]
    }


def _passing_strikes_payload() -> dict[str, Any]:
    return {
        "data": [
            {
                "strike": 88.0,
                "delta": 0.80,
                "dte": 45,
                "putBidPrice": 1.50,
                "putAskPrice": 1.52,
            }
        ]
    }


@pytest.fixture
def stub_full_settings(
    monkeypatch: pytest.MonkeyPatch, default_settings: Settings
) -> Iterator[Settings]:
    """ORATS + FMP-Key gesetzt + 1-Ticker-Universum → integriertes Szenario."""
    patched = default_settings.model_copy(
        update={
            "orats_token": SecretStr("orats-fake"),
            "orats_base_url": "https://api.orats.io/datav2",
            "fmp_key": SecretStr(FAKE_KEY),
            "fmp_base_url": BASE_URL,
            "universe": default_settings.universe.model_copy(update={"allowed_tickers": ["NOW"]}),
        }
    )
    monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
    yield patched


class TestScanAndIdeaUseLiveMacro:
    """Slice 5: `idea` und `scan` rufen FMP an, wenn `FMP_KEY` gesetzt ist."""

    def test_scan_uses_live_vix_when_key_set(self, stub_full_settings: Settings) -> None:
        with respx.mock(assert_all_called=True) as router:
            quote_route = router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(200, json=[{"price": 22.0}])
            )
            router.get(re.compile(r"^https://api\.orats\.io/datav2/cores")).mock(
                return_value=httpx.Response(200, json=_passing_cores_payload("NOW"))
            )
            router.get(re.compile(r"^https://api\.orats\.io/datav2/strikes")).mock(
                return_value=httpx.Response(200, json=_passing_strikes_payload())
            )

            result = csp.scan()
        # FMP wurde GENAU EINMAL angefragt (vor Fan-Out, NICHT pro Ticker).
        assert quote_route.call_count == 1
        # Live-VIX 22.0 erlaubt Pflichtregel 1 via VIX-Leg ⇒ Idea passiert die Regeln.
        assert len(result) == 1
        assert result[0].ticker == "NOW"

    def test_idea_uses_live_vix_when_key_set(self, stub_full_settings: Settings) -> None:
        with respx.mock(assert_all_called=True) as router:
            quote_route = router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote")).mock(
                return_value=httpx.Response(200, json=[{"price": 22.0}])
            )
            router.get(re.compile(r"^https://api\.orats\.io/datav2/cores")).mock(
                return_value=httpx.Response(200, json=_passing_cores_payload("NOW"))
            )
            router.get(re.compile(r"^https://api\.orats\.io/datav2/strikes")).mock(
                return_value=httpx.Response(200, json=_passing_strikes_payload())
            )

            result = csp.idea("NOW")
        assert quote_route.call_count == 1
        assert result.ticker == "NOW"
        assert result.pflichtregeln_passed is True

    def test_scan_without_fmp_key_zero_quote_calls(
        self, monkeypatch: pytest.MonkeyPatch, default_settings: Settings
    ) -> None:
        """Ohne FMP_KEY werden weiterhin Settings-Macro genutzt — kein VIX-Call."""
        patched = default_settings.model_copy(
            update={
                "orats_token": SecretStr("orats-fake"),
                "orats_base_url": "https://api.orats.io/datav2",
                "fmp_key": SecretStr(""),
                "universe": default_settings.universe.model_copy(
                    update={"allowed_tickers": ["NOW"]}
                ),
            }
        )
        monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
        with respx.mock(assert_all_called=False) as router:
            quote_route = router.get(re.compile(rf"^{re.escape(BASE_URL)}/stable/quote"))
            router.get(re.compile(r"^https://api\.orats\.io/datav2/cores")).mock(
                return_value=httpx.Response(200, json=_passing_cores_payload("NOW"))
            )
            router.get(re.compile(r"^https://api\.orats\.io/datav2/strikes")).mock(
                return_value=httpx.Response(200, json=_passing_strikes_payload())
            )
            csp.scan()
        assert quote_route.call_count == 0


class TestPublicMacroExport:
    def test_macro_snapshot_is_public(self) -> None:
        assert csp.macro_snapshot is macro_snapshot
        assert "macro_snapshot" in csp.__all__
