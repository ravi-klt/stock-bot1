from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence


class CandleLike(Protocol):
    high: float
    low: float
    close: float


class PivotType(str, Enum):
    HIGH = "HIGH"
    LOW = "LOW"


class StructureLabel(str, Enum):
    HH = "HH"
    HL = "HL"
    LH = "LH"
    LL = "LL"


class Timeframe(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


class LevelType(str, Enum):
    SUPPORT = "SUPPORT"
    RESISTANCE = "RESISTANCE"


class TrendStructure(str, Enum):
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ConfirmedPivot:
    index: int
    confirmed_at_index: int
    price: float
    pivot_type: PivotType
    label: StructureLabel | None


@dataclass(frozen=True)
class StructuralLevel:
    lower: float
    upper: float
    center: float
    level_type: LevelType
    source: str
    timeframe: Timeframe
    touches: int


@dataclass(frozen=True)
class MarketStructure:
    timeframe: Timeframe

    pivots: tuple[
        ConfirmedPivot,
        ...
    ]

    support_levels: tuple[
        StructuralLevel,
        ...
    ]

    resistance_levels: tuple[
        StructuralLevel,
        ...
    ]

    latest_high_label: (
        StructureLabel | None
    )

    latest_low_label: (
        StructureLabel | None
    )

    trend: TrendStructure


def _validate_pivot_window(
    left_bars: int,
    right_bars: int,
) -> None:

    if left_bars <= 0:
        raise ValueError(
            "left_bars must be greater "
            "than zero."
        )

    if right_bars <= 0:
        raise ValueError(
            "right_bars must be greater "
            "than zero."
        )


def _is_swing_high(
    bars: Sequence[CandleLike],
    index: int,
    left_bars: int,
    right_bars: int,
) -> bool:

    candidate = (
        bars[index].high
    )

    left = bars[
        index - left_bars:index
    ]

    right = bars[
        index + 1:
        index + right_bars + 1
    ]

    return (
        all(
            candidate > item.high
            for item in left
        )
        and
        all(
            candidate > item.high
            for item in right
        )
    )


def _is_swing_low(
    bars: Sequence[CandleLike],
    index: int,
    left_bars: int,
    right_bars: int,
) -> bool:

    candidate = (
        bars[index].low
    )

    left = bars[
        index - left_bars:index
    ]

    right = bars[
        index + 1:
        index + right_bars + 1
    ]

    return (
        all(
            candidate < item.low
            for item in left
        )
        and
        all(
            candidate < item.low
            for item in right
        )
    )


def detect_confirmed_pivots(
    bars: Sequence[CandleLike],
    left_bars: int = 2,
    right_bars: int = 2,
) -> list[ConfirmedPivot]:

    _validate_pivot_window(
        left_bars,
        right_bars,
    )

    minimum_bars = (
        left_bars
        + right_bars
        + 1
    )

    if len(bars) < minimum_bars:
        return []

    pivots: list[
        ConfirmedPivot
    ] = []

    previous_high_price: (
        float | None
    ) = None

    previous_low_price: (
        float | None
    ) = None

    first_index = (
        left_bars
    )

    last_index = (
        len(bars)
        - right_bars
    )

    for index in range(
        first_index,
        last_index,
    ):

        confirmed_at = (
            index
            + right_bars
        )

        if _is_swing_high(
            bars=bars,
            index=index,
            left_bars=left_bars,
            right_bars=right_bars,
        ):

            price = (
                bars[index].high
            )

            label = None

            if (
                previous_high_price
                is not None
            ):

                label = (
                    StructureLabel.HH
                    if price
                    > previous_high_price
                    else StructureLabel.LH
                )

            pivots.append(
                ConfirmedPivot(
                    index=index,
                    confirmed_at_index=(
                        confirmed_at
                    ),
                    price=price,
                    pivot_type=(
                        PivotType.HIGH
                    ),
                    label=label,
                )
            )

            previous_high_price = (
                price
            )

        if _is_swing_low(
            bars=bars,
            index=index,
            left_bars=left_bars,
            right_bars=right_bars,
        ):

            price = (
                bars[index].low
            )

            label = None

            if (
                previous_low_price
                is not None
            ):

                label = (
                    StructureLabel.HL
                    if price
                    > previous_low_price
                    else StructureLabel.LL
                )

            pivots.append(
                ConfirmedPivot(
                    index=index,
                    confirmed_at_index=(
                        confirmed_at
                    ),
                    price=price,
                    pivot_type=(
                        PivotType.LOW
                    ),
                    label=label,
                )
            )

            previous_low_price = (
                price
            )

    pivots.sort(
        key=lambda pivot: (
            pivot.confirmed_at_index,
            pivot.index,
        )
    )

    return pivots


def confirmed_pivots_as_of(
    bars: Sequence[CandleLike],
    as_of_index: int,
    left_bars: int = 2,
    right_bars: int = 2,
) -> list[ConfirmedPivot]:

    if as_of_index < 0:
        return []

    visible_bars = bars[
        :as_of_index + 1
    ]

    return (
        detect_confirmed_pivots(
            bars=visible_bars,
            left_bars=left_bars,
            right_bars=right_bars,
        )
    )


def _cluster_prices(
    prices: list[float],
    tolerance_percent: float,
) -> list[list[float]]:

    if not prices:
        return []

    if tolerance_percent <= 0:
        raise ValueError(
            "tolerance_percent must "
            "be greater than zero."
        )

    ordered = sorted(
        prices
    )

    clusters: list[
        list[float]
    ] = [
        [
            ordered[0]
        ]
    ]

    for price in ordered[1:]:

        current_cluster = (
            clusters[-1]
        )

        center = (
            sum(current_cluster)
            / len(current_cluster)
        )

        tolerance = (
            center
            * tolerance_percent
        )

        if (
            abs(
                price - center
            )
            <= tolerance
        ):

            current_cluster.append(
                price
            )

        else:

            clusters.append(
                [
                    price
                ]
            )

    return clusters


def _levels_from_pivots(
    pivots: Sequence[ConfirmedPivot],
    pivot_type: PivotType,
    level_type: LevelType,
    timeframe: Timeframe,
    tolerance_percent: float = 0.01,
    minimum_touches: int = 2,
) -> list[StructuralLevel]:

    prices = [
        pivot.price
        for pivot in pivots
        if (
            pivot.pivot_type
            == pivot_type
        )
    ]

    clusters = (
        _cluster_prices(
            prices=prices,
            tolerance_percent=(
                tolerance_percent
            ),
        )
    )

    levels: list[
        StructuralLevel
    ] = []

    for cluster in clusters:

        if (
            len(cluster)
            < minimum_touches
        ):
            continue

        lower = min(
            cluster
        )

        upper = max(
            cluster
        )

        center = (
            sum(cluster)
            / len(cluster)
        )

        source = (
            "SWING_LOW_CLUSTER"
            if level_type
            == LevelType.SUPPORT
            else "SWING_HIGH_CLUSTER"
        )

        levels.append(
            StructuralLevel(
                lower=lower,
                upper=upper,
                center=center,
                level_type=(
                    level_type
                ),
                source=source,
                timeframe=timeframe,
                touches=len(
                    cluster
                ),
            )
        )

    return levels


def _latest_label(
    pivots: Sequence[ConfirmedPivot],
    pivot_type: PivotType,
) -> StructureLabel | None:

    matching = [
        pivot
        for pivot in pivots
        if (
            pivot.pivot_type
            == pivot_type
            and
            pivot.label
            is not None
        )
    ]

    if not matching:
        return None

    return (
        matching[-1].label
    )


def _classify_trend(
    latest_high_label:
        StructureLabel | None,
    latest_low_label:
        StructureLabel | None,
) -> TrendStructure:

    if (
        latest_high_label
        == StructureLabel.HH
        and
        latest_low_label
        == StructureLabel.HL
    ):
        return (
            TrendStructure.UPTREND
        )

    if (
        latest_high_label
        == StructureLabel.LH
        and
        latest_low_label
        == StructureLabel.LL
    ):
        return (
            TrendStructure.DOWNTREND
        )

    if (
        latest_high_label
        is None
        or
        latest_low_label
        is None
    ):
        return (
            TrendStructure.UNKNOWN
        )

    return (
        TrendStructure.MIXED
    )


def _analyse_structure(
    bars: Sequence[CandleLike],
    timeframe: Timeframe,
    left_bars: int,
    right_bars: int,
    tolerance_percent: float,
) -> MarketStructure:

    pivots = (
        detect_confirmed_pivots(
            bars=bars,
            left_bars=left_bars,
            right_bars=right_bars,
        )
    )

    support_levels = (
        _levels_from_pivots(
            pivots=pivots,
            pivot_type=PivotType.LOW,
            level_type=(
                LevelType.SUPPORT
            ),
            timeframe=timeframe,
            tolerance_percent=(
                tolerance_percent
            ),
        )
    )

    resistance_levels = (
        _levels_from_pivots(
            pivots=pivots,
            pivot_type=PivotType.HIGH,
            level_type=(
                LevelType.RESISTANCE
            ),
            timeframe=timeframe,
            tolerance_percent=(
                tolerance_percent
            ),
        )
    )

    latest_high_label = (
        _latest_label(
            pivots,
            PivotType.HIGH,
        )
    )

    latest_low_label = (
        _latest_label(
            pivots,
            PivotType.LOW,
        )
    )

    trend = (
        _classify_trend(
            latest_high_label,
            latest_low_label,
        )
    )

    return MarketStructure(
        timeframe=timeframe,

        pivots=tuple(
            pivots
        ),

        support_levels=tuple(
            support_levels
        ),

        resistance_levels=tuple(
            resistance_levels
        ),

        latest_high_label=(
            latest_high_label
        ),

        latest_low_label=(
            latest_low_label
        ),

        trend=trend,
    )


def analyse_daily_structure(
    daily: Sequence[CandleLike],
) -> MarketStructure:

    return _analyse_structure(
        bars=daily,
        timeframe=Timeframe.DAILY,
        left_bars=2,
        right_bars=2,
        tolerance_percent=0.01,
    )


def analyse_weekly_structure(
    weekly: Sequence[CandleLike],
) -> MarketStructure:

    return _analyse_structure(
        bars=weekly,
        timeframe=Timeframe.WEEKLY,
        left_bars=2,
        right_bars=2,
        tolerance_percent=0.02,
    )


def next_major_weekly_resistance(
    proposed_entry: float,
    weekly_structure: MarketStructure,
) -> StructuralLevel | None:
    """
    Return the nearest meaningful weekly
    resistance zone above the proposed
    entry.

    The lower edge of the zone must be
    above entry because that is the first
    resistance price the trade encounters.
    """

    if proposed_entry <= 0:
        raise ValueError(
            "proposed_entry must be "
            "greater than zero."
        )

    if (
        weekly_structure.timeframe
        != Timeframe.WEEKLY
    ):
        raise ValueError(
            "next_major_weekly_resistance "
            "requires WEEKLY structure."
        )

    candidates = [
        level
        for level
        in weekly_structure.resistance_levels
        if (
            level.lower
            > proposed_entry
        )
    ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda level: (
            level.lower
        ),
    )