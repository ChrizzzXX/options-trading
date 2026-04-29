"""Settings-Loader-Tests: erfolgreiches Laden + ConfigError-Pfade."""

from __future__ import annotations

from pathlib import Path

import pytest

from csp.config import Settings
from csp.exceptions import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.toml"


def test_loads_repo_settings() -> None:
    settings = Settings.load(SETTINGS_PATH)
    # Stichproben aus FR12: Schwellwerte exakt wie in der TOML.
    assert settings.rules.vix_min == 20.0
    assert settings.rules.delta_min == -0.25
    assert settings.rules.delta_max == -0.18
    assert settings.rules.dte_min == 30
    assert settings.rules.dte_max == 55
    assert settings.rules.market_cap_min_billion == 50.0
    assert "NOW" in settings.universe.allowed_tickers


def test_missing_file_raises_config_error(tmp_path: Path) -> None:
    missing = tmp_path / "nope.toml"
    with pytest.raises(ConfigError) as excinfo:
        Settings.load(missing)
    assert str(missing) in str(excinfo.value)


def test_malformed_toml_raises_config_error(tmp_path: Path) -> None:
    bad = tmp_path / "bad.toml"
    bad.write_text("this is = = not valid toml [[[", encoding="utf-8")
    with pytest.raises(ConfigError) as excinfo:
        Settings.load(bad)
    assert "valides TOML" in str(excinfo.value)


def test_missing_required_section_raises_config_error(tmp_path: Path) -> None:
    bad = tmp_path / "incomplete.toml"
    bad.write_text("[rules]\nvix_min = 20.0\n", encoding="utf-8")
    with pytest.raises(ConfigError) as excinfo:
        Settings.load(bad)
    assert str(bad) in str(excinfo.value)
