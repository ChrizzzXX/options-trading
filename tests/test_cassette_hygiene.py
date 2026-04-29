"""Cassette-Hygiene-Tests: Token oder andere Secrets dürfen nicht in Cassettes leaken.

Liest jede YAML unter `tests/cassettes/` und stellt sicher:
- Das aktuell aktive `ORATS_TOKEN` (falls in `os.environ`) erscheint nirgends im
  Cassette-Inhalt.
- Kein `apikey=`-Substring (defensiver Schutz; ORATS verwendet `token`, andere
  Vendors `apikey`).

Wenn `ORATS_TOKEN` nicht in der Umgebung gesetzt ist (CI ohne `.env`), wird der
Token-spezifische Test übersprungen — der `apikey`-Check läuft trotzdem.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

CASSETTE_ROOT = Path(__file__).parent / "cassettes"


def _all_cassette_files() -> list[Path]:
    return sorted(CASSETTE_ROOT.rglob("*.yaml"))


def test_at_least_one_cassette_exists() -> None:
    """Sanity: ohne Cassetten ist dieser Test wertlos."""
    files = _all_cassette_files()
    assert files, f"Keine Cassettes unter {CASSETTE_ROOT} gefunden"


def test_no_live_orats_token_in_any_cassette() -> None:
    """Wenn ein lebendiges Token in der Umgebung ist, darf es in keiner Cassette stehen."""
    token = os.environ.get("ORATS_TOKEN", "")
    if not token:
        pytest.skip("ORATS_TOKEN nicht in Umgebung — Token-Leak-Check übersprungen")
    # Schutz vor Trivial-Tokens (z. B. "x") die als Substring in Hex-Daten matchen können.
    if len(token) < 8:
        pytest.skip(f"ORATS_TOKEN zu kurz ({len(token)} Zeichen) für sinnvollen Substring-Check")

    leaks: list[tuple[Path, int]] = []
    for cassette in _all_cassette_files():
        text = cassette.read_text(encoding="utf-8", errors="replace")
        if token in text:
            leaks.append((cassette, text.count(token)))
    assert not leaks, f"ORATS-Token in Cassetten gefunden: {leaks}"


def test_no_apikey_query_param_in_any_cassette() -> None:
    """`apikey=`-Query-Param (für andere Vendors) darf nicht durchsickern."""
    leaks: list[Path] = []
    for cassette in _all_cassette_files():
        text = cassette.read_text(encoding="utf-8", errors="replace")
        # `apikey=` (URL-encoded query string) — VCR scrubbt es, aber doppelt hält besser.
        if "apikey=" in text.lower():
            leaks.append(cassette)
    assert not leaks, f"`apikey=`-Substring in Cassetten gefunden: {leaks}"


def test_no_token_query_value_in_any_cassette() -> None:
    """Kein `token=<wert>`-Pattern: VCR muss `token` als Query-Param scrubbed haben."""
    import re

    pattern = re.compile(r"token=[A-Za-z0-9\-]{8,}")
    leaks: list[tuple[Path, list[str]]] = []
    for cassette in _all_cassette_files():
        text = cassette.read_text(encoding="utf-8", errors="replace")
        matches = pattern.findall(text)
        if matches:
            leaks.append((cassette, matches))
    assert not leaks, f"`token=<wert>`-Pattern in Cassetten gefunden: {leaks}"
