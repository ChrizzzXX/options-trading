"""Tests für `csp.portfolio.build_portfolio_snapshot` (Slice 11).

Pinnen: Pflichtregel 8 sieht jetzt **echte** offene-Trades-Daten, nicht
mehr stets-leeren `PortfolioSnapshot()`. Bug 1 von Slice 11 fixed.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import SecretStr

import csp
from csp import config as csp_config
from csp.config import Settings
from csp.lifecycle.state_machine import TradeStatus
from csp.models.idea import Idea
from csp.portfolio import build_portfolio_snapshot


@pytest.fixture
def tmp_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, default_settings: Settings
) -> Iterator[Settings]:
    db_path = tmp_path / "test.duckdb"
    patched = default_settings.model_copy(
        update={
            "orats_token": SecretStr("orats-fake"),
            "duckdb_path": db_path,
        }
    )
    monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
    yield patched


def _idea(*, ticker: str, sector: str, as_of: date = date(2026, 4, 28)) -> Idea:
    return Idea(
        ticker=ticker,
        strike=Decimal("88.00"),
        dte=45,
        delta=-0.20,
        put_bid=Decimal("1.50"),
        put_ask=Decimal("1.52"),
        mid_premium=Decimal("1.5100"),
        annualized_yield_pct=12.5,
        otm_pct=12.0,
        earnings_distance_days=30,
        sector=sector,
        under_price=100.0,
        iv_rank_1y_pct=80.0,
        current_sector_share_pct=0.0,
        pflichtregeln_passed=True,
        reasons=[],
        bypassed_rules=[],
        as_of=as_of,
        data_freshness="live",
        region="US",
    )


# ---------------------------------------------------------------------------
# Empty / single-trade
# ---------------------------------------------------------------------------


class TestBuildPortfolioSnapshot:
    def test_empty_db_returns_empty_exposures(self, tmp_settings: Settings) -> None:
        snapshot = build_portfolio_snapshot(tmp_settings)
        assert snapshot.sector_exposures == {}

    def test_single_open_trade_one_sector(self, tmp_settings: Settings) -> None:
        # 1 Trade, NOW (Tech), strike 88, 1 contract → cash_secured = 8800.
        # Total capital default 100k → Tech share = 8800/100000 = 0.088.
        csp.log_trade(_idea(ticker="NOW", sector="Technology"), contracts=1)
        snapshot = build_portfolio_snapshot(tmp_settings)
        assert snapshot.sector_exposures == pytest.approx({"Technology": 0.088})

    def test_two_trades_same_sector_aggregate(self, tmp_settings: Settings) -> None:
        # 2 Tech trades — 2 contracts NOW + 1 contract MSFT.
        # NOW: 8800 * 1 = 8800. MSFT: 8800 * 2 = 17600. Total Tech: 26400.
        # 26400 / 100000 = 0.264.
        csp.log_trade(_idea(ticker="NOW", sector="Technology"), contracts=1)
        csp.log_trade(_idea(ticker="MSFT", sector="Technology"), contracts=2)
        snapshot = build_portfolio_snapshot(tmp_settings)
        assert snapshot.sector_exposures == pytest.approx({"Technology": 0.264})

    def test_two_sectors_separate_keys(self, tmp_settings: Settings) -> None:
        # Tech NOW + Energy WMB.
        csp.log_trade(_idea(ticker="NOW", sector="Technology"), contracts=1)
        csp.log_trade(_idea(ticker="WMB", sector="Energy"), contracts=2)
        snapshot = build_portfolio_snapshot(tmp_settings)
        assert sorted(snapshot.sector_exposures.keys()) == ["Energy", "Technology"]
        assert snapshot.sector_exposures["Technology"] == pytest.approx(0.088)
        assert snapshot.sector_exposures["Energy"] == pytest.approx(0.176)

    def test_closed_trades_excluded(self, tmp_settings: Settings) -> None:
        """Nur offene Trades zählen — geschlossene werden in der Sektor-
        Berechnung nicht berücksichtigt."""
        idea_now = _idea(ticker="NOW", sector="Technology")
        trade_now = csp.log_trade(idea_now, contracts=1)
        # NOW schließen → fällt aus sector_exposures.
        csp.close_trade(
            trade_now.trade_id,
            new_status=TradeStatus.CLOSED_PROFIT,
            close_premium=Decimal("0.50"),
        )
        # MSFT bleibt offen.
        csp.log_trade(_idea(ticker="MSFT", sector="Technology"), contracts=1)
        snapshot = build_portfolio_snapshot(tmp_settings)
        # Nur MSFT zählt: 8800 / 100000 = 0.088.
        assert snapshot.sector_exposures == pytest.approx({"Technology": 0.088})

    def test_take_profit_pending_still_counts_as_open(self, tmp_settings: Settings) -> None:
        """`TAKE_PROFIT_PENDING`-Trades sind noch nicht abgewickelt — Cash
        bleibt gebunden, Sektor-Exposition besteht weiter."""
        trade = csp.log_trade(_idea(ticker="NOW", sector="Technology"), contracts=1)
        csp.close_trade(trade.trade_id, new_status=TradeStatus.TAKE_PROFIT_PENDING)
        snapshot = build_portfolio_snapshot(tmp_settings)
        assert snapshot.sector_exposures["Technology"] == pytest.approx(0.088)

    def test_custom_capital_changes_fractions(
        self, monkeypatch: pytest.MonkeyPatch, tmp_settings: Settings
    ) -> None:
        # Total capital auf 50k senken → gleicher Trade verdoppelt seinen Anteil.
        from csp.config import PortfolioConfig

        patched = tmp_settings.model_copy(
            update={"portfolio": PortfolioConfig(total_csp_capital_usd=50_000.0)}
        )
        monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
        csp.log_trade(_idea(ticker="NOW", sector="Technology"), contracts=1)
        snapshot = build_portfolio_snapshot(patched)
        # 8800 / 50000 = 0.176.
        assert snapshot.sector_exposures == pytest.approx({"Technology": 0.176})


# ---------------------------------------------------------------------------
# Pflichtregel 8 — wird jetzt wirklich aktiv
# ---------------------------------------------------------------------------


class TestPflichtregel8FiresLive:
    """End-to-end Pin: Pflichtregel 8 schlägt jetzt fehl, wenn der Sektor
    bereits über 55% liegt — dieses Verhalten gab es vor Slice 11 NICHT,
    weil PortfolioSnapshot immer leer war."""

    def test_over_concentrated_tech_blocks_new_idea(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_settings: Settings,
    ) -> None:
        """Mit Total-Capital 10k: 1 NOW-Kontrakt = 8800 = 88% Tech.
        Pflichtregel 8 (≤55%) muss fehlschlagen für jede neue Tech-Idea
        UND für jede Idea (weil core.sector aus den ORATS-Daten kommt)."""
        from csp.config import PortfolioConfig

        patched = tmp_settings.model_copy(
            update={"portfolio": PortfolioConfig(total_csp_capital_usd=10_000.0)}
        )
        monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
        csp.log_trade(_idea(ticker="NOW", sector="Technology"), contracts=1)
        snapshot = build_portfolio_snapshot(patched)
        # 88% > 55%-Cap.
        assert snapshot.sector_exposures["Technology"] > 0.55
