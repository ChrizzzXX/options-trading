"""Settings-Loader für Pflichtregeln-Schwellwerte und Universum (PRD FR12)."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from csp.exceptions import ConfigError

DEFAULT_SETTINGS_PATH = Path("config/settings.toml")


class RuleThresholds(BaseModel):
    """Die zwölf Pflichtregeln-Schwellwerte aus FR12."""

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


class UniverseConfig(BaseModel):
    """Erlaubte Ticker für Pflichtregel 9."""

    allowed_tickers: list[str] = Field(default_factory=list)


class Settings(BaseSettings):
    """Globale Konfiguration; lädt `config/settings.toml` per Klassenmethode."""

    model_config = SettingsConfigDict(extra="forbid")

    rules: RuleThresholds
    universe: UniverseConfig

    @classmethod
    def load(cls, path: Path | str = DEFAULT_SETTINGS_PATH) -> Settings:
        """Lädt Settings aus einer TOML-Datei. Erhöht ConfigError bei Fehlern."""
        toml_path = Path(path)
        if not toml_path.exists():
            raise ConfigError(f"Settings-Datei fehlt: {toml_path}")
        try:
            with toml_path.open("rb") as fh:
                raw: dict[str, Any] = tomllib.load(fh)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"Settings-Datei {toml_path} ist kein valides TOML: {exc}") from exc

        try:
            return cls.model_validate(raw)
        except Exception as exc:
            raise ConfigError(f"Settings-Datei {toml_path} ungültig: {exc}") from exc
