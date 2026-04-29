"""100%-Coverage-Test für `csp.lifecycle.state_machine` (Slice 6, project rule)."""

from __future__ import annotations

import pytest

from csp.lifecycle.state_machine import (
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    TradeStatus,
    valid_transition,
)


class TestTradeStatus:
    def test_string_values(self) -> None:
        # `StrEnum` → Werte sind Strings, direkt persistierbar.
        assert TradeStatus.OPEN == "open"
        assert TradeStatus.CLOSED_PROFIT == "closed_profit"

    def test_all_six_states_defined(self) -> None:
        # Verträgt sich mit MVP-Scope: 6 Status — ASSIGNED bleibt terminal.
        assert {s.value for s in TradeStatus} == {
            "open",
            "take_profit_pending",
            "closed_profit",
            "closed_loss",
            "assigned",
            "emergency_close",
        }

    def test_terminal_set(self) -> None:
        assert (
            frozenset(
                {
                    TradeStatus.CLOSED_PROFIT,
                    TradeStatus.CLOSED_LOSS,
                    TradeStatus.ASSIGNED,
                    TradeStatus.EMERGENCY_CLOSE,
                }
            )
            == TERMINAL_STATES
        )


class TestTransitionsTable:
    def test_open_can_go_to_all_terminal_states_and_pending(self) -> None:
        assert VALID_TRANSITIONS[TradeStatus.OPEN] == frozenset(
            {
                TradeStatus.CLOSED_PROFIT,
                TradeStatus.CLOSED_LOSS,
                TradeStatus.ASSIGNED,
                TradeStatus.EMERGENCY_CLOSE,
                TradeStatus.TAKE_PROFIT_PENDING,
            }
        )

    def test_take_profit_pending_only_to_closed_profit(self) -> None:
        assert VALID_TRANSITIONS[TradeStatus.TAKE_PROFIT_PENDING] == frozenset(
            {TradeStatus.CLOSED_PROFIT}
        )

    @pytest.mark.parametrize(
        "terminal_state",
        [
            TradeStatus.CLOSED_PROFIT,
            TradeStatus.CLOSED_LOSS,
            TradeStatus.ASSIGNED,
            TradeStatus.EMERGENCY_CLOSE,
        ],
    )
    def test_terminal_states_have_no_outgoing(self, terminal_state: TradeStatus) -> None:
        assert VALID_TRANSITIONS[terminal_state] == frozenset()

    def test_every_status_keyed_in_table(self) -> None:
        # Schutz vor "neue Status hinzugefügt, aber Tabelle vergessen".
        assert set(VALID_TRANSITIONS.keys()) == set(TradeStatus)


class TestValidTransition:
    @pytest.mark.parametrize(
        "from_status, to_status, expected",
        [
            # OPEN → all five allowed targets.
            (TradeStatus.OPEN, TradeStatus.CLOSED_PROFIT, True),
            (TradeStatus.OPEN, TradeStatus.CLOSED_LOSS, True),
            (TradeStatus.OPEN, TradeStatus.ASSIGNED, True),
            (TradeStatus.OPEN, TradeStatus.EMERGENCY_CLOSE, True),
            (TradeStatus.OPEN, TradeStatus.TAKE_PROFIT_PENDING, True),
            # OPEN → OPEN ist verboten (kein Self-Loop).
            (TradeStatus.OPEN, TradeStatus.OPEN, False),
            # TAKE_PROFIT_PENDING → CLOSED_PROFIT (einziger Pfad).
            (TradeStatus.TAKE_PROFIT_PENDING, TradeStatus.CLOSED_PROFIT, True),
            # TAKE_PROFIT_PENDING → andere terminale Stati: verboten.
            (TradeStatus.TAKE_PROFIT_PENDING, TradeStatus.CLOSED_LOSS, False),
            (TradeStatus.TAKE_PROFIT_PENDING, TradeStatus.ASSIGNED, False),
            (TradeStatus.TAKE_PROFIT_PENDING, TradeStatus.EMERGENCY_CLOSE, False),
            (TradeStatus.TAKE_PROFIT_PENDING, TradeStatus.OPEN, False),
            # Terminale Stati → alles: verboten.
            (TradeStatus.CLOSED_PROFIT, TradeStatus.OPEN, False),
            (TradeStatus.CLOSED_LOSS, TradeStatus.OPEN, False),
            (TradeStatus.ASSIGNED, TradeStatus.OPEN, False),
            (TradeStatus.EMERGENCY_CLOSE, TradeStatus.OPEN, False),
            # Terminale Stati → andere terminale Stati: verboten.
            (TradeStatus.ASSIGNED, TradeStatus.CLOSED_PROFIT, False),
        ],
    )
    def test_predicate(
        self,
        from_status: TradeStatus,
        to_status: TradeStatus,
        expected: bool,
    ) -> None:
        assert valid_transition(from_status, to_status) is expected
