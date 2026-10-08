from dataclasses import dataclass

from data.structure import (
    LevelType,
    PivotType,
    StructureLabel,
    Timeframe,
    TrendStructure,
    analyse_daily_structure,
    analyse_weekly_structure,
    confirmed_pivots_as_of,
    detect_confirmed_pivots,
)


@dataclass(frozen=True)
class TestBar:
    high: float
    low: float
    close: float


def bar(
    high: float,
    low: float,
) -> TestBar:

    return TestBar(
        high=high,
        low=low,
        close=(
            high + low
        ) / 2,
    )


def test_confirmed_swing_high():

    bars = [
        bar(5, 4),
        bar(7, 5),
        bar(10, 6),
        bar(8, 5),
        bar(6, 4),
    ]

    pivots = (
        detect_confirmed_pivots(
            bars
        )
    )

    highs = [
        pivot
        for pivot in pivots
        if (
            pivot.pivot_type
            == PivotType.HIGH
        )
    ]

    assert len(highs) == 1

    assert highs[0].index == 2

    assert (
        highs[0]
        .confirmed_at_index
        == 4
    )

    assert highs[0].price == 10


def test_pivot_not_visible_before_confirmation():

    bars = [
        bar(5, 4),
        bar(7, 5),
        bar(10, 6),
        bar(8, 5),
        bar(6, 4),
    ]

    before_confirmation = (
        confirmed_pivots_as_of(
            bars=bars,
            as_of_index=3,
        )
    )

    confirmed = (
        confirmed_pivots_as_of(
            bars=bars,
            as_of_index=4,
        )
    )

    before_highs = [
        pivot
        for pivot
        in before_confirmation
        if (
            pivot.pivot_type
            == PivotType.HIGH
        )
    ]

    confirmed_highs = [
        pivot
        for pivot
        in confirmed
        if (
            pivot.pivot_type
            == PivotType.HIGH
        )
    ]

    assert (
        len(before_highs)
        == 0
    )

    assert (
        len(confirmed_highs)
        == 1
    )


def test_higher_high_label():

    bars = [
        bar(5, 4),
        bar(7, 5),
        bar(10, 6),
        bar(8, 5),
        bar(6, 4),

        bar(8, 5),
        bar(12, 6),
        bar(15, 7),
        bar(11, 6),
        bar(9, 5),
    ]

    pivots = (
        detect_confirmed_pivots(
            bars
        )
    )

    highs = [
        pivot
        for pivot in pivots
        if (
            pivot.pivot_type
            == PivotType.HIGH
        )
    ]

    assert len(highs) >= 2

    assert (
        highs[-1].label
        == StructureLabel.HH
    )


def test_lower_high_label():

    bars = [
        bar(5, 4),
        bar(7, 5),
        bar(15, 6),
        bar(8, 5),
        bar(6, 4),

        bar(8, 5),
        bar(10, 6),
        bar(12, 7),
        bar(9, 6),
        bar(7, 5),
    ]

    pivots = (
        detect_confirmed_pivots(
            bars
        )
    )

    highs = [
        pivot
        for pivot in pivots
        if (
            pivot.pivot_type
            == PivotType.HIGH
        )
    ]

    assert len(highs) >= 2

    assert (
        highs[-1].label
        == StructureLabel.LH
    )


def test_higher_low_label():

    bars = [
        bar(12, 8),
        bar(10, 6),
        bar(9, 4),
        bar(11, 6),
        bar(13, 8),

        bar(12, 9),
        bar(11, 7),
        bar(10, 6),
        bar(12, 8),
        bar(14, 10),
    ]

    pivots = (
        detect_confirmed_pivots(
            bars
        )
    )

    lows = [
        pivot
        for pivot in pivots
        if (
            pivot.pivot_type
            == PivotType.LOW
        )
    ]

    assert len(lows) >= 2

    assert (
        lows[-1].label
        == StructureLabel.HL
    )


def test_daily_structure_timeframe():

    bars = [
        bar(5, 4),
        bar(7, 5),
        bar(10, 6),
        bar(8, 5),
        bar(6, 4),
    ]

    structure = (
        analyse_daily_structure(
            bars
        )
    )

    assert (
        structure.timeframe
        == Timeframe.DAILY
    )


def test_weekly_structure_is_separate():

    bars = [
        bar(100, 90),
        bar(105, 92),
        bar(120, 95),
        bar(110, 93),
        bar(100, 91),
    ]

    structure = (
        analyse_weekly_structure(
            bars
        )
    )

    assert (
        structure.timeframe
        == Timeframe.WEEKLY
    )


def test_clustered_swing_lows_create_support():

    bars = [
        bar(110, 105),
        bar(108, 102),
        bar(106, 100),
        bar(109, 103),
        bar(112, 106),

        bar(110, 104),
        bar(108, 101),
        bar(106, 100.5),
        bar(110, 104),
        bar(113, 107),
    ]

    structure = (
        analyse_daily_structure(
            bars
        )
    )

    supports = (
        structure.support_levels
    )

    assert (
        len(supports)
        >= 1
    )

    support = supports[0]

    assert (
        support.level_type
        == LevelType.SUPPORT
    )

    assert (
        support.timeframe
        == Timeframe.DAILY
    )

    assert support.touches >= 2


def test_clustered_swing_highs_create_resistance():

    bars = [
        bar(100, 95),
        bar(105, 97),
        bar(110, 100),
        bar(106, 98),
        bar(102, 96),

        bar(105, 98),
        bar(109.5, 100),
        bar(110.5, 101),
        bar(106, 99),
        bar(103, 97),
    ]

    structure = (
        analyse_daily_structure(
            bars
        )
    )

    resistance = (
        structure
        .resistance_levels
    )

    assert (
        len(resistance)
        >= 1
    )

    level = resistance[0]

    assert (
        level.level_type
        == LevelType.RESISTANCE
    )

    assert (
        level.timeframe
        == Timeframe.DAILY
    )


def test_uptrend_classification():

    bars = [
        bar(10, 7),
        bar(12, 8),
        bar(15, 9),
        bar(12, 7),
        bar(11, 5),

        bar(13, 8),
        bar(18, 10),
        bar(16, 9),
        bar(14, 7),
        bar(13, 6),

        bar(16, 10),
        bar(21, 12),
        bar(18, 11),
        bar(17, 9),
        bar(16, 8),
    ]

    structure = (
        analyse_daily_structure(
            bars
        )
    )

    assert (
        structure.latest_high_label
        in {
            StructureLabel.HH,
            None,
        }
    )

    assert (
        structure.trend
        in {
            TrendStructure.UPTREND,
            TrendStructure.MIXED,
            TrendStructure.UNKNOWN,
        }
    )