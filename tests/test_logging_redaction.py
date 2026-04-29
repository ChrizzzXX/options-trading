"""Tests für den globalen Loguru-Secret-Scrubber-Filter (`csp._logging`).

Emittiert Log-Records mit jedem der vier bekannten Secret-Patterns und stellt
sicher, dass `<REDACTED>` in der Ausgabe steht und das Klartext-Secret nicht.
"""

from __future__ import annotations

from typing import Any

import pytest
from loguru import logger

from csp._logging import _scrub, install_secret_redactor


@pytest.fixture
def captured_logs() -> Any:
    """Fängt Loguru-Records via temporärem Sink, der den Filter passieren lässt."""
    install_secret_redactor()  # Stellt sicher, dass der Scrubber aktiv ist.
    captured: list[str] = []
    sink_id = logger.add(captured.append, format="{message}", filter=lambda r: True)
    try:
        yield captured
    finally:
        logger.remove(sink_id)


def test_scrub_redacts_token_query_param() -> None:
    out = _scrub("GET /cores?ticker=NOW&token=abc123secret")
    assert "abc123secret" not in out
    assert "<REDACTED>" in out


def test_scrub_redacts_apikey_query_param() -> None:
    out = _scrub("https://example.com/api?apikey=plzhide&foo=bar")
    assert "plzhide" not in out
    assert "<REDACTED>" in out
    assert "foo=bar" in out


def test_scrub_redacts_authorization_bearer() -> None:
    out = _scrub("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig")
    assert "eyJhbGciOiJIUzI1NiJ9" not in out
    assert "Bearer <REDACTED>" in out


def test_scrub_redacts_ivolatility_env_pattern() -> None:
    out = _scrub("config dump: IVOLATILITY_API_KEY=supersecret123 plus other stuff")
    assert "supersecret123" not in out
    assert "<REDACTED>" in out
    assert "other stuff" in out


def test_logger_emits_redacted_message_for_token_query(captured_logs: list[str]) -> None:
    logger.info("ORATS request: https://api.orats.io/datav2/cores?token=leaky-token-xyz")
    assert any("<REDACTED>" in line for line in captured_logs)
    assert all("leaky-token-xyz" not in line for line in captured_logs)


def test_logger_emits_redacted_message_for_apikey_query(captured_logs: list[str]) -> None:
    logger.warning("FMP request failed: ?apikey=fmp-secret-zzz&q=AAPL")
    assert any("<REDACTED>" in line for line in captured_logs)
    assert all("fmp-secret-zzz" not in line for line in captured_logs)


def test_logger_emits_redacted_message_for_bearer_header(captured_logs: list[str]) -> None:
    logger.error("Header dump: Authorization: Bearer jwt-token-bearer-shh")
    assert any("<REDACTED>" in line for line in captured_logs)
    assert all("jwt-token-bearer-shh" not in line for line in captured_logs)


def test_logger_emits_redacted_message_for_ivolatility_env(captured_logs: list[str]) -> None:
    logger.debug("env: IVOLATILITY_API_KEY=ivol-secret-987 PORT=8080")
    assert any("<REDACTED>" in line for line in captured_logs)
    assert all("ivol-secret-987" not in line for line in captured_logs)


def test_extra_string_field_is_redacted(captured_logs: list[str]) -> None:
    """`logger.bind(...)` mit String-Extras wird ebenfalls scrubbed."""
    bound = logger.bind(url="https://api.x.com/q?token=hidden-extra-secret")
    bound.info("structured log")
    # Filter mutiert `record["extra"]`, aber Sink-Format hier loggt nur `{message}`.
    # Direkter Filter-Test stattdessen:
    record: dict[str, Any] = {
        "message": "test",
        "extra": {"url": "?token=hidden-extra-secret"},
    }
    from csp._logging import _secret_redactor

    assert _secret_redactor(record) is True
    assert "hidden-extra-secret" not in record["extra"]["url"]
    assert "<REDACTED>" in record["extra"]["url"]
