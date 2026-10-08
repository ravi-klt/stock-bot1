from state.models import (
    Position,
    PositionState,
    SetupState,
    SetupType,
    TradeEvent,
)

from state.repository import Repository

from datetime import datetime


def create_repository(tmp_path):
    """
    Helper function used by tests.

    Every test gets its own temporary SQLite DB.
    """

    db_path = tmp_path / "test.db"

    repository = Repository(
        str(db_path)
    )

    repository.initialize()

    return repository


def test_position_survives_reload(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    position = Position(
        ticker="MSFT",
        state=PositionState.HOLDING,
        quantity=10,
        actual_entry=487.0,
    )

    repository.save_position(
        position
    )

    loaded = repository.load_position(
        "MSFT"
    )

    assert loaded is not None

    assert loaded.ticker == "MSFT"

    assert (
        loaded.state
        == PositionState.HOLDING
    )

    assert loaded.quantity == 10

    assert (
        loaded.actual_entry
        == 487.0
    )


def test_position_can_be_updated(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    position = Position(
        ticker="MSFT",
        state=PositionState.WATCHING,
    )

    repository.save_position(
        position
    )

    position.state = (
        PositionState.HOLDING
    )

    position.quantity = 10
    position.actual_entry = 487.0

    repository.save_position(
        position
    )

    loaded = repository.load_position(
        "MSFT"
    )

    assert loaded is not None

    assert (
        loaded.state
        == PositionState.HOLDING
    )

    assert loaded.quantity == 10

    assert (
        loaded.actual_entry
        == 487.0
    )


def test_update_state(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    position = Position(
        ticker="MSFT",
        state=PositionState.WATCHING,
    )

    repository.save_position(
        position
    )

    repository.update_state(
        ticker="MSFT",
        state=PositionState.HOLDING,
    )

    loaded = repository.load_position(
        "MSFT"
    )

    assert loaded is not None

    assert (
        loaded.state
        == PositionState.HOLDING
    )


def test_setup_state_survives_reload(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    setup = SetupState(
        ticker="FTNT",

        setup_type=(
            SetupType.SETUP_B
        ),

        state=(
            PositionState.WAIT_RETEST
        ),

        resistance_level=170.0,
        breakout_level=170.0,
    )

    repository.save_setup_state(
        setup
    )

    loaded = (
        repository.load_setup_state(
            "FTNT"
        )
    )

    assert loaded is not None

    assert (
        loaded.ticker
        == "FTNT"
    )

    assert (
        loaded.setup_type
        == SetupType.SETUP_B
    )

    assert (
        loaded.state
        == PositionState.WAIT_RETEST
    )

    assert (
        loaded.resistance_level
        == 170.0
    )

    assert (
        loaded.breakout_level
        == 170.0
    )


def test_missing_position_returns_none(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    result = repository.load_position(
        "UNKNOWN"
    )

    assert result is None


def test_trade_event_can_be_saved(
    tmp_path,
):

    repository = create_repository(
        tmp_path
    )

    event = TradeEvent(
        ticker="MSFT",
        event_type="BUY_READY",
        timestamp=datetime.now(),

        details={
            "setup": "SETUP_A",
            "support": 487.0,
            "recommended_stop": 468.0,
        },
    )

    repository.save_event(
        event
    )