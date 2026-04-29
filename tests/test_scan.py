"""Tests für `csp.scan(...)` (Slice 4).

Schichten:
- ``TestRankingAndTruncation``: Sort yield-DESC + Ticker-ASC-Tie-Break sowie
  ``max_results``-Truncation, getrieben über `make_idea` und respx-Mocks.
- ``TestPerTickerResilience``: pro-Ticker-`ORATSDataError`/`ORATSEmptyDataError`
  → Skip + WARN; alle-fail → leere Liste; Rule-Failer aus Resultat.
- ``TestPublicSurface``: ``max_results=0`` → `ValueError` ohne HTTP; fehlender
  Token → `ConfigError`; ``csp.scan`` als öffentliches Re-export.
- ``TestDeterminism``: zwei Läufe auf identischen Mocks liefern byte-identische
  Listen (NFR20).
- ``TestCassetteSmoke``: 1-Ticker-Universe ``["NOW"]`` gegen die Live-Cassetten;
  Konsistenz-Invariante mit ``csp.idea("NOW")``.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator, Mapping
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import httpx
import pytest
import respx
from loguru import logger

import csp
from csp.config import Settings
from csp.exceptions import ConfigError
from csp.models.idea import Idea
from csp.scan import scan

BASE_URL = "https://api.orats.io/datav2"
FAKE_TOKEN = "test-token-not-real-12345"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _passing_cores_payload(
    ticker: str,
    *,
    spot: float = 100.0,
    sector: str = "Technology",
    mkt_cap_thousands: float = 100_000_000.0,
    iv_pctile_1y: float = 80.0,
    days_to_next_earn: int = 30,
    avg_opt_volu_20d: float = 120_000.0,
) -> dict[str, Any]:
    """Cores-Payload, der pro Pflichtregel passend dimensioniert ist (Defaults)."""
    return {
        "data": [
            {
                "ticker": ticker,
                "pxAtmIv": spot,
                "sectorName": sector,
                "mktCap": mkt_cap_thousands,
                "ivPctile1y": iv_pctile_1y,
                "daysToNextErn": days_to_next_earn,
                "avgOptVolu20d": avg_opt_volu_20d,
            }
        ]
    }


def _passing_strikes_payload(
    *,
    strike: float = 88.0,
    call_delta: float = 0.80,  # ⇒ Put-Delta -0.20 (im Band [-0.25, -0.18]).
    dte: int = 45,
    put_bid: float = 1.50,
    put_ask: float = 1.52,
) -> dict[str, Any]:
    return {
        "data": [
            {
                "strike": strike,
                "delta": call_delta,
                "dte": dte,
                "putBidPrice": put_bid,
                "putAskPrice": put_ask,
            }
        ]
    }


def _ticker_router(
    router: respx.MockRouter,
    payloads: Mapping[str, tuple[dict[str, Any], dict[str, Any]] | int],
) -> None:
    """Setzt pro-Ticker `/cores` + `/strikes`-Routen ein.

    `payloads` Mapping: ticker → (cores_payload, strikes_payload) für Erfolg
    ODER int Status-Code (z. B. 404) für Vendor-Fehler. Beide Endpunkte teilen
    den Status-Code im Fehler-Fall.
    """

    def _make_handler(
        ticker_to_response: dict[str, dict[str, Any] | int],
    ) -> Callable[[httpx.Request], httpx.Response]:
        def handler(request: httpx.Request) -> httpx.Response:
            ticker = request.url.params.get("ticker", "")
            entry = ticker_to_response.get(ticker)
            if entry is None:
                # Patch F9: nicht-registrierter Ticker → laut fehlschlagen, statt
                # still 404 zurückzugeben. Tippfehler in Test-Setups würden sonst
                # über den Skip-und-WARN-Pfad maskiert und als grün durchlaufen.
                raise AssertionError(
                    f"_ticker_router: ticker '{ticker}' wurde nicht im Test-Setup registriert"
                )
            if isinstance(entry, int):
                return httpx.Response(entry, json={"error": "vendor outage"})
            return httpx.Response(200, json=entry)

        return handler

    cores_responses: dict[str, dict[str, Any] | int] = {}
    strikes_responses: dict[str, dict[str, Any] | int] = {}
    for ticker, value in payloads.items():
        if isinstance(value, int):
            cores_responses[ticker] = value
            strikes_responses[ticker] = value
        else:
            cores_payload, strikes_payload = value
            cores_responses[ticker] = cores_payload
            strikes_responses[ticker] = strikes_payload

    router.get(re.compile(rf"^{re.escape(BASE_URL)}/cores")).mock(
        side_effect=_make_handler(cores_responses)
    )
    router.get(re.compile(rf"^{re.escape(BASE_URL)}/strikes")).mock(
        side_effect=_make_handler(strikes_responses)
    )


@pytest.fixture
def stub_settings_factory(
    monkeypatch: pytest.MonkeyPatch, default_settings: Settings
) -> Callable[[list[str]], Settings]:
    """Patcht `Settings.load` mit einem Custom-Universum + Fake-Token + Test-Base-URL."""

    def _make(tickers: list[str]) -> Settings:
        from pydantic import SecretStr

        # Slice-8b: `fmp_key` aus `.env` muss explizit geleert werden, sonst
        # ruft `_fetch_macro` live FMP an statt auf [macro] settings zu fallen
        # — und respx hat hier keine FMP-Route registriert.
        patched = default_settings.model_copy(
            update={
                "orats_token": SecretStr(FAKE_TOKEN),
                "orats_base_url": BASE_URL,
                "fmp_key": SecretStr(""),
                "universe": default_settings.universe.model_copy(
                    update={"allowed_tickers": tickers}
                ),
            }
        )
        from csp import config as csp_config

        monkeypatch.setattr(
            csp_config.Settings,
            "load",
            classmethod(lambda cls, *a, **kw: patched),
        )
        return patched

    return _make


@pytest.fixture
def loguru_warnings() -> Iterator[list[str]]:
    """Sammelt loguru-WARN-Messages für Assertions auf Skip-Logs.

    Patch F8: Filter explizit auf Scan-Skip-Marker (`"scan: Ticker"`), damit
    parallele Tests oder andere Module nicht in den Capture-Topf laufen.
    """
    captured: list[str] = []

    def _sink(msg: object) -> None:
        # Loguru gibt ein `Message`-Objekt mit `.record["message"]` durch.
        record_msg = msg.record["message"]  # type: ignore[attr-defined,index]
        if record_msg.startswith("scan: Ticker"):
            captured.append(record_msg)

    sink_id = logger.add(_sink, level="WARNING")
    try:
        yield captured
    finally:
        logger.remove(sink_id)


# ---------------------------------------------------------------------------
# Ranking & Truncation
# ---------------------------------------------------------------------------


class TestRankingAndTruncation:
    """Sort yield-DESC + Ticker-ASC-Tie-Break, Truncation auf max_results."""

    def test_three_tickers_all_pass_ranked_desc_by_yield(
        self, stub_settings_factory: Callable[[list[str]], Settings]
    ) -> None:
        stub_settings_factory(["AAA", "BBB", "CCC"])
        # AAA mid 1.51/strike 88 → ~13.9% Yield.
        # BBB mid 2.01/strike 88 → ~18.5% Yield (Top).
        # CCC mid 1.01/strike 88 → ~9.3% Yield (Schlusslicht).
        with respx.mock(assert_all_called=True) as router:
            _ticker_router(
                router,
                {
                    "AAA": (
                        _passing_cores_payload("AAA"),
                        _passing_strikes_payload(put_bid=1.50, put_ask=1.52),
                    ),
                    "BBB": (
                        _passing_cores_payload("BBB"),
                        _passing_strikes_payload(put_bid=2.00, put_ask=2.02),
                    ),
                    "CCC": (
                        _passing_cores_payload("CCC"),
                        _passing_strikes_payload(put_bid=1.00, put_ask=1.02),
                    ),
                },
            )
            result = scan()
        assert [i.ticker for i in result] == ["BBB", "AAA", "CCC"]
        # Determinismus-Probe: yields strict descending.
        yields = [i.annualized_yield_pct for i in result]
        assert yields == sorted(yields, reverse=True)

    def test_tie_break_alphabetical_by_ticker(
        self, stub_settings_factory: Callable[[list[str]], Settings]
    ) -> None:
        stub_settings_factory(["BBB", "AAA"])
        # Identische Strikes → identische Yields → Tie-Break per Ticker ASC.
        identical = _passing_strikes_payload(put_bid=1.50, put_ask=1.52)
        with respx.mock(assert_all_called=True) as router:
            _ticker_router(
                router,
                {
                    "AAA": (_passing_cores_payload("AAA"), identical),
                    "BBB": (_passing_cores_payload("BBB"), identical),
                },
            )
            result = scan()
        assert [i.ticker for i in result] == ["AAA", "BBB"]
        assert result[0].annualized_yield_pct == pytest.approx(result[1].annualized_yield_pct)

    def test_max_results_truncates_after_sort(
        self, stub_settings_factory: Callable[[list[str]], Settings]
    ) -> None:
        stub_settings_factory(["AAA", "BBB", "CCC"])
        with respx.mock(assert_all_called=True) as router:
            _ticker_router(
                router,
                {
                    "AAA": (
                        _passing_cores_payload("AAA"),
                        _passing_strikes_payload(put_bid=1.20, put_ask=1.22),
                    ),
                    "BBB": (
                        _passing_cores_payload("BBB"),
                        _passing_strikes_payload(put_bid=2.50, put_ask=2.52),
                    ),
                    "CCC": (
                        _passing_cores_payload("CCC"),
                        _passing_strikes_payload(put_bid=1.80, put_ask=1.82),
                    ),
                },
            )
            result = scan(max_results=2)
        # BBB (Top) + CCC, AAA fällt raus.
        assert [i.ticker for i in result] == ["BBB", "CCC"]


# ---------------------------------------------------------------------------
# Per-Ticker-Resilienz
# ---------------------------------------------------------------------------


class TestPerTickerResilience:
    """Pro-Ticker-Fehler → Skip + WARN; sonstige Ticker liefern weiter."""

    def test_one_ticker_4xx_skipped_others_return(
        self,
        stub_settings_factory: Callable[[list[str]], Settings],
        loguru_warnings: list[str],
    ) -> None:
        stub_settings_factory(["AAA", "BBB", "FAIL"])
        with respx.mock(assert_all_called=False) as router:
            _ticker_router(
                router,
                {
                    "AAA": (
                        _passing_cores_payload("AAA"),
                        _passing_strikes_payload(put_bid=1.50, put_ask=1.52),
                    ),
                    "BBB": (
                        _passing_cores_payload("BBB"),
                        _passing_strikes_payload(put_bid=2.00, put_ask=2.02),
                    ),
                    "FAIL": 404,
                },
            )
            result = scan()
        assert [i.ticker for i in result] == ["BBB", "AAA"]
        assert any("FAIL" in m and "übersprungen" in m for m in loguru_warnings)

    def test_rule_failer_filtered_out(
        self, stub_settings_factory: Callable[[list[str]], Settings]
    ) -> None:
        stub_settings_factory(["GOOD", "BADERN"])
        # BADERN: Earnings in 0 Tagen → Pflichtregel 5 schlägt fehl → pflichtregeln_passed=False.
        bad_cores = _passing_cores_payload("BADERN", days_to_next_earn=0)
        with respx.mock(assert_all_called=True) as router:
            _ticker_router(
                router,
                {
                    "GOOD": (
                        _passing_cores_payload("GOOD"),
                        _passing_strikes_payload(put_bid=1.50, put_ask=1.52),
                    ),
                    "BADERN": (
                        bad_cores,
                        _passing_strikes_payload(put_bid=1.50, put_ask=1.52),
                    ),
                },
            )
            result = scan()
        assert [i.ticker for i in result] == ["GOOD"]

    def test_all_tickers_fail_returns_empty(
        self,
        stub_settings_factory: Callable[[list[str]], Settings],
        loguru_warnings: list[str],
    ) -> None:
        stub_settings_factory(["X1", "X2", "X3"])
        with respx.mock(assert_all_called=False) as router:
            _ticker_router(router, {"X1": 404, "X2": 404, "X3": 404})
            result = scan()
        assert result == []
        # 3 WARN-Logs erwartet (einer pro Ticker).
        assert sum("übersprungen" in m for m in loguru_warnings) == 3

    def test_all_rule_failers_returns_empty(
        self, stub_settings_factory: Callable[[list[str]], Settings]
    ) -> None:
        stub_settings_factory(["E1", "E2"])
        bad_payload = _passing_cores_payload("E1", days_to_next_earn=0)
        bad_payload2 = _passing_cores_payload("E2", days_to_next_earn=0)
        with respx.mock(assert_all_called=True) as router:
            _ticker_router(
                router,
                {
                    "E1": (
                        bad_payload,
                        _passing_strikes_payload(put_bid=1.50, put_ask=1.52),
                    ),
                    "E2": (
                        bad_payload2,
                        _passing_strikes_payload(put_bid=1.50, put_ask=1.52),
                    ),
                },
            )
            result = scan()
        assert result == []


# ---------------------------------------------------------------------------
# Public-Surface-Validation
# ---------------------------------------------------------------------------


class TestPublicSurface:
    def test_max_results_zero_raises_before_http(
        self, stub_settings_factory: Callable[[list[str]], Settings]
    ) -> None:
        stub_settings_factory(["AAA", "BBB"])
        # Wenn `scan` korrekt validiert, läuft NICHTS gegen respx — wir setzen
        # `assert_all_called=False` und prüfen, dass keine Route getroffen wurde.
        with respx.mock(assert_all_called=False) as router:
            cores_route = router.get(re.compile(rf"^{re.escape(BASE_URL)}/cores"))
            strikes_route = router.get(re.compile(rf"^{re.escape(BASE_URL)}/strikes"))
            with pytest.raises(ValueError, match="max_results muss > 0"):
                scan(max_results=0)
            assert cores_route.call_count == 0
            assert strikes_route.call_count == 0

    def test_negative_max_results_also_raises(
        self, stub_settings_factory: Callable[[list[str]], Settings]
    ) -> None:
        stub_settings_factory(["AAA"])
        with pytest.raises(ValueError, match="max_results muss > 0"):
            scan(max_results=-3)

    def test_missing_token_raises_config_error(
        self, monkeypatch: pytest.MonkeyPatch, default_settings: Settings
    ) -> None:
        from pydantic import SecretStr

        from csp import config as csp_config

        patched = default_settings.model_copy(update={"orats_token": SecretStr("")})
        monkeypatch.setattr(
            csp_config.Settings,
            "load",
            classmethod(lambda cls, *a, **kw: patched),
        )
        with pytest.raises(ConfigError, match="ORATS_TOKEN"):
            scan()

    def test_csp_scan_is_public_export(self) -> None:
        assert csp.scan is scan
        assert "scan" in csp.__all__


# ---------------------------------------------------------------------------
# Determinismus (NFR20)
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_two_runs_field_equivalent_and_same_order(
        self, stub_settings_factory: Callable[[list[str]], Settings]
    ) -> None:
        """Patch F7: Pickle-Bytes-Vergleich war Pydantic-/Protocol-Versions-fragil;
        Pydantic-Modell-Equality plus expliziter Ticker-Reihenfolge-Vergleich
        liefert dieselbe Determinismus-Aussage robust."""
        stub_settings_factory(["AAA", "BBB", "CCC"])
        scenario = {
            "AAA": (
                _passing_cores_payload("AAA"),
                _passing_strikes_payload(put_bid=1.50, put_ask=1.52),
            ),
            "BBB": (
                _passing_cores_payload("BBB"),
                _passing_strikes_payload(put_bid=2.00, put_ask=2.02),
            ),
            "CCC": (
                _passing_cores_payload("CCC"),
                _passing_strikes_payload(put_bid=1.00, put_ask=1.02),
            ),
        }
        with respx.mock(assert_all_called=True) as router:
            _ticker_router(router, scenario)
            run_a = scan()
        with respx.mock(assert_all_called=True) as router:
            _ticker_router(router, scenario)
            run_b = scan()
        # Modell-Equality (Pydantic v2 BaseModel.__eq__) + Reihenfolge.
        assert run_a == run_b
        assert [i.ticker for i in run_a] == [i.ticker for i in run_b]
        # Yields auf 6 Nachkommastellen identisch — fängt Float-Drift in der
        # Yield-Berechnung ab, falls Order-of-Operations je nach Lauf wechselte.
        assert [round(i.annualized_yield_pct, 6) for i in run_a] == [
            round(i.annualized_yield_pct, 6) for i in run_b
        ]


# ---------------------------------------------------------------------------
# Make-Idea-Factory-Smoke
# ---------------------------------------------------------------------------


class TestMakeIdeaFactory:
    """Vergewissert sich, dass die `make_idea`-Conftest-Fixture saubere `Idea` baut."""

    def test_factory_produces_valid_idea(self, make_idea: Callable[..., Idea]) -> None:
        i = make_idea("xyz", 18.0)
        assert isinstance(i, Idea)
        assert i.ticker == "XYZ"
        assert i.annualized_yield_pct == 18.0
        assert i.pflichtregeln_passed is True

    def test_factory_failed_idea(self, make_idea: Callable[..., Idea]) -> None:
        i = make_idea("aaa", 0.0, passed=False)
        assert i.pflichtregeln_passed is False
        assert i.reasons  # nicht leer


# ---------------------------------------------------------------------------
# Patches aus Slice-4-Review (P2, P11, P12, P13, A4-AC#1, F8 Filter-Smoke)
# ---------------------------------------------------------------------------


class TestPatches:
    """Tests für die in der Adversarial-Review aufgedeckten Lücken (siehe Spec
    Change Log Eintrag "2026-04-29 — Review iteration 1")."""

    def test_p2_future_as_of_raises_before_http(
        self, stub_settings_factory: Callable[[list[str]], Settings]
    ) -> None:
        """Patch P2: `as_of` in der Zukunft → `ValueError` am Public-Rand,
        kein HTTP-Aufruf gegen `/hist/*`. Spiegelt `csp.idea`'s Verhalten."""
        stub_settings_factory(["AAA"])
        future = datetime.now(ZoneInfo("Europe/Berlin")).date() + timedelta(days=1)
        with respx.mock(assert_all_called=False) as router:
            cores_route = router.get(re.compile(rf"^{re.escape(BASE_URL)}/hist/cores"))
            with pytest.raises(ValueError, match="liegt in der Zukunft"):
                scan(as_of=future)
            assert cores_route.call_count == 0

    def test_p11_duplicate_tickers_dedupe(
        self, stub_settings_factory: Callable[[list[str]], Settings]
    ) -> None:
        """Patch P11: Duplikate im Universum führen nicht zu doppelten HTTP-Calls
        und nicht zu doppelten `Idea`-Einträgen."""
        stub_settings_factory(["AAA", "AAA", "BBB"])
        with respx.mock(assert_all_called=True) as router:
            _ticker_router(
                router,
                {
                    "AAA": (
                        _passing_cores_payload("AAA"),
                        _passing_strikes_payload(put_bid=1.50, put_ask=1.52),
                    ),
                    "BBB": (
                        _passing_cores_payload("BBB"),
                        _passing_strikes_payload(put_bid=2.00, put_ask=2.02),
                    ),
                },
            )
            result = scan()
            # Inside the `with` block: respx state is still live.
            # Genau 2 unique Tickers ⇒ 2 cores + 2 strikes = 4 Requests insgesamt
            # (NICHT 3 cores + 3 strikes wie ohne Dedupe).
            cores_calls = [c for c in router.calls if c.request.url.path.endswith("/cores")]
            assert len(cores_calls) == 2
        assert [i.ticker for i in result] == ["BBB", "AAA"]

    def test_p12_empty_universe_raises_config_error(
        self, monkeypatch: pytest.MonkeyPatch, default_settings: Settings
    ) -> None:
        """Patch P12: leeres `allowed_tickers` → `ConfigError` (defense-in-depth,
        auch wenn `pydantic-settings` `min_length=1` heute schon prüft).

        Konstruiert ein eigenes `UniverseConfig` via `model_construct` (bypassed
        Validators) statt das Session-Scoped `default_settings` zu mutieren —
        sonst leakt der leere Universe-Zustand in nachfolgende Tests.
        """
        from pydantic import SecretStr

        from csp import config as csp_config

        empty_universe = csp_config.UniverseConfig.model_construct(allowed_tickers=[])
        patched = default_settings.model_copy(
            update={
                "orats_token": SecretStr(FAKE_TOKEN),
                "orats_base_url": BASE_URL,
                "universe": empty_universe,
            }
        )
        monkeypatch.setattr(
            csp_config.Settings,
            "load",
            classmethod(lambda cls, *a, **kw: patched),
        )
        with pytest.raises(ConfigError, match="allowed_tickers"):
            scan()

    def test_p13_single_httpx_client_shared_across_tickers(
        self,
        monkeypatch: pytest.MonkeyPatch,
        stub_settings_factory: Callable[[list[str]], Settings],
    ) -> None:
        """Patch P13: pinnt die "ONE shared `httpx.AsyncClient`"-Invariante aus
        Spec §Always (NFR5). Ein zukünftiger Refactor, der pro Ticker einen
        Client öffnet, würde diesen Test umgehen — daher Counter via Spy."""
        stub_settings_factory(["AAA", "BBB", "CCC"])
        original_init = httpx.AsyncClient.__init__
        instantiations: list[float] = []

        def counting_init(self: httpx.AsyncClient, *args: Any, **kwargs: Any) -> None:
            instantiations.append(0.0)
            original_init(self, *args, **kwargs)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", counting_init)
        with respx.mock(assert_all_called=True) as router:
            _ticker_router(
                router,
                {
                    "AAA": (
                        _passing_cores_payload("AAA"),
                        _passing_strikes_payload(put_bid=1.50, put_ask=1.52),
                    ),
                    "BBB": (
                        _passing_cores_payload("BBB"),
                        _passing_strikes_payload(put_bid=2.00, put_ask=2.02),
                    ),
                    "CCC": (
                        _passing_cores_payload("CCC"),
                        _passing_strikes_payload(put_bid=1.00, put_ask=1.02),
                    ),
                },
            )
            scan()
        # Genau eine `httpx.AsyncClient`-Instanz für die ganze Scan-Sitzung.
        assert len(instantiations) == 1, (
            f"Erwartet: 1 AsyncClient-Instanz, gefunden: {len(instantiations)}"
        )

    def test_ac1_three_ticker_universe_one_fails_two_tie_at_yield(
        self,
        stub_settings_factory: Callable[[list[str]], Settings],
        loguru_warnings: list[str],
    ) -> None:
        """Spec AC #1 verbatim: 3-Ticker-Universum, 2 passieren mit identischer
        Yield, 1 wirft `ORATSDataError`. Erwartet: ranked Liste Länge 2,
        AAA vor BBB (Ticker-ASC-Tie-Break), 1 WARN-Log für FAIL."""
        stub_settings_factory(["AAA", "BBB", "FAIL"])
        identical_strikes = _passing_strikes_payload(put_bid=1.50, put_ask=1.52)
        with respx.mock(assert_all_called=False) as router:
            _ticker_router(
                router,
                {
                    "AAA": (_passing_cores_payload("AAA"), identical_strikes),
                    "BBB": (_passing_cores_payload("BBB"), identical_strikes),
                    "FAIL": 404,
                },
            )
            result = scan()
        assert len(result) == 2
        assert result[0].ticker == "AAA"
        assert result[1].ticker == "BBB"
        # Identische Yields trotz Tie-Break-Pfad.
        assert result[0].annualized_yield_pct == pytest.approx(result[1].annualized_yield_pct)
        # Genau 1 Skip-WARN, der "FAIL" nennt.
        assert sum("FAIL" in m for m in loguru_warnings) == 1


# Cassette-Smoke wurde während der Implementierung gestrichen — siehe spec
# Change Log "2026-04-29 — Implementation deviation". Begründung: ein
# Live-`strikes_NOW.yaml` existiert heute nicht (nur `cores_NOW.yaml` und die
# historischen `hist_*_NOW_20260424.yaml`-Pärchen). Stacked `use_cassette` ist
# bei VCR.py undefiniertes Verhalten. Die Orchestrierungs-Invariante wird
# durch die respx-Integrationen oben äquivalent abgedeckt; reale Cassette-Pfade
# bleiben über den manuellen `Verification`-Smoke verifizierbar.
