import json
import os
from pathlib import Path

from dotenv import load_dotenv
from dataclasses import dataclass

# this will give the base directory of project like it return : stock-bot1
BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

WATCHLIST_FILE = BASE_DIR / "config" / "watchlist.json"


def get_database_path() -> str:
    return os.getenv("DATABASE_PATH", "trading.db")


class ConfigurationError(Exception):
    """
        Raised when application configuration
        is missing or malformed.
    """
    pass

@dataclass(frozen=True)
class AppConfig:
    app_env: str
    database_path: str

    ibkr_host: str
    ibkr_port: int | None
    ibkr_client_id: int | None

    telegram_bot_token: str | None
    telegram_chat_id: str | None

def _optional_int(
    variable_name: str,
) -> int | None:

    raw_value = os.getenv(variable_name)

    if raw_value is None:
        return None

    raw_value = raw_value.strip()

    if not raw_value:
        return None

    try:
        return int(raw_value)

    except ValueError as exc:
        raise ConfigurationError(
            f"{variable_name} must be an integer."
        ) from exc

def load_config() -> AppConfig:

    database_path = os.getenv(
        "DATABASE_PATH",
        "trading.db",
    ).strip()

    if not database_path:
        raise ConfigurationError(
            "DATABASE_PATH cannot be empty."
        )

    app_env = os.getenv(
        "APP_ENV",
        "development",
    ).strip()

    if not app_env:
        raise ConfigurationError(
            "APP_ENV cannot be empty."
        )

    ibkr_host = os.getenv(
        "IBKR_HOST",
        "127.0.0.1",
    ).strip()

    if not ibkr_host:
        raise ConfigurationError(
            "IBKR_HOST cannot be empty."
        )

    return AppConfig(
        app_env=app_env,

        database_path=database_path,

        ibkr_host=ibkr_host,

        ibkr_port=_optional_int(
            "IBKR_PORT"
        ),

        ibkr_client_id=_optional_int(
            "IBKR_CLIENT_ID"
        ),

        telegram_bot_token=(
            os.getenv(
                "TELEGRAM_BOT_TOKEN"
            )
            or None
        ),

        telegram_chat_id=(
            os.getenv(
                "TELEGRAM_CHAT_ID"
            )
            or None
        ),
    )

def load_watchlist(
    watchlist_path: Path | None = None,
) -> list[str]:

    path = (
        watchlist_path
        if watchlist_path is not None
        else WATCHLIST_FILE
    )

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

    except FileNotFoundError as exc:
        raise ConfigurationError(
            f"Watchlist file not found: {path}"
        ) from exc

    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Watchlist contains invalid JSON: {path}"
        ) from exc

    if not isinstance(data, dict):
        raise ConfigurationError(
            "Watchlist root must be a JSON object."
        )

    if "tickers" not in data:
        raise ConfigurationError(
            "Watchlist must contain a 'tickers' field."
        )

    tickers = data["tickers"]

    if not isinstance(tickers, list):
        raise ConfigurationError(
            "'tickers' must be a JSON array."
        )

    normalized_tickers: list[str] = []

    for ticker in tickers:

        if not isinstance(ticker, str):
            raise ConfigurationError(
                "Every ticker must be a string."
            )

        ticker = ticker.strip().upper()

        if not ticker:
            raise ConfigurationError(
                "Ticker cannot be empty."
            )

        if ticker not in normalized_tickers:
            normalized_tickers.append(
                ticker
            )

    return normalized_tickers

def get_database_path() -> str:
    """
        Backward-compatible helper used
        by code from earlier days.
    """
    return load_config().database_path            