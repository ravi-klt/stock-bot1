from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    time,
)
from zoneinfo import ZoneInfo

from broker.ibkr_client import (
    BrokerBar,
    IBKRClient,
)


NEW_YORK = ZoneInfo(
    "America/New_York"
)


class MarketDataError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class DailyBar:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class WeeklyBar:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class MarketDataBundle:
    daily: list[DailyBar]
    weekly: list[WeeklyBar]


def _parse_ibkr_date(
    value: str,
) -> date:

    value = value.strip()

    if (
        len(value) >= 8
        and
        value[:8].isdigit()
    ):
        return datetime.strptime(
            value[:8],
            "%Y%m%d",
        ).date()

    try:
        return date.fromisoformat(
            value
        )

    except ValueError as exc:
        raise MarketDataError(
            f"Unsupported IBKR bar date: "
            f"{value}"
        ) from exc


def _new_york_now(
    now: datetime | None,
) -> datetime:

    if now is None:
        return datetime.now(
            NEW_YORK
        )

    if now.tzinfo is None:
        return now.replace(
            tzinfo=NEW_YORK
        )

    return now.astimezone(
        NEW_YORK
    )


def _validate_ohlcv(
    bar: BrokerBar,
) -> None:

    values = (
        bar.open,
        bar.high,
        bar.low,
        bar.close,
    )

    if any(
        value <= 0
        for value in values
    ):
        raise MarketDataError(
            f"Invalid non-positive OHLC "
            f"for {bar.date}."
        )

    if bar.high < bar.low:
        raise MarketDataError(
            f"High below low for "
            f"{bar.date}."
        )

    if bar.high < max(
        bar.open,
        bar.close,
    ):
        raise MarketDataError(
            f"High is below open/close "
            f"for {bar.date}."
        )

    if bar.low > min(
        bar.open,
        bar.close,
    ):
        raise MarketDataError(
            f"Low is above open/close "
            f"for {bar.date}."
        )

    if bar.volume < 0:
        raise MarketDataError(
            f"Negative volume for "
            f"{bar.date}."
        )


def _validate_ordering(
    bars: list[BrokerBar],
) -> None:

    dates = [
        _parse_ibkr_date(
            bar.date
        )
        for bar in bars
    ]

    for previous, current in zip(
        dates,
        dates[1:],
    ):
        if current <= previous:
            raise MarketDataError(
                "Market bars must be "
                "strictly ordered from "
                "oldest to newest."
            )


def _daily_completed(
    bar_date: date,
    now: datetime,
) -> bool:

    if bar_date < now.date():
        return True

    if bar_date > now.date():
        return False

    if now.weekday() >= 5:
        return False

    return (
        now.time()
        >= time(16, 15)
    )


def _weekly_completed(
    bar_date: date,
    now: datetime,
) -> bool:

    bar_week = (
        bar_date.isocalendar().year,
        bar_date.isocalendar().week,
    )

    current_week = (
        now.date()
        .isocalendar()
    )

    current_week_key = (
        current_week.year,
        current_week.week,
    )

    if bar_week < current_week_key:
        return True

    if bar_week > current_week_key:
        return False

    return (
        now.weekday() >= 4
        and
        now.time()
        >= time(16, 15)
    )


class MarketDataService:

    def __init__(
        self,
        ibkr_client: IBKRClient,
    ) -> None:

        self.ibkr_client = (
            ibkr_client
        )

    def _validate_raw_bars(
        self,
        bars: list[BrokerBar],
    ) -> None:

        if not bars:
            raise MarketDataError(
                "No market data returned."
            )

        _validate_ordering(
            bars
        )

        for bar in bars:
            _validate_ohlcv(
                bar
            )

    def get_daily_bars(
        self,
        ticker: str,
        now: datetime | None = None,
        max_stale_days: int = 7,
    ) -> list[DailyBar]:

        raw_bars = (
            self.ibkr_client
            .get_daily_bars(
                ticker
            )
        )

        self._validate_raw_bars(
            raw_bars
        )

        ny_now = _new_york_now(
            now
        )

        completed: list[
            DailyBar
        ] = []

        for bar in raw_bars:

            bar_date = (
                _parse_ibkr_date(
                    bar.date
                )
            )

            if not _daily_completed(
                bar_date,
                ny_now,
            ):
                continue

            completed.append(
                DailyBar(
                    date=bar_date,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                )
            )

        if not completed:
            raise MarketDataError(
                "No completed daily "
                "bars are available."
            )

        age_days = (
            ny_now.date()
            - completed[-1].date
        ).days

        if age_days > max_stale_days:
            raise MarketDataError(
                f"Daily market data is "
                f"stale by {age_days} days."
            )

        return completed

    def get_weekly_bars(
        self,
        ticker: str,
        now: datetime | None = None,
        max_stale_days: int = 14,
    ) -> list[WeeklyBar]:

        raw_bars = (
            self.ibkr_client
            .get_weekly_bars(
                ticker
            )
        )

        self._validate_raw_bars(
            raw_bars
        )

        ny_now = _new_york_now(
            now
        )

        completed: list[
            WeeklyBar
        ] = []

        for bar in raw_bars:

            bar_date = (
                _parse_ibkr_date(
                    bar.date
                )
            )

            if not _weekly_completed(
                bar_date,
                ny_now,
            ):
                continue

            completed.append(
                WeeklyBar(
                    date=bar_date,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                )
            )

        if not completed:
            raise MarketDataError(
                "No completed weekly "
                "bars are available."
            )

        age_days = (
            ny_now.date()
            - completed[-1].date
        ).days

        if age_days > max_stale_days:
            raise MarketDataError(
                f"Weekly market data is "
                f"stale by {age_days} days."
            )

        return completed

    def load_market_data(
        self,
        ticker: str,
        now: datetime | None = None,
    ) -> MarketDataBundle:

        daily = self.get_daily_bars(
            ticker=ticker,
            now=now,
        )

        weekly = self.get_weekly_bars(
            ticker=ticker,
            now=now,
        )

        return MarketDataBundle(
            daily=daily,
            weekly=weekly,
        )

    def get_sample_daily_bars(
        self,
        ticker: str,
        duration: str = "3 M",
    ) -> list[DailyBar]:

        raw_bars = (
            self.ibkr_client
            .request_daily_bars(
                ticker=ticker,
                duration=duration,
            )
        )

        return [
            DailyBar(
                date=_parse_ibkr_date(
                    bar.date
                ),
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
            )
            for bar in raw_bars
        ]