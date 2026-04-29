"""CSP-Strategie: Strike-Auswahl und `Idea`-Konstruktion.

Reine, synchrone Funktionen — kein I/O. Die async-Komposition (ORATS-Fetch +
Pflichtregeln + Idea-Bau) lebt in `csp.idea`. Hier: pure Logik.

`_select_strike` wählt aus einer ungeordneten Strike-Liste den DTE-/Delta-nächsten
Kandidaten innerhalb des Pflichtregel-2-Delta-Bands. `build_idea` ruft den
Pflichtregeln-Gate auf, ordnet die Override-Semantik korrekt zu und erzeugt das
populierte `Idea`-Modell.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from csp.config import Settings
from csp.exceptions import ORATSEmptyDataError
from csp.filters.pflichtregeln import passes_csp_filters
from csp.models.core import MacroSnapshot, OratsCore, OratsStrike, PortfolioSnapshot
from csp.models.idea import Idea


def _select_strike(
    strikes: list[OratsStrike],
    target_delta: float,
    dte: int,
    settings: Settings,
) -> OratsStrike:
    """Wählt den am besten zum Target passenden Strike aus der Kette.

    Algorithmus (siehe `spec-idea-singleticker.md` §Always):
    1. Strikes nach DTE gruppieren.
    2. Expiration mit minimalem ``|dte - requested|`` wählen; bei Gleichstand
       den niedrigeren DTE.
    3. Innerhalb dieser Expiration: Strikes filtern, deren Put-Delta in
       ``[settings.rules.delta_min, settings.rules.delta_max]`` liegt UND
       deren Put-Quotes positiv sind (``put_bid > 0`` und ``put_ask > 0``;
       Penny-Optionen ohne realen Bid scheiden hier aus, sonst entstünde
       eine Idee mit Quasi-Null-Yield).
    4. Aus diesen den Strike mit minimalem ``|delta - target_delta|`` wählen.
       Tie-Breaks der Reihe nach: (a) niedrigerer Strike (höherer OTM-Anteil),
       (b) Delta selbst, (c) Eingangsreihenfolge — damit die Auswahl bei
       identischen Datensätzen stabil und reproduzierbar bleibt (NFR18).

    Wichtige Konsequenz: weil das Pflichtregel-2-Delta-Band schon hier
    vorgefiltert wird, kann Pflichtregel 2 nicht über ``override=True``
    umgangen werden — wer ein Delta außerhalb des Bands nehmen will, muss
    das Setting ändern. Pflichtregeln 1, 3-9 sind regulär bypass-fähig.

    Raises:
        ORATSEmptyDataError: wenn die Strike-Liste leer ist ODER kein Strike
            innerhalb der gewählten Expiration ins Delta-Band fällt bzw.
            positive Quotes hat. Status bleibt 200 — HTTP war OK, semantisch
            existiert kein passender Strike.
    """
    if not strikes:
        raise ORATSEmptyDataError(
            status=200,
            body=f"kein passender Strike für target_delta={target_delta} (leere Strike-Liste)",
            url_redacted="<no-url>",
        )

    # 1+2: nächste Expiration finden. Tie-Break: niedrigerer DTE bevorzugt.
    available_dtes = sorted({s.dte for s in strikes}, key=lambda d: (abs(d - dte), d))
    chosen_dte = available_dtes[0]
    in_expiration = [s for s in strikes if s.dte == chosen_dte]

    # 3: Delta-Band-Filter + Positivitäts-Floor auf den Quotes.
    lo = settings.rules.delta_min
    hi = settings.rules.delta_max
    in_band = [s for s in in_expiration if lo <= s.delta <= hi and s.put_bid > 0 and s.put_ask > 0]

    if not in_band:
        raise ORATSEmptyDataError(
            status=200,
            body=(
                f"kein passender Strike für target_delta={target_delta} "
                f"in Delta-Band [{lo}, {hi}] bei DTE {chosen_dte}"
            ),
            url_redacted="<no-url>",
        )

    # 4: minimaler Delta-Abstand; mehrstufiger Tie-Break für stabile Reproduktion.
    indexed = list(enumerate(in_band))
    best = sorted(
        indexed,
        key=lambda pair: (
            abs(pair[1].delta - target_delta),
            pair[1].strike,
            pair[1].delta,
            pair[0],
        ),
    )[0][1]
    return best


def _decimal(value: float) -> Decimal:
    """Konvertiert einen Float aus ORATS in einen `Decimal` ohne Binär-Float-Artefakte.

    Der Umweg über ``str(value)`` vermeidet, dass ``Decimal(0.1)`` als
    ``Decimal('0.1000000000000000055511151231257827021181583404541015625')`` ankommt.
    """
    return Decimal(str(value))


def build_idea(
    core: OratsCore,
    strike: OratsStrike,
    macro: MacroSnapshot,
    portfolio: PortfolioSnapshot,
    settings: Settings,
    *,
    as_of: date,
    data_freshness: Literal["live", "eod", "stale", "unavailable"],
    region: Literal["US", "EU"],
    override: bool,
) -> Idea:
    """Baut eine vollständig populierte `Idea` aus Kern, Strike und Kontext.

    Override-Semantik (deckt sich mit `passes_csp_filters`):
    - Pass (alle 9 Regeln OK):                  ``passed=True,  reasons=[],     bypassed=[]``.
    - Fail ohne ``override``:                   ``passed=False, reasons=<rules>, bypassed=[]``.
    - Fail mit ``override=True``:               ``passed=True,  reasons=[],      bypassed=<rules>``.
    """
    # `passes_csp_filters` liefert (passed_after_override, raw_reasons). Den ersten
    # Wert verwerfen wir bewusst: `raw_reasons` + `override` reichen, um die drei
    # Idea-Zustände eindeutig herzuleiten — ein zweiter Boolean-Pfad würde nur
    # Divergenz-Risiko erzeugen, falls der Gate später um nicht-bypass-bare
    # Regeln erweitert wird.
    _, raw_reasons = passes_csp_filters(
        core,
        strike,
        macro,
        portfolio,
        settings,
        override=override,
    )

    if override and raw_reasons:
        # Fail-mit-Override: Regeln werden bewusst ignoriert.
        idea_reasons: list[str] = []
        idea_bypassed: list[str] = list(raw_reasons)
        idea_passed = True
    elif raw_reasons:
        # Fail-ohne-Override.
        idea_reasons = list(raw_reasons)
        idea_bypassed = []
        idea_passed = False
    else:
        # Pass — beide Listen leer; `override` irrelevant.
        idea_reasons = []
        idea_bypassed = []
        idea_passed = True

    # Kennzahlen ableiten. Money über Decimal(str(...)), damit keine
    # Binär-Float-Artefakte einfließen; Verhältnisse bleiben float.
    strike_dec = _decimal(strike.strike)
    put_bid_dec = _decimal(strike.put_bid)
    put_ask_dec = _decimal(strike.put_ask)
    mid_premium = ((put_bid_dec + put_ask_dec) / Decimal(2)).quantize(Decimal("0.0001"))
    # Annualisierte Yield: float, direkt aus den Decimals abgeleitet.
    annualized_yield_pct = float(mid_premium / strike_dec) * 365.0 / strike.dte * 100.0
    # OTM-Anteil aus Spot (float) und Strike (cast).
    otm_pct = (core.under_price - float(strike.strike)) / core.under_price * 100.0
    sector_share_pct = portfolio.sector_exposures.get(core.sector, 0.0) * 100.0

    return Idea(
        ticker=core.ticker,
        strike=strike_dec,
        dte=strike.dte,
        delta=strike.delta,
        put_bid=put_bid_dec,
        put_ask=put_ask_dec,
        mid_premium=mid_premium,
        annualized_yield_pct=annualized_yield_pct,
        otm_pct=otm_pct,
        earnings_distance_days=core.days_to_next_earn,
        under_price=core.under_price,
        iv_rank_1y_pct=core.ivr,
        current_sector_share_pct=sector_share_pct,
        pflichtregeln_passed=idea_passed,
        reasons=idea_reasons,
        bypassed_rules=idea_bypassed,
        as_of=as_of,
        data_freshness=data_freshness,
        region=region,
    )
