"""Tests für die Pydantic-Validatoren auf den Datenträgern (P2/P3/P5/P10).

Slice-9-Härtung (D5/D27): zusätzlich `TestFiniteValidators` für NaN/±Inf-Refusal
auf jedem numerischen Feld von `MacroSnapshot` / `OratsCore` / `OratsStrike`.
"""

from __future__ import annotations

import math
from typing import ClassVar

import pytest
from pydantic import ValidationError

from csp.models.core import MacroSnapshot, OratsCore, OratsStrike

_VALID_CORE_KW: dict[str, object] = {
    "ticker": "NOW",
    "under_price": 85.0,
    "sector": "Technology",
    "mkt_cap_thousands": 170_000_000.0,
    "ivr": 94.0,
    "days_to_next_earn": 30,
    "avg_opt_volu_20d": 120_000,
}

_VALID_STRIKE_KW: dict[str, object] = {
    "strike": 78.0,
    "delta": -0.22,
    "dte": 55,
    "put_ask": 4.32,
    "put_bid": 4.28,
}


class TestOratsCoreValidators:
    @pytest.mark.parametrize("bad_price", [0.0, -1.0, -0.0001])
    def test_under_price_must_be_positive(self, bad_price: float) -> None:
        """P2: under_price muss > 0 sein (Pydantic Field(gt=0))."""
        with pytest.raises(ValidationError):
            OratsCore(**{**_VALID_CORE_KW, "under_price": bad_price})

    @pytest.mark.parametrize("bad_days", [-1, -7])
    def test_days_to_next_earn_non_negative(self, bad_days: int) -> None:
        """P10: days_to_next_earn >= 0."""
        with pytest.raises(ValidationError):
            OratsCore(**{**_VALID_CORE_KW, "days_to_next_earn": bad_days})

    def test_days_to_next_earn_zero_allowed(self) -> None:
        """0 = "heute Earnings" muss zulässig sein (Regel-5-Failpfad)."""
        core = OratsCore(**{**_VALID_CORE_KW, "days_to_next_earn": 0})
        assert core.days_to_next_earn == 0

    @pytest.mark.parametrize(
        "ticker_in",
        ["now", "Now", "now ".strip(), "nOw"],
    )
    def test_ticker_normalised_to_uppercase(self, ticker_in: str) -> None:
        """P9: Ticker werden case-insensitiv durch Uppercase-Normalisierung verglichen."""
        core = OratsCore(**{**_VALID_CORE_KW, "ticker": ticker_in})
        assert core.ticker == "NOW"


class TestEarningsSentinelDetection:
    """Slice-12: ORATS-`nextErn = '0000-00-00'`-Sentinel.

    `daysToNextErn = 0` ist mehrdeutig — entweder "heute Earnings" oder
    Zero-Fallback weil ORATS das Datum noch nicht aktualisiert hat. Der
    `model_validator` löst den zweiten Fall auf:
    - `wksNextErn > 0`: Distanz aus Wochen ableiten (1 Woche = 7 Tage).
    - sonst: `days_to_next_earn = None`.
    """

    _RAW_VALID: ClassVar[dict[str, object]] = {
        "ticker": "ACME",
        "pxAtmIv": 100.0,
        "sectorName": "Technology",
        "mktCap": 100_000_000.0,
        "ivPctile1y": 80.0,
        "avgOptVolu20d": 120_000.0,
    }

    def test_real_next_ern_passes_through(self) -> None:
        """Wenn `nextErn` ein reales Datum ist, bleibt `daysToNextErn` unverändert."""
        core = OratsCore(
            **self._RAW_VALID,
            nextErn="2026-07-15",
            daysToNextErn=42,
            wksNextErn=6,
        )
        assert core.days_to_next_earn == 42

    def test_real_next_ern_with_zero_days_means_today(self) -> None:
        """Legitimer "heute Earnings"-Fall (0 Tage, valides Datum) bleibt 0."""
        core = OratsCore(
            **self._RAW_VALID,
            nextErn="2026-04-29",
            daysToNextErn=0,
            wksNextErn=0,
        )
        assert core.days_to_next_earn == 0

    def test_sentinel_with_wks_fallback_derives_days(self) -> None:
        """Sentinel-Datum + `wksNextErn=12` → 84 Tage (12 * 7)."""
        core = OratsCore(
            **self._RAW_VALID,
            nextErn="0000-00-00",
            daysToNextErn=0,
            wksNextErn=12,
        )
        assert core.days_to_next_earn == 84

    def test_sentinel_without_wks_returns_none(self) -> None:
        """Sentinel-Datum + `wksNextErn=0` → None (Datum unbekannt)."""
        core = OratsCore(
            **self._RAW_VALID,
            nextErn="0000-00-00",
            daysToNextErn=0,
            wksNextErn=0,
        )
        assert core.days_to_next_earn is None

    def test_sentinel_with_missing_wks_returns_none(self) -> None:
        """Sentinel-Datum, `wksNextErn` komplett fehlend → None."""
        core = OratsCore(
            **self._RAW_VALID,
            nextErn="0000-00-00",
            daysToNextErn=0,
        )
        assert core.days_to_next_earn is None

    def test_synthetic_kwargs_without_next_ern_unchanged(self) -> None:
        """Snake-case-Kwargs ohne `nextErn` (Test-Mocks) → Validator no-op."""
        core = OratsCore(**{**_VALID_CORE_KW, "days_to_next_earn": 30})
        assert core.days_to_next_earn == 30

    def test_explicit_none_for_days_allowed(self) -> None:
        """``None`` direkt zu setzen ist zulässig (Sentinel-Form)."""
        core = OratsCore(**{**_VALID_CORE_KW, "days_to_next_earn": None})
        assert core.days_to_next_earn is None


class TestOratsStrikeValidators:
    @pytest.mark.parametrize("bad_delta", [-1.0001, 0.01, 0.5, -10.0])
    def test_delta_must_be_in_range(self, bad_delta: float) -> None:
        """P5: delta in [-1, 0]."""
        with pytest.raises(ValidationError):
            OratsStrike(**{**_VALID_STRIKE_KW, "delta": bad_delta})

    @pytest.mark.parametrize("ok_delta", [-1.0, 0.0, -0.5, -0.22])
    def test_delta_boundary_values_allowed(self, ok_delta: float) -> None:
        strike = OratsStrike(**{**_VALID_STRIKE_KW, "delta": ok_delta})
        assert strike.delta == ok_delta

    def test_negative_bid_rejected(self) -> None:
        """P3: put_bid < 0 muss scheitern."""
        with pytest.raises(ValidationError) as excinfo:
            OratsStrike(**{**_VALID_STRIKE_KW, "put_bid": -0.01, "put_ask": 0.10})
        assert "put_bid" in str(excinfo.value)

    def test_crossed_quotes_rejected(self) -> None:
        """P3: put_ask < put_bid muss scheitern (überkreuzte Quotes)."""
        with pytest.raises(ValidationError) as excinfo:
            OratsStrike(**{**_VALID_STRIKE_KW, "put_bid": 4.40, "put_ask": 4.20})
        assert "überkreuzte Quotes" in str(excinfo.value) or "put_ask" in str(excinfo.value)

    def test_equal_bid_ask_allowed(self) -> None:
        """Spread = 0 (locked market) ist zulässig."""
        strike = OratsStrike(**{**_VALID_STRIKE_KW, "put_bid": 4.30, "put_ask": 4.30})
        assert strike.put_ask == strike.put_bid

    def test_zero_bid_allowed(self) -> None:
        """put_bid == 0 ist zulässig (illiquide Optionen, kein Crossed)."""
        strike = OratsStrike(**{**_VALID_STRIKE_KW, "put_bid": 0.0, "put_ask": 0.10})
        assert strike.put_bid == 0.0


# ---------------------------------------------------------------------------
# Slice-9-Härtung — finite-Validators auf allen numerischen Feldern (D5/D27).
# ---------------------------------------------------------------------------


_NON_FINITE = [float("nan"), float("inf"), float("-inf")]


class TestFiniteValidators:
    """Stellt sicher, dass NaN und ±Inf an der Vendor-Grenze abgelehnt werden.

    Sort-Reihenfolge in `csp.scan` und Pflichtregeln-Vergleiche dürfen keine
    nicht-finiten Floats sehen — sonst wird NFR20 (Determinismus) und das
    Ranking-Verhalten unbestimmt.
    """

    @pytest.mark.parametrize("bad", _NON_FINITE)
    def test_macro_vix_close_finite(self, bad: float) -> None:
        with pytest.raises(ValidationError, match="nicht finite"):
            MacroSnapshot(vix_close=bad)

    @pytest.mark.parametrize(
        "field", ["under_price", "mkt_cap_thousands", "ivr", "avg_opt_volu_20d"]
    )
    @pytest.mark.parametrize("bad", _NON_FINITE)
    def test_orats_core_numeric_finite(self, field: str, bad: float) -> None:
        # Bestimmte Felder haben zusätzliche Bounds-Checks (gt/ge/le), die VOR
        # unserem finite-Validator an pydantic ausgelöst werden — wir akzeptieren
        # jeden ValidationError, Hauptsache der Wert wird abgelehnt. Der finite-
        # Validator deckt die "kein anderer Schutz greift"-Felder ab
        # (mkt_cap_thousands, ivr, avg_opt_volu_20d ohne gt/ge).
        with pytest.raises(ValidationError):
            OratsCore(**{**_VALID_CORE_KW, field: bad})

    @pytest.mark.parametrize("field", ["strike", "delta", "put_ask", "put_bid"])
    @pytest.mark.parametrize("bad", _NON_FINITE)
    def test_orats_strike_numeric_finite(self, field: str, bad: float) -> None:
        # `delta` hat `ge=-1.0, le=0.0`; `put_*` haben Crossed-Quotes-Check.
        # Pure-finite-Validator-Treffer auf `strike` (keine andere Bounds-Regel).
        with pytest.raises(ValidationError):
            OratsStrike(**{**_VALID_STRIKE_KW, field: bad})

    @pytest.mark.parametrize("bad", _NON_FINITE)
    def test_strike_finite_validator_specifically_fires(self, bad: float) -> None:
        """Pinnt, dass `strike` keinen anderen Bounds-Check hat — der finite-
        Validator IST hier die einzige Verteidigung."""
        with pytest.raises(ValidationError, match="nicht finite"):
            OratsStrike(**{**_VALID_STRIKE_KW, "strike": bad})

    @pytest.mark.parametrize("field", ["mkt_cap_thousands", "ivr", "avg_opt_volu_20d"])
    @pytest.mark.parametrize("bad", _NON_FINITE)
    def test_core_finite_validator_specifically_fires(self, field: str, bad: float) -> None:
        """Felder ohne gt/ge — finite-Validator ist die einzige Verteidigung."""
        with pytest.raises(ValidationError, match="nicht finite"):
            OratsCore(**{**_VALID_CORE_KW, field: bad})

    def test_finite_floats_pass(self) -> None:
        """Smoke: gültige finite-Werte werden nicht abgelehnt."""
        macro = MacroSnapshot(vix_close=18.7)
        assert math.isfinite(macro.vix_close)
        core = OratsCore(**_VALID_CORE_KW)
        assert math.isfinite(core.under_price)
        strike = OratsStrike(**_VALID_STRIKE_KW)
        assert math.isfinite(strike.delta)
