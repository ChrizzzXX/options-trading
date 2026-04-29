"""Pflichtregeln-Tests: pro Regel eine Klasse + Orchestrator + Override + Regression.

Die `_core()`/`_strike()`-Hilfen starten von einem **synthetischen** Baseline
(`HAPPY_CORE` / `HAPPY_STRIKE`), nicht vom NOW-Cassette-Fixture, weil die echten
NOW-Daten vom 2026-04-24 drei Pflichtregeln verletzen (siehe Reconciliation
in `tests/fixtures/now_2026_04_24.py`-Modul-Docstring). Tests, die einen "guten"
Kandidaten brauchen, bekommen ihn explizit.

Die echten NOW-Werte werden ausschließlich von `TestNowRegression` benutzt — dort
wird die wahre Verdikt asserted (3 Pflichtregeln scheitern).
"""

from __future__ import annotations

from typing import ClassVar

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
from tests.fixtures.now_2026_04_24 import NOW_MACRO

# Synthetischer "alle 9 Regeln passen"-Baseline. Nicht aus den echten Cassette-Daten
# abgeleitet — der reale NOW-78-Strike vom 2026-04-24 verletzt drei Regeln.
HAPPY_CORE = OratsCore.model_validate(
    {
        "ticker": "NOW",
        "pxAtmIv": 85.0,
        "sectorName": "Technology",
        "mktCap": 170_000_000,
        "ivPctile1y": 94,
        "daysToNextErn": 30,
        "avgOptVolu20d": 120_000.0,
    }
)
HAPPY_STRIKE = OratsStrike.model_validate(
    {
        "strike": 78.0,
        "delta": -0.22,
        "dte": 45,
        "putAskPrice": 4.32,
        "putBidPrice": 4.28,
    }
)


def _core(**overrides: object) -> OratsCore:
    base = HAPPY_CORE.model_dump()
    base.update(overrides)
    return OratsCore(**base)


def _strike(**overrides: object) -> OratsStrike:
    base = HAPPY_STRIKE.model_dump()
    base.update(overrides)
    return OratsStrike(**base)


def _macro(vix: float) -> MacroSnapshot:
    return MacroSnapshot(vix_close=vix)


class TestRule01VolatilityRegime:
    def test_passes_via_vix_leg(self, default_settings: Settings) -> None:
        # Niedriger IVR — VIX-Leg muss tragen.
        core = _core(ivr=10.0)
        passed, reason = rule_01_volatility_regime(
            core, HAPPY_STRIKE, _macro(25.0), PortfolioSnapshot(), default_settings
        )
        assert passed
        assert reason is None

    def test_passes_via_ivr_leg(self, default_settings: Settings) -> None:
        # Niedriger VIX — IVR-Leg muss tragen.
        passed, reason = rule_01_volatility_regime(
            HAPPY_CORE, HAPPY_STRIKE, _macro(18.0), PortfolioSnapshot(), default_settings
        )
        assert passed
        assert reason is None

    def test_fails_when_both_legs_low(self, default_settings: Settings) -> None:
        core = _core(ivr=35.0)
        passed, reason = rule_01_volatility_regime(
            core, HAPPY_STRIKE, _macro(18.0), PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Pflichtregel 1" in reason
        assert "VIX 18,00" in reason
        assert "IVR 35,00" in reason

    @pytest.mark.parametrize(
        ("vix", "ivr", "expected"),
        [
            # P12: Beide Schenkel an / unter Schwelle gepinnt; Default vix_min=20, ivr_min=40.
            (18.0, 45.0, True),  # IVR-Leg trägt: 45 ≥ 40, VIX-Leg fällt: 18 < 20
            (20.0, 10.0, True),  # VIX-Leg trägt exakt an Schwelle: 20 ≥ 20
            (20.0, 40.0, True),  # Beide exakt an Schwelle → pass
            (19.99, 39.99, False),  # Beide knapp unter → fail
        ],
    )
    def test_threshold_grazing_boundaries(
        self, default_settings: Settings, vix: float, ivr: float, expected: bool
    ) -> None:
        core = _core(ivr=ivr)
        passed, _ = rule_01_volatility_regime(
            core, HAPPY_STRIKE, _macro(vix), PortfolioSnapshot(), default_settings
        )
        assert passed is expected


class TestRule02DeltaBand:
    def test_passes_inside_band(self, default_settings: Settings) -> None:
        passed, reason = rule_02_delta_band(
            HAPPY_CORE, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed
        assert reason is None

    def test_fails_below_band(self, default_settings: Settings) -> None:
        strike = _strike(delta=-0.30)
        passed, reason = rule_02_delta_band(
            HAPPY_CORE, strike, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Pflichtregel 2" in reason
        assert "-0,30" in reason

    def test_fails_above_band(self, default_settings: Settings) -> None:
        strike = _strike(delta=-0.10)
        passed, reason = rule_02_delta_band(
            HAPPY_CORE, strike, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "-0,10" in reason


class TestRule03DteWindow:
    def test_passes_at_upper_boundary(self, default_settings: Settings) -> None:
        passed, _ = rule_03_dte_window(
            HAPPY_CORE, _strike(dte=55), NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_below_min(self, default_settings: Settings) -> None:
        passed, reason = rule_03_dte_window(
            HAPPY_CORE, _strike(dte=20), NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "DTE 20" in reason

    def test_fails_above_max(self, default_settings: Settings) -> None:
        passed, reason = rule_03_dte_window(
            HAPPY_CORE, _strike(dte=70), NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "DTE 70" in reason


class TestRule04OtmDistance:
    def test_passes_at_threshold(self, default_settings: Settings) -> None:
        passed, _ = rule_04_otm_distance(
            HAPPY_CORE, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_below_threshold(self, default_settings: Settings) -> None:
        # Strike 80 mit Spot 85 → OTM nur ≈ 5,88 %.
        passed, reason = rule_04_otm_distance(
            HAPPY_CORE, _strike(strike=80.0), NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Pflichtregel 4" in reason
        assert "%" in reason

    def test_invalid_spot_rejected_at_model_boundary(self, default_settings: Settings) -> None:
        """P14: under_price <= 0 wird von Pydantic verworfen, Rule 4 sieht solche Daten nie."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            _core(under_price=0.0)
        with pytest.raises(ValidationError):
            _core(under_price=-1.0)


class TestRule05EarningsDistance:
    def test_passes_far_from_earnings(self, default_settings: Settings) -> None:
        passed, _ = rule_05_earnings_distance(
            HAPPY_CORE, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_when_earnings_today(self, default_settings: Settings) -> None:
        # ORATS gotcha: 0 Tage = "heute Earnings".
        core = _core(days_to_next_earn=0)
        passed, reason = rule_05_earnings_distance(
            core, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "0 Tagen" in reason

    def test_fails_just_below_threshold(self, default_settings: Settings) -> None:
        core = _core(days_to_next_earn=7)
        passed, reason = rule_05_earnings_distance(
            core, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "7 Tagen" in reason

    def test_fails_when_earnings_distance_unknown(self, default_settings: Settings) -> None:
        """Slice-12: ``days_to_next_earn=None`` → Fail mit eigener deutscher Begründung.

        Differenziert "heute Earnings" (0) von "ORATS-Datum nicht verfügbar"
        (None). Beide failen Rule 5, aber mit unterschiedlicher Diagnose.
        Override-Pfad bleibt offen (siehe ``TestPassesCspFiltersOrchestrator``).
        """
        core = _core(days_to_next_earn=None)
        passed, reason = rule_05_earnings_distance(
            core, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Earnings-Datum bei Vendor nicht verfügbar" in reason
        assert "manuell prüfen" in reason
        # Der konkrete "X Tagen"-String darf nicht erscheinen, sonst verwirrt.
        assert "Tagen" not in reason


class TestRule06Liquidity:
    def test_passes_with_good_volume_and_tight_spread(self, default_settings: Settings) -> None:
        passed, _ = rule_06_liquidity(
            HAPPY_CORE, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_on_low_volume_only(self, default_settings: Settings) -> None:
        core = _core(avg_opt_volu_20d=10_000)
        passed, reason = rule_06_liquidity(
            core, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Volumen 10000" in reason
        assert "Spread" not in reason

    def test_fails_on_wide_spread_only(self, default_settings: Settings) -> None:
        strike = _strike(put_bid=4.20, put_ask=4.40)  # Spread 0,20
        passed, reason = rule_06_liquidity(
            HAPPY_CORE, strike, NOW_MACRO, PortfolioSnapshot(), default_settings
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
            core, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_just_below_boundary(self, default_settings: Settings) -> None:
        # 49,9 Mrd in Tausend.
        core = _core(mkt_cap_thousands=49_900_000.0)
        passed, reason = rule_07_market_cap(
            core, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
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
            core, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
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
            core, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed


class TestRule08SectorCap:
    def test_passes_when_sector_below_cap(self, default_settings: Settings) -> None:
        portfolio = PortfolioSnapshot(sector_exposures={"Technology": 0.30})
        passed, _ = rule_08_sector_cap(
            HAPPY_CORE, HAPPY_STRIKE, NOW_MACRO, portfolio, default_settings
        )
        assert passed

    def test_passes_when_sector_unknown(self, default_settings: Settings) -> None:
        # Sektor nicht im Portfolio → 0,0 % → passt.
        portfolio = PortfolioSnapshot(sector_exposures={"Energy": 0.40})
        passed, _ = rule_08_sector_cap(
            HAPPY_CORE, HAPPY_STRIKE, NOW_MACRO, portfolio, default_settings
        )
        assert passed

    def test_fails_when_sector_above_cap(self, default_settings: Settings) -> None:
        portfolio = PortfolioSnapshot(sector_exposures={"Technology": 0.60})
        passed, reason = rule_08_sector_cap(
            HAPPY_CORE, HAPPY_STRIKE, NOW_MACRO, portfolio, default_settings
        )
        assert not passed
        assert reason is not None
        assert "Sektor Technology" in reason
        assert "60,0 %" in reason
        assert "55,0 %" in reason

    @pytest.mark.parametrize(
        ("share", "expected"),
        [
            # P4: sector_cap_pct=55.0; share*100 produzierte fälschlich 55.000…01 > 55.0.
            (0.5499, True),  # knapp darunter → pass
            (0.5500, True),  # exakt an Grenze → pass (FP-sicherer Vergleich)
            (0.5501, False),  # knapp darüber → fail
        ],
    )
    def test_fp_boundary_at_exact_threshold(
        self, default_settings: Settings, share: float, expected: bool
    ) -> None:
        portfolio = PortfolioSnapshot(sector_exposures={"Technology": share})
        passed, _ = rule_08_sector_cap(
            HAPPY_CORE, HAPPY_STRIKE, NOW_MACRO, portfolio, default_settings
        )
        assert passed is expected


class TestRule09Universe:
    def test_passes_when_in_universe(self, default_settings: Settings) -> None:
        passed, _ = rule_09_universe(
            HAPPY_CORE, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert passed

    def test_fails_when_not_in_universe(self, default_settings: Settings) -> None:
        core = _core(ticker="XXX")
        passed, reason = rule_09_universe(
            core, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert reason is not None
        assert "Pflichtregel 9" in reason
        assert "XXX" in reason


class TestPassesCspFilters:
    def test_synthetic_happy_path_returns_true_empty_reasons(
        self,
        default_settings: Settings,
    ) -> None:
        """Synthetischer Baseline-Kandidat erfüllt alle 9 Regeln.

        Nicht der echte NOW-78 — der bricht 3 Regeln (siehe TestNowRegression).
        """
        passed, reasons = passes_csp_filters(
            HAPPY_CORE,
            HAPPY_STRIKE,
            MacroSnapshot(vix_close=18.7),
            PortfolioSnapshot(),
            default_settings,
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
            core, HAPPY_STRIKE, NOW_MACRO, PortfolioSnapshot(), default_settings
        )
        assert not passed
        assert any("Pflichtregel 9 — Ticker XXX nicht im Universum" in r for r in reasons)

    def test_sector_cap_failure_format(self, default_settings: Settings) -> None:
        portfolio = PortfolioSnapshot(sector_exposures={"Technology": 0.60})
        passed, reasons = passes_csp_filters(
            HAPPY_CORE, HAPPY_STRIKE, NOW_MACRO, portfolio, default_settings
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

    def test_override_bypasses_unknown_earnings_distance(
        self,
        default_settings: Settings,
    ) -> None:
        """Slice-12: ``override=True`` lässt auch den Sentinel-Fail durch.

        Pflichtregel-Invariante respektiert: "unbekannt" failt strikt, aber der
        Override-Pfad (laut Memory routine) bypasst es wie jede andere Regel.
        """
        core = _core(days_to_next_earn=None)
        passed, reasons = passes_csp_filters(
            core,
            HAPPY_STRIKE,
            NOW_MACRO,
            PortfolioSnapshot(),
            default_settings,
            override=True,
        )
        assert passed
        assert any("Earnings-Datum bei Vendor nicht verfügbar" in r for r in reasons)

    def test_override_with_zero_violations_is_silent(
        self,
        default_settings: Settings,
    ) -> None:
        """P11: override=True ohne Verstöße darf keinen WARN emittieren.

        Verwendet den synthetischen HAPPY-Baseline statt des echten NOW-78
        (der 3 Regeln verletzt — kein zero-violation-Fall).
        """
        from loguru import logger

        captured: list[str] = []

        def sink(message: object) -> None:
            captured.append(str(message))

        handler_id = logger.add(sink, level="WARNING", format="{message}")
        try:
            passed, reasons = passes_csp_filters(
                HAPPY_CORE,
                HAPPY_STRIKE,
                MacroSnapshot(vix_close=18.7),
                PortfolioSnapshot(),
                default_settings,
                override=True,
            )
        finally:
            logger.remove(handler_id)
        assert passed
        assert reasons == []
        assert captured == []


@pytest.mark.now_regression
class TestNowRegression:
    """Echter NOW-78 vom 2026-04-24, geladen aus den ORATS-Cassetten.

    Reconciliation: Der ursprüngliche synthetische Fixture (Premium 4,30,
    DTE 55, Earnings in 30 Tagen, Spread 0,04) war über-optimistisch. Real
    bricht NOW-78 zwei Pflichtregeln (3, 6).

    Slice-12-Update: vorher waren es drei Brüche (3, 5, 6). Pflichtregel 5
    (Earnings) galt fälschlich als "heute Earnings" (`daysToNextErn = 0`),
    weil ORATS den Sentinel `nextErn = '0000-00-00'` mit Zero-Fallback
    zurückliefert. Der NOW-Cassette-Datensatz hat aber `wksNextErn = 12`
    (12 Wochen ≈ 84 Tage bis zum nächsten Earnings) — die wahre Distanz
    passiert die 8-Tage-Schwelle problemlos. Der Test dokumentiert jetzt
    die korrigierte Wahrheit.
    """

    EXPECTED_FAILURE_REASONS: ClassVar[list[str]] = [
        "Pflichtregel 3 — DTE 56 außerhalb [30, 55]",
        "Pflichtregel 6 — Liquidität ungenügend: Spread 0,15 USD > 0,05 USD",
    ]

    def test_now_78_real_gate_verdict(
        self,
        default_settings: Settings,
        now_core: OratsCore,
        now_strike: OratsStrike,
        now_macro: MacroSnapshot,
        now_empty_portfolio: PortfolioSnapshot,
    ) -> None:
        """NOW-78 vom 2026-04-24: 3 Regeln scheitern, 6 passieren — exact match."""
        passed, reasons = passes_csp_filters(
            now_core, now_strike, now_macro, now_empty_portfolio, default_settings
        )
        assert not passed
        assert reasons == self.EXPECTED_FAILURE_REASONS, (
            f"Erwartete genau 2 Pflichtregel-Brüche (Slice-12 Earnings-Fix), sah:\n"
            f"  reasons: {reasons}\n"
            f"  expected: {self.EXPECTED_FAILURE_REASONS}"
        )

    def test_now_78_metadata_from_cassette(
        self,
        now_core: OratsCore,
        now_strike: OratsStrike,
    ) -> None:
        """Pinnt die Cassette-Werte (Spot, IVR, Strike, DTE, Spread) für die Reconciliation."""
        # /hist/cores 2026-04-24 — pxAtmIv = 89.84, ivPctile1y = 96
        assert now_core.ticker == "NOW"
        assert now_core.under_price == 89.84
        assert now_core.ivr == 96.0
        # Slice-12: Sentinel-Auflösung — `wksNextErn=12` → 12*7 = 84 Tage.
        # Vor Slice 12 war hier 0 (fälschlich als "heute Earnings" interpretiert).
        assert now_core.days_to_next_earn == 84
        assert now_core.sector == "Technology"
        # /hist/strikes 2026-04-24 — Strike 78, DTE 56, putBid 2.70, putAsk 2.85
        assert now_strike.strike == 78.0
        assert now_strike.dte == 56
        assert now_strike.put_bid == 2.7
        assert now_strike.put_ask == 2.85
        # Put-Delta = call_delta - 1 = 0.779 - 1 ≈ -0.221
        assert -0.23 < now_strike.delta < -0.21


def test_public_reexport_resolves_to_orchestrator() -> None:
    assert csp.passes_csp_filters is passes_csp_filters
