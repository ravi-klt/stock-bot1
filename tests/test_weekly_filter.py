from dataclasses import dataclass

import pytest

from data.relative_strength import (
    RelativeStrengthRating,
    calculate_relative_strength,
)

from data.structure import (
    LevelType,
    MarketStructure,
    StructuralLevel,
    Timeframe,
    TrendStructure,
    next_major_weekly_resistance,
)

from strategy.weekly_filter import (
    OverheadRoomStatus,
    WeeklyEligibility,
    overhead_room_is_acceptable,
    passes_weekly_filter,
)


@dataclass(frozen=True)
class PriceBar:
    close: float


def weekly_structure(
    trend: TrendStructure,
    resistance_levels=(),
) -> MarketStructure:

    return MarketStructure(
        timeframe=(
            Timeframe.WEEKLY
        ),
        pivots=(),
        support_levels=(),
        resistance_levels=tuple(
            resistance_levels
        ),
        latest_high_label=None,
        latest_low_label=None,
        trend=trend,
    )


def resistance(
    lower: float,
    upper: float,
) -> StructuralLevel:

    return StructuralLevel(
        lower=lower,
        upper=upper,
        center=(
            lower + upper
        ) / 2,
        level_type=(
            LevelType.RESISTANCE
        ),
        source=(
            "SWING_HIGH_CLUSTER"
        ),
        timeframe=(
            Timeframe.WEEKLY
        ),
        touches=2,
    )


def growth_bars(
    start: float,
    final: float,
    count: int = 61,
) -> list[PriceBar]:
    """
    Create a simple deterministic
    price path from start to final.
    """

    if count < 2:
        raise ValueError(
            "count must be at least 2."
        )

    step = (
        final - start
    ) / (
        count - 1
    )

    return [
        PriceBar(
            close=(
                start
                + step * index
            )
        )
        for index in range(
            count
        )
    ]


def test_healthy_weekly_uptrend_passes():

    structure = weekly_structure(
        TrendStructure.UPTREND
    )

    result = (
        passes_weekly_filter(
            structure
        )
    )

    assert (
        result
        == WeeklyEligibility.PASS
    )


def test_clear_weekly_downtrend_fails():

    structure = weekly_structure(
        TrendStructure.DOWNTREND
    )

    result = (
        passes_weekly_filter(
            structure
        )
    )

    assert (
        result
        == WeeklyEligibility.FAIL
    )


def test_mixed_weekly_structure_waits():

    structure = weekly_structure(
        TrendStructure.MIXED
    )

    result = (
        passes_weekly_filter(
            structure
        )
    )

    assert (
        result
        == WeeklyEligibility.WAIT
    )


def test_unknown_weekly_structure_waits():

    structure = weekly_structure(
        TrendStructure.UNKNOWN
    )

    result = (
        passes_weekly_filter(
            structure
        )
    )

    assert (
        result
        == WeeklyEligibility.WAIT
    )


def test_next_major_weekly_resistance():

    structure = weekly_structure(
        trend=(
            TrendStructure.UPTREND
        ),
        resistance_levels=(
            resistance(
                95,
                97,
            ),
            resistance(
                119,
                121,
            ),
            resistance(
                139,
                142,
            ),
        ),
    )

    result = (
        next_major_weekly_resistance(
            proposed_entry=110,
            weekly_structure=(
                structure
            ),
        )
    )

    assert result is not None

    assert result.lower == 119
    assert result.upper == 121


def test_no_resistance_above_entry_returns_none():

    structure = weekly_structure(
        trend=(
            TrendStructure.UPTREND
        ),
        resistance_levels=(
            resistance(
                90,
                92,
            ),
            resistance(
                95,
                98,
            ),
        ),
    )

    result = (
        next_major_weekly_resistance(
            proposed_entry=100,
            weekly_structure=(
                structure
            ),
        )
    )

    assert result is None


def test_resistance_too_close_is_poor():

    level = resistance(
        lower=102,
        upper=104,
    )

    result = (
        overhead_room_is_acceptable(
            proposed_entry=100,
            proposed_stop=95,
            next_weekly_resistance=(
                level
            ),
            atr=4,
        )
    )

    # room:
    # 102 - 100 = 2
    #
    # room ATR:
    # 2 / 4 = 0.5
    #
    # risk:
    # 100 - 95 = 5
    #
    # room vs risk:
    # 2 / 5 = 0.4

    assert (
        result.status
        == OverheadRoomStatus.POOR
    )

    assert (
        result.room_atr
        == pytest.approx(
            0.5
        )
    )

    assert (
        result.room_vs_risk
        == pytest.approx(
            0.4
        )
    )


def test_no_rigid_two_r_rule():

    level = resistance(
        lower=109,
        upper=111,
    )

    result = (
        overhead_room_is_acceptable(
            proposed_entry=100,
            proposed_stop=95,
            next_weekly_resistance=(
                level
            ),
            atr=2.5,
        )
    )

    # risk:
    # 100 - 95 = 5
    #
    # room:
    # 109 - 100 = 9
    #
    # room / risk:
    # 9 / 5 = 1.8R
    #
    # A rigid 2R rule would reject it.
    #
    # But room in ATR:
    # 9 / 2.5 = 3.6 ATR
    #
    # So the bot does not reject
    # purely because 1.8 < 2.

    assert (
        result.room_vs_risk
        == pytest.approx(
            1.8
        )
    )

    assert (
        result.room_atr
        == pytest.approx(
            3.6
        )
    )

    assert (
        result.status
        == OverheadRoomStatus.ACCEPTABLE
    )


def test_no_weekly_resistance_is_not_automatic_failure():

    result = (
        overhead_room_is_acceptable(
            proposed_entry=100,
            proposed_stop=95,
            next_weekly_resistance=None,
            atr=4,
        )
    )

    assert (
        result.status
        == OverheadRoomStatus.ACCEPTABLE
    )

    assert result.resistance is None


def test_strong_relative_strength():

    stock = growth_bars(
        start=100,
        final=130,
    )

    benchmark = growth_bars(
        start=100,
        final=110,
    )

    sector = growth_bars(
        start=100,
        final=115,
    )

    result = (
        calculate_relative_strength(
            stock=stock,
            benchmark=benchmark,
            sector=sector,
        )
    )

    assert (
        result.rating
        == RelativeStrengthRating.STRONG
    )

    assert (
        result.medium_vs_benchmark
        > 0
    )

    assert (
        result.medium_vs_sector
        > 0
    )


def test_weak_relative_strength():

    stock = growth_bars(
        start=100,
        final=95,
    )

    benchmark = growth_bars(
        start=100,
        final=110,
    )

    sector = growth_bars(
        start=100,
        final=105,
    )

    result = (
        calculate_relative_strength(
            stock=stock,
            benchmark=benchmark,
            sector=sector,
        )
    )

    assert (
        result.rating
        == RelativeStrengthRating.WEAK
    )


def test_mixed_relative_strength_is_neutral():

    stock = growth_bars(
        start=100,
        final=112,
    )

    benchmark = growth_bars(
        start=100,
        final=110,
    )

    sector = growth_bars(
        start=100,
        final=120,
    )

    result = (
        calculate_relative_strength(
            stock=stock,
            benchmark=benchmark,
            sector=sector,
        )
    )

    assert (
        result.rating
        == RelativeStrengthRating.NEUTRAL
    )