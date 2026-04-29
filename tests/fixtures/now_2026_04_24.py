"""NOW-78-Strike-Fixture vom 2026-04-24 — Regressionsanker (PRD FR29 / NFR18).

Quelle der Wahrheit sind die ORATS-Cassetten:
- `tests/cassettes/orats/hist_cores_NOW_20260424.yaml` (recorded 2026-04-29)
- `tests/cassettes/orats/hist_strikes_NOW_20260424.yaml` (recorded 2026-04-29)

Beim Modul-Import werden die YAML-Cassetten geladen, die gzip-kodierten Bodies
dekompiriert und die ersten Items per Pydantic-Modellen geparst. Das macht den
Fixture eine reine Funktion über die Cassette-Daten — Re-Recording (mit
explicit-reason commit) ändert die Fixture-Werte automatisch mit.

Reconciliation gegen die ursprünglichen synthetischen Werte (Spec Change Log):
- spot war 85.0 (synth) → 89.84 (real, pxAtmIv)
- premium-Mid war 4.30 (PRD §Journey 5) → 2.775 (real, putBid 2.70 / putAsk 2.85)
- spread war 0.04 (synth) → 0.15 (real) — bricht Pflichtregel 6
- daysToNextErn war 30 (synth) → 0 (real, "Earnings heute") — bricht Pflichtregel 5
- DTE war 55 (PRD) → 56 (real, 2026-04-24 → 2026-06-18) — bricht Pflichtregel 3
- IVR 94 (PRD) → 96 (real, ivPctile1y) — kein Bruch
- mkt_cap_thousands 170_000_000 (synth) → 93_972_640 (real) — passt weiterhin
- sector "Technology" (synth) ≡ sectorName "Technology" (real, ORATS-Mapping)
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

import yaml

from csp.models.core import MacroSnapshot, OratsCore, OratsStrike, PortfolioSnapshot

CASSETTE_DIR = Path(__file__).resolve().parents[1] / "cassettes" / "orats"
HIST_CORES_CASSETTE = CASSETTE_DIR / "hist_cores_NOW_20260424.yaml"
HIST_STRIKES_CASSETTE = CASSETTE_DIR / "hist_strikes_NOW_20260424.yaml"


def _decode_first_response_json(cassette_path: Path) -> Any:
    """Liest VCR-YAML, holt den Body der ersten Interaktion, gunzipt und parst JSON.

    `Content-Encoding` kann je nach VCR-Version bzw. Vendor entweder als
    `list[str]` (kanonische VCR-Form, z. B. `["gzip"]`) oder als plain `str`
    (z. B. `"gzip"`) abgelegt sein — wir behandeln beide Formen robust.
    """
    raw = yaml.safe_load(cassette_path.read_text())
    interaction = raw["interactions"][0]
    body_bytes = interaction["response"]["body"]["string"]
    enc_raw = interaction["response"]["headers"].get("Content-Encoding", [])
    enc_list = enc_raw if isinstance(enc_raw, list) else [enc_raw]
    is_gzip = any("gzip" in (e or "") for e in enc_list)
    if is_gzip:
        body_bytes = gzip.decompress(body_bytes)
    return json.loads(body_bytes)


def _load_now_core_from_cassette() -> OratsCore:
    """Lädt den ORATS /hist/cores-Snapshot für NOW vom 2026-04-24."""
    payload = _decode_first_response_json(HIST_CORES_CASSETTE)
    items = payload["data"]
    assert items, f"Leere data-Liste in {HIST_CORES_CASSETTE}"
    return OratsCore.model_validate(items[0])


def _load_now_78_strike_from_cassette() -> OratsStrike:
    """Findet NOW-Strike 78 mit DTE 55-56 in den /hist/strikes-Daten und parst ihn.

    Konvertiert ORATS' Call-Delta-Feld (`delta`) in das Put-Delta (= delta - 1.0),
    bevor `OratsStrike` validiert wird — ORATS gibt im /hist/strikes-Endpunkt
    nur das Call-Delta zurück.
    """
    payload = _decode_first_response_json(HIST_STRIKES_CASSETTE)
    items = payload["data"]
    candidates = [
        x
        for x in items
        if x.get("strike") == 78
        and x.get("dte") in (55, 56)
        and x.get("putBidPrice") is not None
        and x.get("putAskPrice") is not None
        and x.get("delta") is not None
    ]
    assert candidates, (
        "Kein NOW-78-Strike mit DTE 55/56 in der Cassette gefunden — "
        "Re-Recording oder Datenstruktur geändert"
    )
    raw = dict(candidates[0])
    raw["delta"] = float(raw["delta"]) - 1.0  # Call-Delta → Put-Delta
    return OratsStrike.model_validate(raw)


NOW_CORE: OratsCore = _load_now_core_from_cassette()
NOW_STRIKE: OratsStrike = _load_now_78_strike_from_cassette()

# VIX 18,7 entspricht der ursprünglichen Spec-I/O-Matrix-Vorgabe — Pflichtregel 1
# muss nur via IVR-Schenkel passen können. VIX wird nicht von ORATS geliefert,
# daher bleibt der MacroSnapshot eine separate Test-Konstante.
NOW_MACRO = MacroSnapshot(vix_close=18.7)
NOW_PORTFOLIO_EMPTY = PortfolioSnapshot(sector_exposures={})
