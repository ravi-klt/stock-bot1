from dataclasses import dataclass

import pytest

from data.indicators import (
    atr14,
    candle_range,
    close_location,
    ema20,
    ma50,
    range_in_atr,
    true_range,
    volume_ma20,
    volume_ratio,
)


@dataclass(frozen=True)
class TestCandle:
    open: float
    high: float
    low: float
    close: float
    volume: float


def make_constant_range_bars(
    count: int,
) -> list[TestCandle]:
    """
    Creates steadily rising candles
    where every True Range is 2.

    Example close sequence:
    100, 101, 102, ...

    Every candle:
    high = close + 1
    low = close - 1
    """

    bars = []

    for index in range(count):
        close = (
            100.0
            + index
        )

        bars.append(
            TestCandle(
                open=close,
                high=close + 1,
                low=close - 1,
                close=close,
                volume=1_000_000,
            )
        )

    return bars


def test_candle_range():

    candle = TestCandle(
        open=100,
        high=110,
        low=90,
        close=105,
        volume=1_000_000,
    )

    assert (
        candle_range(candle)
        == 20
    )


def test_true_range_without_previous_close():

    candle = TestCandle(
        open=100,
        high=105,
        low=99,
        close=104,
        volume=1_000_000,
    )

    assert (
        true_range(candle)
        == 6
    )


def test_true_range_includes_gap():

    candle = TestCandle(
        open=110,
        high=112,
        low=108,
        close=111,
        volume=1_000_000,
    )

    result = true_range(
        candle=candle,
        previous_close=100,
    )

    assert result == 12


def test_atr14():

    bars = (
        make_constant_range_bars(
            14
        )
    )

    result = atr14(
        bars
    )

    # Every True Range is 2:
    #
    # high = close + 1
    # low  = close - 1
    #
    # therefore ATR14 = 2.
    assert result == pytest.approx(
        2.0
    )


def test_volume_ma20():

    bars = []

    for index in range(
        1,
        21,
    ):
        bars.append(
            TestCandle(
                open=100,
                high=101,
                low=99,
                close=100,
                volume=(
                    index * 100
                ),
            )
        )

    result = volume_ma20(
        bars
    )

    # Volumes:
    # 100, 200, ... 2000
    #
    # arithmetic mean =
    # (100 + 2000) / 2
    # = 1050
    assert result == pytest.approx(
        1050.0
    )


def test_volume_ratio():

    candle = TestCandle(
        open=100,
        high=101,
        low=99,
        close=100,
        volume=13_000_000,
    )

    result = volume_ratio(
        candle=candle,
        average_volume=10_000_000,
    )

    assert result == pytest.approx(
        1.3
    )


def test_volume_ratio_rejects_zero_average():

    candle = TestCandle(
        open=100,
        high=101,
        low=99,
        close=100,
        volume=1_000_000,
    )

    with pytest.raises(
        ValueError
    ):
        volume_ratio(
            candle=candle,
            average_volume=0,
        )


def test_range_in_atr():

    candle = TestCandle(
        open=100,
        high=108,
        low=100,
        close=106,
        volume=1_000_000,
    )

    result = range_in_atr(
        candle=candle,
        atr=4,
    )

    assert result == pytest.approx(
        2.0
    )


def test_range_in_atr_rejects_zero_atr():

    candle = TestCandle(
        open=100,
        high=108,
        low=100,
        close=106,
        volume=1_000_000,
    )

    with pytest.raises(
        ValueError
    ):
        range_in_atr(
            candle=candle,
            atr=0,
        )


def test_close_location():

    candle = TestCandle(
        open=100,
        high=110,
        low=90,
        close=105,
        volume=1_000_000,
    )

    result = close_location(
        candle
    )

    # (105 - 90)
    # -----------
    # (110 - 90)
    #
    # = 15 / 20
    # = 0.75

    assert result == pytest.approx(
        0.75
    )


def test_close_location_flat_candle():

    candle = TestCandle(
        open=100,
        high=100,
        low=100,
        close=100,
        volume=1_000_000,
    )

    assert (
        close_location(candle)
        == 0.5
    )


def test_ema20_constant_prices():

    bars = [
        TestCandle(
            open=100,
            high=101,
            low=99,
            close=100,
            volume=1_000_000,
        )
        for _ in range(25)
    ]

    result = ema20(
        bars
    )

    # Constant price means EMA
    # must remain exactly 100.
    assert result == pytest.approx(
        100.0
    )


def test_ema_with_small_period_manual_check():

    bars = [
        TestCandle(
            open=close,
            high=close + 1,
            low=close - 1,
            close=close,
            volume=1_000_000,
        )
        for close in [
            10.0,
            11.0,
            12.0,
            13.0,
        ]
    ]

    result = ema20(
        bars=bars,
        period=3,
    )

    # Initial SMA:
    # (10 + 11 + 12) / 3 = 11
    #
    # multiplier:
    # 2 / (3 + 1) = 0.5
    #
    # next EMA:
    # 13 * 0.5 + 11 * 0.5
    # = 12

    assert result == pytest.approx(
        12.0
    )


def test_ma50():

    bars = [
        TestCandle(
            open=float(value),
            high=float(value + 1),
            low=float(value - 1),
            close=float(value),
            volume=1_000_000,
        )
        for value in range(
            1,
            51,
        )
    ]

    result = ma50(
        bars
    )

    # Mean of 1 through 50:
    #
    # (1 + 50) / 2
    # = 25.5

    assert result == pytest.approx(
        25.5
    )


def test_not_enough_bars_for_atr14():

    bars = (
        make_constant_range_bars(
            10
        )
    )

    with pytest.raises(
        ValueError
    ):
        atr14(
            bars
        )


def test_not_enough_bars_for_ma50():

    bars = (
        make_constant_range_bars(
            20
        )
    )

    with pytest.raises(
        ValueError
    ):
        ma50(
            bars
        )