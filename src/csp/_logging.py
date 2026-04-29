"""Globale Loguru-Konfiguration mit Secret-Scrubbing-Filter.

Wird beim Import von `csp` einmal aktiv. Entfernt vor jeder Log-Emission:
- `token=…`, `apikey=…`, `api_key=…`, `api-key=…` Query-Param-Werte
- `Authorization: Bearer …` Header
- `IVOLATILITY_API_KEY=…` (env-Style-Leak)

Die Funktion mutiert `record["message"]` in-place, damit auch f-strings und
strukturierte `extra`-Felder nicht das Klartext-Token preisgeben.
"""

from __future__ import annotations

import re
import sys
from typing import Any

from loguru import logger

# Wieder-verwendet die Patterns aus `clients.orats` — gleiche Quelle der Wahrheit.
# Lazy-Import vermeiden, da `_logging` selbst zu Modul-Init-Zeit importiert wird.
_QUERY_PARAM_RE = re.compile(
    r"([?&](?:token|apikey|api_key|api-key)=)[^&\s#]+",
    flags=re.IGNORECASE,
)
_BEARER_RE = re.compile(r"(?i)(authorization\s*:\s*bearer\s+)\S+")
_IVOL_ENV_RE = re.compile(r"(?i)(IVOLATILITY_API_KEY\s*=\s*)\S+")
_REDACTED = "<REDACTED>"


def _scrub(text: str) -> str:
    """Wendet alle drei Scrubber an. Idempotent."""
    if not text:
        return text
    out = _QUERY_PARAM_RE.sub(r"\1" + _REDACTED, text)
    out = _BEARER_RE.sub(r"\1" + _REDACTED, out)
    out = _IVOL_ENV_RE.sub(r"\1" + _REDACTED, out)
    return out


def _secret_redactor(record: Any) -> bool:
    """Loguru-Filter: scrubbt `record["message"]` und alle string-`extra`-Felder.

    Gibt `True` zurück, damit der Record weiterhin emittiert wird (Filter-Semantik).
    Typsignatur ist `Any`, weil Loguru's `Record`-TypedDict nicht stabil exportiert
    ist (mypy: incompatible callable; runtime: Loguru passt dict-like Records rein).
    """
    record["message"] = _scrub(record.get("message", ""))
    extras = record.get("extra", {})
    for key, value in list(extras.items()):
        if isinstance(value, str):
            extras[key] = _scrub(value)
    return True


def install_secret_redactor() -> None:
    """Installiert den globalen Sink-Filter. Idempotent: alte Sinks werden entfernt."""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | {message}",
        filter=_secret_redactor,
    )
