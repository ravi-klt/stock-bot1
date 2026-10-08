from state.models import Position, PositionState


VALID_TRANSITIONS: dict[PositionState, set[PositionState]] = {
    PositionState.WATCHING: {
        PositionState.SETUP_A_ACTIVE,
        PositionState.SETUP_B_ACTIVE,
        PositionState.PENDING_REMOVAL,
        PositionState.HOLDING,
        PositionState.SYNC_ERROR,
    },

      PositionState.SETUP_A_ACTIVE: {
        PositionState.WATCHING,
        PositionState.BUY_READY,
        PositionState.SYNC_ERROR,
    },

    PositionState.SETUP_B_ACTIVE: {
        PositionState.WATCHING,
        PositionState.WAIT_RETEST,
        PositionState.SYNC_ERROR,
    },

    PositionState.WAIT_RETEST: {
        PositionState.WATCHING,
        PositionState.BUY_READY,
        PositionState.SYNC_ERROR,
    },

    PositionState.BUY_READY: {
        PositionState.WATCHING,
        PositionState.HOLDING,
        PositionState.SYNC_ERROR,
    },

    PositionState.HOLDING: {
        PositionState.TREND_WINNER,
        PositionState.ROLLOVER_HOLDING,
        PositionState.EXIT_REVIEW,
        PositionState.CLOSED,
        PositionState.SYNC_ERROR,
    },

    PositionState.TREND_WINNER: {
        PositionState.ROLLOVER_HOLDING,
        PositionState.EXIT_REVIEW,
        PositionState.CLOSED,
        PositionState.SYNC_ERROR,
    },

    PositionState.ROLLOVER_HOLDING: {
        PositionState.HOLDING,
        PositionState.TREND_WINNER,
        PositionState.EXIT_REVIEW,
        PositionState.CLOSED,
        PositionState.SYNC_ERROR,
    },

    PositionState.PENDING_REMOVAL: {
        PositionState.WATCHING,
        PositionState.CLOSED,
        PositionState.SYNC_ERROR,
    },

    PositionState.EXIT_REVIEW: {
        PositionState.HOLDING,
        PositionState.TREND_WINNER,
        PositionState.CLOSED,
        PositionState.SYNC_ERROR,
    },

    PositionState.CLOSED: {
        PositionState.WATCHING,
    },

    PositionState.SYNC_ERROR: {
        PositionState.WATCHING,
        PositionState.HOLDING,
        PositionState.TREND_WINNER,
        PositionState.ROLLOVER_HOLDING,
        PositionState.PENDING_REMOVAL,
    }
}


def can_transition(
    current_state: PositionState,
    new_state: PositionState,
) -> bool:
    allowed_states = VALID_TRANSITIONS.get(current_state, set())
    return new_state in allowed_states


def validate_transition(
    current_state: PositionState,
    new_state: PositionState,
) -> None:
    if not can_transition(current_state, new_state):
        raise ValueError(
            f"Invalid state transition: "
            f"{current_state.value} -> {new_state.value}"
        )


def transition_position(
    position: Position,
    new_state: PositionState,
) -> None:
    validate_transition(position.state, new_state)
    position.state = new_state