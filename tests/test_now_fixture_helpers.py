"""Unit-Tests für `_decode_first_response_json` (NOW-Fixture-Helfer).

Verifiziert robustes Handling beider `Content-Encoding`-Formen (list[str] vs. str).
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import yaml

from tests.fixtures.now_2026_04_24 import _decode_first_response_json

_PAYLOAD = {"data": [{"foo": "bar", "n": 42}]}


def _write_cassette(tmp_path: Path, body_bytes: bytes, content_encoding: object) -> Path:
    """Schreibt eine Mini-VCR-YAML mit kontrollierter `Content-Encoding`-Form.

    VCR speichert Bodies als `!!binary` (Python-`bytes`) im YAML — wir replizieren
    das mit einem PyYAML-Custom-Representer, damit der Helfer-Test 1:1 das
    echte Cassette-Format trifft.
    """
    cassette = tmp_path / "fixture.yaml"
    interactions = [
        {
            "request": {"uri": "https://example.com/x"},
            "response": {
                "status": {"code": 200, "message": "OK"},
                "headers": {"Content-Encoding": content_encoding},
                "body": {"string": body_bytes},  # bytes → !!binary
            },
        }
    ]
    cassette.write_text(yaml.safe_dump({"interactions": interactions}))
    return cassette


def test_decode_handles_content_encoding_as_list(tmp_path: Path) -> None:
    """Kanonische VCR-Form: `Content-Encoding: ["gzip"]`."""
    raw = json.dumps(_PAYLOAD).encode()
    body = gzip.compress(raw)
    cassette = _write_cassette(tmp_path, body, ["gzip"])
    result = _decode_first_response_json(cassette)
    assert result == _PAYLOAD


def test_decode_handles_content_encoding_as_string(tmp_path: Path) -> None:
    """Alternative Form (manche VCR-Versionen / Vendor-Headers): plain `"gzip"`."""
    raw = json.dumps(_PAYLOAD).encode()
    body = gzip.compress(raw)
    cassette = _write_cassette(tmp_path, body, "gzip")
    result = _decode_first_response_json(cassette)
    assert result == _PAYLOAD


def test_decode_handles_no_gzip_with_list(tmp_path: Path) -> None:
    """Nicht-gzip-Body wird als JSON direkt geparst."""
    raw = json.dumps(_PAYLOAD).encode()
    cassette = _write_cassette(tmp_path, raw, [])
    result = _decode_first_response_json(cassette)
    assert result == _PAYLOAD


def test_decode_handles_missing_content_encoding(tmp_path: Path) -> None:
    """`Content-Encoding` komplett abwesend → keine gzip-Annahme."""
    raw = json.dumps(_PAYLOAD).encode()
    cassette = tmp_path / "fixture.yaml"
    interactions = [
        {
            "request": {"uri": "https://example.com/x"},
            "response": {
                "status": {"code": 200, "message": "OK"},
                "headers": {},  # kein Content-Encoding
                "body": {"string": raw.decode("latin-1")},
            },
        }
    ]
    cassette.write_text(yaml.safe_dump({"interactions": interactions}))
    result = _decode_first_response_json(cassette)
    assert result == _PAYLOAD
