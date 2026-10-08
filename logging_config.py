import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


LOG_DIR = Path(__file__).resolve().parent / "logs"

LOG_FILE = LOG_DIR / "bot.log"


class JsonFormatter(
    logging.Formatter
):

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:

        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(
                record,
                "%Y-%m-%dT%H:%M:%S",
            ),

            "level": record.levelname,

            "logger": record.name,

            "message": record.getMessage(),
        }

        for field_name in (
            "event_type",
            "ticker",
            "state",
            "reason",
        ):

            value = getattr(
                record,
                field_name,
                None,
            )

            if value is not None:
                log_data[field_name] = value

        if record.exc_info:
            log_data["exception"] = (
                self.formatException(
                    record.exc_info
                )
            )

        return json.dumps(
            log_data,
            default=str,
        )


def configure_logging() -> None:

    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    root_logger = logging.getLogger()

    root_logger.setLevel(
        logging.INFO
    )

    # Prevent duplicate handlers if configuration
    # is called more than once.
    if root_logger.handlers:
        return

    formatter = JsonFormatter()

    console_handler = (
        logging.StreamHandler()
    )

    console_handler.setFormatter(
        formatter
    )

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )

    file_handler.setFormatter(
        formatter
    )

    root_logger.addHandler(
        console_handler
    )

    root_logger.addHandler(
        file_handler
    )


def get_logger(
    name: str,
) -> logging.Logger:

    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    event_type: str,
    reason: str,
    ticker: str | None = None,
    state: str | None = None,
    level: int = logging.INFO,
) -> None:

    logger.log(
        level,
        reason,
        extra={
            "event_type": event_type,
            "ticker": ticker,
            "state": state,
            "reason": reason,
        },
    )