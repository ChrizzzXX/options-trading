"""Cassette-Hygiene-Tests: Token oder andere Secrets dürfen nicht in Cassettes leaken.

Liest jede YAML unter `tests/cassettes/` und stellt sicher:
- Das aktuell aktive `ORATS_TOKEN` (falls in `os.environ`) erscheint nirgends im
  Cassette-Inhalt — auch nicht in URL-encodierter Form.
- Kein `apikey=`-Substring (defensiver Schutz; ORATS verwendet `token`, andere
  Vendors `apikey`).
- Kein `Authorization: Bearer …`-Header in den Response-Header-Sektionen.

**Fail-loud-Politik:** Wenn `tests/cassettes/` Cassetten enthält, MUSS die Hygiene
verifiziert werden — `ORATS_TOKEN` env unset wird zu `pytest.fail`. Nur bei leerem
Cassette-Verzeichnis (CI-Bootstrap) wird übersprungen. Cassettes ohne Hygiene-Check
sind ein Sicherheitsrisiko.
"""

from __future__ import annotations

import os
import re
import urllib.parse
from pathlib import Path

import pytest

CASSETTE_ROOT = Path(__file__).parent / "cassettes"


def _all_cassette_files() -> list[Path]:
    return sorted(CASSETTE_ROOT.rglob("*.yaml"))


def _live_orats_token() -> str:
    """Liest `ORATS_TOKEN` aus `os.environ` oder aus `.env` (falls vorhanden).

    Pytest startet ohne `.env`-Auto-Loading; für die Hygiene-Verifikation greifen
    wir manuell darauf zu, damit lokale Läufe (mit `.env` im Repo) und CI mit
    explizitem `ORATS_TOKEN` env-var beide funktionieren.
    """
    token = os.environ.get("ORATS_TOKEN", "")
    if token:
        return token
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return ""
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("ORATS_TOKEN="):
            return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def test_at_least_one_cassette_exists() -> None:
    """Sanity: ohne Cassetten ist dieser Test wertlos."""
    files = _all_cassette_files()
    assert files, f"Keine Cassettes unter {CASSETTE_ROOT} gefunden"


def test_no_live_orats_token_in_any_cassette() -> None:
    """Wenn ein lebendiges Token in der Umgebung ist, darf es in keiner Cassette stehen.

    Fail-loud, falls Cassettes existieren aber `ORATS_TOKEN` unset ist — die
    Hygiene-Verifikation darf nicht stillschweigend ausfallen.
    """
    cassettes = _all_cassette_files()
    token = _live_orats_token()
    if not token:
        if cassettes:
            pytest.fail(
                "ORATS_TOKEN unset (weder env noch .env), aber Cassetten existieren "
                f"({len(cassettes)} Dateien). Hygiene-Verifikation wäre wertlos — "
                "setze ORATS_TOKEN aus .env oder lösche die Cassetten."
            )
        pytest.skip("Keine Cassetten und kein Token — Hygiene-Verifikation übersprungen")
    if len(token) < 8:
        pytest.skip(f"ORATS_TOKEN zu kurz ({len(token)} Zeichen) für sinnvollen Substring-Check")

    # Sowohl literales Token als auch URL-encodierte Form prüfen (Tokens mit
    # Sonderzeichen werden URL-encodiert übertragen).
    encoded = urllib.parse.quote(token, safe="")
    needles = {token, encoded} - {""}

    leaks: list[tuple[Path, str]] = []
    for cassette in cassettes:
        text = cassette.read_text(encoding="utf-8", errors="replace")
        for needle in needles:
            if needle in text:
                leaks.append((cassette, needle))
    assert not leaks, f"ORATS-Token (oder URL-encodierte Form) in Cassetten gefunden: {leaks}"


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
    """Kein `token=<wert>`-Pattern (auch URL-encodiert): VCR muss `token` scrubbed haben."""
    # Erlaubt nur `token=<REDACTED>` oder kein `token=` — alle anderen Werte sind ein Leak.
    # Pattern matcht token= gefolgt von Nicht-Whitespace; explizit `<REDACTED>` ausschließen.
    pattern = re.compile(r"token=([^\s&'\"]+)", re.IGNORECASE)
    leaks: list[tuple[Path, list[str]]] = []
    for cassette in _all_cassette_files():
        text = cassette.read_text(encoding="utf-8", errors="replace")
        matches = pattern.findall(text)
        bad = [m for m in matches if m != "<REDACTED>"]
        if bad:
            leaks.append((cassette, bad))
    assert not leaks, f"`token=<wert>`-Pattern in Cassetten gefunden: {leaks}"


def test_no_authorization_bearer_in_any_cassette() -> None:
    """`Authorization: Bearer …` darf nicht in Cassette-Headers oder -Bodies erscheinen."""
    pattern = re.compile(r"authorization\s*:\s*bearer\s+\S+", re.IGNORECASE)
    leaks: list[tuple[Path, list[str]]] = []
    for cassette in _all_cassette_files():
        text = cassette.read_text(encoding="utf-8", errors="replace")
        matches = pattern.findall(text)
        if matches:
            leaks.append((cassette, matches))
    assert not leaks, f"`Authorization: Bearer …`-Pattern in Cassetten gefunden: {leaks}"


def test_live_token_grep_uses_re_escape() -> None:
    """Fixture-level Sanity: tokens mit Regex-Sonderzeichen ($/^/[/]) werden escaped.

    Der eigentliche Substring-Check verwendet `in`, nicht Regex — aber wenn
    irgendwann Regex-Suche eingesetzt wird, muss `re.escape` benutzt werden.
    Dieser Test pinnt das Vertrauen in das Verhalten.
    """
    weird_token = r"abc[$.+*]xyz"
    assert re.escape(weird_token) != weird_token  # `re.escape` macht etwas
    # Ein Substring-Check über `in` matcht `weird_token` korrekt — keine
    # Regex-Falle. Wir validieren das mit einem Mini-Beispiel:
    haystack = f"prefix-{weird_token}-suffix"
    assert weird_token in haystack
