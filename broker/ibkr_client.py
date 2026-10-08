from dataclasses import dataclass
from itertools import count
from threading import Event, Thread
from time import sleep

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.wrapper import EWrapper

from logging_config import (
    get_logger,
    log_event,
)


logger = get_logger(__name__)


INFORMATIONAL_ERROR_CODES = {
    2104,
    2106,
    2158,
}


@dataclass(frozen=True)
class BrokerPosition:
    account: str
    symbol: str
    con_id: int
    quantity: float
    average_cost: float
    currency: str


@dataclass(frozen=True)
class BrokerBar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class BrokerOpenOrder:
    order_id: int
    symbol: str
    action: str
    order_type: str
    quantity: float
    aux_price: float
    limit_price: float
    status: str


def build_us_stock_contract(
    ticker: str,
) -> Contract:

    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError(
            "Ticker cannot be empty."
        )

    contract = Contract()

    contract.symbol = ticker
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"

    return contract


class _NativeIBApp(
    EWrapper,
    EClient,
):

    def __init__(self) -> None:

        EWrapper.__init__(self)

        EClient.__init__(
            self,
            self,
        )

        self.ready_event = Event()

        self.positions_event = Event()

        self.open_orders_event = Event()

        self.positions: list[
            BrokerPosition
        ] = []

        self.open_orders: list[
            BrokerOpenOrder
        ] = []

        self.contract_events: dict[
            int,
            Event,
        ] = {}

        self.contract_results: dict[
            int,
            list,
        ] = {}

        self.historical_events: dict[
            int,
            Event,
        ] = {}

        self.historical_results: dict[
            int,
            list[BrokerBar],
        ] = {}

        self.request_errors: dict[
            int,
            str,
        ] = {}

    def nextValidId(
        self,
        orderId: int,
    ) -> None:

        self.ready_event.set()

        log_event(
            logger=logger,
            event_type="IBKR_READY",
            reason=(
                "IBKR API handshake completed."
            ),
        )

    def error(
        self,
        reqId: int,
        errorTime: int,
        errorCode: int,
        errorString: str,
        advancedOrderRejectJson: str = "",
    ) -> None:

        message = (
            f"reqId={reqId}, "
            f"errorCode={errorCode}, "
            f"message={errorString}"
        )

        if (
            errorCode
            in INFORMATIONAL_ERROR_CODES
        ):
            log_event(
                logger=logger,
                event_type="IBKR_INFO",
                reason=message,
            )

            return

        log_event(
            logger=logger,
            event_type="IBKR_ERROR",
            reason=message,
        )

        if reqId < 0:
            return

        self.request_errors[
            reqId
        ] = message

        contract_event = (
            self.contract_events.get(
                reqId
            )
        )

        if contract_event is not None:
            contract_event.set()

        historical_event = (
            self.historical_events.get(
                reqId
            )
        )

        if historical_event is not None:
            historical_event.set()

    def connectionClosed(
        self,
    ) -> None:

        self.ready_event.clear()

        log_event(
            logger=logger,
            event_type=(
                "IBKR_CONNECTION_CLOSED"
            ),
            reason=(
                "IBKR API connection closed."
            ),
        )

    def contractDetails(
        self,
        reqId: int,
        contractDetails,
    ) -> None:

        results = (
            self.contract_results
            .setdefault(
                reqId,
                [],
            )
        )

        results.append(
            contractDetails
        )

    def contractDetailsEnd(
        self,
        reqId: int,
    ) -> None:

        event = (
            self.contract_events.get(
                reqId
            )
        )

        if event is not None:
            event.set()

    def position(
        self,
        account: str,
        contract: Contract,
        position,
        avgCost: float,
    ) -> None:

        self.positions.append(
            BrokerPosition(
                account=account,

                symbol=(
                    contract.symbol.upper()
                ),

                con_id=contract.conId,

                quantity=float(
                    position
                ),

                average_cost=float(
                    avgCost
                ),

                currency=(
                    contract.currency
                    or ""
                ),
            )
        )

    def positionEnd(
        self,
    ) -> None:

        self.positions_event.set()

    def openOrder(
        self,
        orderId,
        contract,
        order,
        orderState,
    ) -> None:

        self.open_orders.append(
            BrokerOpenOrder(
                order_id=int(
                    orderId
                ),

                symbol=(
                    contract.symbol.upper()
                ),

                action=(
                    order.action.upper()
                ),

                order_type=(
                    order.orderType.upper()
                ),

                quantity=float(
                    order.totalQuantity
                ),

                aux_price=float(
                    order.auxPrice
                ),

                limit_price=float(
                    order.lmtPrice
                ),

                status=(
                    orderState.status
                    or ""
                ),
            )
        )

    def openOrderEnd(
        self,
    ) -> None:

        self.open_orders_event.set()

    def historicalData(
        self,
        reqId: int,
        bar,
    ) -> None:

        results = (
            self.historical_results
            .setdefault(
                reqId,
                [],
            )
        )

        results.append(
            BrokerBar(
                date=str(
                    bar.date
                ),

                open=float(
                    bar.open
                ),

                high=float(
                    bar.high
                ),

                low=float(
                    bar.low
                ),

                close=float(
                    bar.close
                ),

                volume=float(
                    bar.volume
                ),
            )
        )

    def historicalDataEnd(
        self,
        reqId: int,
        start: str,
        end: str,
    ) -> None:

        event = (
            self.historical_events.get(
                reqId
            )
        )

        if event is not None:
            event.set()


class IBKRClient:

    def __init__(
        self,
        host: str,
        port: int,
        client_id: int,
    ) -> None:

        self.host = host
        self.port = port
        self.client_id = client_id

        self._app = _NativeIBApp()

        self._api_thread: (
            Thread | None
        ) = None

        self._request_ids = count(1)

    @property
    def is_connected(
        self,
    ) -> bool:

        return (
            self._app.isConnected()
            and
            self._app.ready_event.is_set()
        )

    def connect(
        self,
        timeout_seconds: float = 10.0,
    ) -> bool:

        if self.is_connected:
            return True

        self._app.ready_event.clear()

        log_event(
            logger=logger,
            event_type="IBKR_CONNECTING",
            reason=(
                f"Connecting to "
                f"{self.host}:{self.port}, "
                f"clientId={self.client_id}."
            ),
        )

        self._app.connect(
            self.host,
            self.port,
            clientId=self.client_id,
        )

        self._api_thread = Thread(
            target=self._app.run,
            daemon=True,
            name="ibkr-api-thread",
        )

        self._api_thread.start()

        ready = (
            self._app
            .ready_event
            .wait(
                timeout_seconds
            )
        )

        if not ready:
            self.disconnect()

            raise ConnectionError(
                "IBKR connection did not "
                "become ready."
            )

        log_event(
            logger=logger,
            event_type="IBKR_CONNECTED",
            reason=(
                "IBKR connection ready."
            ),
        )

        return True

    def disconnect(
        self,
    ) -> None:

        if self._app.isConnected():
            self._app.disconnect()

        self._app.ready_event.clear()

        if (
            self._api_thread
            is not None
            and
            self._api_thread.is_alive()
        ):
            self._api_thread.join(
                timeout=2.0
            )

        log_event(
            logger=logger,
            event_type="IBKR_DISCONNECTED",
            reason=(
                "IBKR client disconnected."
            ),
        )

    def reconnect(
        self,
        max_attempts: int = 3,
        initial_delay_seconds: float = 2.0,
    ) -> bool:

        delay = (
            initial_delay_seconds
        )

        last_error: (
            Exception | None
        ) = None

        for attempt in range(
            1,
            max_attempts + 1,
        ):

            try:
                self.disconnect()

                if attempt > 1:
                    sleep(delay)
                    delay *= 2

                return self.connect()

            except Exception as exc:

                last_error = exc

                log_event(
                    logger=logger,
                    event_type=(
                        "IBKR_RECONNECT_FAILED"
                    ),
                    reason=(
                        f"Reconnect attempt "
                        f"{attempt}/"
                        f"{max_attempts} "
                        f"failed: {exc}"
                    ),
                )

        raise ConnectionError(
            "Unable to reconnect to IBKR."
        ) from last_error

    def _ensure_connected(
        self,
    ) -> None:

        if not self.is_connected:
            raise ConnectionError(
                "IBKR client is not connected."
            )

    def _next_request_id(
        self,
    ) -> int:

        return next(
            self._request_ids
        )

    def resolve_us_stock(
        self,
        ticker: str,
        timeout_seconds: float = 10.0,
    ) -> Contract:

        self._ensure_connected()

        request_id = (
            self._next_request_id()
        )

        request_contract = (
            build_us_stock_contract(
                ticker
            )
        )

        event = Event()

        self._app.contract_events[
            request_id
        ] = event

        self._app.contract_results[
            request_id
        ] = []

        self._app.reqContractDetails(
            request_id,
            request_contract,
        )

        completed = event.wait(
            timeout_seconds
        )

        error = (
            self._app
            .request_errors
            .pop(
                request_id,
                None,
            )
        )

        results = (
            self._app
            .contract_results
            .pop(
                request_id,
                [],
            )
        )

        self._app.contract_events.pop(
            request_id,
            None,
        )

        if error is not None:
            raise RuntimeError(
                error
            )

        if not completed:
            raise TimeoutError(
                f"Contract resolution timed "
                f"out for {ticker}."
            )

        contracts = [
            details.contract
            for details in results
            if (
                details.contract.secType
                == "STK"
                and
                details.contract.currency
                == "USD"
            )
        ]

        unique_contracts = {
            contract.conId: contract
            for contract in contracts
        }

        if len(unique_contracts) != 1:
            raise LookupError(
                f"Ticker {ticker} did not "
                "resolve uniquely."
            )

        contract = next(
            iter(
                unique_contracts.values()
            )
        )

        log_event(
            logger=logger,
            event_type=(
                "IBKR_CONTRACT_RESOLVED"
            ),
            ticker=contract.symbol,
            reason=(
                f"Resolved conId="
                f"{contract.conId}."
            ),
        )

        return contract

    def read_positions(
        self,
        timeout_seconds: float = 10.0,
    ) -> list[BrokerPosition]:

        self._ensure_connected()

        self._app.positions = []

        self._app.positions_event.clear()

        self._app.reqPositions()

        completed = (
            self._app
            .positions_event
            .wait(
                timeout_seconds
            )
        )

        self._app.cancelPositions()

        if not completed:
            raise TimeoutError(
                "Timed out reading positions."
            )

        return list(
            self._app.positions
        )

    def get_position(
        self,
        ticker: str,
    ) -> BrokerPosition | None:

        ticker = ticker.strip().upper()

        positions = [
            position
            for position
            in self.read_positions()
            if position.symbol == ticker
        ]

        if not positions:
            return None

        if len(positions) > 1:
            raise RuntimeError(
                f"Multiple IBKR positions "
                f"found for {ticker}. "
                "V1 will not guess."
            )

        return positions[0]

    def read_open_orders(
        self,
        timeout_seconds: float = 10.0,
    ) -> list[BrokerOpenOrder]:

        self._ensure_connected()

        self._app.open_orders = []

        self._app.open_orders_event.clear()

        self._app.reqAllOpenOrders()

        completed = (
            self._app
            .open_orders_event
            .wait(
                timeout_seconds
            )
        )

        if not completed:
            raise TimeoutError(
                "Timed out reading "
                "open orders."
            )

        return list(
            self._app.open_orders
        )

    def get_open_orders(
        self,
        ticker: str,
    ) -> list[BrokerOpenOrder]:

        ticker = ticker.strip().upper()

        return [
            order
            for order
            in self.read_open_orders()
            if order.symbol == ticker
        ]

    def _request_historical_bars(
        self,
        ticker: str,
        duration: str,
        bar_size: str,
        timeout_seconds: float,
    ) -> list[BrokerBar]:

        self._ensure_connected()

        contract = (
            self.resolve_us_stock(
                ticker
            )
        )

        request_id = (
            self._next_request_id()
        )

        event = Event()

        self._app.historical_events[
            request_id
        ] = event

        self._app.historical_results[
            request_id
        ] = []

        self._app.reqHistoricalData(
            request_id,
            contract,
            "",
            duration,
            bar_size,
            "TRADES",
            1,
            1,
            False,
            [],
        )

        completed = event.wait(
            timeout_seconds
        )

        error = (
            self._app
            .request_errors
            .pop(
                request_id,
                None,
            )
        )

        bars = (
            self._app
            .historical_results
            .pop(
                request_id,
                [],
            )
        )

        self._app.historical_events.pop(
            request_id,
            None,
        )

        if error is not None:
            raise RuntimeError(
                error
            )

        if not completed:

            self._app.cancelHistoricalData(
                request_id
            )

            raise TimeoutError(
                f"Historical data timed "
                f"out for {ticker}."
            )

        return bars

    def get_daily_bars(
        self,
        ticker: str,
        duration: str = "1 Y",
    ) -> list[BrokerBar]:

        return (
            self._request_historical_bars(
                ticker=ticker,
                duration=duration,
                bar_size="1 day",
                timeout_seconds=15.0,
            )
        )

    def get_weekly_bars(
        self,
        ticker: str,
        duration: str = "3 Y",
    ) -> list[BrokerBar]:

        return (
            self._request_historical_bars(
                ticker=ticker,
                duration=duration,
                bar_size="1 week",
                timeout_seconds=15.0,
            )
        )

    def request_daily_bars(
        self,
        ticker: str,
        duration: str = "1 Y",
        timeout_seconds: float = 15.0,
    ) -> list[BrokerBar]:

        return (
            self._request_historical_bars(
                ticker=ticker,
                duration=duration,
                bar_size="1 day",
                timeout_seconds=(
                    timeout_seconds
                ),
            )
        )