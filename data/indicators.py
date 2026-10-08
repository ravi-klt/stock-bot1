from typing import Protocol, Sequence


class CandleLike(Protocol):
    """
    Minimal candle contract required
    by the indicator functions.

    Any object with these attributes
    can be used, including DailyBar
    and WeeklyBar.
    """

    open: float
    high: float
    low: float
    close: float
    volume: float


def _require_bars(
    bars: Sequence[CandleLike],
    required: int,
    indicator_name: str,
) -> None:
    if len(bars) < required:
        raise ValueError(
            f"{indicator_name} requires at least "
            f"{required} bars; received {len(bars)}."
        )


def candle_range(
    candle: CandleLike,
) -> float:
    """
    Absolute high-low range of one candle.
    """

    return candle.high - candle.low


def true_range(
    candle: CandleLike,
    previous_close: float | None = None,
) -> float:
    """
    True Range captures both the candle's
    own range and any gap from the previous
    close.
    """

    high_low = (
        candle.high
        - candle.low
    )

    if previous_close is None:
        return high_low

    high_previous = abs(
        candle.high
        - previous_close
    )

    low_previous = abs(
        candle.low
        - previous_close
    )

    return max(
        high_low,
        high_previous,
        low_previous,
    )


def atr14(
    bars: Sequence[CandleLike],
    period: int = 14,
) -> float:
    """
    Average of the latest `period`
    True Range values.

    Default period = 14.
    """

    if period <= 0:
        raise ValueError(
            "ATR period must be greater than zero."
        )

    _require_bars(
        bars=bars,
        required=period,
        indicator_name=f"ATR{period}",
    )

    true_ranges: list[float] = []

    for index, candle in enumerate(
        bars
    ):
        previous_close = (
            bars[index - 1].close
            if index > 0
            else None
        )

        true_ranges.append(
            true_range(
                candle=candle,
                previous_close=previous_close,
            )
        )

    latest_ranges = (
        true_ranges[-period:]
    )

    return (
        sum(latest_ranges)
        / period
    )


def volume_ma20(
    bars: Sequence[CandleLike],
    period: int = 20,
) -> float:
    """
    Average volume of the latest
    `period` completed candles.

    Default period = 20.
    """

    if period <= 0:
        raise ValueError(
            "Volume MA period must be "
            "greater than zero."
        )

    _require_bars(
        bars=bars,
        required=period,
        indicator_name=(
            f"Volume MA{period}"
        ),
    )

    latest_bars = (
        bars[-period:]
    )

    total_volume = sum(
        candle.volume
        for candle in latest_bars
    )

    return (
        total_volume
        / period
    )


def volume_ratio(
    candle: CandleLike,
    average_volume: float,
) -> float:
    """
    Current candle volume divided by
    average volume.
    """

    if average_volume <= 0:
        raise ValueError(
            "Average volume must be "
            "greater than zero."
        )

    return (
        candle.volume
        / average_volume
    )


def range_in_atr(
    candle: CandleLike,
    atr: float,
) -> float:
    """
    Candle high-low range expressed
    in ATR units.
    """

    if atr <= 0:
        raise ValueError(
            "ATR must be greater than zero."
        )

    return (
        candle_range(candle)
        / atr
    )


def close_location(
    candle: CandleLike,
) -> float:
    """
    Close position inside the candle.

    0.0 = close at low
    0.5 = midpoint
    1.0 = close at high
    """

    range_value = (
        candle_range(candle)
    )

    if range_value == 0:
        return 0.5

    return (
        candle.close
        - candle.low
    ) / range_value


def ema20(
    bars: Sequence[CandleLike],
    period: int = 20,
) -> float:
    """
    Latest exponential moving average.

    Uses the first `period` closes'
    simple average as the EMA seed.
    """

    if period <= 0:
        raise ValueError(
            "EMA period must be greater "
            "than zero."
        )

    _require_bars(
        bars=bars,
        required=period,
        indicator_name=f"EMA{period}",
    )

    first_period = (
        bars[:period]
    )

    ema = (
        sum(
            candle.close
            for candle
            in first_period
        )
        / period
    )

    multiplier = (
        2.0
        / (period + 1)
    )

    for candle in bars[period:]:
        ema = (
            candle.close
            * multiplier
        ) + (
            ema
            * (1.0 - multiplier)
        )

    return ema


def ma50(
    bars: Sequence[CandleLike],
    period: int = 50,
) -> float:
    """
    Simple moving average of the latest
    `period` closing prices.

    Default period = 50.
    """

    if period <= 0:
        raise ValueError(
            "MA period must be greater "
            "than zero."
        )

    _require_bars(
        bars=bars,
        required=period,
        indicator_name=f"MA{period}",
    )

    latest_bars = (
        bars[-period:]
    )

    return (
        sum(
            candle.close
            for candle
            in latest_bars
        )
        / period
    )