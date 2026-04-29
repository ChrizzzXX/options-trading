"""End-to-end Tests für `csp.log_idea`/`log_trade`/`close_trade`/
`list_open_positions`/`get_idea`/`list_ideas` (Slice 6)."""

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
from csp.exceptions import LifecycleError
from csp.lifecycle.state_machine import TradeStatus
from csp.models.idea import Idea


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


def _idea(
    *,
    ticker: str = "NOW",
    as_of: date = date(2026, 4, 29),
    strike: float = 88.0,
    mid_premium: str = "1.5100",
    bypassed: list[str] | None = None,
    yield_pct: float = 13.92,
) -> Idea:
    return Idea(
        ticker=ticker,
        strike=Decimal(str(strike)),
        dte=45,
        delta=-0.20,
        put_bid=Decimal("1.50"),
        put_ask=Decimal("1.52"),
        mid_premium=Decimal(mid_premium),
        annualized_yield_pct=yield_pct,
        otm_pct=12.0,
        earnings_distance_days=30,
        sector="Technology",
        under_price=100.0,
        iv_rank_1y_pct=80.0,
        current_sector_share_pct=0.0,
        pflichtregeln_passed=not bypassed,
        reasons=[],
        bypassed_rules=bypassed or [],
        as_of=as_of,
        data_freshness="live",
        region="US",
    )


# ---------------------------------------------------------------------------
# log_idea
# ---------------------------------------------------------------------------


class TestLogIdea:
    def test_passing_idea_persists_returns_uuid(self, tmp_settings: Settings) -> None:
        idea_id = csp.log_idea(_idea())
        assert isinstance(idea_id, str)
        assert len(idea_id) == 36  # UUID4 string

    def test_override_idea_persists_with_bypass_count(self, tmp_settings: Settings) -> None:
        idea_id = csp.log_idea(_idea(bypassed=["Pflichtregel 5", "Pflichtregel 6"]))
        all_ideas = csp.list_ideas()
        assert len(all_ideas) == 1
        only_overrides = csp.list_ideas(overrides_only=True)
        assert [i.bypassed_rules for i in only_overrides] == [["Pflichtregel 5", "Pflichtregel 6"]]
        assert idea_id  # non-empty


# ---------------------------------------------------------------------------
# log_trade
# ---------------------------------------------------------------------------


class TestLogTrade:
    def test_log_trade_creates_open_position(self, tmp_settings: Settings) -> None:
        trade = csp.log_trade(_idea(), contracts=2, notes="initial")
        assert trade.status is TradeStatus.OPEN
        assert trade.contracts == 2
        assert trade.notes == "initial"
        # cash_secured = 88 * 2 * 100 = 17600
        assert trade.cash_secured == Decimal("17600.0000")
        assert trade.open_premium == Decimal("1.5100")

    def test_log_trade_idempotent_on_rerun(self, tmp_settings: Settings) -> None:
        idea = _idea()
        first = csp.log_trade(idea, contracts=1)
        second = csp.log_trade(idea, contracts=1)
        assert first.trade_id == second.trade_id
        assert len(csp.list_open_positions()) == 1

    def test_log_trade_different_contracts_creates_separate(self, tmp_settings: Settings) -> None:
        idea = _idea()
        t1 = csp.log_trade(idea, contracts=1)
        t2 = csp.log_trade(idea, contracts=3)
        assert t1.trade_id != t2.trade_id
        assert {t.contracts for t in csp.list_open_positions()} == {1, 3}

    def test_log_trade_zero_contracts_raises(self, tmp_settings: Settings) -> None:
        with pytest.raises(LifecycleError, match="contracts muss > 0"):
            csp.log_trade(_idea(), contracts=0)

    def test_log_trade_negative_contracts_raises(self, tmp_settings: Settings) -> None:
        with pytest.raises(LifecycleError, match="contracts muss > 0"):
            csp.log_trade(_idea(), contracts=-1)


# ---------------------------------------------------------------------------
# close_trade
# ---------------------------------------------------------------------------


class TestCloseTrade:
    def test_close_to_profit_computes_pnl(self, tmp_settings: Settings) -> None:
        trade = csp.log_trade(_idea(), contracts=1)
        closed = csp.close_trade(
            trade.trade_id,
            new_status=TradeStatus.CLOSED_PROFIT,
            close_premium=Decimal("0.5000"),
            close_date_value=date(2026, 5, 15),
        )
        # PnL = (1.51 - 0.50) * 1 * 100 = 101.00
        assert closed.status is TradeStatus.CLOSED_PROFIT
        assert closed.pnl == Decimal("101.0000")
        assert closed.close_date == date(2026, 5, 15)

    def test_close_to_loss_computes_pnl(self, tmp_settings: Settings) -> None:
        trade = csp.log_trade(_idea(mid_premium="1.0000"), contracts=2)
        closed = csp.close_trade(
            trade.trade_id,
            new_status=TradeStatus.CLOSED_LOSS,
            close_premium=Decimal("3.0000"),
        )
        # PnL = (1.00 - 3.00) * 2 * 100 = -400.00
        assert closed.status is TradeStatus.CLOSED_LOSS
        assert closed.pnl == Decimal("-400.0000")

    def test_close_to_assigned_pnl_none(self, tmp_settings: Settings) -> None:
        trade = csp.log_trade(_idea())
        closed = csp.close_trade(trade.trade_id, new_status=TradeStatus.ASSIGNED)
        assert closed.status is TradeStatus.ASSIGNED
        assert closed.pnl is None
        assert closed.close_date is not None  # heute

    def test_close_to_emergency_close_computes_pnl(self, tmp_settings: Settings) -> None:
        trade = csp.log_trade(_idea(), contracts=1)
        closed = csp.close_trade(
            trade.trade_id,
            new_status=TradeStatus.EMERGENCY_CLOSE,
            close_premium=Decimal("2.0000"),
        )
        # Negativ — Emergency-Close oft mit Verlust.
        assert closed.pnl == Decimal("-49.0000")

    def test_close_to_take_profit_pending_no_pnl(self, tmp_settings: Settings) -> None:
        trade = csp.log_trade(_idea())
        intermediate = csp.close_trade(trade.trade_id, new_status=TradeStatus.TAKE_PROFIT_PENDING)
        assert intermediate.status is TradeStatus.TAKE_PROFIT_PENDING
        assert intermediate.pnl is None
        assert intermediate.close_date is None

    def test_take_profit_pending_then_close(self, tmp_settings: Settings) -> None:
        trade = csp.log_trade(_idea(), contracts=1)
        csp.close_trade(trade.trade_id, new_status=TradeStatus.TAKE_PROFIT_PENDING)
        # Jetzt ist die einzige erlaubte Folge: TPP → CLOSED_PROFIT.
        closed = csp.close_trade(
            trade.trade_id,
            new_status=TradeStatus.CLOSED_PROFIT,
            close_premium=Decimal("0.5000"),
        )
        assert closed.status is TradeStatus.CLOSED_PROFIT
        assert closed.pnl == Decimal("101.0000")

    def test_invalid_transition_raises_no_db_write(self, tmp_settings: Settings) -> None:
        trade = csp.log_trade(_idea())
        # ASSIGNED → CLOSED_PROFIT ist verboten.
        csp.close_trade(trade.trade_id, new_status=TradeStatus.ASSIGNED)
        with pytest.raises(LifecycleError, match="ungültiger Übergang"):
            csp.close_trade(
                trade.trade_id,
                new_status=TradeStatus.CLOSED_PROFIT,
                close_premium=Decimal("0.50"),
            )
        # Status nach abgewiesenem Close: immer noch ASSIGNED.
        opens = csp.list_open_positions()
        assert all(t.trade_id != trade.trade_id for t in opens)

    def test_close_unknown_trade_raises(self, tmp_settings: Settings) -> None:
        with pytest.raises(LifecycleError, match="trade nicht gefunden"):
            csp.close_trade(
                "does-not-exist",
                new_status=TradeStatus.CLOSED_PROFIT,
                close_premium=Decimal("0.50"),
            )

    def test_close_profit_without_premium_raises(self, tmp_settings: Settings) -> None:
        trade = csp.log_trade(_idea())
        with pytest.raises(LifecycleError, match="close_premium ist Pflicht"):
            csp.close_trade(trade.trade_id, new_status=TradeStatus.CLOSED_PROFIT)


# ---------------------------------------------------------------------------
# list_open_positions
# ---------------------------------------------------------------------------


class TestListOpenPositions:
    def test_empty_db(self, tmp_settings: Settings) -> None:
        assert csp.list_open_positions() == []

    def test_filters_to_open_and_take_profit_pending(self, tmp_settings: Settings) -> None:
        t_now = csp.log_trade(_idea(ticker="NOW"))
        t_msft = csp.log_trade(_idea(ticker="MSFT"))
        # NOW → CLOSED_PROFIT; MSFT → TAKE_PROFIT_PENDING.
        csp.close_trade(
            t_now.trade_id,
            new_status=TradeStatus.CLOSED_PROFIT,
            close_premium=Decimal("0.5000"),
        )
        csp.close_trade(t_msft.trade_id, new_status=TradeStatus.TAKE_PROFIT_PENDING)
        opens = csp.list_open_positions()
        assert {t.trade_id for t in opens} == {t_msft.trade_id}

    def test_sort_by_date_then_ticker(self, tmp_settings: Settings) -> None:
        # Drei Trades, zwei am gleichen Tag.
        csp.log_trade(_idea(ticker="MSFT", as_of=date(2026, 4, 28)))
        csp.log_trade(_idea(ticker="AAPL", as_of=date(2026, 4, 28)))
        csp.log_trade(_idea(ticker="ZTS", as_of=date(2026, 4, 30)))
        opens = csp.list_open_positions()
        assert [t.ticker for t in opens] == ["AAPL", "MSFT", "ZTS"]


# ---------------------------------------------------------------------------
# get_idea
# ---------------------------------------------------------------------------


class TestGetIdea:
    def test_returns_original_idea(self, tmp_settings: Settings) -> None:
        original = _idea()
        trade = csp.log_trade(original)
        retrieved = csp.get_idea(trade.trade_id)
        assert retrieved == original

    def test_unknown_trade_raises(self, tmp_settings: Settings) -> None:
        with pytest.raises(LifecycleError, match="trade nicht gefunden"):
            csp.get_idea("does-not-exist")


# ---------------------------------------------------------------------------
# list_ideas
# ---------------------------------------------------------------------------


class TestListIdeas:
    def test_empty(self, tmp_settings: Settings) -> None:
        assert csp.list_ideas() == []

    def test_orders_desc_by_as_of(self, tmp_settings: Settings) -> None:
        csp.log_idea(_idea(as_of=date(2026, 4, 20)))
        csp.log_idea(_idea(as_of=date(2026, 4, 29), ticker="MSFT"))
        csp.log_idea(_idea(as_of=date(2026, 4, 25), ticker="AAPL"))
        results = csp.list_ideas()
        assert [(i.as_of, i.ticker) for i in results] == [
            (date(2026, 4, 29), "MSFT"),
            (date(2026, 4, 25), "AAPL"),
            (date(2026, 4, 20), "NOW"),
        ]

    def test_overrides_only(self, tmp_settings: Settings) -> None:
        csp.log_idea(_idea())  # passing
        csp.log_idea(_idea(bypassed=["Pflichtregel 1"]))
        only_overrides = csp.list_ideas(overrides_only=True)
        assert len(only_overrides) == 1
        assert only_overrides[0].bypassed_rules == ["Pflichtregel 1"]

    def test_since_filter(self, tmp_settings: Settings) -> None:
        csp.log_idea(_idea(as_of=date(2026, 4, 1)))
        csp.log_idea(_idea(as_of=date(2026, 4, 29)))
        recent = csp.list_ideas(since=date(2026, 4, 15))
        assert [i.as_of for i in recent] == [date(2026, 4, 29)]


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


class TestPublicSurface:
    def test_all_lifecycle_exports(self) -> None:
        for name in (
            "log_idea",
            "log_trade",
            "close_trade",
            "list_open_positions",
            "get_idea",
            "list_ideas",
            "Trade",
            "TradeStatus",
            "LifecycleError",
            "IdempotencyError",
        ):
            assert name in csp.__all__
            assert getattr(csp, name) is not None
