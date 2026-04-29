"""csp — Bibliothek für deutsche Cash-Secured-Put-Recherche.

Slices: Pflichtregeln-Gate, ORATS-Client, Idea, Scan. Öffentliche Symbole für Claude Code.
"""

from csp._logging import install_secret_redactor
from csp.clients.fmp import FmpClient
from csp.clients.orats import OratsClient
from csp.config import Settings
from csp.exceptions import (
    ConfigError,
    FMPDataError,
    FMPEmptyDataError,
    ORATSDataError,
    ORATSEmptyDataError,
    PflichtregelError,
)
from csp.filters.pflichtregeln import passes_csp_filters
from csp.health import fmp_health_check, orats_health_check
from csp.idea import idea
from csp.macro import macro_snapshot
from csp.models.core import MacroSnapshot, OratsCore, OratsStrike, PortfolioSnapshot
from csp.models.idea import Idea
from csp.scan import scan

# Secret-redigierender Loguru-Sink — einmal beim Modul-Import installieren.
install_secret_redactor()

__all__ = [
    "ConfigError",
    "FMPDataError",
    "FMPEmptyDataError",
    "FmpClient",
    "Idea",
    "MacroSnapshot",
    "ORATSDataError",
    "ORATSEmptyDataError",
    "OratsClient",
    "OratsCore",
    "OratsStrike",
    "PflichtregelError",
    "PortfolioSnapshot",
    "Settings",
    "fmp_health_check",
    "idea",
    "macro_snapshot",
    "orats_health_check",
    "passes_csp_filters",
    "scan",
]
