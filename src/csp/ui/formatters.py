"""Deutsche Locale-Formatter für Geld, Prozente, Daten (Slice 7).

Zentrale Quelle der Wahrheit für FBG-Mail-Strings, Daily-Brief-Markdown und
Sheets-Zellen. Format-Konventionen aus project-context.md "Numeric output
formatting":

- USD-Preise: `1.234,56 USD` (Tausender-Punkt, Dezimal-Komma).
- Prozente: `13,3 %` (eine Nachkommastelle, Leerzeichen vor `%`).
- DTE / Counts: ganze Zahlen.
- Datum (User-facing, FBG-Mail / Sheets): `27.04.2026`.
- Datum (DB / JSON): ISO `2026-04-27` — bleibt unverändert, wird hier nicht erzeugt.

Alle Helpers sind reine Funktionen — keine Locale-Setzung global, kein I/O.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal


def format_usd(amount: Decimal | float, *, decimals: int = 2) -> str:
    """Formatiert einen USD-Betrag in deutscher Locale: `1.234,56 USD`.

    Args:
        amount: ``Decimal`` (bevorzugt für Geld) oder ``float``.
        decimals: Nachkommastellen (Default 2; z. B. 4 für Mid-Prämie).

    Returns:
        Z. B. ``"1.234,56 USD"``, ``"-1.234,5600 USD"``, ``"0,00 USD"``.
    """
    # Decimal akzeptiert kein direktes float-`%`-Format. Normalisierung über
    # `Decimal(str(value))` vermeidet Binär-Float-Artefakte.
    value = Decimal(str(amount))
    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    quantized = abs_value.quantize(Decimal(10) ** -decimals)
    parts = format(quantized, "f").split(".")
    int_part = parts[0]
    frac_part = parts[1] if len(parts) > 1 else ""
    # Tausenderpunkte einfügen — von rechts in 3er-Blöcken.
    int_with_dots = _group_thousands(int_part, sep=".")
    formatted = f"{int_with_dots},{frac_part}" if decimals > 0 else int_with_dots
    return f"{sign}{formatted} USD"


def format_pct(value: float, *, decimals: int = 1) -> str:
    """Formatiert einen Prozent-Wert: `13,3 %` (Leerzeichen vor `%`).

    Erwartet `value` bereits als Prozentpunkte (also 13.3, nicht 0.133).
    """
    quantized = Decimal(str(value)).quantize(Decimal(10) ** -decimals)
    parts = format(abs(quantized), "f").split(".")
    int_part = parts[0]
    frac_part = parts[1] if len(parts) > 1 else ""
    int_with_dots = _group_thousands(int_part, sep=".")
    sign = "-" if quantized < 0 else ""
    formatted = f"{sign}{int_with_dots},{frac_part}" if decimals > 0 else f"{sign}{int_with_dots}"
    return f"{formatted} %"


def format_signed_int(value: int) -> str:
    """Formatiert eine Ganzzahl mit explizitem Vorzeichen: `+52`, `-3`, `0`."""
    if value > 0:
        return f"+{value}"
    return str(value)


def format_date_de(value: date) -> str:
    """Formatiert ein Datum als `27.04.2026` (zweistellige Tag/Monat, vierstelliges Jahr)."""
    return value.strftime("%d.%m.%Y")


def _group_thousands(integer_string: str, *, sep: str) -> str:
    """`"12345"` → `"12.345"`. Negative Vorzeichen muss der Caller draußen halten."""
    # Position-für-Position; `int(str)` würde die Vorzeichen-Hygiene zerlegen.
    if not integer_string:
        return integer_string
    chars: list[str] = []
    for i, ch in enumerate(reversed(integer_string)):
        if i > 0 and i % 3 == 0:
            chars.append(sep)
        chars.append(ch)
    return "".join(reversed(chars))
