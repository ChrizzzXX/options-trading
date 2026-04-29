"""Tests für `csp.persistence` (Slice 6) — Migrationen, ideas + trades CRUD."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest
from pydantic import SecretStr

from csp import config as csp_config
from csp.config import Settings
from csp.lifecycle.state_machine import TradeStatus
from csp.models.idea import Idea
from csp.models.trade import Trade
from csp.persistence import connection
from csp.persistence.db import _apply_migrations, _list_migrations
from csp.persistence.ideas import get_idea_by_id, insert_idea, list_ideas
from csp.persistence.trades import (
    find_open_trade_by_idea,
    get_trade,
    insert_trade,
    list_open_trades,
    update_trade,
)


@pytest.fixture
def tmp_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, default_settings: Settings
) -> Iterator[Settings]:
    """Settings mit Test-DuckDB-Pfad — pro Test eine frische DB."""
    db_path = tmp_path / "test.duckdb"
    patched = default_settings.model_copy(
        update={
            "orats_token": SecretStr("orats-fake"),
            "duckdb_path": db_path,
        }
    )
    monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
    yield patched


def _sample_idea(
    *,
    ticker: str = "NOW",
    as_of: date = date(2026, 4, 29),
    passed: bool = True,
    bypassed: list[str] | None = None,
    yield_pct: float = 13.92,
) -> Idea:
    return Idea(
        ticker=ticker.upper(),
        strike=Decimal("88.00"),
        dte=45,
        delta=-0.20,
        put_bid=Decimal("1.50"),
        put_ask=Decimal("1.52"),
        mid_premium=Decimal("1.5100"),
        annualized_yield_pct=yield_pct,
        otm_pct=12.0,
        earnings_distance_days=30,
        under_price=100.0,
        iv_rank_1y_pct=80.0,
        current_sector_share_pct=0.0,
        pflichtregeln_passed=passed,
        reasons=[],
        bypassed_rules=bypassed or [],
        as_of=as_of,
        data_freshness="live",
        region="US",
    )


# ---------------------------------------------------------------------------
# Migrations
# ---------------------------------------------------------------------------


class TestMigrations:
    def test_list_migrations_finds_001_initial(self) -> None:
        migrations = _list_migrations()
        assert (1, migrations[0][1]) == (1, migrations[0][1])
        assert migrations[0][1].name == "001_initial.sql"

    def test_first_connection_applies_001(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings) as con:
            applied = con.execute("SELECT version FROM _migrations").fetchall()
        assert applied == [(1,)]

    def test_second_connection_does_not_reapply(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings):
            pass
        with connection(tmp_settings) as con:
            applied = con.execute("SELECT version FROM _migrations ORDER BY version").fetchall()
        assert applied == [(1,)]

    def test_apply_migrations_idempotent_on_existing_db(self, tmp_settings: Settings) -> None:
        # Direkt zweimal `_apply_migrations` aufrufen — keine `UNIQUE`-Violation.
        with duckdb.connect(str(tmp_settings.duckdb_path)) as con:
            _apply_migrations(con)
            _apply_migrations(con)
            count = con.execute("SELECT COUNT(*) FROM _migrations WHERE version = 1").fetchone()
        assert count == (1,)

    def test_memory_db_works(
        self, monkeypatch: pytest.MonkeyPatch, default_settings: Settings
    ) -> None:
        # `:memory:` als Path — kein Verzeichnis erzeugen.
        patched = default_settings.model_copy(
            update={"orats_token": SecretStr("x"), "duckdb_path": Path(":memory:")}
        )
        monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
        with connection(patched) as con:
            con.execute(
                "INSERT INTO ideas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    "id1",
                    "NOW",
                    date(2026, 4, 29),
                    True,
                    0,
                    "US",
                    "live",
                    13.0,
                    _sample_idea().model_dump_json(),
                    datetime.now(UTC),
                ],
            )
            count = con.execute("SELECT COUNT(*) FROM ideas").fetchone()
        assert count == (1,)


# ---------------------------------------------------------------------------
# Ideas CRUD
# ---------------------------------------------------------------------------


class TestIdeasCrud:
    def test_insert_and_round_trip(self, tmp_settings: Settings) -> None:
        idea = _sample_idea()
        with connection(tmp_settings) as con:
            insert_idea(con, idea_id="idea-1", idea=idea)
            loaded = get_idea_by_id(con, "idea-1")
        assert loaded == idea

    def test_get_unknown_returns_none(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings) as con:
            assert get_idea_by_id(con, "does-not-exist") is None

    def test_insert_or_replace_idempotent(self, tmp_settings: Settings) -> None:
        idea = _sample_idea()
        with connection(tmp_settings) as con:
            insert_idea(con, idea_id="idea-1", idea=idea)
            insert_idea(con, idea_id="idea-1", idea=idea)  # zweimal — kein Fehler
            count = con.execute("SELECT COUNT(*) FROM ideas").fetchone()
        assert count == (1,)

    def test_list_ideas_orders_desc_by_as_of(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings) as con:
            insert_idea(con, idea_id="i-old", idea=_sample_idea(as_of=date(2026, 4, 20)))
            insert_idea(
                con,
                idea_id="i-new",
                idea=_sample_idea(ticker="MSFT", as_of=date(2026, 4, 29)),
            )
            insert_idea(con, idea_id="i-mid", idea=_sample_idea(as_of=date(2026, 4, 25)))
            results = list_ideas(con)
        assert [i.as_of for i in results] == [
            date(2026, 4, 29),
            date(2026, 4, 25),
            date(2026, 4, 20),
        ]

    def test_list_ideas_overrides_only(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings) as con:
            insert_idea(con, idea_id="passing", idea=_sample_idea(passed=True))
            insert_idea(
                con,
                idea_id="override",
                idea=_sample_idea(
                    passed=True,  # via override → pflichtregeln_passed=True, bypassed > 0
                    bypassed=["Pflichtregel 5", "Pflichtregel 6"],
                ),
            )
            all_results = list_ideas(con)
            override_only = list_ideas(con, overrides_only=True)
        assert len(all_results) == 2
        assert len(override_only) == 1
        assert override_only[0].bypassed_rules == [
            "Pflichtregel 5",
            "Pflichtregel 6",
        ]

    def test_list_ideas_since_filters(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings) as con:
            insert_idea(con, idea_id="old", idea=_sample_idea(as_of=date(2026, 4, 1)))
            insert_idea(
                con,
                idea_id="new",
                idea=_sample_idea(as_of=date(2026, 4, 29)),
            )
            since_apr15 = list_ideas(con, since=date(2026, 4, 15))
        assert [i.as_of for i in since_apr15] == [date(2026, 4, 29)]


# ---------------------------------------------------------------------------
# Trades CRUD
# ---------------------------------------------------------------------------


class TestTradesCrud:
    def _seed_idea(self, con: duckdb.DuckDBPyConnection, *, idea_id: str = "idea-1") -> str:
        insert_idea(con, idea_id=idea_id, idea=_sample_idea())
        return idea_id

    def _make_trade(
        self,
        *,
        trade_id: str = "trade-1",
        idea_id: str = "idea-1",
        status: TradeStatus = TradeStatus.OPEN,
        contracts: int = 1,
        ticker: str = "NOW",
        open_date: date = date(2026, 4, 29),
    ) -> Trade:
        now = datetime.now(UTC)
        return Trade(
            trade_id=trade_id,
            idea_id=idea_id,
            ticker=ticker,
            status=status,
            contracts=contracts,
            open_date=open_date,
            open_premium=Decimal("1.5100"),
            cash_secured=Decimal("8800.0000"),
            inserted_at=now,
            updated_at=now,
        )

    def test_insert_and_get_round_trip(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings) as con:
            self._seed_idea(con)
            trade = self._make_trade()
            insert_trade(con, trade)
            loaded = get_trade(con, "trade-1")
        assert loaded is not None
        assert loaded.ticker == "NOW"
        assert loaded.status is TradeStatus.OPEN
        assert loaded.open_premium == Decimal("1.5100")

    def test_get_unknown_trade_returns_none(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings) as con:
            assert get_trade(con, "nope") is None

    def test_list_open_trades_filters_by_status(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings) as con:
            self._seed_idea(con)
            insert_trade(con, self._make_trade(trade_id="t-open", status=TradeStatus.OPEN))
            insert_trade(
                con,
                self._make_trade(trade_id="t-tpp", status=TradeStatus.TAKE_PROFIT_PENDING),
            )
            insert_trade(
                con,
                self._make_trade(trade_id="t-closed", status=TradeStatus.CLOSED_PROFIT),
            )
            opens = list_open_trades(con)
        assert {t.trade_id for t in opens} == {"t-open", "t-tpp"}

    def test_list_open_sorted_by_date_then_ticker(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings) as con:
            self._seed_idea(con)
            insert_trade(
                con,
                self._make_trade(
                    trade_id="z-newer-z",
                    open_date=date(2026, 4, 30),
                    ticker="ZTS",
                ),
            )
            insert_trade(
                con,
                self._make_trade(
                    trade_id="a-older-msft",
                    open_date=date(2026, 4, 28),
                    ticker="MSFT",
                ),
            )
            insert_trade(
                con,
                self._make_trade(
                    trade_id="b-older-aapl",
                    open_date=date(2026, 4, 28),
                    ticker="AAPL",
                ),
            )
            opens = list_open_trades(con)
        assert [t.trade_id for t in opens] == [
            "b-older-aapl",  # 4/28 + AAPL
            "a-older-msft",  # 4/28 + MSFT
            "z-newer-z",  # 4/30
        ]

    def test_update_trade_sets_close_fields(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings) as con:
            self._seed_idea(con)
            insert_trade(con, self._make_trade())
            update_trade(
                con,
                trade_id="trade-1",
                new_status=TradeStatus.CLOSED_PROFIT,
                close_date=date(2026, 5, 15),
                close_premium=Decimal("0.5000"),
                pnl=Decimal("101.0000"),
                notes="TP hit",
            )
            updated = get_trade(con, "trade-1")
        assert updated is not None
        assert updated.status is TradeStatus.CLOSED_PROFIT
        assert updated.close_date == date(2026, 5, 15)
        assert updated.close_premium == Decimal("0.5000")
        assert updated.pnl == Decimal("101.0000")
        assert updated.notes == "TP hit"

    def test_find_open_trade_by_idea(self, tmp_settings: Settings) -> None:
        with connection(tmp_settings) as con:
            idea_id = self._seed_idea(con)
            insert_trade(con, self._make_trade(idea_id=idea_id, contracts=2))
            found = find_open_trade_by_idea(con, idea_id, 2)
            not_found = find_open_trade_by_idea(con, idea_id, 7)
        assert found is not None
        assert found.contracts == 2
        assert not_found is None
