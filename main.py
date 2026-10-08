import logging

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from broker.ibkr_client import IBKRClient
from broker.reconciliation import (
    ReconciliationService,
    ReconciliationSummary,
)

from config import (
    AppConfig,
    ConfigurationError,
    load_config,
    load_watchlist,
)

from logging_config import (
    configure_logging,
    get_logger,
    log_event,
)

from state.repository import Repository


logger = get_logger(__name__)


class HealthStatus(str, Enum):
    READY = "READY"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True)
class SystemHealth:
    status: HealthStatus
    database_ready: bool
    broker_connected: bool
    reconciliation_ok: bool
    message: str

    @property
    def ready(self) -> bool:
        return (
            self.status
            == HealthStatus.READY
        )


@dataclass
class BotRuntime:
    config: AppConfig

    repository: Repository

    ibkr_client: IBKRClient

    reconciliation_service:ReconciliationService

    watchlist_loader: Callable[[], list[str]]

    watchlist: list[str]

    health: SystemHealth

    def reconcile(
        self,
    ) -> ReconciliationSummary:

        self.watchlist = (
            self.watchlist_loader()
        )

        log_event(
            logger=logger,
            event_type="WATCHLIST_RELOADED",
            reason=(
                f"Loaded "
                f"{len(self.watchlist)} "
                f"watchlist tickers."
            ),
        )

        result = (
            self.reconciliation_service
            .sync_positions(
                self.watchlist
            )
        )

        broker_connected = bool(
            getattr(
                self.ibkr_client,
                "is_connected",
                False,
            )
        )

        self.health = _build_health(
            database_ready=True,
            broker_connected=(
                broker_connected
            ),
            reconciliation_ok=(
                result.success
            ),
        )

        _log_health(
            self.health
        )

        return result

    def reconnect_and_reconcile(
        self,
    ) -> SystemHealth:

        try:
            connected = (
                self.ibkr_client
                .reconnect()
            )

        except Exception as exc:

            self.health = (
                _build_health(
                    database_ready=True,
                    broker_connected=False,
                    reconciliation_ok=False,
                    message=(
                        "IBKR reconnect "
                        f"failed: {exc}"
                    ),
                )
            )

            log_event(
                logger=logger,
                event_type=(
                    "IBKR_RECOVERY_FAILED"
                ),
                reason=str(exc),
                level=logging.WARNING,
            )

            _log_health(
                self.health
            )

            return self.health

        if not connected:

            self.health = (
                _build_health(
                    database_ready=True,
                    broker_connected=False,
                    reconciliation_ok=False,
                    message=(
                        "IBKR reconnect "
                        "returned false."
                    ),
                )
            )

            _log_health(
                self.health
            )

            return self.health

        log_event(
            logger=logger,
            event_type=(
                "IBKR_RECOVERED"
            ),
            reason=(
                "IBKR connection "
                "restored. Running "
                "reconciliation."
            ),
        )

        self.reconcile()

        return self.health

    def shutdown(
        self,
    ) -> None:

        try:
            self.ibkr_client.disconnect()

        except Exception as exc:

            log_event(
                logger=logger,
                event_type=(
                    "IBKR_DISCONNECT_FAILED"
                ),
                reason=str(exc),
                level=logging.WARNING,
            )

        log_event(
            logger=logger,
            event_type="BOT_STOPPED",
            reason=(
                "Bot shutdown completed."
            ),
        )


def _create_ibkr_client(
    config: AppConfig,
) -> IBKRClient:

    if config.ibkr_port is None:
        raise ConfigurationError(
            "IBKR_PORT must be configured "
            "before starting the bot."
        )

    if config.ibkr_client_id is None:
        raise ConfigurationError(
            "IBKR_CLIENT_ID must be "
            "configured before starting "
            "the bot."
        )

    return IBKRClient(
        host=config.ibkr_host,
        port=config.ibkr_port,
        client_id=config.ibkr_client_id,
    )


def _build_health(
    database_ready: bool,
    broker_connected: bool,
    reconciliation_ok: bool,
    message: str | None = None,
) -> SystemHealth:

    ready = (
        database_ready
        and
        broker_connected
        and
        reconciliation_ok
    )

    status = (
        HealthStatus.READY
        if ready
        else HealthStatus.DEGRADED
    )

    if message is None:

        if ready:
            message = (
                "Database, IBKR and "
                "reconciliation are ready."
            )

        elif not broker_connected:
            message = (
                "IBKR is unavailable. "
                "Persistent state remains "
                "protected."
            )

        elif not reconciliation_ok:
            message = (
                "IBKR is connected but "
                "reconciliation failed."
            )

        else:
            message = (
                "Application is degraded."
            )

    return SystemHealth(
        status=status,
        database_ready=database_ready,
        broker_connected=(
            broker_connected
        ),
        reconciliation_ok=(
            reconciliation_ok
        ),
        message=message,
    )


def _log_health(
    health: SystemHealth,
) -> None:

    event_type = (
        "BOT_READY"
        if health.ready
        else "BOT_DEGRADED"
    )

    level = (
        logging.INFO
        if health.ready
        else logging.WARNING
    )

    log_event(
        logger=logger,
        event_type=event_type,
        reason=(
            f"status="
            f"{health.status.value}, "
            f"database_ready="
            f"{health.database_ready}, "
            f"broker_connected="
            f"{health.broker_connected}, "
            f"reconciliation_ok="
            f"{health.reconciliation_ok}, "
            f"message="
            f"{health.message}"
        ),
        level=level,
    )


def start_bot(
    config: AppConfig | None = None,
    repository: Repository | None = None,
    ibkr_client: IBKRClient | None = None,
    watchlist_loader:
        Callable[[], list[str]]
        = load_watchlist,
) -> BotRuntime:

    configure_logging()

    log_event(
        logger=logger,
        event_type="BOT_STARTING",
        reason=(
            "Chat 2 Bot V1 starting."
        ),
    )

    resolved_config = (
        config
        if config is not None
        else load_config()
    )

    log_event(
        logger=logger,
        event_type="CONFIG_LOADED",
        reason=(
            f"Environment="
            f"{resolved_config.app_env}."
        ),
    )

    resolved_repository = (
        repository
        if repository is not None
        else Repository(
            resolved_config.database_path
        )
    )

    resolved_repository.initialize()

    log_event(
        logger=logger,
        event_type="DATABASE_READY",
        reason=(
            f"SQLite initialized at "
            f"{resolved_config.database_path}."
        ),
    )

    resolved_ibkr_client = (
        ibkr_client
        if ibkr_client is not None
        else _create_ibkr_client(
            resolved_config
        )
    )

    broker_connected = False

    try:

        broker_connected = bool(
            resolved_ibkr_client.connect()
        )

    except Exception as exc:

        broker_connected = False

        log_event(
            logger=logger,
            event_type=(
                "IBKR_STARTUP_UNAVAILABLE"
            ),
            reason=str(exc),
            level=logging.WARNING,
        )

    watchlist = (
        watchlist_loader()
    )

    log_event(
        logger=logger,
        event_type="WATCHLIST_LOADED",
        reason=(
            f"Loaded "
            f"{len(watchlist)} "
            f"watchlist tickers."
        ),
    )

    reconciliation_service = (
        ReconciliationService(
            ibkr_client=(
                resolved_ibkr_client
            ),
            repository=(
                resolved_repository
            ),
        )
    )

    reconciliation_result = (
        reconciliation_service
        .sync_positions(
            watchlist
        )
    )

    health = _build_health(
        database_ready=True,
        broker_connected=(
            broker_connected
        ),
        reconciliation_ok=(
            reconciliation_result
            .success
        ),
    )

    _log_health(
        health
    )

    return BotRuntime(
        config=resolved_config,

        repository=(
            resolved_repository
        ),

        ibkr_client=(
            resolved_ibkr_client
        ),

        reconciliation_service=(
            reconciliation_service
        ),

        watchlist_loader=(
            watchlist_loader
        ),

        watchlist=watchlist,

        health=health,
    )


def main() -> None:

    runtime: BotRuntime | None = None

    try:

        runtime = start_bot()

        log_event(
            logger=logger,
            event_type=(
                "WEEK1_STARTUP_CHECK"
            ),
            reason=(
                "Week 1 startup and "
                "recovery wiring completed."
            ),
        )

    except ConfigurationError as exc:

        configure_logging()

        log_event(
            logger=logger,
            event_type=(
                "CONFIGURATION_FAILURE"
            ),
            reason=str(exc),
            level=logging.ERROR,
        )

        raise

    except Exception as exc:

        configure_logging()

        log_event(
            logger=logger,
            event_type=(
                "BOT_STARTUP_FAILURE"
            ),
            reason=str(exc),
            level=logging.ERROR,
        )

        raise

    finally:

        if runtime is not None:
            runtime.shutdown()


if __name__ == "__main__":
    main()