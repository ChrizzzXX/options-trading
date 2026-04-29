"""csp — Bibliothek für deutsche Cash-Secured-Put-Recherche.

Slices: Pflichtregeln-Gate, ORATS-Client, Idea, Scan. Öffentliche Symbole für Claude Code.
"""

from csp._logging import install_secret_redactor
from csp.clients.fmp import FmpClient
from csp.clients.orats import OratsClient
from csp.config import Settings
from csp.daily_brief import daily_brief
from csp.exceptions import (
    ConfigError,
    FMPDataError,
    FMPEmptyDataError,
    IdempotencyError,
    LifecycleError,
    ORATSDataError,
    ORATSEmptyDataError,
    PflichtregelError,
)
from csp.export import export_to_sheets
from csp.filters.pflichtregeln import passes_csp_filters
from csp.health import fmp_health_check, orats_health_check
from csp.idea import idea
from csp.lifecycle.state_machine import TradeStatus
from csp.lifecycle_api import (
    close_trade,
    get_idea,
    list_ideas,
    list_open_positions,
    log_idea,
    log_trade,
)
from csp.macro import macro_snapshot
from csp.models.core import MacroSnapshot, OratsCore, OratsStrike, PortfolioSnapshot
from csp.models.daily_brief import DailyBrief
from csp.models.idea import Idea
from csp.models.trade import Trade
from csp.scan import scan

# Secret-redigierender Loguru-Sink — einmal beim Modul-Import installieren.
install_secret_redactor()

__all__ = [
    "ConfigError",
    "DailyBrief",
    "FMPDataError",
    "FMPEmptyDataError",
    "FmpClient",
    "Idea",
    "IdempotencyError",
    "LifecycleError",
    "MacroSnapshot",
    "ORATSDataError",
    "ORATSEmptyDataError",
    "OratsClient",
    "OratsCore",
    "OratsStrike",
    "PflichtregelError",
    "PortfolioSnapshot",
    "Settings",
    "Trade",
    "TradeStatus",
    "close_trade",
    "daily_brief",
    "export_to_sheets",
    "fmp_health_check",
    "get_idea",
    "idea",
    "list_ideas",
    "list_open_positions",
    "log_idea",
    "log_trade",
    "macro_snapshot",
    "orats_health_check",
    "passes_csp_filters",
    "scan",
]
