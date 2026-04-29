"""Tests für `csp.ui.formatters` (Slice 7)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from csp.ui.formatters import (
    _group_thousands,
    format_date_de,
    format_pct,
    format_signed_int,
    format_usd,
)


class TestFormatUSD:
    @pytest.mark.parametrize(
        "amount, expected",
        [
            (Decimal("0"), "0,00 USD"),
            (Decimal("1.50"), "1,50 USD"),
            (Decimal("1234.56"), "1.234,56 USD"),
            (Decimal("12345678.9"), "12.345.678,90 USD"),
            (Decimal("-1234.5"), "-1.234,50 USD"),
            (1234.56, "1.234,56 USD"),
        ],
    )
    def test_default_two_decimals(self, amount: Decimal | float, expected: str) -> None:
        assert format_usd(amount) == expected

    def test_custom_decimals(self) -> None:
        assert format_usd(Decimal("1.5500"), decimals=4) == "1,5500 USD"

    def test_zero_decimals(self) -> None:
        assert format_usd(Decimal("8800"), decimals=0) == "8.800 USD"


class TestFormatPct:
    @pytest.mark.parametrize(
        "value, decimals, expected",
        [
            (13.3, 1, "13,3 %"),
            (96.0, 0, "96 %"),
            (0.0, 1, "0,0 %"),
            (-1.5, 1, "-1,5 %"),
            (1234.5, 1, "1.234,5 %"),
        ],
    )
    def test_format(self, value: float, decimals: int, expected: str) -> None:
        assert format_pct(value, decimals=decimals) == expected


class TestFormatSignedInt:
    @pytest.mark.parametrize(
        "value, expected",
        [(0, "0"), (5, "+5"), (-3, "-3")],
    )
    def test_signed(self, value: int, expected: str) -> None:
        assert format_signed_int(value) == expected


class TestFormatDateDe:
    def test_format(self) -> None:
        assert format_date_de(date(2026, 4, 27)) == "27.04.2026"

    def test_padding(self) -> None:
        assert format_date_de(date(2026, 1, 5)) == "05.01.2026"


class TestGroupThousands:
    def test_short_int(self) -> None:
        assert _group_thousands("123", sep=".") == "123"

    def test_thousand_boundary(self) -> None:
        assert _group_thousands("1234", sep=".") == "1.234"

    def test_million(self) -> None:
        assert _group_thousands("1234567", sep=".") == "1.234.567"

    def test_empty(self) -> None:
        assert _group_thousands("", sep=".") == ""
