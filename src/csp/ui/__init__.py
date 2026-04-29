"""csp.ui — Formatierungs-Helpers für deutsche User-Strings (Slice 7).

`formatters.py` ist die einzige Stelle für deutsche Locale-Konvertierung
(USD-Beträge, Prozente, Daten). Wird von `Idea.format_fbg_mail()` und
`csp.daily_brief().to_markdown()` benutzt; Code-Logik bleibt unangetastet
englisch.
"""

from csp.ui.formatters import (
    format_date_de,
    format_pct,
    format_signed_int,
    format_usd,
)

__all__ = [
    "format_date_de",
    "format_pct",
    "format_signed_int",
    "format_usd",
]
