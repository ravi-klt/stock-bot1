from dataclasses import dataclass
from datetime import (
    datetime,
    timezone,
)

from broker.ibkr_client import (
    BrokerOpenOrder,
    BrokerPosition,
    IBKRClient,
)

from logging_config import (
    get_logger,
    log_event,
)

from state.models import (
    Position,
    PositionState,
    TradeEvent,
)

from state.repository import (
    Repository,
)


logger = get_logger(__name__)


@dataclass(frozen=True)
class ReconciliationSummary:
    success: bool
    managed_tickers: tuple[str, ...]
    events: tuple[str, ...]


class ReconciliationService:

    def __init__(
        self,
        ibkr_client: IBKRClient,
        repository: Repository,
    ) -> None:

        self.ibkr_client = (
            ibkr_client
        )

        self.repository = (
            repository
        )

    def _now(
        self,
    ) -> datetime:

        return datetime.now(
            timezone.utc
        )

    def _create_event(
        self,
        ticker: str,
        event_type: str,
        details: dict | None = None,
    ) -> TradeEvent:

        return TradeEvent(
            ticker=ticker,
            event_type=event_type,
            timestamp=self._now(),
            details=details or {},
        )

    def _persist_event(
        self,
        event: TradeEvent,
    ) -> None:

        self.repository.save_event(
            event
        )

        log_event(
            logger=logger,
            ticker=event.ticker,
            event_type=event.event_type,
            reason=str(
                event.details
            ),
        )

    def _persist_position_events(
        self,
        position: Position,
        events: list[TradeEvent],
    ) -> None:

        if not events:

            self.repository.save_position(
                position
            )

            return

        self.repository.save_position_and_event(
            position,
            events[0],
        )

        log_event(
            logger=logger,
            ticker=events[0].ticker,
            state=position.state.value,
            event_type=(
                events[0].event_type
            ),
            reason=str(
                events[0].details
            ),
        )

        for event in events[1:]:

            self._persist_event(
                event
            )

    def _build_position_map(
        self,
        positions: list[
            BrokerPosition
        ],
    ) -> dict[
        str,
        BrokerPosition,
    ]:

        result: dict[
            str,
            BrokerPosition
        ] = {}

        for position in positions:

            ticker = (
                position.symbol.upper()
            )

            if ticker in result:
                raise RuntimeError(
                    f"Multiple IBKR positions "
                    f"returned for {ticker}. "
                    "V1 will not guess "
                    "between accounts."
                )

            result[ticker] = (
                position
            )

        return result

    def _sync_owned_position(
        self,
        ticker: str,
        broker_position: BrokerPosition,
        in_watchlist: bool,
    ) -> list[str]:

        db_position = (
            self.repository
            .load_position(
                ticker
            )
        )

        previous_quantity = (
            db_position.quantity
            if db_position
            else 0.0
        )

        previous_state = (
            db_position.state
            if db_position
            else None
        )

        if db_position is None:

            db_position = Position(
                ticker=ticker,

                state=(
                    PositionState.HOLDING
                    if in_watchlist
                    else PositionState
                    .ROLLOVER_HOLDING
                ),

                quantity=(
                    broker_position
                    .quantity
                ),

                actual_entry=(
                    broker_position
                    .average_cost
                ),

                entry_date=self._now(),

                last_sync_time=(
                    self._now()
                ),
            )

        else:

            db_position.quantity = (
                broker_position.quantity
            )

            db_position.actual_entry = (
                broker_position
                .average_cost
            )

            db_position.last_sync_time = (
                self._now()
            )

            if in_watchlist:

                if db_position.state not in {
                    PositionState
                    .TREND_WINNER,

                    PositionState
                    .EXIT_REVIEW,
                }:
                    db_position.state = (
                        PositionState
                        .HOLDING
                    )

            else:
                db_position.state = (
                    PositionState
                    .ROLLOVER_HOLDING
                )

            if (
                db_position.entry_date
                is None
            ):
                db_position.entry_date = (
                    self._now()
                )

        events: list[
            TradeEvent
        ] = []

        event_types: list[str] = []

        if previous_quantity <= 0:

            events.append(
                self._create_event(
                    ticker,
                    "POSITION_DETECTED",
                    {
                        "quantity":
                            broker_position
                            .quantity,

                        "average_cost":
                            broker_position
                            .average_cost,
                    },
                )
            )

            event_types.append(
                "POSITION_DETECTED"
            )

        elif (
            broker_position.quantity
            > previous_quantity
        ):

            events.append(
                self._create_event(
                    ticker,
                    (
                        "MANUAL_POSITION_"
                        "INCREASE"
                    ),
                    {
                        "previous_quantity":
                            previous_quantity,

                        "new_quantity":
                            broker_position
                            .quantity,

                        "average_cost":
                            broker_position
                            .average_cost,
                    },
                )
            )

            event_types.append(
                "MANUAL_POSITION_INCREASE"
            )

        elif (
            0
            < broker_position.quantity
            < previous_quantity
        ):

            events.append(
                self._create_event(
                    ticker,
                    "MANUAL_PARTIAL_EXIT",
                    {
                        "previous_quantity":
                            previous_quantity,

                        "new_quantity":
                            broker_position
                            .quantity,
                    },
                )
            )

            event_types.append(
                "MANUAL_PARTIAL_EXIT"
            )

        elif (
            previous_state
            == PositionState.SYNC_ERROR
        ):

            events.append(
                self._create_event(
                    ticker,
                    "SYNC_RECOVERED",
                    {
                        "quantity":
                            broker_position
                            .quantity,
                    },
                )
            )

            event_types.append(
                "SYNC_RECOVERED"
            )

        if (
            not in_watchlist
            and
            previous_state
            != PositionState
            .ROLLOVER_HOLDING
        ):

            events.append(
                self._create_event(
                    ticker,
                    "ROLLOVER_CREATED",
                    {
                        "reason":
                            "Ticker removed "
                            "from watchlist "
                            "while still owned."
                    },
                )
            )

            event_types.append(
                "ROLLOVER_CREATED"
            )

        self._persist_position_events(
            db_position,
            events,
        )

        return event_types

    def _sync_zero_position(
        self,
        ticker: str,
        in_watchlist: bool,
    ) -> list[str]:

        db_position = (
            self.repository
            .load_position(
                ticker
            )
        )

        if db_position is None:

            if in_watchlist:

                self.repository.save_position(
                    Position(
                        ticker=ticker,
                        state=(
                            PositionState
                            .WATCHING
                        ),
                        quantity=0,
                        last_sync_time=(
                            self._now()
                        ),
                    )
                )

            return []

        if db_position.quantity > 0:

            previous_quantity = (
                db_position.quantity
            )

            db_position.quantity = 0

            db_position.state = (
                PositionState.CLOSED
            )

            db_position.last_sync_time = (
                self._now()
            )

            event = (
                self._create_event(
                    ticker,
                    "POSITION_CLOSED",
                    {
                        "previous_quantity":
                            previous_quantity,
                    },
                )
            )

            self._persist_position_events(
                db_position,
                [
                    event
                ],
            )

            return [
                "POSITION_CLOSED"
            ]

        if not in_watchlist:

            db_position.state = (
                PositionState.CLOSED
            )

            db_position.last_sync_time = (
                self._now()
            )

            self.repository.save_position(
                db_position
            )

            return []

        if (
            db_position.state
            in {
                PositionState.CLOSED,
                PositionState
                .PENDING_REMOVAL,
                PositionState.SYNC_ERROR,
            }
        ):

            db_position.state = (
                PositionState.WATCHING
            )

        db_position.last_sync_time = (
            self._now()
        )

        self.repository.save_position(
            db_position
        )

        return []

    def _mark_sync_failure(
        self,
        managed_tickers: set[str],
        error: Exception,
    ) -> list[str]:

        events = []

        for ticker in sorted(
            managed_tickers
        ):

            position = (
                self.repository
                .load_position(
                    ticker
                )
            )

            event = (
                self._create_event(
                    ticker,
                    "SYNC_FAILURE",
                    {
                        "error":
                            str(error),

                        "previous_state":
                            (
                                position
                                .state
                                .value
                                if position
                                else None
                            ),
                    },
                )
            )

            if (
                position is not None
                and
                (
                    position.quantity > 0
                    or
                    position.state
                    in {
                        PositionState
                        .ROLLOVER_HOLDING,

                        PositionState
                        .PENDING_REMOVAL,

                        PositionState
                        .HOLDING,

                        PositionState
                        .TREND_WINNER,

                        PositionState
                        .EXIT_REVIEW,
                    }
                )
            ):

                position.state = (
                    PositionState
                    .SYNC_ERROR
                )

                self.repository \
                    .save_position_and_event(
                        position,
                        event,
                    )

            else:
                self.repository.save_event(
                    event
                )

            log_event(
                logger=logger,
                ticker=ticker,
                event_type=(
                    "SYNC_FAILURE"
                ),
                reason=str(error),
            )

            events.append(
                "SYNC_FAILURE"
            )

        return events

    def _reconcile_stop(
        self,
        position: Position,
        orders: list[
            BrokerOpenOrder
        ],
    ) -> None:

        if (
            position.recommended_stop
            is None
        ):
            return

        stop_orders = [
            order
            for order in orders
            if (
                order.symbol
                == position.ticker
                and
                order.action == "SELL"
                and
                order.order_type
                in {
                    "STP",
                    "STP LMT",
                }
                and
                0
                < order.aux_price
                < 1e100
            )
        ]

        if len(stop_orders) != 1:

            event = (
                self._create_event(
                    position.ticker,
                    "STOP_MISMATCH",
                    {
                        "recommended_stop":
                            position
                            .recommended_stop,

                        "visible_stop_orders":
                            len(
                                stop_orders
                            ),
                    },
                )
            )

            self._persist_event(
                event
            )

            return

        actual_stop = (
            stop_orders[0]
            .aux_price
        )

        position.current_stop = (
            actual_stop
        )

        self.repository.save_position(
            position
        )

        difference = abs(
            actual_stop
            - position.recommended_stop
        )

        if difference <= 0.01:

            log_event(
                logger=logger,
                ticker=position.ticker,
                state=position.state.value,
                event_type="STOP_SYNC_OK",
                reason=(
                    f"Broker stop "
                    f"{actual_stop} matches "
                    f"recommended stop."
                ),
            )

        else:

            event = (
                self._create_event(
                    position.ticker,
                    "STOP_MISMATCH",
                    {
                        "recommended_stop":
                            position
                            .recommended_stop,

                        "actual_stop":
                            actual_stop,
                    },
                )
            )

            self._persist_event(
                event
            )

    def sync_positions(
        self,
        current_watchlist: list[str],
    ) -> ReconciliationSummary:

        current = {
            ticker.strip().upper()
            for ticker
            in current_watchlist
        }

        previous = set(
            self.repository
            .load_last_watchlist_snapshot()
            or []
        )

        removed = (
            previous
            - current
        )

        open_positions = (
            self.repository
            .get_open_positions()
        )

        sync_errors = (
            self.repository
            .get_sync_error_positions()
        )

        managed = (
            current
            | removed
            | {
                position.ticker
                for position
                in open_positions
            }
            | {
                position.ticker
                for position
                in sync_errors
            }
        )

        try:
            broker_positions = (
                self.ibkr_client
                .read_positions()
            )

            position_map = (
                self._build_position_map(
                    broker_positions
                )
            )

        except Exception as exc:

            event_types = (
                self._mark_sync_failure(
                    managed,
                    exc,
                )
            )

            return (
                ReconciliationSummary(
                    success=False,

                    managed_tickers=tuple(
                        sorted(
                            managed
                        )
                    ),

                    events=tuple(
                        event_types
                    ),
                )
            )

        try:
            open_orders = (
                self.ibkr_client
                .read_open_orders()
            )

        except Exception as exc:

            open_orders = []

            log_event(
                logger=logger,
                event_type=(
                    "OPEN_ORDERS_"
                    "SYNC_FAILURE"
                ),
                reason=str(exc),
            )

        all_event_types: list[
            str
        ] = []

        for ticker in sorted(
            managed
        ):

            broker_position = (
                position_map.get(
                    ticker
                )
            )

            if (
                broker_position
                is not None
                and
                broker_position.quantity > 0
            ):

                event_types = (
                    self
                    ._sync_owned_position(
                        ticker=ticker,

                        broker_position=(
                            broker_position
                        ),

                        in_watchlist=(
                            ticker
                            in current
                        ),
                    )
                )

            else:

                event_types = (
                    self
                    ._sync_zero_position(
                        ticker=ticker,

                        in_watchlist=(
                            ticker
                            in current
                        ),
                    )
                )

            all_event_types.extend(
                event_types
            )

            updated_position = (
                self.repository
                .load_position(
                    ticker
                )
            )

            if (
                updated_position
                is not None
                and
                updated_position.quantity > 0
            ):
                self._reconcile_stop(
                    updated_position,
                    open_orders,
                )

        self.repository \
            .save_watchlist_snapshot(
                sorted(
                    current
                )
            )

        return ReconciliationSummary(
            success=True,

            managed_tickers=tuple(
                sorted(
                    managed
                )
            ),

            events=tuple(
                all_event_types
            ),
        )