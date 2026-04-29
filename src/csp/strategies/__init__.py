"""Strategie-Module der csp-Bibliothek.

MVP enthält ausschließlich CSP. Iron Condor, Strangle und Put-Credit-Spread sind
für die Growth-Phase deferred — `AbstractStrategy` wird erst dann eingeführt,
wenn mehr als eine Strategie tatsächlich existiert.
"""

from csp.strategies.csp import build_idea

__all__ = ["build_idea"]
