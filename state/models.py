from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

class PositionState(str, Enum):
    WATCHING = "WATCHING"

    SETUP_A_ACTIVE = "SETUP_A_ACTIVE"
    SETUP_B_ACTIVE = "SETUP_B_ACTIVE"

    WAIT_RETEST = "WAIT_RETEST"
    BUY_READY = "BUY_READY"

    HOLDING = "HOLDING"
    TREND_WINNER = "TREND_WINNER"

    ROLLOVER_HOLDING = "ROLLOVER_HOLDING"
    PENDING_REMOVAL = "PENDING_REMOVAL"

    EXIT_REVIEW = "EXIT_REVIEW"

    CLOSED = "CLOSED"
    SYNC_ERROR = "SYNC_ERROR"

class SetupType(str, Enum):
    SETUP_A = "SETUP_A"
    SETUP_B = "SETUP_B"

@dataclass
class Position:
    ticker: str
    state: PositionState

    quantity: float = 0.0
    actual_entry: float | None = None

    setup_type: SetupType | None = None

    initial_stop: float | None = None
    current_stop: float | None = None
    recommended_stop: float | None = None

    highest_price: float | None = None

    entry_date: datetime | None = None
    last_sync_time: datetime | None = None

@dataclass
class SetupState:
    ticker: str
    setup_type: SetupType
    state: PositionState

    support_level: float | None = None
    resistance_level: float | None = None

    breakout_level: float | None = None
    breakout_date: datetime | None = None

    retest_low: float | None = None

    last_evaluation_date: datetime | None = None
    expiry_date: datetime | None = None

@dataclass
class TradeEvent:
    ticker: str
    event_type: str
    timestamp: datetime

    details: dict[str, Any] = field(default_factory=dict)        