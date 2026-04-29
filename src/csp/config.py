"""Settings-Loader für Pflichtregeln-Schwellwerte und Universum (PRD FR12)."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from csp.exceptions import ConfigError

DEFAULT_SETTINGS_PATH = Path("config/settings.toml")


class RuleThresholds(BaseModel):
    """Die zwölf Pflichtregeln-Schwellwerte aus FR12."""

    model_config = ConfigDict(extra="forbid")

    vix_min: float
    ivr_min: float
    delta_min: float
    delta_max: float
    dte_min: int
    dte_max: int
    strike_otm_min_pct: float
    earnings_min_days: int
    options_volume_min: int
    spread_max_usd: float
    market_cap_min_billion: float
    sector_cap_pct: float

    @model_validator(mode="after")
    def _validate_orderings(self) -> RuleThresholds:
        """Erzwingt natürliche Ordnungen und Vorzeichen aller Schwellwerte.

        Tippfehler in `settings.toml` (z. B. vertauschte delta_min/delta_max) müssen
        beim Laden scheitern, nicht erst im Regelcode auffallen.
        """
        if not (self.delta_min < self.delta_max <= 0):
            raise ValueError(
                f"delta_min ({self.delta_min}) muss < delta_max ({self.delta_max}) <= 0 sein"
            )
        if self.vix_min < 0:
            raise ValueError(f"vix_min ({self.vix_min}) muss >= 0 sein")
        if self.ivr_min < 0:
            raise ValueError(f"ivr_min ({self.ivr_min}) muss >= 0 sein")
        if not (self.dte_min < self.dte_max):
            raise ValueError(f"dte_min ({self.dte_min}) muss < dte_max ({self.dte_max}) sein")
        if self.strike_otm_min_pct < 0:
            raise ValueError(f"strike_otm_min_pct ({self.strike_otm_min_pct}) muss >= 0 sein")
        if self.earnings_min_days < 0:
            raise ValueError(f"earnings_min_days ({self.earnings_min_days}) muss >= 0 sein")
        if self.options_volume_min < 0:
            raise ValueError(f"options_volume_min ({self.options_volume_min}) muss >= 0 sein")
        if self.spread_max_usd <= 0:
            raise ValueError(f"spread_max_usd ({self.spread_max_usd}) muss > 0 sein")
        if self.market_cap_min_billion <= 0:
            raise ValueError(
                f"market_cap_min_billion ({self.market_cap_min_billion}) muss > 0 sein"
            )
        if not (0 < self.sector_cap_pct <= 100):
            raise ValueError(f"sector_cap_pct ({self.sector_cap_pct}) muss in (0, 100] liegen")
        return self


class UniverseConfig(BaseModel):
    """Erlaubte Ticker für Pflichtregel 9."""

    model_config = ConfigDict(extra="forbid")

    allowed_tickers: list[str] = Field(min_length=1)

    @field_validator("allowed_tickers")
    @classmethod
    def _uppercase_tickers(cls, value: list[str]) -> list[str]:
        """Normalisiert alle Ticker auf Großbuchstaben (case-insensitiver Universumsabgleich)."""
        return [t.upper() for t in value]


class Settings(BaseSettings):
    """Globale Konfiguration; lädt `config/settings.toml` per Klassenmethode."""

    model_config = SettingsConfigDict(extra="forbid")

    rules: RuleThresholds
    universe: UniverseConfig

    @classmethod
    def load(cls, path: Path | str = DEFAULT_SETTINGS_PATH) -> Settings:
        """Lädt Settings aus einer TOML-Datei. Erhöht ConfigError bei Fehlern.

        Fängt nur erwartete Fehlertypen (TOML, Validation, OS); KeyboardInterrupt und
        unerwartete Bugs müssen propagieren statt verschluckt zu werden.
        """
        toml_path = Path(path)
        if not toml_path.exists():
            raise ConfigError(f"Settings-Datei fehlt: {toml_path}")
        try:
            with toml_path.open("rb") as fh:
                raw: dict[str, Any] = tomllib.load(fh)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"Settings-Datei {toml_path} ist kein valides TOML: {exc}") from exc
        except OSError as exc:
            raise ConfigError(f"Settings-Datei {toml_path} nicht lesbar: {exc}") from exc

        try:
            return cls.model_validate(raw)
        except ValidationError as exc:
            raise ConfigError(f"Settings-Datei {toml_path} ungültig: {exc}") from exc
