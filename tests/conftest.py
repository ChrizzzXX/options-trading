"""Geteilte Pytest-Fixtures für alle Slices."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from csp.config import Settings
from csp.models.core import MacroSnapshot, PortfolioSnapshot
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
