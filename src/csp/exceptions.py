"""Typisierte Ausnahmen für die csp-Bibliothek."""

from __future__ import annotations


class ConfigError(Exception):
    """Konfigurationsdatei fehlt oder ist ungültig."""


class PflichtregelError(Exception):
    """Integritätsfehler im Pflichtregeln-Modul (kein normaler Regelausfall)."""


class ORATSDataError(Exception):
    """ORATS-Vendor-Fehler (4xx final oder 5xx/429 nach Retries).

    Trägt HTTP-Status, Response-Body (auf 200 Zeichen geschnitten) und die
    Anfrage-URL mit redigiertem Token. Token oder andere Secrets dürfen
    weder in `args` noch in der Repräsentation auftauchen.
    """

    def __init__(self, *, status: int, body: str, url_redacted: str) -> None:
        self.status = status
        self.body = body
        self.url_redacted = url_redacted
        message = f"ORATS-Fehler {status} bei {url_redacted}: {body[:200]}"
        super().__init__(message)
