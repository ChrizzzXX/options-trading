"""Settings-Loader-Tests: erfolgreiches Laden + ConfigError-Pfade + Validator-Hygiene."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from csp.config import RuleThresholds, Settings, UniverseConfig
from csp.exceptions import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.toml"


_VALID_RULES_KW: dict[str, object] = {
    "vix_min": 20.0,
    "ivr_min": 40.0,
    "delta_min": -0.25,
    "delta_max": -0.18,
    "dte_min": 30,
    "dte_max": 55,
    "strike_otm_min_pct": 8.0,
    "earnings_min_days": 8,
    "options_volume_min": 50_000,
    "spread_max_usd": 0.05,
    "market_cap_min_billion": 50.0,
    "sector_cap_pct": 55.0,
}


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


# ---------- P1: RuleThresholds ordering / sign validators ----------


class TestRuleThresholdsValidator:
    def test_inverted_delta_band_rejected(self) -> None:
        """delta_min muss < delta_max sein; vertauschte Werte → ValidationError."""
        with pytest.raises(ValidationError) as excinfo:
            RuleThresholds(**{**_VALID_RULES_KW, "delta_min": -0.18, "delta_max": -0.25})
        assert "delta_min" in str(excinfo.value)

    def test_delta_max_positive_rejected(self) -> None:
        """delta_max <= 0 (Put-Delta darf nicht positiv werden)."""
        with pytest.raises(ValidationError):
            RuleThresholds(**{**_VALID_RULES_KW, "delta_max": 0.05})

    def test_inverted_dte_window_rejected(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            RuleThresholds(**{**_VALID_RULES_KW, "dte_min": 55, "dte_max": 30})
        assert "dte_min" in str(excinfo.value)

    @pytest.mark.parametrize(
        ("field", "bad_value"),
        [
            ("vix_min", -1.0),
            ("ivr_min", -0.1),
            ("strike_otm_min_pct", -5.0),
            ("earnings_min_days", -1),
            ("options_volume_min", -100),
            ("spread_max_usd", 0.0),
            ("spread_max_usd", -0.01),
            ("market_cap_min_billion", 0.0),
            ("market_cap_min_billion", -10.0),
            ("sector_cap_pct", 0.0),
            ("sector_cap_pct", 100.01),
            ("sector_cap_pct", -1.0),
        ],
    )
    def test_individual_field_constraints(self, field: str, bad_value: float) -> None:
        with pytest.raises(ValidationError) as excinfo:
            RuleThresholds(**{**_VALID_RULES_KW, field: bad_value})
        assert field in str(excinfo.value)

    def test_extra_key_rejected(self) -> None:
        """P6: extra='forbid' fängt Tippfehler wie `vix_mn` statt `vix_min`."""
        with pytest.raises(ValidationError):
            RuleThresholds(**{**_VALID_RULES_KW, "vix_mn": 99.0})


# ---------- P6/P8/P9: UniverseConfig ----------


class TestUniverseConfig:
    def test_empty_allowed_tickers_rejected(self) -> None:
        """P8: Leere Universumsliste muss scheitern (allowed_tickers min_length=1)."""
        with pytest.raises(ValidationError):
            UniverseConfig(allowed_tickers=[])

    def test_tickers_uppercased(self) -> None:
        """P9: Ticker werden case-insensitiv normalisiert."""
        cfg = UniverseConfig(allowed_tickers=["now", "AAPL", "msFT"])
        assert cfg.allowed_tickers == ["NOW", "AAPL", "MSFT"]

    def test_extra_key_rejected(self) -> None:
        """P6: extra='forbid' auch hier."""
        with pytest.raises(ValidationError):
            UniverseConfig(allowed_tickers=["NOW"], typo_field=True)


# ---------- P7: Settings.load with specific exception types ----------


class TestSettingsLoad:
    def test_validation_error_from_bad_thresholds(self, tmp_path: Path) -> None:
        """Ungültige Werte (P1-Regel) müssen als ConfigError aus load() bubbeln."""
        bad = tmp_path / "bad.toml"
        # delta_min > delta_max trips the model_validator
        bad.write_text(
            """
[rules]
vix_min = 20.0
ivr_min = 40.0
delta_min = -0.10
delta_max = -0.25
dte_min = 30
dte_max = 55
strike_otm_min_pct = 8.0
earnings_min_days = 8
options_volume_min = 50000
spread_max_usd = 0.05
market_cap_min_billion = 50.0
sector_cap_pct = 55.0

[universe]
allowed_tickers = ["NOW"]
""",
            encoding="utf-8",
        )
        with pytest.raises(ConfigError) as excinfo:
            Settings.load(bad)
        assert "ungültig" in str(excinfo.value)

    def test_keyboard_interrupt_propagates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """P7: KeyboardInterrupt darf nicht als ConfigError verschluckt werden."""
        bad = tmp_path / "tomlfile.toml"
        bad.write_text("[rules]\n", encoding="utf-8")

        import csp.config as config_mod

        def boom(*_args: object, **_kwargs: object) -> object:
            raise KeyboardInterrupt

        monkeypatch.setattr(config_mod.tomllib, "load", boom)
        with pytest.raises(KeyboardInterrupt):
            Settings.load(bad)

    def test_unreadable_file_raises_config_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """OSError (z. B. fehlende Lesepermission) wird in ConfigError gewickelt."""
        bad = tmp_path / "exists.toml"
        bad.write_text("[rules]\n", encoding="utf-8")

        original_open = Path.open

        def patched_open(self: Path, *args: object, **kwargs: object) -> object:
            if self == bad:
                raise PermissionError("simulated permission denied")
            return original_open(self, *args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(Path, "open", patched_open)
        with pytest.raises(ConfigError) as excinfo:
            Settings.load(bad)
        assert "nicht lesbar" in str(excinfo.value)
