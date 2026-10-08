from config import AppConfig

from broker.ibkr_client import (
    BrokerPosition,
)

from main import (
    HealthStatus,
    start_bot,
)

from state.models import (
    Position,
    PositionState,
)

from state.repository import (
    Repository,
)


class FakeBroker:

    def __init__(
        self,
        positions=None,
        available=True,
    ) -> None:

        self.positions = (
            positions or []
        )

        self.available = (
            available
        )

        self.connected = False

    @property
    def is_connected(
        self,
    ) -> bool:

        return self.connected

    def connect(
        self,
    ) -> bool:

        if not self.available:
            raise ConnectionError(
                "IBKR unavailable"
            )

        self.connected = True

        return True

    def reconnect(
        self,
    ) -> bool:

        if not self.available:
            raise ConnectionError(
                "IBKR unavailable"
            )

        self.connected = True

        return True

    def disconnect(
        self,
    ) -> None:

        self.connected = False

    def read_positions(
        self,
    ):

        if (
            not self.available
            or
            not self.connected
        ):
            raise ConnectionError(
                "IBKR unavailable"
            )

        return list(
            self.positions
        )

    def read_open_orders(
        self,
    ):

        if (
            not self.available
            or
            not self.connected
        ):
            raise ConnectionError(
                "IBKR unavailable"
            )

        return []


def create_config(
    database_path: str,
) -> AppConfig:

    return AppConfig(
        app_env="test",
        database_path=database_path,
        ibkr_host="127.0.0.1",
        ibkr_port=7497,
        ibkr_client_id=7,
        telegram_bot_token=None,
        telegram_chat_id=None,
    )


def create_repository(
    database_path,
) -> Repository:

    repository = Repository(
        str(
            database_path
        )
    )

    repository.initialize()

    return repository


def msft_position(
    quantity: float,
    average_cost: float = 487.0,
) -> BrokerPosition:

    return BrokerPosition(
        account="TEST",
        symbol="MSFT",
        con_id=12345,
        quantity=quantity,
        average_cost=average_cost,
        currency="USD",
    )


def test_restart_preserves_wait_retest_state(
    tmp_path,
):

    database_path = (
        tmp_path
        / "restart_wait.db"
    )

    first_repository = (
        create_repository(
            database_path
        )
    )

    first_repository.save_position(
        Position(
            ticker="MSFT",

            state=(
                PositionState
                .WAIT_RETEST
            ),

            quantity=0,
        )
    )

    # Simulate a brand-new
    # Python process using the
    # same SQLite database.
    restarted_repository = (
        Repository(
            str(
                database_path
            )
        )
    )

    broker = FakeBroker(
        positions=[],
        available=True,
    )

    runtime = start_bot(
        config=create_config(
            str(
                database_path
            )
        ),

        repository=(
            restarted_repository
        ),

        ibkr_client=broker,

        watchlist_loader=(
            lambda: [
                "MSFT"
            ]
        ),
    )

    loaded = (
        runtime.repository
        .load_position(
            "MSFT"
        )
    )

    assert loaded is not None

    assert (
        loaded.state
        == PositionState.WAIT_RETEST
    )

    assert (
        runtime.health.status
        == HealthStatus.READY
    )

    runtime.shutdown()


def test_restart_preserves_holding(
    tmp_path,
):

    database_path = (
        tmp_path
        / "restart_holding.db"
    )

    first_repository = (
        create_repository(
            database_path
        )
    )

    first_repository.save_position(
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

    restarted_repository = (
        Repository(
            str(
                database_path
            )
        )
    )

    broker = FakeBroker(
        positions=[
            msft_position(
                quantity=10,
                average_cost=487.0,
            )
        ],
        available=True,
    )

    runtime = start_bot(
        config=create_config(
            str(
                database_path
            )
        ),

        repository=(
            restarted_repository
        ),

        ibkr_client=broker,

        watchlist_loader=(
            lambda: [
                "MSFT"
            ]
        ),
    )

    loaded = (
        runtime.repository
        .load_position(
            "MSFT"
        )
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

    assert (
        loaded.current_stop
        == 474.0
    )

    assert runtime.health.ready

    runtime.shutdown()


def test_ibkr_unavailable_preserves_trusted_state(
    tmp_path,
):

    database_path = (
        tmp_path
        / "broker_down.db"
    )

    repository = (
        create_repository(
            database_path
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
        positions=[],
        available=False,
    )

    runtime = start_bot(
        config=create_config(
            str(
                database_path
            )
        ),

        repository=repository,

        ibkr_client=broker,

        watchlist_loader=(
            lambda: [
                "MSFT"
            ]
        ),
    )

    loaded = (
        repository.load_position(
            "MSFT"
        )
    )

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

    assert (
        runtime.health.status
        == HealthStatus.DEGRADED
    )

    assert not (
        runtime.health
        .broker_connected
    )

    runtime.shutdown()


def test_reconnect_resumes_reconciliation(
    tmp_path,
):

    database_path = (
        tmp_path
        / "recovery.db"
    )

    repository = (
        create_repository(
            database_path
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
        positions=[],
        available=False,
    )

    runtime = start_bot(
        config=create_config(
            str(
                database_path
            )
        ),

        repository=repository,

        ibkr_client=broker,

        watchlist_loader=(
            lambda: [
                "MSFT"
            ]
        ),
    )

    failed_state = (
        repository.load_position(
            "MSFT"
        )
    )

    assert (
        failed_state is not None
    )

    assert (
        failed_state.quantity
        == 10
    )

    assert (
        failed_state.state
        == PositionState.SYNC_ERROR
    )

    assert not runtime.health.ready

    # Simulate TWS / IB Gateway
    # coming back online.
    broker.available = True

    # Also simulate that the user
    # manually sold four shares
    # while the bot was offline.
    broker.positions = [
        msft_position(
            quantity=6,
            average_cost=487.0,
        )
    ]

    health = (
        runtime
        .reconnect_and_reconcile()
    )

    recovered = (
        repository.load_position(
            "MSFT"
        )
    )

    assert recovered is not None

    assert (
        recovered.quantity
        == 6
    )

    assert (
        recovered.state
        == PositionState.HOLDING
    )

    assert (
        health.status
        == HealthStatus.READY
    )

    assert health.ready

    runtime.shutdown()


def test_successful_startup_reports_ready(
    tmp_path,
):

    database_path = (
        tmp_path
        / "healthy.db"
    )

    repository = (
        create_repository(
            database_path
        )
    )

    broker = FakeBroker(
        positions=[],
        available=True,
    )

    runtime = start_bot(
        config=create_config(
            str(
                database_path
            )
        ),

        repository=repository,

        ibkr_client=broker,

        watchlist_loader=(
            lambda: [
                "MSFT",
                "FTNT",
            ]
        ),
    )

    assert runtime.health.ready

    assert (
        runtime.health
        .database_ready
    )

    assert (
        runtime.health
        .broker_connected
    )

    assert (
        runtime.health
        .reconciliation_ok
    )

    runtime.shutdown()