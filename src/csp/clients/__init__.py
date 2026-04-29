"""Vendor-Client-Pakete (ORATS, FMP, IVolatility, Sheets).

Re-exportiert `OratsClient` für ergonomische Imports von der Slice-Grenze aus.
"""

from __future__ import annotations

from csp.clients.orats import OratsClient

__all__ = ["OratsClient"]
