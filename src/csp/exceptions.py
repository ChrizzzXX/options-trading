"""Typisierte Ausnahmen für die csp-Bibliothek."""

from __future__ import annotations


class ConfigError(Exception):
    """Konfigurationsdatei fehlt oder ist ungültig."""


class PflichtregelError(Exception):
    """Integritätsfehler im Pflichtregeln-Modul (kein normaler Regelausfall)."""


class ORATSDataError(Exception):
    """ORATS-Vendor-Fehler (4xx final oder 5xx/429/Transport nach Retries).

    Trägt HTTP-Status, Response-Body (auf 200 Zeichen geschnitten, secret-redigiert)
    und die Anfrage-URL mit redigiertem Token. Token oder andere Secrets dürfen
    weder in `args` noch in der Repräsentation auftauchen.

    Status-Sentinels:
    - `0` oder `-1`: Transport-Fehler (Connect/Read/Timeout/Pool — kein HTTP-Status).
    - `200`: Subklassen wie `ORATSEmptyDataError` (HTTP-OK, aber leere `data`-Liste).
    - `4xx`/`5xx`/`429`: HTTP-Statuscode wie geliefert.
    """

    def __init__(self, *, status: int, body: str, url_redacted: str) -> None:
        # Lazy-Import, um zirkuläre Imports zu vermeiden (orats.py → exceptions).
        from csp.clients.orats import _redact_text

        self.status = status
        self.body = _redact_text(body)
        self.url_redacted = url_redacted
        message = f"ORATS-Fehler {status} bei {url_redacted}: {self.body[:200]}"
        super().__init__(message)


class ORATSEmptyDataError(ORATSDataError):
    """ORATS lieferte HTTP 200, aber `data` ist leer.

    Eigene Subklasse, damit Caller "kein Datensatz" von echten Vendor-Fehlern
    unterscheiden können. Status bleibt `200` — HTTP war OK, semantisch nicht.
    """
