from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from broker.ibkr_client import (
    BrokerBar,
    BrokerPosition,
)

from broker.reconciliation import (
    ReconciliationService,
)

from data.market_data import (
    MarketDataError,
    MarketDataService,
)

from state.models import (
    Position,
    PositionState,
)

from state.repository import (
    Repository,
)


NEW_YORK = ZoneInfo(
    "America/New_York"
)


class FakeBroker:

    def __init__(
        self,
        positions=None,
        open_orders=None,
        daily_bars=None,
        weekly_bars=None,
        fail_positions=False,
    ):

        self.positions = (
            positions or []
        )

        self.open_orders = (
            open_orders or []
        )

        self.daily_bars = (
            daily_bars or []
        )

        self.weekly_bars = (
            weekly_bars or []
        )

        self.fail_positions = (
            fail_positions
        )

    def read_positions(
        self,
    ):

        if self.fail_positions:
            raise ConnectionError(
                "IBKR unavailable"
            )

        return self.positions

    def read_open_orders(
        self,
    ):
        return self.open_orders

    def get_daily_bars(
        self,
        ticker,
    ):
        return self.daily_bars

    def get_weekly_bars(
        self,
        ticker,
    ):
        return self.weekly_bars


def create_repository(
    tmp_path,
):

    db_path = (
        tmp_path / "test.db"
    )

    repository = Repository(
        str(
            db_path
        )
    )

    repository.initialize()

    return repository


def broker_position(
    quantity,
    average_cost=487.0,
):

    return BrokerPosition(
        account="TEST",
        symbol="MSFT",
        con_id=12345,
        quantity=quantity,
        average_cost=average_cost,
        currency="USD",
    )


def test_db_zero_ibkr_owned_becomes_holding(
    tmp_path,
):

    repository = (
        create_repository(
            tmp_path
        )
    )

    broker = FakeBroker(
        positions=[
            broker_position(
                10
            )
        ]
    )

    service = (
        ReconciliationService(
            broker,
            repository,
        )
    )

    result = (
        service.sync_positions(
            [
                "MSFT"
            ]
        )
    )

    loaded = (
        repository.load_position(
            "MSFT"
        )
    )

    assert result.success

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

    assert (
        "POSITION_DETECTED"
        in result.events
    )


def test_manual_partial_sale_updates_quantity(
    tmp_path,
):

    repository = (
        create_repository(
            tmp_path
        )
    )

    repository.save_position(
        Position(
            ticker="MSFT",
            state=(
                PositionState.HOLDING
            ),
            quantity=10,
            actual_entry=487.0,
        )
    )

    repository \
        .save_watchlist_snapshot(
            [
                "MSFT"
            ]
        )

    broker = FakeBroker(
        positions=[
            broker_position(
                6
            )
        ]
    )

    service = (
        ReconciliationService(
            broker,
            repository,
        )
    )

    result = (
        service.sync_positions(
            [
                "MSFT"
            ]
        )
    )

    loaded = (
        repository.load_position(
            "MSFT"
        )
    )

    assert loaded is not None

    assert loaded.quantity == 6

    assert (
        loaded.state
        == PositionState.HOLDING
    )

    assert (
        "MANUAL_PARTIAL_EXIT"
        in result.events
    )


def test_full_manual_sale_closes_position(
    tmp_path,
):

    repository = (
        create_repository(
            tmp_path
        )
    )

    repository.save_position(
        Position(
            ticker="MSFT",
            state=(
                PositionState.HOLDING
            ),
            quantity=10,
            actual_entry=487.0,
        )
    )

    repository \
        .save_watchlist_snapshot(
            [
                "MSFT"
            ]
        )

    broker = FakeBroker(
        positions=[]
    )

    service = (
        ReconciliationService(
            broker,
            repository,
        )
    )

    result = (
        service.sync_positions(
            [
                "MSFT"
            ]
        )
    )

    loaded = (
        repository.load_position(
            "MSFT"
        )
    )

    assert loaded is not None

    assert loaded.quantity == 0

    assert (
        loaded.state
        == PositionState.CLOSED
    )

    assert (
        "POSITION_CLOSED"
        in result.events
    )


def test_removed_owned_ticker_becomes_rollover(
    tmp_path,
):

    repository = (
        create_repository(
            tmp_path
        )
    )

    repository.save_position(
        Position(
            ticker="MSFT",
            state=(
                PositionState.HOLDING
            ),
            quantity=10,
            actual_entry=487.0,
        )
    )

    repository \
        .save_watchlist_snapshot(
            [
                "MSFT"
            ]
        )

    broker = FakeBroker(
        positions=[
            broker_position(
                10
            )
        ]
    )

    service = (
        ReconciliationService(
            broker,
            repository,
        )
    )

    result = (
        service.sync_positions(
            []
        )
    )

    loaded = (
        repository.load_position(
            "MSFT"
        )
    )

    assert loaded is not None

    assert (
        loaded.state
        == PositionState
        .ROLLOVER_HOLDING
    )

    assert loaded.quantity == 10

    assert (
        "ROLLOVER_CREATED"
        in result.events
    )


def test_ibkr_failure_does_not_zero_position(
    tmp_path,
):

    repository = (
        create_repository(
            tmp_path
        )
    )

    repository.save_position(
        Position(
            ticker="MSFT",
            state=(
                PositionState.HOLDING
            ),
            quantity=10,
            actual_entry=487.0,
            current_stop=474.0,
        )
    )

    broker = FakeBroker(
        fail_positions=True
    )

    service = (
        ReconciliationService(
            broker,
            repository,
        )
    )

    result = (
        service.sync_positions(
            [
                "MSFT"
            ]
        )
    )

    loaded = (
        repository.load_position(
            "MSFT"
        )
    )

    assert not result.success

    assert loaded is not None

    assert loaded.quantity == 10

    assert (
        loaded.actual_entry
        == 487.0
    )

    assert (
        loaded.current_stop
        == 474.0
    )

    assert (
        loaded.state
        == PositionState.SYNC_ERROR
    )


def test_current_daily_bar_is_excluded_before_close():

    broker = FakeBroker(
        daily_bars=[
            BrokerBar(
                date="20260916",
                open=100,
                high=105,
                low=99,
                close=104,
                volume=10_000_000,
            ),

            BrokerBar(
                date="20260917",
                open=104,
                high=108,
                low=103,
                close=107,
                volume=6_000_000,
            ),
        ]
    )

    service = (
        MarketDataService(
            broker
        )
    )

    now = datetime(
        2026,
        9,
        17,
        15,
        0,
        tzinfo=NEW_YORK,
    )

    bars = (
        service.get_daily_bars(
            "MSFT",
            now=now,
        )
    )

    assert len(bars) == 1

    assert (
        bars[0].date.isoformat()
        == "2026-09-16"
    )


def test_missing_daily_data_fails():

    broker = FakeBroker(
        daily_bars=[]
    )

    service = (
        MarketDataService(
            broker
        )
    )

    with pytest.raises(
        MarketDataError
    ):

        service.get_daily_bars(
            "MSFT"
        )


def test_stale_daily_data_fails():

    broker = FakeBroker(
        daily_bars=[
            BrokerBar(
                date="20260801",
                open=100,
                high=105,
                low=99,
                close=104,
                volume=10_000_000,
            )
        ]
    )

    service = (
        MarketDataService(
            broker
        )
    )

    now = datetime(
        2026,
        9,
        17,
        18,
        0,
        tzinfo=NEW_YORK,
    )

    with pytest.raises(
        MarketDataError
    ):

        service.get_daily_bars(
            "MSFT",
            now=now,
        )


def test_impossible_ohlc_fails():

    broker = FakeBroker(
        daily_bars=[
            BrokerBar(
                date="20260916",
                open=100,
                high=99,
                low=98,
                close=103,
                volume=10_000_000,
            )
        ]
    )

    service = (
        MarketDataService(
            broker
        )
    )

    now = datetime(
        2026,
        9,
        17,
        18,
        0,
        tzinfo=NEW_YORK,
    )

    with pytest.raises(
        MarketDataError
    ):

        service.get_daily_bars(
            "MSFT",
            now=now,
        )