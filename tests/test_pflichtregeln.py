"""Pflichtregeln-Tests: pro Regel eine Klasse + Orchestrator + Override + Regression."""

from __future__ import annotations

import pytest

import csp
from csp.config import Settings
from csp.filters.pflichtregeln import (
    passes_csp_filters,
    rule_01_volatility_regime,
    rule_02_delta_band,
    rule_03_dte_window,
    rule_04_otm_distance,
    rule_05_earnings_distance,
    rule_06_liquidity,
    rule_07_market_cap,
    rule_08_sector_cap,
    rule_09_universe,
)
from csp.models.core import MacroSnapshot, OratsCore, OratsStrike, PortfolioSnapshot
from tests.fixtures.now_2026_04_24 import NOW_CORE, NOW_MACRO, NOW_STRIKE


def _core(**overrides: object) -> OratsCore:
    base = NOW_CORE.model_dump()
    base.update(overrides)
    return OratsCore(**base)


def _strike(**overrides: object) -> OratsStrike:
    base = NOW_STRIKE.model_dump()
    base.update(overrides)
    return OratsStrike(**base)


def _macro(vix: float) -> MacroSnapshot:
    return MacroSnapshot(vix_close=vix)


class TestRule01VolatilityRegime:
    def test_passes_via_vix_leg(self, default_settings: Settings) -> None:
        # Niedriger IVR — VIX-Leg muss tragen.
        core = _core(ivr=10.0)
        passed, reason = rule_01_volatility_regime(
            core, NOW_STRIKE, _macro(25.0), PortfolioSnapshot(), default_settings
        )
        assert passed
        assert reason is None

    def test_passes_via_ivr_leg(self, default_settings: Settings) -> None:
        # Niedriger VIX — IVR-Leg muss tragen.
        passed, reason = rule_01_volatility_regime(
            NOW_CORE, NOW_STRIKE, _macro(18.0), PortfolioSnapshot(), default_settings
        )
        assert passed
        assert reason is None

    def test_fails_when_both_legs_low(self, default_settings: Settings) -> None:
        core = _core(ivr=35.0)
        passed, reason = rule_01_volatility_regime(
            core, NOW_STRIKE, _macro(18.0), PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Pflichtregel 1" in reason
        assert "VIX 18,00" in reason
        assert "IVR 35,00" in reason


class TestRule02DeltaBand:
    def test_passes_inside_band(self, default_settings: Settings) -> None:
        passed, reason = rule_02_delta_band(
            NOW_CORE, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed
        assert reason is None

    def test_fails_below_band(self, default_settings: Settings) -> None:
        strike = _strike(delta=-0.30)
        passed, reason = rule_02_delta_band(
            NOW_CORE, strike, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Pflichtregel 2" in reason
        assert "-0,30" in reason

    def test_fails_above_band(self, default_settings: Settings) -> None:
        strike = _strike(delta=-0.10)
        passed, reason = rule_02_delta_band(
            NOW_CORE, strike, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "-0,10" in reason


class TestRule03DteWindow:
    def test_passes_at_upper_boundary(self, default_settings: Settings) -> None:
        passed, _ = rule_03_dte_window(
            NOW_CORE, _strike(dte=55), NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_below_min(self, default_settings: Settings) -> None:
        passed, reason = rule_03_dte_window(
            NOW_CORE, _strike(dte=20), NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "DTE 20" in reason

    def test_fails_above_max(self, default_settings: Settings) -> None:
        passed, reason = rule_03_dte_window(
            NOW_CORE, _strike(dte=70), NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "DTE 70" in reason


class TestRule04OtmDistance:
    def test_passes_at_threshold(self, default_settings: Settings) -> None:
        passed, _ = rule_04_otm_distance(
            NOW_CORE, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_below_threshold(self, default_settings: Settings) -> None:
        # Strike 80 mit Spot 85 → OTM nur ≈ 5,88 %.
        passed, reason = rule_04_otm_distance(
            NOW_CORE, _strike(strike=80.0), NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Pflichtregel 4" in reason
        assert "%" in reason

    def test_fails_when_spot_invalid(self, default_settings: Settings) -> None:
        core = _core(under_price=0.0)
        passed, reason = rule_04_otm_distance(
            core, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Spotpreis" in reason


class TestRule05EarningsDistance:
    def test_passes_far_from_earnings(self, default_settings: Settings) -> None:
        passed, _ = rule_05_earnings_distance(
            NOW_CORE, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_when_earnings_today(self, default_settings: Settings) -> None:
        # ORATS gotcha: 0 Tage = "heute Earnings".
        core = _core(days_to_next_earn=0)
        passed, reason = rule_05_earnings_distance(
            core, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "0 Tagen" in reason

    def test_fails_just_below_threshold(self, default_settings: Settings) -> None:
        core = _core(days_to_next_earn=7)
        passed, reason = rule_05_earnings_distance(
            core, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "7 Tagen" in reason


class TestRule06Liquidity:
    def test_passes_with_good_volume_and_tight_spread(self, default_settings: Settings) -> None:
        passed, _ = rule_06_liquidity(
            NOW_CORE, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_on_low_volume_only(self, default_settings: Settings) -> None:
        core = _core(avg_opt_volu_20d=10_000)
        passed, reason = rule_06_liquidity(
            core, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Volumen 10000" in reason
        assert "Spread" not in reason

    def test_fails_on_wide_spread_only(self, default_settings: Settings) -> None:
        strike = _strike(put_bid=4.20, put_ask=4.40)  # Spread 0,20
        passed, reason = rule_06_liquidity(
            NOW_CORE, strike, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Spread 0,20" in reason

    def test_fails_on_both(self, default_settings: Settings) -> None:
        core = _core(avg_opt_volu_20d=10_000)
        strike = _strike(put_bid=4.20, put_ask=4.40)
        passed, reason = rule_06_liquidity(
            core, strike, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Volumen" in reason
        assert "Spread" in reason


class TestRule07MarketCap:
    def test_passes_at_boundary(self, default_settings: Settings) -> None:
        # Setting in Mrd: 50 → 50_000_000 in Tausend.
        core = _core(mkt_cap_thousands=50_000_000.0)
        passed, _ = rule_07_market_cap(
            core, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_just_below_boundary(self, default_settings: Settings) -> None:
        # 49,9 Mrd in Tausend.
        core = _core(mkt_cap_thousands=49_900_000.0)
        passed, reason = rule_07_market_cap(
            core, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Pflichtregel 7" in reason
        assert "49,90 Mrd" in reason

    def test_unit_conversion_pitfall_small_cap(self, default_settings: Settings) -> None:
        """Naive Lesart (mkt_cap_thousands ≥ market_cap_min_billion) würde fälschlich passen.

        Ein 1-Mrd-USD-Wert (= 1_000_000 in Tausend) ist deutlich > 50 (naiv).
        Korrekte Konvertierung muss diesen Fall scheitern lassen.
        """
        core = _core(mkt_cap_thousands=1_000_000.0)  # = 1 Mrd USD
        passed, reason = rule_07_market_cap(
            core, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "1,00 Mrd" in reason

    def test_unit_conversion_pitfall_passes_when_truly_large(
        self, default_settings: Settings
    ) -> None:
        # 96.524 Tausend (naiv ORATS-Ausgabewert) wäre nur 96,5 Mio USD — muss scheitern.
        core = _core(mkt_cap_thousands=96_524.0)
        passed, _ = rule_07_market_cap(
            core, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed


class TestRule08SectorCap:
    def test_passes_when_sector_below_cap(self, default_settings: Settings) -> None:
        portfolio = PortfolioSnapshot(sector_exposures={"Technology": 0.30})
        passed, _ = rule_08_sector_cap(NOW_CORE, NOW_STRIKE, NOW_MACRO, portfolio, default_settings)
        assert passed

    def test_passes_when_sector_unknown(self, default_settings: Settings) -> None:
        # Sektor nicht im Portfolio → 0,0 % → passt.
        portfolio = PortfolioSnapshot(sector_exposures={"Energy": 0.40})
        passed, _ = rule_08_sector_cap(NOW_CORE, NOW_STRIKE, NOW_MACRO, portfolio, default_settings)
        assert passed

    def test_fails_when_sector_above_cap(self, default_settings: Settings) -> None:
        portfolio = PortfolioSnapshot(sector_exposures={"Technology": 0.60})
        passed, reason = rule_08_sector_cap(
            NOW_CORE, NOW_STRIKE, NOW_MACRO, portfolio, default_settings
        )
        assert not passed
        assert reason is not None
        assert "Sektor Technology" in reason
        assert "60,0 %" in reason
        assert "55,0 %" in reason


class TestRule09Universe:
    def test_passes_when_in_universe(self, default_settings: Settings) -> None:
        passed, _ = rule_09_universe(
            NOW_CORE, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_when_not_in_universe(self, default_settings: Settings) -> None:
        core = _core(ticker="XXX")
        passed, reason = rule_09_universe(
            core, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Pflichtregel 9" in reason
        assert "XXX" in reason


class TestPassesCspFilters:
    def test_now_happy_path_returns_true_empty_reasons(
        self,
        default_settings: Settings,
        now_core: OratsCore,
        now_strike: OratsStrike,
        now_macro: MacroSnapshot,
        now_empty_portfolio: PortfolioSnapshot,
    ) -> None:
        passed, reasons = passes_csp_filters(
            now_core, now_strike, now_macro, now_empty_portfolio, default_settings
        )
        assert passed
        assert reasons == []

    def test_collects_all_failures_in_rule_order(self, default_settings: Settings) -> None:
        # Bricht Regel 2 (Delta), 3 (DTE) und 5 (Earnings).
        core = _core(days_to_next_earn=2)
        strike = _strike(delta=-0.05, dte=20)
        passed, reasons = passes_csp_filters(
            core, strike, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert len(reasons) == 3
        assert reasons[0].startswith("Pflichtregel 2")
        assert reasons[1].startswith("Pflichtregel 3")
        assert reasons[2].startswith("Pflichtregel 5")

    def test_collects_failures_for_rules_2_and_5(self, default_settings: Settings) -> None:
        core = _core(days_to_next_earn=2)
        strike = _strike(delta=-0.05)
        passed, reasons = passes_csp_filters(
            core, strike, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert len(reasons) == 2
        assert reasons[0].startswith("Pflichtregel 2")
        assert reasons[1].startswith("Pflichtregel 5")

    def test_universe_miss(self, default_settings: Settings) -> None:
        core = _core(ticker="XXX")
        passed, reasons = passes_csp_filters(
            core, NOW_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert any("Pflichtregel 9 — Ticker XXX nicht im Universum" in r for r in reasons)

    def test_sector_cap_failure_format(self, default_settings: Settings) -> None:
        portfolio = PortfolioSnapshot(sector_exposures={"Technology": 0.60})
        passed, reasons = passes_csp_filters(
            NOW_CORE, NOW_STRIKE, NOW_MACRO, portfolio, default_settings
        )
        assert not passed
        sector_reasons = [r for r in reasons if r.startswith("Pflichtregel 8")]
        assert sector_reasons
        assert "Technology" in sector_reasons[0]
        assert "60,0 %" in sector_reasons[0]
        assert "55,0 %" in sector_reasons[0]

    def test_override_returns_true_preserves_reasons_and_warns(
        self,
        default_settings: Settings,
    ) -> None:
        from loguru import logger

        captured: list[str] = []

        def sink(message: object) -> None:
            captured.append(str(message))

        handler_id = logger.add(sink, level="WARNING", format="{message}")
        try:
            core = _core(days_to_next_earn=2)
            strike = _strike(delta=-0.05)
            passed, reasons = passes_csp_filters(
                core,
                strike,
                NOW_MACRO,
                PortfolioSnapshot(),
                default_settings,
                override=True,
            )
        finally:
            logger.remove(handler_id)
        assert passed
        assert len(reasons) >= 1
        assert any("Pflichtregel 2" in r for r in reasons)
        assert any("Override" in line for line in captured)


@pytest.mark.now_regression
class TestNowRegression:
    def test_now_78_passes_all_rules(
        self,
        default_settings: Settings,
        now_core: OratsCore,
        now_strike: OratsStrike,
        now_macro: MacroSnapshot,
        now_empty_portfolio: PortfolioSnapshot,
    ) -> None:
        """NOW-78 vom 2026-04-24: alle 9 Pflichtregeln grün, leeres Portfolio."""
        passed, reasons = passes_csp_filters(
            now_core, now_strike, now_macro, now_empty_portfolio, default_settings
        )
        assert passed, f"NOW-78 sollte passen, scheiterte aber: {reasons}"
        assert reasons == []


def test_public_reexport_resolves_to_orchestrator() -> None:
    assert csp.passes_csp_filters is passes_csp_filters
