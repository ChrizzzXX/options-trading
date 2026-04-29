"""csp.lifecycle — Trade-Lebenszyklus (Slice 6).

`state_machine.py` ist die einzige Quelle der Wahrheit über erlaubte Status-
Übergänge. MVP-Scope: manuelle Position-Pflege via `csp.log_trade` /
`csp.close_trade`; keine automatischen Übergänge. `take_profit_pending` ist der
einzige Zwischenstatus; `assigned`, `closed_profit`, `closed_loss`,
`emergency_close` sind alle terminal.
"""

from csp.lifecycle.state_machine import (
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    TradeStatus,
    valid_transition,
)

__all__ = [
    "TERMINAL_STATES",
    "VALID_TRANSITIONS",
    "TradeStatus",
    "valid_transition",
]
