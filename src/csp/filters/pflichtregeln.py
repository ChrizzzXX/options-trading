"""Die neun inviolablen CSP-Pflichtregeln (PRD FR8/FR11/FR12).

Jede Regel ist eine reine Funktion `rule_NN(core, strike, macro, portfolio, settings)`
mit Rückgabe `(passed, German reason | None)`. Der Orchestrator
:func:`passes_csp_filters` ruft alle neun Regeln in fester Reihenfolge auf,
sammelt sämtliche Fehlertexte und schließt mit dem `override`-Pfad ab.

Anmerkung zur Marktkapitalisierungs-Einheit (Pflichtregel 7):
- Setting `market_cap_min_billion` ist in **Milliarden** USD.
- ORATS-Feld `mkt_cap_thousands` ist in **Tausend** USD.
- Umrechnung: `min_thousands = setting * 1_000_000`.
"""

from __future__ import annotations

from loguru import logger

from csp.config import Settings
from csp.models.core import MacroSnapshot, OratsCore, OratsStrike, PortfolioSnapshot

RuleResult = tuple[bool, str | None]
THOUSANDS_PER_BILLION = 1_000_000


def _de_num(value: float, decimals: int = 2) -> str:
    """Formatiert eine Zahl im deutschen Locale (Komma als Dezimaltrenner)."""
    return f"{value:.{decimals}f}".replace(".", ",")


def _de_pct(value: float, decimals: int = 1) -> str:
    """Formatiert einen Prozentwert: `13,3 %` (Leerzeichen vor Prozentzeichen)."""
    return f"{_de_num(value, decimals)} %"


def rule_01_volatility_regime(
    core: OratsCore,
    strike: OratsStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    settings: Settings,
) -> RuleResult:
    """Pflichtregel 1: VIX ≥ vix_min ODER IVR ≥ ivr_min."""
    vix_ok = macro.vix_close >= settings.rules.vix_min
    ivr_ok = core.ivr >= settings.rules.ivr_min
    if vix_ok or ivr_ok:
        return True, None
    reason = (
        f"Pflichtregel 1 — Volatilitätsregime zu ruhig: "
        f"VIX {_de_num(macro.vix_close)} < {_de_num(settings.rules.vix_min)} "
        f"und IVR {_de_num(core.ivr)} < {_de_num(settings.rules.ivr_min)}"
    )
    return False, reason


def rule_02_delta_band(
    core: OratsCore,
    strike: OratsStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    settings: Settings,
) -> RuleResult:
    """Pflichtregel 2: Delta im Band [delta_min, delta_max]."""
    lo = settings.rules.delta_min
    hi = settings.rules.delta_max
    if lo <= strike.delta <= hi:
        return True, None
    reason = (
        f"Pflichtregel 2 — Delta {_de_num(strike.delta)} außerhalb [{_de_num(lo)}, {_de_num(hi)}]"
    )
    return False, reason


def rule_03_dte_window(
    core: OratsCore,
    strike: OratsStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    settings: Settings,
) -> RuleResult:
    """Pflichtregel 3: DTE im Fenster [dte_min, dte_max]."""
    lo = settings.rules.dte_min
    hi = settings.rules.dte_max
    if lo <= strike.dte <= hi:
        return True, None
    reason = f"Pflichtregel 3 — DTE {strike.dte} außerhalb [{lo}, {hi}]"
    return False, reason


def rule_04_otm_distance(
    core: OratsCore,
    strike: OratsStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    settings: Settings,
) -> RuleResult:
    """Pflichtregel 4: Strike mindestens strike_otm_min_pct unterhalb des Spotpreises.

    Das Modell `OratsCore` erzwingt `under_price > 0` per Field-Validator (P2),
    daher entfällt hier die defensive Null-/Negativ-Prüfung.
    """
    otm_pct = (core.under_price - strike.strike) / core.under_price * 100.0
    threshold = settings.rules.strike_otm_min_pct
    if otm_pct >= threshold:
        return True, None
    reason = (
        f"Pflichtregel 4 — OTM nur {_de_pct(otm_pct)} (< {_de_pct(threshold)}) "
        f"bei Spot {_de_num(core.under_price)} und Strike {_de_num(strike.strike)}"
    )
    return False, reason


def rule_05_earnings_distance(
    core: OratsCore,
    strike: OratsStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    settings: Settings,
) -> RuleResult:
    """Pflichtregel 5: Earnings frühestens in earnings_min_days Tagen."""
    threshold = settings.rules.earnings_min_days
    if core.days_to_next_earn >= threshold:
        return True, None
    reason = f"Pflichtregel 5 — Earnings in {core.days_to_next_earn} Tagen (< {threshold})"
    return False, reason


def rule_06_liquidity(
    core: OratsCore,
    strike: OratsStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    settings: Settings,
) -> RuleResult:
    """Pflichtregel 6: Optionsvolumen und Bid-Ask-Spread."""
    volume_ok = core.avg_opt_volu_20d >= settings.rules.options_volume_min
    spread = strike.put_ask - strike.put_bid
    spread_ok = spread <= settings.rules.spread_max_usd
    if volume_ok and spread_ok:
        return True, None
    parts: list[str] = []
    if not volume_ok:
        parts.append(f"Volumen {core.avg_opt_volu_20d} < {settings.rules.options_volume_min}")
    if not spread_ok:
        parts.append(f"Spread {_de_num(spread)} USD > {_de_num(settings.rules.spread_max_usd)} USD")
    reason = "Pflichtregel 6 — Liquidität ungenügend: " + "; ".join(parts)
    return False, reason


def rule_07_market_cap(
    core: OratsCore,
    strike: OratsStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    settings: Settings,
) -> RuleResult:
    """Pflichtregel 7: Marktkapitalisierung ≥ market_cap_min_billion (Mrd USD).

    Konvertiert den Setting-Wert (Milliarden) einmalig in Tausend USD,
    um direkt mit `core.mkt_cap_thousands` (ORATS-Konvention) zu vergleichen.
    """
    min_thousands = settings.rules.market_cap_min_billion * THOUSANDS_PER_BILLION
    if core.mkt_cap_thousands >= min_thousands:
        return True, None
    actual_billion = core.mkt_cap_thousands / THOUSANDS_PER_BILLION
    reason = (
        f"Pflichtregel 7 — Marktkapitalisierung {_de_num(actual_billion)} Mrd USD "
        f"< {_de_num(settings.rules.market_cap_min_billion)} Mrd USD"
    )
    return False, reason


def rule_08_sector_cap(
    core: OratsCore,
    strike: OratsStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    settings: Settings,
) -> RuleResult:
    """Pflichtregel 8: Aktuelle Sektorgewichtung ≤ sector_cap_pct.

    Vergleicht den rohen Anteil (0..1) gegen `sector_cap_pct / 100`, um
    Float-Rundungsartefakte an der exakten Grenze zu vermeiden (P4).
    """
    current_share = portfolio.sector_exposures.get(core.sector, 0.0)
    threshold_pct = settings.rules.sector_cap_pct
    threshold_share = threshold_pct / 100.0
    if current_share <= threshold_share:
        return True, None
    current_pct = current_share * 100.0
    reason = (
        f"Pflichtregel 8 — Sektor {core.sector} bereits {_de_pct(current_pct)} "
        f"> {_de_pct(threshold_pct)}"
    )
    return False, reason


def rule_09_universe(
    core: OratsCore,
    strike: OratsStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    settings: Settings,
) -> RuleResult:
    """Pflichtregel 9: Ticker liegt im konfigurierten Universum."""
    if core.ticker in settings.universe.allowed_tickers:
        return True, None
    reason = f"Pflichtregel 9 — Ticker {core.ticker} nicht im Universum"
    return False, reason


_ALL_RULES = (
    rule_01_volatility_regime,
    rule_02_delta_band,
    rule_03_dte_window,
    rule_04_otm_distance,
    rule_05_earnings_distance,
    rule_06_liquidity,
    rule_07_market_cap,
    rule_08_sector_cap,
    rule_09_universe,
)


def passes_csp_filters(
    core: OratsCore,
    strike: OratsStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    settings: Settings,
    *,
    override: bool = False,
) -> tuple[bool, list[str]]:
    """Wertet alle neun Pflichtregeln aus und liefert `(passed, reasons)`.

    Sammelt **immer** sämtliche Fehlerursachen in Regel-Reihenfolge — kein Short-Circuit.
    Mit `override=True` wird `passed=True` erzwungen, die Begründungen bleiben erhalten,
    und es wird ein loguru-WARN protokolliert. Persistenz folgt im Lifecycle-Slice (FR9).

    Hinweis zur Signatur: Die fünfte Position `settings` weicht bewusst von PRD Zeile 409
    ab — FR12 verbietet hartkodierte Schwellwerte, daher wird Settings injiziert.
    """
    reasons: list[str] = []
    for rule in _ALL_RULES:
        passed, reason = rule(core, strike, macro, portfolio, settings)
        if not passed and reason is not None:
            reasons.append(reason)

    if override:
        if reasons:
            logger.warning(
                "Pflichtregeln-Override aktiv für Ticker {ticker}: {n} Verstöße ignoriert",
                ticker=core.ticker,
                n=len(reasons),
            )
        return True, reasons

    return len(reasons) == 0, reasons
