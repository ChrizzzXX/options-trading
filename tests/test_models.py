"""Tests für die Pydantic-Validatoren auf den Datenträgern (P2/P3/P5/P10)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from csp.models.core import OratsCore, OratsStrike

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
