from dataclasses import dataclass
from enum import Enum

from data.structure import (
    MarketStructure,
    StructuralLevel,
    Timeframe,
    TrendStructure,
)


class WeeklyEligibility(str, Enum):
    PASS = "PASS"
    WAIT = "WAIT"
    FAIL = "FAIL"


class OverheadRoomStatus(str, Enum):
    ACCEPTABLE = "ACCEPTABLE"
    POOR = "POOR"


@dataclass(frozen=True)
class OverheadRoomAssessment:
    status: OverheadRoomStatus

    resistance: (
        StructuralLevel | None
    )

    room_dollars: float | None

    room_atr: float | None

    initial_risk: float

    room_vs_risk: float | None

    reasons: tuple[str, ...]


def passes_weekly_filter(
    weekly_structure: MarketStructure,
) -> WeeklyEligibility:
    """
    Higher-timeframe gate for new
    long entries.

    PASS does not mean BUY.

    It only means the weekly context
    allows daily setup analysis to
    continue.
    """

    if (
        weekly_structure.timeframe
        != Timeframe.WEEKLY
    ):
        raise ValueError(
            "Weekly filter requires "
            "WEEKLY market structure."
        )

    if (
        weekly_structure.trend
        == TrendStructure.DOWNTREND
    ):
        return (
            WeeklyEligibility.FAIL
        )

    if (
        weekly_structure.trend
        == TrendStructure.UPTREND
    ):
        return (
            WeeklyEligibility.PASS
        )

    return WeeklyEligibility.WAIT


def overhead_room_is_acceptable(
    proposed_entry: float,
    proposed_stop: float,
    next_weekly_resistance:
        StructuralLevel | None,
    atr: float,
) -> OverheadRoomAssessment:
    """
    Assess space between the proposed
    entry and next major weekly resistance.

    This deliberately avoids a single
    rigid R-multiple rule.

    Multiple structural measurements are
    considered together.
    """

    if proposed_entry <= 0:
        raise ValueError(
            "proposed_entry must be "
            "greater than zero."
        )

    if proposed_stop <= 0:
        raise ValueError(
            "proposed_stop must be "
            "greater than zero."
        )

    if proposed_stop >= proposed_entry:
        raise ValueError(
            "For a long entry, proposed_stop "
            "must be below proposed_entry."
        )

    if atr <= 0:
        raise ValueError(
            "ATR must be greater than zero."
        )

    initial_risk = (
        proposed_entry
        - proposed_stop
    )

    if next_weekly_resistance is None:

        return OverheadRoomAssessment(
            status=(
                OverheadRoomStatus.ACCEPTABLE
            ),
            resistance=None,
            room_dollars=None,
            room_atr=None,
            initial_risk=initial_risk,
            room_vs_risk=None,
            reasons=(
                "No major weekly resistance "
                "identified above entry.",
            ),
        )

    resistance_price = (
        next_weekly_resistance.lower
    )

    room_dollars = (
        resistance_price
        - proposed_entry
    )

    if room_dollars <= 0:

        return OverheadRoomAssessment(
            status=(
                OverheadRoomStatus.POOR
            ),
            resistance=(
                next_weekly_resistance
            ),
            room_dollars=(
                room_dollars
            ),
            room_atr=0.0,
            initial_risk=(
                initial_risk
            ),
            room_vs_risk=0.0,
            reasons=(
                "Major weekly resistance "
                "is at or below entry.",
            ),
        )

    room_atr = (
        room_dollars
        / atr
    )

    room_vs_risk = (
        room_dollars
        / initial_risk
    )

    warnings: list[str] = []

    if room_atr < 1.0:
        warnings.append(
            "Major weekly resistance is "
            "less than 1 ATR above entry."
        )

    if room_vs_risk < 1.5:
        warnings.append(
            "Nearby upside room is small "
            "relative to initial risk."
        )

    if len(warnings) >= 2:

        return OverheadRoomAssessment(
            status=(
                OverheadRoomStatus.POOR
            ),
            resistance=(
                next_weekly_resistance
            ),
            room_dollars=(
                room_dollars
            ),
            room_atr=room_atr,
            initial_risk=(
                initial_risk
            ),
            room_vs_risk=(
                room_vs_risk
            ),
            reasons=tuple(
                warnings
            ),
        )

    reasons: list[str] = [
        "Major weekly resistance is not "
        "structurally too close."
    ]

    if warnings:
        reasons.extend(
            warnings
        )

    return OverheadRoomAssessment(
        status=(
            OverheadRoomStatus.ACCEPTABLE
        ),
        resistance=(
            next_weekly_resistance
        ),
        room_dollars=(
            room_dollars
        ),
        room_atr=room_atr,
        initial_risk=initial_risk,
        room_vs_risk=(
            room_vs_risk
        ),
        reasons=tuple(
            reasons
        ),
    )