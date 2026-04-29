"""Tests für `OratsClient` — Retry-Policy (respx) + Antwort-Parsing (Cassettes).

Drei Schichten:
- `TestRetryPolicy`: `respx`-Mocks pinnen 4xx/5xx/429-Verhalten und Token-Redaktion.
- `TestCassettes`: vcrpy-Cassettes pinnen die echte ORATS-Antwortform für
  `/cores` (heute), `/hist/cores` und `/hist/strikes` für 2026-04-24.
- `TestRecording`: einmaliger Live-HTTP-Lauf zum Aufnehmen der Cassettes
  (mit `pytest --vcr-record=once -k recording`); im Standard-Lauf übersprungen
  (Marker nicht selektiert; record_mode="none" als Default).

Cassettes werden direkt via `vcr.VCR(...).use_cassette(name)` benutzt — die
pytest-vcr-Auto-Naming-Magie ist hier zu inflexibel (Class.test-Namen statt
gewünschter `cores_NOW.yaml`-Pfade).

Token wird ausschließlich aus `os.environ` gelesen — niemals als Literal.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Iterator
from datetime import date
from pathlib import Path

import httpx
import pytest
import respx
from vcr import VCR

from csp.clients.orats import (
    RATE_LIMIT_PER_MIN,
    OratsClient,
    _put_delta_from_call_delta,
    _redact_url,
)
from csp.exceptions import ORATSDataError
from csp.models.core import OratsCore, OratsStrike

BASE_URL = "https://api.orats.io/datav2"
FAKE_TOKEN = "test-token-not-real-12345"
CASSETTE_DIR = Path(__file__).parent / "cassettes" / "orats"


def _vcr(record_mode: str = "none") -> VCR:
    """VCR-Instanz mit Token-Scrubbing und Standard-Replay-only-Modus."""
    return VCR(
        cassette_library_dir=str(CASSETTE_DIR),
        record_mode=record_mode,
        filter_query_parameters=["token", "apikey"],
    )


def _record_mode(request: pytest.FixtureRequest) -> str:
    """Liest `--vcr-record` aus pytest-vcr; default `none`."""
    cli = request.config.getoption("--vcr-record")
    return cli or "none"


@pytest.fixture
def vcr_recorder(request: pytest.FixtureRequest) -> Iterator[VCR]:
    """Liefert eine VCR-Instanz, deren record_mode von der CLI gesteuert wird."""
    yield _vcr(_record_mode(request))


def _live_token() -> str:
    """Lebendiges Token für Token-Leak-Asserts (None falls nicht in der Umgebung)."""
    return os.environ.get("ORATS_TOKEN", "")


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Setzt `asyncio.sleep` auf einen No-Op, damit Backoff-Tests schnell laufen."""

    async def _noop(_seconds: float) -> None:
        return None

    monkeypatch.setattr("csp.clients.orats.asyncio.sleep", _noop)


def _run(coro):  # type: ignore[no-untyped-def]
    return asyncio.run(coro)


class TestRedactUrlAndPutDelta:
    """Reine Hilfsfunktionen — separat getestet, damit der Aufruferpfad simpel bleibt."""

    def test_redact_url_replaces_token(self) -> None:
        url = f"https://api.orats.io/datav2/cores?ticker=NOW&token={FAKE_TOKEN}"
        redacted = _redact_url(url, FAKE_TOKEN)
        assert FAKE_TOKEN not in redacted
        assert "<REDACTED>" in redacted

    def test_redact_url_with_empty_token_passes_through(self) -> None:
        # Defensive: leeres Token darf den URL nicht zerstören (str.replace mit "" ist No-Op).
        url = "https://api.orats.io/datav2/cores?ticker=NOW"
        assert _redact_url(url, "") == url

    def test_put_delta_from_call_delta_subtracts_one(self) -> None:
        assert _put_delta_from_call_delta(0.78) == pytest.approx(-0.22)
        assert _put_delta_from_call_delta(0.05) == pytest.approx(-0.95)
        assert _put_delta_from_call_delta(1.0) == pytest.approx(0.0)


class TestRetryPolicy:
    """Verifiziert 4xx-Sofortabbruch, 5xx/429-Backoff, Token-Redaktion in Exceptions."""

    def test_4xx_raises_immediately_one_attempt(self) -> None:
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{BASE_URL}/cores").mock(
                return_value=httpx.Response(401, text="unauthorized")
            )

            async def call() -> None:
                async with httpx.AsyncClient() as client:
                    orats = OratsClient(client, base_url=BASE_URL, token=FAKE_TOKEN)
                    await orats.cores("NOW")

            with pytest.raises(ORATSDataError) as exc_info:
                _run(call())

            assert route.call_count == 1
            assert exc_info.value.status == 401
            # Token darf weder in der String-Repräsentation noch in `args` auftauchen.
            assert FAKE_TOKEN not in str(exc_info.value)
            assert "<REDACTED>" in str(exc_info.value)

    def test_5xx_retries_three_times_then_raises(self, no_sleep: None) -> None:
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{BASE_URL}/cores").mock(
                return_value=httpx.Response(503, text="service unavailable")
            )

            async def call() -> None:
                async with httpx.AsyncClient() as client:
                    orats = OratsClient(client, base_url=BASE_URL, token=FAKE_TOKEN)
                    await orats.cores("NOW")

            with pytest.raises(ORATSDataError) as exc_info:
                _run(call())

            assert route.call_count == 3
            assert exc_info.value.status == 503

    def test_429_then_200_returns_model(self, no_sleep: None) -> None:
        success_payload = {
            "data": [
                {
                    "ticker": "NOW",
                    "pxAtmIv": 90.0,
                    "sectorName": "Technology",
                    "mktCap": 100_000_000,
                    "ivPctile1y": 80,
                    "daysToNextErn": 30,
                    "avgOptVolu20d": 100_000.0,
                }
            ]
        }
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{BASE_URL}/cores").mock(
                side_effect=[
                    httpx.Response(429, text="rate limited"),
                    httpx.Response(200, json=success_payload),
                ]
            )

            async def call() -> OratsCore:
                async with httpx.AsyncClient() as client:
                    orats = OratsClient(client, base_url=BASE_URL, token=FAKE_TOKEN)
                    return await orats.cores("NOW")

            result = _run(call())
            assert route.call_count == 2
            assert isinstance(result, OratsCore)
            assert result.ticker == "NOW"
            assert result.ivr == 80

    def test_4xx_message_contains_redacted_url_not_live_token(self) -> None:
        """Auch wenn das echte Token gesetzt ist, darf es nicht in der Exception erscheinen."""
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{BASE_URL}/cores").mock(return_value=httpx.Response(403, text="forbidden"))

            async def call() -> None:
                async with httpx.AsyncClient() as client:
                    orats = OratsClient(client, base_url=BASE_URL, token=FAKE_TOKEN)
                    await orats.cores("NOW")

            with pytest.raises(ORATSDataError) as exc_info:
                _run(call())

            msg = str(exc_info.value)
            assert FAKE_TOKEN not in msg
            assert "<REDACTED>" in msg
            live = _live_token()
            if live:
                assert live not in msg

    def test_rate_limit_constant_documented(self) -> None:
        # project-context.md: ORATS-Plan-Tier = 1000 req/min.
        assert RATE_LIMIT_PER_MIN == 1_000

    def test_empty_data_raises_oratsdataerror(self) -> None:
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{BASE_URL}/cores").mock(
                return_value=httpx.Response(200, json={"data": []})
            )

            async def call() -> None:
                async with httpx.AsyncClient() as client:
                    orats = OratsClient(client, base_url=BASE_URL, token=FAKE_TOKEN)
                    await orats.cores("XXX")

            with pytest.raises(ORATSDataError) as exc_info:
                _run(call())
            assert exc_info.value.status == 200
            assert "leere data-Liste" in str(exc_info.value)

    def test_strikes_filters_none_quotes_and_converts_call_delta_to_put_delta(
        self,
    ) -> None:
        payload = {
            "data": [
                # gültiger Eintrag — DTE 56, Strike 78
                {
                    "strike": 78,
                    "delta": 0.78,
                    "dte": 56,
                    "putAskPrice": 2.85,
                    "putBidPrice": 2.7,
                },
                # gefiltert: putBidPrice fehlt
                {
                    "strike": 80,
                    "delta": 0.7,
                    "dte": 56,
                    "putAskPrice": 3.0,
                    "putBidPrice": None,
                },
                # gefiltert: delta fehlt
                {
                    "strike": 82,
                    "delta": None,
                    "dte": 56,
                    "putAskPrice": 3.5,
                    "putBidPrice": 3.4,
                },
            ]
        }
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{BASE_URL}/hist/strikes").mock(
                return_value=httpx.Response(200, json=payload)
            )

            async def call() -> list[OratsStrike]:
                async with httpx.AsyncClient() as client:
                    orats = OratsClient(client, base_url=BASE_URL, token=FAKE_TOKEN)
                    return await orats.strikes("NOW", trade_date=date(2026, 4, 24))

            results = _run(call())
            assert len(results) == 1
            assert results[0].strike == 78
            assert results[0].delta == pytest.approx(-0.22)
            assert results[0].dte == 56

    def test_strikes_live_path_without_trade_date(self) -> None:
        payload = {"data": []}
        with respx.mock(assert_all_called=True) as router:
            route = router.get(f"{BASE_URL}/strikes").mock(
                return_value=httpx.Response(200, json=payload)
            )

            async def call() -> list[OratsStrike]:
                async with httpx.AsyncClient() as client:
                    orats = OratsClient(client, base_url=BASE_URL, token=FAKE_TOKEN)
                    return await orats.strikes("NOW")

            assert _run(call()) == []
            assert route.call_count == 1

    def test_ivrank_and_summaries_return_first_item_or_empty(self) -> None:
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{BASE_URL}/ivrank").mock(
                return_value=httpx.Response(200, json={"data": [{"ticker": "NOW", "ivr": 96}]})
            )
            router.get(f"{BASE_URL}/summaries").mock(
                return_value=httpx.Response(200, json={"data": []})
            )

            async def call() -> tuple[dict[str, object], dict[str, object]]:
                async with httpx.AsyncClient() as client:
                    orats = OratsClient(client, base_url=BASE_URL, token=FAKE_TOKEN)
                    iv = await orats.ivrank("NOW")
                    s = await orats.summaries("NOW")
                    return iv, s

            iv, s = _run(call())
            assert iv == {"ticker": "NOW", "ivr": 96}
            assert s == {}


class TestCassettes:
    """Liest die echten Antwortformen aus den eingespielten Cassetten und parst sie."""

    def test_cores_now_parses(self, vcr_recorder: VCR) -> None:
        async def call() -> OratsCore:
            async with httpx.AsyncClient() as client:
                orats = OratsClient(client, base_url=BASE_URL, token=FAKE_TOKEN)
                return await orats.cores("NOW")

        with vcr_recorder.use_cassette("cores_NOW.yaml"):
            core = _run(call())

        assert core.ticker == "NOW"
        assert core.under_price > 0
        assert core.mkt_cap_thousands > 0
        assert core.sector
        assert isinstance(core.days_to_next_earn, int)

    def test_hist_strikes_now_20260424_parses(self, vcr_recorder: VCR) -> None:
        async def call() -> list[OratsStrike]:
            async with httpx.AsyncClient() as client:
                orats = OratsClient(client, base_url=BASE_URL, token=FAKE_TOKEN)
                return await orats.strikes("NOW", trade_date=date(2026, 4, 24))

        with vcr_recorder.use_cassette("hist_strikes_NOW_20260424.yaml"):
            strikes = _run(call())

        assert len(strikes) > 0
        candidates = [s for s in strikes if s.strike == 78.0]
        assert candidates, "Strike 78 nicht in der NOW-Cassette gefunden"
        # NOW-78 mit DTE in [55, 56] muss vorhanden sein. Reale Daten zeigen DTE=56;
        # PRD-Heuristik sagte 55 — siehe Spec Change Log Reconciliation.
        target = [s for s in candidates if s.dte in (55, 56)]
        assert target, (
            f"NOW-78 mit DTE 55 oder 56 nicht gefunden, sah: {[s.dte for s in candidates]}"
        )

    def test_hist_cores_now_20260424_parses(self, vcr_recorder: VCR) -> None:
        """Historischer /cores-Snapshot für 2026-04-24 — Quellwerte für Regression."""

        async def call() -> dict[str, object]:
            async with httpx.AsyncClient() as client:
                orats = OratsClient(client, base_url=BASE_URL, token=FAKE_TOKEN)
                return await orats._request_with_retry(
                    "GET", "/hist/cores", {"ticker": "NOW", "tradeDate": "20260424"}
                )

        with vcr_recorder.use_cassette("hist_cores_NOW_20260424.yaml"):
            payload = _run(call())

        items = payload["data"]
        assert isinstance(items, list)
        assert len(items) == 1
        core = OratsCore.model_validate(items[0])
        assert core.ticker == "NOW"
        assert core.under_price > 0


@pytest.mark.recording
class TestRecording:
    """Live-HTTP — nur via `pytest --vcr-record=once -k recording`.

    Der Standard-Pytest-Lauf überspringt diese Klasse implizit, weil der
    Recording-Marker nicht selektiert wird; zusätzlich greift `record_mode="none"`
    in `vcr_recorder` und blockiert echte HTTP-Aufrufe in den Cassette-Tests.
    """

    def test_record_cores_now(self, vcr_recorder: VCR) -> None:
        token = os.environ.get("ORATS_TOKEN", "")
        if not token:
            pytest.skip("ORATS_TOKEN nicht gesetzt — Recording übersprungen")
        base_url = os.environ.get("ORATS_BASE_URL", BASE_URL)

        async def call() -> OratsCore:
            async with httpx.AsyncClient(timeout=30.0) as client:
                orats = OratsClient(client, base_url=base_url, token=token)
                return await orats.cores("NOW")

        with vcr_recorder.use_cassette("cores_NOW.yaml"):
            core = _run(call())
        assert core.ticker == "NOW"

    def test_record_hist_strikes_now_20260424(self, vcr_recorder: VCR) -> None:
        token = os.environ.get("ORATS_TOKEN", "")
        if not token:
            pytest.skip("ORATS_TOKEN nicht gesetzt — Recording übersprungen")
        base_url = os.environ.get("ORATS_BASE_URL", BASE_URL)

        async def call() -> list[OratsStrike]:
            async with httpx.AsyncClient(timeout=30.0) as client:
                orats = OratsClient(client, base_url=base_url, token=token)
                return await orats.strikes("NOW", trade_date=date(2026, 4, 24))

        with vcr_recorder.use_cassette("hist_strikes_NOW_20260424.yaml"):
            strikes = _run(call())
        assert len(strikes) > 0

    def test_record_hist_cores_now_20260424(self, vcr_recorder: VCR) -> None:
        token = os.environ.get("ORATS_TOKEN", "")
        if not token:
            pytest.skip("ORATS_TOKEN nicht gesetzt — Recording übersprungen")
        base_url = os.environ.get("ORATS_BASE_URL", BASE_URL)

        async def call() -> dict[str, object]:
            async with httpx.AsyncClient(timeout=30.0) as client:
                orats = OratsClient(client, base_url=base_url, token=token)
                return await orats._request_with_retry(
                    "GET", "/hist/cores", {"ticker": "NOW", "tradeDate": "20260424"}
                )

        with vcr_recorder.use_cassette("hist_cores_NOW_20260424.yaml"):
            payload = _run(call())
        assert payload.get("data")


def test_public_reexports_resolve() -> None:
    """`csp.OratsClient`, `csp.ORATSDataError`, `csp.orats_health_check` müssen auflösen."""
    import csp

    assert csp.OratsClient is OratsClient
    assert csp.ORATSDataError is ORATSDataError
    assert callable(csp.orats_health_check)


class TestHealthCheck:
    """`orats_health_check` — sync-wrapper um async-`OratsClient.cores`."""

    def test_raises_config_error_when_token_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from csp.exceptions import ConfigError
        from csp.health import orats_health_check

        monkeypatch.delenv("ORATS_TOKEN", raising=False)
        with pytest.raises(ConfigError, match="ORATS_TOKEN"):
            orats_health_check("NOW")

    def test_returns_orats_core_with_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Pinnt den Sync-Wrapper-Pfad: respx fängt die HTTP-Anfrage,
        `asyncio.run` wird tatsächlich durchlaufen."""
        from csp.health import orats_health_check

        monkeypatch.setenv("ORATS_TOKEN", FAKE_TOKEN)
        monkeypatch.setenv("ORATS_BASE_URL", BASE_URL)
        payload = {
            "data": [
                {
                    "ticker": "NOW",
                    "pxAtmIv": 90.0,
                    "sectorName": "Technology",
                    "mktCap": 100_000_000,
                    "ivPctile1y": 80,
                    "daysToNextErn": 30,
                    "avgOptVolu20d": 100_000.0,
                }
            ]
        }
        with respx.mock(assert_all_called=True) as router:
            router.get(f"{BASE_URL}/cores").mock(return_value=httpx.Response(200, json=payload))
            core = orats_health_check("NOW")
        assert isinstance(core, OratsCore)
        assert core.ticker == "NOW"
