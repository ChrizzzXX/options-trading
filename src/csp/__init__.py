"""csp — Bibliothek für deutsche Cash-Secured-Put-Recherche.

Slices: Pflichtregeln-Gate, ORATS-Client. Öffentliche Symbole für Claude Code.
"""

from csp._logging import install_secret_redactor
from csp.clients.orats import OratsClient
from csp.config import Settings
from csp.exceptions import ConfigError, ORATSDataError, ORATSEmptyDataError, PflichtregelError
from csp.filters.pflichtregeln import passes_csp_filters
from csp.health import orats_health_check
from csp.idea import idea
from csp.models.core import MacroSnapshot, OratsCore, OratsStrike, PortfolioSnapshot
from csp.models.idea import Idea

# Secret-redigierender Loguru-Sink — einmal beim Modul-Import installieren.
install_secret_redactor()

__all__ = [
    "ConfigError",
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
    "idea",
    "orats_health_check",
    "passes_csp_filters",
]
