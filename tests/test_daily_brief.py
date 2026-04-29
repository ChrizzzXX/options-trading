"""Tests für `csp.daily_brief()` und `DailyBrief.to_markdown()` (Slice 7)."""

from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import UTC, date
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx
from pydantic import SecretStr

import csp
from csp import config as csp_config
from csp.config import Settings
from csp.models.core import MacroSnapshot
from csp.models.daily_brief import DailyBrief
from csp.models.idea import Idea
from csp.models.trade import Trade

ORATS_BASE = "https://api.orats.io/datav2"
FMP_BASE = "https://financialmodelingprep.com"


@pytest.fixture
def stub_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    default_settings: Settings,
) -> Iterator[Settings]:
    db_path = tmp_path / "test.duckdb"
    patched = default_settings.model_copy(
        update={
            "orats_token": SecretStr("orats-fake"),
            "orats_base_url": ORATS_BASE,
            "fmp_key": SecretStr(""),  # no FMP — fallback to settings
            "fmp_base_url": FMP_BASE,
            "duckdb_path": db_path,
            "universe": default_settings.universe.model_copy(update={"allowed_tickers": ["NOW"]}),
        }
    )
    monkeypatch.setattr(csp_config.Settings, "load", classmethod(lambda cls, *a, **kw: patched))
    yield patched


def _passing_now_cores() -> dict[str, Any]:
    return {
        "data": [
            {
                "ticker": "NOW",
                "pxAtmIv": 100.0,
                "sectorName": "Technology",
                "mktCap": 100_000_000.0,
                "ivPctile1y": 80.0,
                "daysToNextErn": 30,
                "avgOptVolu20d": 120_000.0,
            }
        ]
    }


def _passing_now_strikes() -> dict[str, Any]:
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


# ---------------------------------------------------------------------------
# Daily-Brief — Komposition
# ---------------------------------------------------------------------------


class TestDailyBrief:
    def test_empty_state_returns_macro_only(self, stub_settings: Settings) -> None:
        """Frische DB, kein Trade, ein Pass-Idea via Scan."""
        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/cores")).mock(
                return_value=httpx.Response(200, json=_passing_now_cores())
            )
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/strikes")).mock(
                return_value=httpx.Response(200, json=_passing_now_strikes())
            )
            brief = csp.daily_brief()

        assert isinstance(brief, DailyBrief)
        assert brief.macro.vix_close == stub_settings.macro.vix_close
        assert brief.open_positions == []
        assert len(brief.ranked_ideas) == 1
        assert brief.ranked_ideas[0].ticker == "NOW"

    def test_with_open_position(self, stub_settings: Settings) -> None:
        # Eine offene Position eröffnen, dann brief generieren.
        idea = _idea_for_log(ticker="NOW", as_of=date(2026, 4, 28))
        csp.log_trade(idea, contracts=1)

        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/cores")).mock(
                return_value=httpx.Response(200, json=_passing_now_cores())
            )
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/strikes")).mock(
                return_value=httpx.Response(200, json=_passing_now_strikes())
            )
            brief = csp.daily_brief()

        assert len(brief.open_positions) == 1
        assert brief.open_positions[0].ticker == "NOW"

    def test_max_ideas_zero_raises(self, stub_settings: Settings) -> None:
        with pytest.raises(ValueError, match="max_ideas muss > 0"):
            csp.daily_brief(max_ideas=0)


def _idea_for_log(*, ticker: str, as_of: date) -> Idea:
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
        sector="Technology",
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
# Action-Heuristiken
# ---------------------------------------------------------------------------


class TestActions:
    def test_override_position_surfaces_action(self, stub_settings: Settings) -> None:
        # Override-Idea via log_trade → action sollte erscheinen.
        override_idea = _idea_for_log(ticker="NOW", as_of=date(2026, 4, 28)).model_copy(
            update={"bypassed_rules": ["Pflichtregel 5"], "pflichtregeln_passed": True}
        )
        csp.log_trade(override_idea)
        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/cores")).mock(
                return_value=httpx.Response(200, json=_passing_now_cores())
            )
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/strikes")).mock(
                return_value=httpx.Response(200, json=_passing_now_strikes())
            )
            brief = csp.daily_brief()
        assert any("Override-Trade" in a for a in brief.actions)

    def test_open_position_with_imminent_earnings_warns(self, stub_settings: Settings) -> None:
        """Slice-11 Bug 2 fix: offene Position mit `daysToNextErn` ≤ 7 → WARN.

        Vorher: keine Heuristik gegen offene Positionen vor Earnings — die
        emergency-close-Logik aus project-context.md hat nie gefeuert.
        """
        csp.log_trade(_idea_for_log(ticker="NOW", as_of=date(2026, 4, 28)))
        # `daysToNextErn=3` — innerhalb der 7-Tage-emergency-close-Zone.
        cores_imminent = {
            "data": [
                {
                    "ticker": "NOW",
                    "pxAtmIv": 100.0,
                    "sectorName": "Technology",
                    "mktCap": 100_000_000.0,
                    "ivPctile1y": 80.0,
                    "daysToNextErn": 3,
                    "avgOptVolu20d": 120_000.0,
                }
            ]
        }
        with respx.mock(assert_all_called=False) as router:
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/cores")).mock(
                return_value=httpx.Response(200, json=cores_imminent)
            )
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/strikes")).mock(
                return_value=httpx.Response(200, json=_passing_now_strikes())
            )
            brief = csp.daily_brief()
        assert any("Earnings in 3 Tagen" in a and "emergency-close" in a for a in brief.actions)

    def test_open_position_with_distant_earnings_no_warn(self, stub_settings: Settings) -> None:
        """daysToNextErn = 30 → keine emergency-close-WARN."""
        csp.log_trade(_idea_for_log(ticker="NOW", as_of=date(2026, 4, 28)))
        with respx.mock(assert_all_called=True) as router:
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/cores")).mock(
                return_value=httpx.Response(200, json=_passing_now_cores())
            )
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/strikes")).mock(
                return_value=httpx.Response(200, json=_passing_now_strikes())
            )
            brief = csp.daily_brief()
        assert not any("emergency-close" in a for a in brief.actions)

    def test_open_position_with_unknown_earnings_no_warn(self, stub_settings: Settings) -> None:
        """Slice-12: ORATS-Sentinel auf einer offenen Position → kein
        spurious emergency-close-WARN.

        Vorher: ``nextErn='0000-00-00'`` führte zu ``daysToNextErn=0`` und
        damit zu einer falschen "Earnings in 0 Tagen — emergency-close"-
        Warnung jeden Tag, an dem ORATS den Sentinel zurückliefert. Mit der
        Slice-12-Sentinel-Erkennung wird ``days_to_next_earn`` zu ``None``
        (oder ``wksNextErn * 7``), und der ``days_left is not None``-Guard
        in ``_compute_actions`` schluckt den ersten Fall still.
        """
        csp.log_trade(_idea_for_log(ticker="NOW", as_of=date(2026, 4, 28)))
        # Sentinel-Payload: nextErn = '0000-00-00', wksNextErn = 0.
        cores_sentinel = {
            "data": [
                {
                    "ticker": "NOW",
                    "pxAtmIv": 100.0,
                    "sectorName": "Technology",
                    "mktCap": 100_000_000.0,
                    "ivPctile1y": 80.0,
                    "daysToNextErn": 0,
                    "nextErn": "0000-00-00",
                    "wksNextErn": 0,
                    "avgOptVolu20d": 120_000.0,
                }
            ]
        }
        with respx.mock(assert_all_called=False) as router:
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/cores")).mock(
                return_value=httpx.Response(200, json=cores_sentinel)
            )
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/strikes")).mock(
                return_value=httpx.Response(200, json=_passing_now_strikes())
            )
            brief = csp.daily_brief()
        # Kein emergency-close-WARN — Sentinel wurde stillschweigend ignoriert.
        assert not any("emergency-close" in a for a in brief.actions)

    def test_orats_failure_for_open_position_skips_earnings_warn(
        self, stub_settings: Settings
    ) -> None:
        """Wenn ORATS für eine offene Position 4xx liefert: kein WARN-Log,
        keine Action — kein Hard-Fail des `daily_brief`."""
        csp.log_trade(_idea_for_log(ticker="NOW", as_of=date(2026, 4, 28)))
        # 1. ORATS-Aufruf (für scan) liefert OK; 2. Aufruf (earnings-fetch
        # für offene Positionen) liefert 404. respx hat eine Route je
        # Aufruf — wir müssen `side_effect` benutzen.
        scan_cores = httpx.Response(200, json=_passing_now_cores())
        earnings_404 = httpx.Response(404, text="not found")
        responses = iter([scan_cores, earnings_404])
        with respx.mock(assert_all_called=False) as router:
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/cores")).mock(
                side_effect=lambda req: next(responses)
            )
            router.get(re.compile(rf"^{re.escape(ORATS_BASE)}/strikes")).mock(
                return_value=httpx.Response(200, json=_passing_now_strikes())
            )
            brief = csp.daily_brief()
        # Kein emergency-close-WARN da Earnings-Distance unbekannt.
        assert not any("emergency-close" in a for a in brief.actions)
        # Daily-Brief hat trotzdem normal komplettiert.
        assert isinstance(brief, DailyBrief)


# ---------------------------------------------------------------------------
# DailyBrief.to_markdown
# ---------------------------------------------------------------------------


class TestToMarkdown:
    def test_empty_state_renders(self) -> None:
        brief = DailyBrief(
            as_of=date(2026, 4, 29),
            macro=MacroSnapshot(vix_close=18.7),
        )
        md = brief.to_markdown()
        assert "# CSP DAILY BRIEF — 29.04.2026" in md
        assert "## Makro" in md
        assert "VIX: 18,70 %" in md
        assert "Offene Positionen (0)" in md
        assert "_keine offenen Positionen_" in md
        assert "Top-Ideen heute (0)" in md
        assert "_keine Pflichtregeln-bestandenen Kandidaten_" in md

    def test_full_state_renders(self) -> None:
        from datetime import datetime

        idea = _idea_for_log(ticker="NOW", as_of=date(2026, 4, 29))
        trade = Trade(
            trade_id="t1",
            idea_id="i1",
            ticker="NOW",
            status=csp.TradeStatus.OPEN,
            contracts=1,
            open_date=date(2026, 4, 28),
            open_premium=Decimal("1.5100"),
            cash_secured=Decimal("8800.0000"),
            inserted_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        brief = DailyBrief(
            as_of=date(2026, 4, 29),
            macro=MacroSnapshot(vix_close=22.0),
            open_positions=[trade],
            ranked_ideas=[idea],
            actions=["⚠ NOW: Earnings-Warnung", "ℹ Override-Trade aktiv"],  # noqa: RUF001
        )
        md = brief.to_markdown()
        # Tabelle für offene Positionen.
        assert "| Ticker | Strike | Open-Date | Status | Prämie offen |" in md
        assert "| NOW | 88,00 USD | 28.04.2026 | open | 1,51 USD |" in md
        # Tabelle für ranked ideas.
        assert "| Ticker | IVR | DTE | Strike | Δ | Ann.Yield |" in md
        assert "| NOW | 80 % | 45 | 88,00 USD | -0,20 | 12,5 % |" in md
        # Actions.
        assert "## Aktionen" in md
        assert "⚠ NOW: Earnings-Warnung" in md
        assert "ℹ Override-Trade aktiv" in md  # noqa: RUF001


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


class TestPublicSurface:
    def test_daily_brief_and_DailyBrief_exported(self) -> None:
        assert "daily_brief" in csp.__all__
        assert "DailyBrief" in csp.__all__
        assert csp.DailyBrief is DailyBrief
