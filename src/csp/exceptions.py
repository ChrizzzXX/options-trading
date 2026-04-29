"""Typisierte Ausnahmen für die csp-Bibliothek (Slice: Pflichtregeln-Gate)."""

from __future__ import annotations


class ConfigError(Exception):
    """Konfigurationsdatei fehlt oder ist ungültig."""


class PflichtregelError(Exception):
    """Integritätsfehler im Pflichtregeln-Modul (kein normaler Regelausfall)."""
