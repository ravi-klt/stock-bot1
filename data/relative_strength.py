from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence


class CloseLike(Protocol):
    close: float


class RelativeStrengthRating(str, Enum):
    STRONG = "STRONG"
    NEUTRAL = "NEUTRAL"
    WEAK = "WEAK"


@dataclass(frozen=True)
class RelativeStrengthResult:
    rating: RelativeStrengthRating

    stock_short_return: float
    benchmark_short_return: float
    sector_short_return: float

    stock_medium_return: float
    benchmark_medium_return: float
    sector_medium_return: float

    short_vs_benchmark: float
    short_vs_sector: float

    medium_vs_benchmark: float
    medium_vs_sector: float


def _validate_window(
    window: int,
) -> None:
    if window <= 0:
        raise ValueError(
            "Relative-strength window must "
            "be greater than zero."
        )


def _performance_return(
    bars: Sequence[CloseLike],
    window: int,
) -> float:
    """
    Calculate price performance over
    the requested completed-bar window.

    Example:
    start = 100
    end = 110

    return = 110 / 100 - 1
           = 0.10
           = 10%
    """

    _validate_window(window)

    required_bars = (
        window + 1
    )

    if len(bars) < required_bars:
        raise ValueError(
            "Performance calculation requires "
            f"at least {required_bars} bars; "
            f"received {len(bars)}."
        )

    starting_close = (
        bars[-required_bars].close
    )

    ending_close = (
        bars[-1].close
    )

    if starting_close <= 0:
        raise ValueError(
            "Starting close must be "
            "greater than zero."
        )

    return (
        ending_close
        / starting_close
        - 1.0
    )


def calculate_relative_strength(
    stock: Sequence[CloseLike],
    benchmark: Sequence[CloseLike],
    sector: Sequence[CloseLike],
    short_window: int = 20,
    medium_window: int = 60,
) -> RelativeStrengthResult:
    """
    Compare stock performance with a
    broad-market benchmark and relevant
    sector over short and medium windows.

    Classification:

    STRONG:
        stock outperforms both benchmark
        and sector over both windows.

    WEAK:
        stock underperforms both benchmark
        and sector over both windows.

    Everything else:
        NEUTRAL.

    Relative strength is context only.
    It is not an entry trigger.
    """

    if medium_window <= short_window:
        raise ValueError(
            "medium_window must be greater "
            "than short_window."
        )

    stock_short = (
        _performance_return(
            stock,
            short_window,
        )
    )

    benchmark_short = (
        _performance_return(
            benchmark,
            short_window,
        )
    )

    sector_short = (
        _performance_return(
            sector,
            short_window,
        )
    )

    stock_medium = (
        _performance_return(
            stock,
            medium_window,
        )
    )

    benchmark_medium = (
        _performance_return(
            benchmark,
            medium_window,
        )
    )

    sector_medium = (
        _performance_return(
            sector,
            medium_window,
        )
    )

    short_vs_benchmark = (
        stock_short
        - benchmark_short
    )

    short_vs_sector = (
        stock_short
        - sector_short
    )

    medium_vs_benchmark = (
        stock_medium
        - benchmark_medium
    )

    medium_vs_sector = (
        stock_medium
        - sector_medium
    )

    strong = (
        short_vs_benchmark > 0
        and short_vs_sector > 0
        and medium_vs_benchmark > 0
        and medium_vs_sector > 0
    )

    weak = (
        short_vs_benchmark < 0
        and short_vs_sector < 0
        and medium_vs_benchmark < 0
        and medium_vs_sector < 0
    )

    if strong:
        rating = (
            RelativeStrengthRating.STRONG
        )

    elif weak:
        rating = (
            RelativeStrengthRating.WEAK
        )

    else:
        rating = (
            RelativeStrengthRating.NEUTRAL
        )

    return RelativeStrengthResult(
        rating=rating,

        stock_short_return=stock_short,
        benchmark_short_return=(
            benchmark_short
        ),
        sector_short_return=(
            sector_short
        ),

        stock_medium_return=(
            stock_medium
        ),
        benchmark_medium_return=(
            benchmark_medium
        ),
        sector_medium_return=(
            sector_medium
        ),

        short_vs_benchmark=(
            short_vs_benchmark
        ),
        short_vs_sector=(
            short_vs_sector
        ),

        medium_vs_benchmark=(
            medium_vs_benchmark
        ),
        medium_vs_sector=(
            medium_vs_sector
        ),
    )