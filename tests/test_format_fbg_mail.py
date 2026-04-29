"""Tests für `Idea.format_fbg_mail` (Slice 7, FR15)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from csp.models.idea import Idea


def _idea(
    *,
    bypassed: list[str] | None = None,
    reasons: list[str] | None = None,
    passed: bool = True,
) -> Idea:
    return Idea(
        ticker="NOW",
        strike=Decimal("78.00"),
        dte=52,
        delta=-0.21,
        put_bid=Decimal("1.42"),
        put_ask=Decimal("1.52"),
        mid_premium=Decimal("1.4700"),
        annualized_yield_pct=13.3,
        otm_pct=15.1,
        earnings_distance_days=86,
        under_price=91.84,
        iv_rank_1y_pct=96.0,
        current_sector_share_pct=38.0,
        pflichtregeln_passed=passed,
        reasons=reasons or [],
        bypassed_rules=bypassed or [],
        as_of=date(2026, 4, 27),
        data_freshness="live",
        region="US",
    )


class TestFormatFbgMail:
    def test_passing_idea_renders_all_fields(self) -> None:
        out = _idea().format_fbg_mail()
        # Header
        assert "CSP-IDEE | NOW | 27.04.2026" in out
        assert "(Override aktiv)" not in out
        # Felder mit deutscher Locale.
        assert "Kurs:              91,84 USD" in out
        assert "Strike:            78,00 USD" in out
        assert "Abstand OTM:       15,1 %" in out
        assert "Delta:             -0,21" in out
        # Verfall = 27.04.2026 + 52 Tage = 18.06.2026
        assert "Verfall:           18.06.2026 (52 DTE)" in out
        assert "IV-Rang 1y:        96 %" in out
        assert "Prämie Bid/Ask:    1,42 USD / 1,52 USD" in out
        assert "Empf. Limit:       1,4700 USD (Mid-Point)" in out
        # Cash = 78 * 1 * 100 = 7800
        assert "Cash-Bedarf:       7.800 USD (1 Kontrakt)" in out
        assert "Ann. Rendite:      13,3 % p.a." in out
        assert "Nächste Earnings:  86 Tage Abstand" in out
        assert "Pflichtregeln:     OK" in out

    def test_default_reasoning_synthesized(self) -> None:
        out = _idea().format_fbg_mail()
        assert "IVR 96 %" in out
        assert "Strike 15,1 % OTM" in out
        assert "52 DTE" in out

    def test_custom_reasoning_replaces_default(self) -> None:
        out = _idea().format_fbg_mail(reasoning="Post-Earnings-IV-Crush nutzbar; Kerntitel.")
        assert "Begründung:        Post-Earnings-IV-Crush nutzbar; Kerntitel." in out
        assert "Theta-Beschleunigungsfenster" not in out

    def test_multiple_contracts_uses_plural(self) -> None:
        out = _idea().format_fbg_mail(contracts=3)
        # Cash = 78 * 3 * 100 = 23.400
        assert "Cash-Bedarf:       23.400 USD (3 Kontrakte)" in out

    def test_override_idea_marks_header_and_lists_bypassed(self) -> None:
        out = _idea(
            bypassed=["Pflichtregel 5 — Earnings 0 Tage", "Pflichtregel 6 — Spread 0,15 USD"]
        ).format_fbg_mail()
        assert "(Override aktiv)" in out
        assert "Pflichtregeln:     NICHT BESTANDEN" in out
        assert "Bypassed (Override):" in out
        assert "  - Pflichtregel 5 — Earnings 0 Tage" in out
        assert "  - Pflichtregel 6 — Spread 0,15 USD" in out

    def test_failing_idea_lists_reasons(self) -> None:
        out = _idea(
            passed=False,
            reasons=["Pflichtregel 3 — DTE 56 außerhalb"],
        ).format_fbg_mail()
        assert "Pflichtregeln:     NICHT BESTANDEN" in out
        assert "Verstöße:" in out
        assert "  - Pflichtregel 3 — DTE 56 außerhalb" in out

    def test_returns_multiline_string(self) -> None:
        out = _idea().format_fbg_mail()
        # Sanity: enthält 3 `---`-Trenner, mehrere Zeilen.
        assert out.count("---") == 3
        assert out.count("\n") > 10

    def test_pflichtregeln_passed_with_bypass_still_marked_failing(self) -> None:
        # Override-Pfad: pflichtregeln_passed=True UND bypassed_rules nichtleer.
        out = _idea(
            passed=True,
            bypassed=["Pflichtregel 5"],
        ).format_fbg_mail()
        assert "Pflichtregeln:     NICHT BESTANDEN" in out


@pytest.mark.parametrize(
    "passed, bypassed, expected",
    [
        (True, [], "OK"),
        (False, [], "NICHT BESTANDEN"),
        (True, ["Pflichtregel 5"], "NICHT BESTANDEN"),
    ],
)
def test_pflichtregeln_marker_matrix(passed: bool, bypassed: list[str], expected: str) -> None:
    out = _idea(passed=passed, bypassed=bypassed).format_fbg_mail()
    assert f"Pflichtregeln:     {expected}" in out
