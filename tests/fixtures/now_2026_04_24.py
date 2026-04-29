"""NOW-78-Strike-Fixture vom 2026-04-24 — Regressionsanker (PRD FR29 / NFR18).

Solange der echte ORATS-Cassette nicht aufgenommen ist, dient dieser Fixture als
Surrogat. Jedes Feld trägt einen Quellen-Tag, damit beim Joinen des Cassettes
nachvollziehbar ist, welche Werte bestätigt vs. plausibel-extrapoliert sind.

Quellen-Schlüssel:
- PRD §X.Y: direkt aus der PRD belegt
- brief §X.Y: aus dem archivierten Brief belegt
- inferred-plausible: nicht in PRD/Brief gepinnt, aber konsistent mit Journey 5
"""

from __future__ import annotations

from csp.models.core import MacroSnapshot, OratsCore, OratsStrike, PortfolioSnapshot

NOW_CORE = OratsCore(
    ticker="NOW",  # PRD §Journey 5 (NOW idea, 2026-04-24)
    under_price=85.0,  # inferred-plausible: Strike 78 muss ≥ 8 % OTM erfüllen → Spot ≥ ≈84,78
    sector="Technology",  # inferred-plausible: ServiceNow GICS-Sektor
    mkt_cap_thousands=170_000_000.0,  # inferred-plausible: ServiceNow ≈170 Mrd USD (≥ 50 Mrd)
    ivr=94.0,  # PRD §Journey 5 (IVR 94)
    days_to_next_earn=30,  # inferred-plausible: ≥ 8 Tage (Pflichtregel 5)
    avg_opt_volu_20d=120_000,  # inferred-plausible: ≥ 50 000 (Pflichtregel 6)
)

NOW_STRIKE = OratsStrike(
    strike=78.0,  # PRD §Journey 5 (Strike 78)
    delta=-0.22,  # spec §I/O-Matrix (delta -0,22 im Band [-0,25, -0,18])
    dte=55,  # PRD §Journey 5 (DTE 55)
    put_ask=4.32,  # inferred-plausible: Mid ≈ Premium 4,30 (PRD §Journey 5), Spread 0,04
    put_bid=4.28,  # inferred-plausible: siehe put_ask
)

# VIX 18,7 entspricht der I/O-Matrix-Vorgabe — Pflichtregel 1 passt nur via IVR-Schenkel.
NOW_MACRO = MacroSnapshot(vix_close=18.7)  # spec §I/O-Matrix (VIX 18,7)

NOW_PORTFOLIO_EMPTY = PortfolioSnapshot(sector_exposures={})  # spec §I/O-Matrix (empty portfolio)
