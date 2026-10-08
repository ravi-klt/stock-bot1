import pytest

from state.models import Position, PositionState
from state.state_machine import (
    can_transition,
    transition_position,
)


def test_watching_can_become_setup_a():

    assert can_transition(
        PositionState.WATCHING,
        PositionState.SETUP_A_ACTIVE,
    )


def test_setup_b_can_wait_for_retest():

    assert can_transition(
        PositionState.SETUP_B_ACTIVE,
        PositionState.WAIT_RETEST,
    )


def test_buy_ready_can_become_holding():

    assert can_transition(
        PositionState.BUY_READY,
        PositionState.HOLDING,
    )


def test_closed_cannot_become_trend_winner():

    assert not can_transition(
        PositionState.CLOSED,
        PositionState.TREND_WINNER,
    )


def test_invalid_transition_raises_error():

    position = Position(
        ticker="MSFT",
        state=PositionState.CLOSED,
    )

    with pytest.raises(ValueError):

        transition_position(
            position,
            PositionState.TREND_WINNER,
        )