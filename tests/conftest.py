"""Geteilte Pytest-Fixtures für alle Slices."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from csp.config import Settings
from csp.models.core import MacroSnapshot, PortfolioSnapshot
from csp.models.idea import Idea
from tests.fixtures.now_2026_04_24 import (
    NOW_CORE,
    NOW_MACRO,
    NOW_PORTFOLIO_EMPTY,
    NOW_STRIKE,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.toml"
CASSETTE_DIR = PROJECT_ROOT / "tests" / "cassettes" / "orats"


@pytest.fixture(scope="session")
def vcr_config() -> dict[str, Any]:
    """VCR-Konfiguration: Token-Scrubbing + Replay-only by default.

    Cassettes liegen unter `tests/cassettes/orats/`. Für die einmalige Aufnahme
    wird auf der CLI `--record-mode=once` übergeben (überschreibt `record_mode`
    pro Lauf). Standardlauf bleibt strikt offline.
    """
    return {
        "filter_query_parameters": ["token", "apikey"],
        "cassette_library_dir": str(CASSETTE_DIR),
        "record_mode": "none",
    }


@pytest.fixture(scope="session")
def default_settings() -> Settings:
    """Settings, geladen aus dem Repo-`config/settings.toml`."""
    return Settings.load(SETTINGS_PATH)


@pytest.fixture
def empty_portfolio() -> PortfolioSnapshot:
    return PortfolioSnapshot(sector_exposures={})


@pytest.fixture
def macro_vix_18_7() -> MacroSnapshot:
    """Makro-Snapshot mit ruhigem VIX (Pflichtregel 1 darf nur via IVR-Leg passen)."""
    return MacroSnapshot(vix_close=18.7)


@pytest.fixture
def now_core() -> object:
    return NOW_CORE


@pytest.fixture
def now_strike() -> object:
    return NOW_STRIKE


@pytest.fixture
def now_macro() -> object:
    return NOW_MACRO


@pytest.fixture
def now_empty_portfolio() -> object:
    return NOW_PORTFOLIO_EMPTY


@pytest.fixture
def make_idea() -> Callable[..., Idea]:
    """Factory für synthetische `Idea`-Objekte zur Sort-/Filter-Test-Verifikation.

    Erlaubt es Tests, deterministische Ranking-Annahmen ohne HTTP zu verifizieren.
    Default-Felder produzieren ein plausibles Pass-Idea; nur `ticker` und
    `yield_pct` sind Caller-relevant. (Patch F6+A3 aus Slice-4-Review:
    `sector`-Parameter wurde entfernt — er wurde im Modell nie benutzt und
    versprach eine Anpassbarkeit, die nicht existierte.)
    """

    def _factory(
        ticker: str,
        yield_pct: float,
        *,
        passed: bool = True,
    ) -> Idea:
        return Idea(
            ticker=ticker.upper(),
            strike=Decimal("100.00"),
            dte=45,
            delta=-0.20,
            put_bid=Decimal("1.50"),
            put_ask=Decimal("1.60"),
            mid_premium=Decimal("1.5500"),
            annualized_yield_pct=yield_pct,
            otm_pct=10.0,
            earnings_distance_days=30,
            sector="Technology",
            under_price=110.0,
            iv_rank_1y_pct=80.0,
            current_sector_share_pct=0.0,
            pflichtregeln_passed=passed,
            reasons=[] if passed else ["Pflichtregel X — synthetischer Fail"],
            bypassed_rules=[],
            as_of=date(2026, 4, 29),
            data_freshness="live",
            region="US",
        )

    return _factory
