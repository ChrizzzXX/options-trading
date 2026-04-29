"""Tests für `csp.idea(...)` (Slice 3).

Schichten:
- ``TestSelectStrike``: Unit-Tests des reinen Strike-Selektors (DTE/Delta-nearest,
  Band-Filter, Tie-Breaks, Edge-Cases).
- ``TestBuildIdea``: Unit-Tests der reinen `build_idea`-Funktion (3-Zustand-Override-
  Semantik, Decimal/float-Disziplin, abgeleitete Kennzahlen).
- ``TestIdeaIntegration``: End-to-End via cassette-getragene `OratsClient`-Stubs
  (NOW-78 Reconciliation: 3 Pflichtregeln durchfallen; Override-Pfad; Live-Happy-
  Path via respx-Mock).
- ``TestPublicReexports``: ``csp.idea``, ``csp.Idea`` resolvieren.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from typing import Any

import httpx
import pytest
import respx

import csp
from csp.config import Settings
from csp.exceptions import ORATSEmptyDataError
from csp.idea import idea
from csp.models.core import MacroSnapshot, OratsCore, OratsStrike, PortfolioSnapshot
from csp.models.idea import Idea
from csp.strategies.csp import _select_strike, build_idea
from tests.fixtures.now_2026_04_24 import NOW_CORE, NOW_MACRO, NOW_STRIKE

BASE_URL = "https://api.orats.io/datav2"
FAKE_TOKEN = "test-token-not-real-12345"


def _strike(
    *, strike: float, delta: float, dte: int, put_bid: float = 1.0, put_ask: float = 1.05
) -> OratsStrike:
    return OratsStrike(
        strike=strike,
        delta=delta,
        dte=dte,
        putBidPrice=put_bid,
        putAskPrice=put_ask,
    )


def _run(coro: Any) -> Any:  # type: ignore[no-untyped-def]
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# _select_strike
# ---------------------------------------------------------------------------


class TestSelectStrike:
    """Strike-Selektor: DTE-nearest → Delta-Band → Delta-nearest → niedrigerer Strike."""

    def test_picks_dte_nearest_then_delta_nearest(self, default_settings: Settings) -> None:
        # Drei Expirations; gewünscht DTE 45 ⇒ DTE 44 gewinnt (näher als 30/60).
        strikes = [
            _strike(strike=80, delta=-0.20, dte=30),
            _strike(strike=80, delta=-0.20, dte=44),
            _strike(strike=80, delta=-0.20, dte=60),
        ]
        chosen = _select_strike(strikes, target_delta=-0.20, dte=45, settings=default_settings)
        assert chosen.dte == 44

    def test_dte_tie_break_prefers_lower_dte(self, default_settings: Settings) -> None:
        # Wunsch DTE 45 ⇒ |45-40|=5 == |45-50|=5; niedrigerer DTE gewinnt.
        strikes = [
            _strike(strike=80, delta=-0.20, dte=40),
            _strike(strike=80, delta=-0.20, dte=50),
        ]
        chosen = _select_strike(strikes, target_delta=-0.20, dte=45, settings=default_settings)
        assert chosen.dte == 40

    def test_filters_strikes_outside_delta_band(self, default_settings: Settings) -> None:
        # Band [-0.25, -0.18]; -0.10 / -0.30 ausserhalb, -0.20 drin.
        strikes = [
            _strike(strike=80, delta=-0.10, dte=45),
            _strike(strike=78, delta=-0.20, dte=45),
            _strike(strike=76, delta=-0.30, dte=45),
        ]
        chosen = _select_strike(strikes, target_delta=-0.20, dte=45, settings=default_settings)
        assert chosen.strike == 78
        assert chosen.delta == pytest.approx(-0.20)

    def test_picks_closest_delta_within_band(self, default_settings: Settings) -> None:
        # Drei in-band Kandidaten; -0.20 am nächsten zu Target -0.20.
        strikes = [
            _strike(strike=78, delta=-0.18, dte=45),
            _strike(strike=77, delta=-0.20, dte=45),
            _strike(strike=76, delta=-0.25, dte=45),
        ]
        chosen = _select_strike(strikes, target_delta=-0.20, dte=45, settings=default_settings)
        assert chosen.strike == 77

    def test_delta_tie_break_prefers_lower_strike(self, default_settings: Settings) -> None:
        # Beide haben |delta - (-0.20)| = 0.02 ⇒ niedrigerer Strike gewinnt (höherer OTM%).
        strikes = [
            _strike(strike=80, delta=-0.18, dte=45),
            _strike(strike=78, delta=-0.22, dte=45),
        ]
        chosen = _select_strike(strikes, target_delta=-0.20, dte=45, settings=default_settings)
        assert chosen.strike == 78

    def test_empty_list_raises_orats_empty_data_error(self, default_settings: Settings) -> None:
        with pytest.raises(ORATSEmptyDataError) as exc_info:
            _select_strike([], target_delta=-0.20, dte=45, settings=default_settings)
        assert "kein passender Strike" in str(exc_info.value)
        assert exc_info.value.status == 200

    def test_no_strike_in_band_raises(self, default_settings: Settings) -> None:
        # Alle Strikes haben Delta außerhalb [-0.25, -0.18].
        strikes = [
            _strike(strike=85, delta=-0.10, dte=45),
            _strike(strike=70, delta=-0.40, dte=45),
        ]
        with pytest.raises(ORATSEmptyDataError) as exc_info:
            _select_strike(strikes, target_delta=-0.20, dte=45, settings=default_settings)
        msg = str(exc_info.value)
        assert "kein passender Strike" in msg
        assert "Delta-Band" in msg


# ---------------------------------------------------------------------------
# build_idea — drei Zustände der Override-Semantik
# ---------------------------------------------------------------------------


def _happy_core(default_settings: Settings) -> OratsCore:
    """Pass-fähiger Core: NOW-Universum, Tech, große Cap, IVR über Schwelle, Earnings 30d."""
    return OratsCore(
        ticker="NOW",
        pxAtmIv=90.0,
        sectorName="Technology",
        mktCap=100_000_000.0,  # 100 Mrd USD (über 50 Mrd Schwelle).
        ivPctile1y=80.0,
        daysToNextErn=30,
        avgOptVolu20d=120_000.0,
    )


def _happy_strike() -> OratsStrike:
    """Pass-fähiger Strike: DTE 45, Delta -0.20, gutes Spread, Strike 81 (10% OTM)."""
    return OratsStrike(
        strike=81.0,
        delta=-0.20,
        dte=45,
        putBidPrice=1.50,
        putAskPrice=1.52,
    )


class TestBuildIdea:
    """Drei Zustände: Pass / Fail-ohne-Override / Fail-mit-Override."""

    def test_pass_state_populates_clean_idea(self, default_settings: Settings) -> None:
        core = _happy_core(default_settings)
        strike = _happy_strike()
        result = build_idea(
            core,
            strike,
            MacroSnapshot(vix_close=18.7),
            PortfolioSnapshot(),
            default_settings,
            as_of=date(2026, 4, 28),
            data_freshness="live",
            region="US",
            override=False,
        )
        assert result.pflichtregeln_passed is True
        assert result.reasons == []
        assert result.bypassed_rules == []
        assert result.ticker == "NOW"
        assert result.region == "US"
        assert result.data_freshness == "live"

    def test_fail_without_override_carries_reasons(self, default_settings: Settings) -> None:
        # NOW-78 historisch fällt durch 3 Regeln (DTE 56, Earnings 0, Spread 0.15).
        result = build_idea(
            NOW_CORE,
            NOW_STRIKE,
            NOW_MACRO,
            PortfolioSnapshot(),
            default_settings,
            as_of=date(2026, 4, 24),
            data_freshness="eod",
            region="US",
            override=False,
        )
        assert result.pflichtregeln_passed is False
        assert len(result.reasons) == 3
        assert result.bypassed_rules == []
        assert result.reasons[0].startswith("Pflichtregel 3")
        assert result.reasons[1].startswith("Pflichtregel 5")
        assert result.reasons[2].startswith("Pflichtregel 6")

    def test_fail_with_override_moves_reasons_to_bypassed(self, default_settings: Settings) -> None:
        result_no_ovr = build_idea(
            NOW_CORE,
            NOW_STRIKE,
            NOW_MACRO,
            PortfolioSnapshot(),
            default_settings,
            as_of=date(2026, 4, 24),
            data_freshness="eod",
            region="US",
            override=False,
        )
        result_ovr = build_idea(
            NOW_CORE,
            NOW_STRIKE,
            NOW_MACRO,
            PortfolioSnapshot(),
            default_settings,
            as_of=date(2026, 4, 24),
            data_freshness="eod",
            region="US",
            override=True,
        )
        assert result_ovr.pflichtregeln_passed is True
        assert result_ovr.reasons == []
        assert result_ovr.bypassed_rules == result_no_ovr.reasons

    def test_pass_with_override_flag_keeps_lists_empty(self, default_settings: Settings) -> None:
        # Override darf keinen False-Positiv produzieren, wenn nichts zu umgehen ist.
        core = _happy_core(default_settings)
        strike = _happy_strike()
        result = build_idea(
            core,
            strike,
            MacroSnapshot(vix_close=18.7),
            PortfolioSnapshot(),
            default_settings,
            as_of=date(2026, 4, 28),
            data_freshness="live",
            region="US",
            override=True,
        )
        assert result.pflichtregeln_passed is True
        assert result.reasons == []
        assert result.bypassed_rules == []

    def test_money_fields_are_decimal(self, default_settings: Settings) -> None:
        core = _happy_core(default_settings)
        strike = _happy_strike()
        result = build_idea(
            core,
            strike,
            MacroSnapshot(vix_close=18.7),
            PortfolioSnapshot(),
            default_settings,
            as_of=date(2026, 4, 28),
            data_freshness="live",
            region="US",
            override=False,
        )
        assert isinstance(result.strike, Decimal)
        assert isinstance(result.put_bid, Decimal)
        assert isinstance(result.put_ask, Decimal)
        assert isinstance(result.mid_premium, Decimal)
        # Decimal('1.50') statt Float-Artefakt: Mid = (1.50 + 1.52) / 2 = 1.51, quantisiert.
        assert result.mid_premium == Decimal("1.5100")
        # Ratios bleiben float.
        assert isinstance(result.delta, float)
        assert isinstance(result.annualized_yield_pct, float)
        assert isinstance(result.otm_pct, float)

    def test_annualized_yield_formula(self, default_settings: Settings) -> None:
        # mid = 1.51, strike = 81, dte = 45 ⇒ 1.51/81 * 365/45 * 100 ≈ 15.115...
        core = _happy_core(default_settings)
        strike = _happy_strike()
        result = build_idea(
            core,
            strike,
            MacroSnapshot(vix_close=18.7),
            PortfolioSnapshot(),
            default_settings,
            as_of=date(2026, 4, 28),
            data_freshness="live",
            region="US",
            override=False,
        )
        expected = float(Decimal("1.5100") / Decimal("81")) * 365.0 / 45 * 100.0
        assert result.annualized_yield_pct == pytest.approx(expected, rel=1e-9)

    def test_otm_pct_formula(self, default_settings: Settings) -> None:
        # under_price=90, strike=81 ⇒ (90-81)/90 * 100 = 10.0
        core = _happy_core(default_settings)
        strike = _happy_strike()
        result = build_idea(
            core,
            strike,
            MacroSnapshot(vix_close=18.7),
            PortfolioSnapshot(),
            default_settings,
            as_of=date(2026, 4, 28),
            data_freshness="live",
            region="US",
            override=False,
        )
        assert result.otm_pct == pytest.approx(10.0)

    def test_sector_share_pct_from_portfolio(self, default_settings: Settings) -> None:
        core = _happy_core(default_settings)
        strike = _happy_strike()
        # Portfolio hat 30% Tech-Anteil ⇒ field zeigt 30.0 (% darstellbar; <=55 cap-konform).
        portfolio = PortfolioSnapshot(sector_exposures={"Technology": 0.30})
        result = build_idea(
            core,
            strike,
            MacroSnapshot(vix_close=18.7),
            portfolio,
            default_settings,
            as_of=date(2026, 4, 28),
            data_freshness="live",
            region="US",
            override=False,
        )
        assert result.current_sector_share_pct == pytest.approx(30.0)

    def test_override_emits_warn_log(self, default_settings: Settings) -> None:
        # Loguru direkt in eine Liste sammeln statt über stdlib-`caplog` zu brücken —
        # einfacher und weniger fragil. Tighten: Substring-Match auf den tatsächlichen
        # deutschen Text, den `passes_csp_filters` emittiert ("Pflichtregeln-Override
        # aktiv für Ticker NOW: 3 Verstöße ignoriert"). So bricht der Test, wenn die
        # WARN-Quelle zerstört wird, statt zufällig auf irgendeinem "override" zu matchen.
        from loguru import logger

        messages: list[str] = []
        handler_id = logger.add(messages.append, level="WARNING", format="{message}")
        try:
            build_idea(
                NOW_CORE,
                NOW_STRIKE,
                NOW_MACRO,
                PortfolioSnapshot(),
                default_settings,
                as_of=date(2026, 4, 24),
                data_freshness="eod",
                region="US",
                override=True,
            )
        finally:
            logger.remove(handler_id)
        joined = " | ".join(messages)
        assert "Pflichtregeln-Override aktiv für Ticker NOW" in joined


# ---------------------------------------------------------------------------
# Integration: csp.idea(...) end-to-end via gemockten OratsClient (cassette-frei,
# damit auch der historische Pfad gegen die echten cassette-Bytes läuft, ohne
# pytest-vcr-Modul-Magie zu vermischen mit respx).
# ---------------------------------------------------------------------------


def _strikes_payload_for_now() -> dict[str, Any]:
    """Synthetic payload, der NOW-Strike 78 mit DTE 56 enthält — exakt der Reconciliation-
    Anker. ORATS gibt im /hist/strikes-Endpunkt das CALL-Delta zurück; OratsClient
    konvertiert intern zu Put-Delta. Wir liefern call_delta = 0.7790 ⇒ put = -0.2210."""
    return {
        "data": [
            {
                "strike": 78,
                "delta": 0.7790244841371401,
                "dte": 56,
                "putBidPrice": 2.7,
                "putAskPrice": 2.85,
            },
        ]
    }


def _hist_cores_payload_for_now() -> dict[str, Any]:
    """Spiegelt die echte cassette: pxAtmIv 89.84, sectorName Technology, IVR 96, Earnings 0."""
    return {
        "data": [
            {
                "ticker": "NOW",
                "pxAtmIv": 89.84,
                "sectorName": "Technology",
                "mktCap": 93_972_640.0,
                "ivPctile1y": 96.0,
                "daysToNextErn": 0,
                "avgOptVolu20d": 116_894.6,
            }
        ]
    }


@pytest.fixture
def stub_settings(
    monkeypatch: pytest.MonkeyPatch, default_settings: Settings
) -> Iterator[Settings]:
    """Patcht `Settings.load` in `csp.idea`, damit weder `.env` noch `os.environ` benötigt wird."""
    from pydantic import SecretStr

    # Wir kopieren die default_settings und überschreiben Token + Base-URL.
    patched = default_settings.model_copy(
        update={"orats_token": SecretStr(FAKE_TOKEN), "orats_base_url": BASE_URL}
    )
    from csp import config as csp_config

    monkeypatch.setattr(
        csp_config.Settings,
        "load",
        classmethod(lambda cls, *a, **kw: patched),
    )
    yield patched


class TestIdeaIntegration:
    """End-to-End-Pfad: `csp.idea(ticker, ...)` → respx-gemockter OratsClient."""

    def test_now_78_historical_three_rules_fail(self, stub_settings: Settings) -> None:
        with respx.mock(assert_all_called=True) as router:
            cores_route = router.get(f"{BASE_URL}/hist/cores").mock(
                return_value=httpx.Response(200, json=_hist_cores_payload_for_now())
            )
            strikes_route = router.get(f"{BASE_URL}/hist/strikes").mock(
                return_value=httpx.Response(200, json=_strikes_payload_for_now())
            )
            result = idea("NOW", dte=55, target_delta=-0.20, as_of=date(2026, 4, 24))
        # P4: tradeDate-Parameter explizit prüfen — sonst würde der Test auch dann
        # passieren, wenn `idea()` versehentlich ein anderes Datum (z. B. heute)
        # an /hist/cores oder /hist/strikes schickte.
        assert cores_route.calls.last.request.url.params["tradeDate"] == "20260424"
        assert strikes_route.calls.last.request.url.params["tradeDate"] == "20260424"
        assert result.pflichtregeln_passed is False
        assert len(result.reasons) == 3
        assert result.reasons[0].startswith("Pflichtregel 3")
        assert result.reasons[1].startswith("Pflichtregel 5")
        assert result.reasons[2].startswith("Pflichtregel 6")
        assert result.bypassed_rules == []
        assert result.ticker == "NOW"
        assert result.data_freshness == "eod"
        assert result.region == "US"
        assert result.as_of == date(2026, 4, 24)

    def test_now_78_with_override_moves_reasons_to_bypassed(self, stub_settings: Settings) -> None:
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{BASE_URL}/hist/cores").mock(
                return_value=httpx.Response(200, json=_hist_cores_payload_for_now())
            )
            router.get(f"{BASE_URL}/hist/strikes").mock(
                return_value=httpx.Response(200, json=_strikes_payload_for_now())
            )
            result = idea(
                "NOW",
                dte=55,
                target_delta=-0.20,
                as_of=date(2026, 4, 24),
                override=True,
            )
        assert result.pflichtregeln_passed is True
        assert result.reasons == []
        assert len(result.bypassed_rules) == 3
        assert result.bypassed_rules[0].startswith("Pflichtregel 3")

    def test_live_happy_path_passes(self, stub_settings: Settings) -> None:
        # Live-Endpunkte (`/cores` + `/strikes`) liefern eine pass-fähige Konstellation.
        live_cores = {
            "data": [
                {
                    "ticker": "NOW",
                    "pxAtmIv": 90.0,
                    "sectorName": "Technology",
                    "mktCap": 100_000_000.0,
                    "ivPctile1y": 80.0,
                    "daysToNextErn": 30,
                    "avgOptVolu20d": 120_000.0,
                }
            ]
        }
        # Strike 81, DTE 45, Delta -0.20 (call_delta 0.80), bid 1.50 ask 1.52.
        live_strikes = {
            "data": [
                {
                    "strike": 81,
                    "delta": 0.80,
                    "dte": 45,
                    "putBidPrice": 1.50,
                    "putAskPrice": 1.52,
                },
            ]
        }
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{BASE_URL}/cores").mock(return_value=httpx.Response(200, json=live_cores))
            router.get(f"{BASE_URL}/strikes").mock(
                return_value=httpx.Response(200, json=live_strikes)
            )
            result = idea("NOW", dte=45, target_delta=-0.20)
        assert result.pflichtregeln_passed is True
        assert result.reasons == []
        assert result.bypassed_rules == []
        assert result.data_freshness == "live"
        # P11: `idea()` löst `as_of` über Europe/Berlin auf (TZ-aware-Hard-Rule).
        # Wir berechnen das Erwartete identisch — kein flaky `date.today()`.
        from datetime import datetime
        from zoneinfo import ZoneInfo

        assert result.as_of == datetime.now(ZoneInfo("Europe/Berlin")).date()
        assert result.region == "US"
        # P10: Call-Delta 0,80 → Put-Delta -0,20 (OratsClient konvertiert intern).
        # Strike als Decimal pinnt, dass Money-Disziplin durch die ganze Kette hält.
        assert result.delta == pytest.approx(-0.20)
        assert result.strike == Decimal("81")

    def test_live_no_strike_in_band_raises(self, stub_settings: Settings) -> None:
        # /strikes liefert nur Strikes mit zu kleinem Delta — kein Band-Match.
        live_cores = _hist_cores_payload_for_now()
        live_strikes = {
            "data": [
                {  # call_delta 0.95 ⇒ put -0.05 (außerhalb -0.25..-0.18).
                    "strike": 60,
                    "delta": 0.95,
                    "dte": 45,
                    "putBidPrice": 0.10,
                    "putAskPrice": 0.12,
                }
            ]
        }
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{BASE_URL}/cores").mock(return_value=httpx.Response(200, json=live_cores))
            router.get(f"{BASE_URL}/strikes").mock(
                return_value=httpx.Response(200, json=live_strikes)
            )
            with pytest.raises(ORATSEmptyDataError) as exc_info:
                idea("NOW", dte=45, target_delta=-0.20)
        assert "kein passender Strike" in str(exc_info.value)

    def test_missing_token_raises_config_error(
        self, monkeypatch: pytest.MonkeyPatch, default_settings: Settings
    ) -> None:
        from pydantic import SecretStr

        from csp import config as csp_config
        from csp.exceptions import ConfigError

        patched = default_settings.model_copy(update={"orats_token": SecretStr("")})
        monkeypatch.setattr(
            csp_config.Settings,
            "load",
            classmethod(lambda cls, *a, **kw: patched),
        )
        with pytest.raises(ConfigError, match="ORATS_TOKEN"):
            idea("NOW")

    def test_future_as_of_raises_value_error(self, stub_settings: Settings) -> None:
        # P6: `as_of` in der Zukunft → ValueError statt generischer "leere data-Liste"-Fehler.
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        future = datetime.now(ZoneInfo("Europe/Berlin")).date() + timedelta(days=1)
        with pytest.raises(ValueError, match="liegt in der Zukunft"):
            idea("NOW", as_of=future)


# ---------------------------------------------------------------------------
# Public re-exports (`csp.idea`, `csp.Idea`).
# ---------------------------------------------------------------------------


class TestPublicReexports:
    def test_csp_idea_function_resolves(self) -> None:
        assert csp.idea is idea

    def test_csp_idea_model_resolves(self) -> None:
        assert csp.Idea is Idea
