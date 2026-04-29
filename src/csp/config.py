"""Settings-Loader für Pflichtregeln-Schwellwerte und Universum (PRD FR12).

Liest TOML-basierte Regelschwellen plus Vendor-Credentials aus `.env`. ORATS-Token
und Basis-URL werden hier gebündelt — Caller (z. B. `orats_health_check`) lesen
sie via `Settings.load()`, niemals direkt aus `os.environ`.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from csp.exceptions import ConfigError

DEFAULT_SETTINGS_PATH = Path("config/settings.toml")
DEFAULT_ORATS_BASE_URL = "https://api.orats.io/datav2"
DEFAULT_FMP_BASE_URL = "https://financialmodelingprep.com/api"


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


class MacroConfig(BaseModel):
    """Statische Makro-Werte (heute nur VIX-Close).

    `vix_close` ist ein Platzhalter, bis der FMP-Client-Slice eine Live-VIX-Quelle
    liefert (deferred-work D13). Bis dahin liest `csp.idea(...)` den Wert hier
    und konstruiert daraus den `MacroSnapshot`.
    """

    model_config = ConfigDict(extra="forbid")

    vix_close: float = Field(
        gt=0.0,
        le=200.0,
        description=(
            "VIX-Schlusskurs (Cboe Volatility Index); muss > 0 sein (0/NaN deutet "
            "auf eine fehlende Macro-Quelle hin) und <= 200 (typo-Schutz: 187 statt "
            "18,7 würde Pflichtregel 1 immer passieren lassen)."
        ),
    )


class Settings(BaseSettings):
    """Globale Konfiguration; lädt TOML (Regeln) + `.env` (Vendor-Secrets).

    `orats_token` und `orats_base_url` kommen über `pydantic-settings` aus `.env`
    bzw. der Umgebung. `orats_token` ist ein `SecretStr` — das Token wird in
    `repr(settings)` als `'**********'` ausgegeben, niemals im Klartext.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    rules: RuleThresholds
    universe: UniverseConfig
    macro: MacroConfig
    orats_token: SecretStr = Field(
        default=SecretStr(""),
        description="ORATS-API-Token aus .env. Leer = ConfigError beim Vendor-Aufruf.",
    )
    orats_base_url: str = Field(
        default=DEFAULT_ORATS_BASE_URL,
        description="ORATS-Datav2-Basis-URL (override via ORATS_BASE_URL env).",
    )
    fmp_key: SecretStr = Field(
        default=SecretStr(""),
        description=(
            "FMP-API-Key aus .env. Leer ⇒ `csp.macro_snapshot()` fällt auf "
            "`[macro] vix_close` aus settings.toml zurück (Slice-5-Verhalten)."
        ),
    )
    fmp_base_url: str = Field(
        default=DEFAULT_FMP_BASE_URL,
        description="FMP-API-Basis-URL (override via FMP_BASE_URL env). Stable-Namespace.",
    )
    duckdb_path: Path = Field(
        default=Path("data/trades.duckdb"),
        description=(
            "Pfad zur DuckDB-Datei (Slice 6). `:memory:` als String möglich für Tests; "
            "andernfalls wird das Eltern-Verzeichnis bei Bedarf erstellt. Override "
            "via DUCKDB_PATH env."
        ),
    )

    @classmethod
    def load(cls, path: Path | str = DEFAULT_SETTINGS_PATH) -> Settings:
        """Lädt Settings aus einer TOML-Datei + .env. Erhöht ConfigError bei Fehlern.

        TOML liefert `rules`/`universe`; `.env` liefert `orats_token`/`orats_base_url`
        (über pydantic-settings). Kein direkter `os.environ`-Zugriff in Callern.

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
            return cls(**raw)
        except ValidationError as exc:
            raise ConfigError(f"Settings-Datei {toml_path} ungültig: {exc}") from exc
