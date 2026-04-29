"""Portfolio-Snapshot-Builder (Slice 11) — `PortfolioSnapshot` aus DuckDB.

Pflichtregel 8 vergleicht den aktuellen Sektor-Anteil gegen `sector_cap_pct`.
Bisher (vor Slice 11) wurde `PortfolioSnapshot()` mit leeren `sector_exposures`
übergeben, sodass die Regel **immer** mit `0% ≤ 55%` durchging — ein stiller
Korrektheits-Bug, der erst beim ersten echten `log_trade(...)` sichtbar wäre.

Slice-11-Fix: `_build_portfolio_snapshot(settings)` lädt offene Trades aus
DuckDB, mappt jeden Trade über `idea.sector` (FK) zu seinem GICS-Sektor,
summiert `cash_secured` pro Sektor, und teilt durch
`Settings.portfolio.total_csp_capital_usd`.

Aufrufer (`csp.idea`, `csp.scan`) ruft synchron in seinem Sync-Wrapper, BEVOR
der Async-Path gestartet wird — DuckDB-Calls sind in-Process und schnell.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from loguru import logger

from csp.config import Settings
from csp.models.core import PortfolioSnapshot
from csp.persistence import connection
from csp.persistence.ideas import get_idea_by_id
from csp.persistence.trades import list_open_trades


def build_portfolio_snapshot(settings: Settings) -> PortfolioSnapshot:
    """Erzeugt einen `PortfolioSnapshot` aus den offenen Trades in DuckDB.

    Algorithmus:
    1. Liste aller Trades mit Status ``OPEN`` oder ``TAKE_PROFIT_PENDING``.
    2. Pro Trade: lade die zugehörige `Idea` über `idea_id`, lese `idea.sector`.
    3. Summiere `cash_secured` (Decimal) pro Sektor.
    4. Teile durch `settings.portfolio.total_csp_capital_usd` → fraction (0..1).

    Edge cases:
    - Leere DB / keine offenen Trades → leeres `sector_exposures`-Dict
      (Pflichtregel 8 passt automatisch durch — korrekt: keine Konzentration).
    - FK-Inkonsistenz (Trade ohne Idea) → WARN-Log, Trade übersprungen
      (defensiv; sollte nie passieren wegen FK-Constraint).
    - Total-Kapital-Setting deckt nicht die Summe der `cash_secured` →
      Anteil > 1.0 möglich; Pflichtregel-8-Regel würde fail-blocken, was
      semantisch korrekt ist ("du bist über-exponiert auf alles").

    Args:
        settings: für `total_csp_capital_usd` UND DuckDB-Connection.

    Returns:
        `PortfolioSnapshot(sector_exposures={"Technology": 0.45, "Energy": 0.10})`
        oder leerer Snapshot wenn keine offenen Trades.
    """
    capital = Decimal(str(settings.portfolio.total_csp_capital_usd))
    sums_per_sector: defaultdict[str, Decimal] = defaultdict(lambda: Decimal(0))

    with connection(settings) as con:
        opens = list_open_trades(con)
        for trade in opens:
            idea = get_idea_by_id(con, trade.idea_id)
            if idea is None:
                # FK-Inkonsistenz — sollte nie passieren, aber defensiv gegen
                # nicht-migrationsbasierte DB-Corruption.
                logger.warning(
                    "build_portfolio_snapshot: trade {tid} verweist auf "
                    "fehlende idea {iid} — übersprungen",
                    tid=trade.trade_id,
                    iid=trade.idea_id,
                )
                continue
            sums_per_sector[idea.sector] += trade.cash_secured

    sector_exposures: dict[str, float] = {
        sector: float(total / capital) for sector, total in sums_per_sector.items()
    }
    return PortfolioSnapshot(sector_exposures=sector_exposures)
