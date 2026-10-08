import json
import sqlite3
from datetime import datetime
from pathlib import Path

from state.models import (
    Position,
    PositionState,
    SetupState,
    SetupType,
    TradeEvent,
)


class Repository:

    def __init__(
        self,
        database_path: str,
    ):
        self.database_path = (
            database_path
        )

    def initialize(
        self,
    ) -> None:

        schema_path = (
            Path(__file__)
            .resolve()
            .parent
            / "schema.sql"
        )

        schema = schema_path.read_text(
            encoding="utf-8"
        )

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.executescript(
                schema
            )

    def _position_values(
        self,
        position: Position,
    ) -> tuple:

        return (
            position.ticker,
            position.state.value,
            position.quantity,
            position.actual_entry,

            (
                position.setup_type.value
                if position.setup_type
                else None
            ),

            position.initial_stop,
            position.current_stop,
            position.recommended_stop,
            position.highest_price,

            (
                position.entry_date
                .isoformat()
                if position.entry_date
                else None
            ),

            (
                position.last_sync_time
                .isoformat()
                if position.last_sync_time
                else None
            ),
        )

    def _upsert_position(
        self,
        connection,
        position: Position,
    ) -> None:

        connection.execute(
            """
            INSERT INTO positions (
                ticker,
                state,
                quantity,
                actual_entry,
                setup_type,
                initial_stop,
                current_stop,
                recommended_stop,
                highest_price,
                entry_date,
                last_sync_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(ticker)
            DO UPDATE SET
                state = excluded.state,
                quantity = excluded.quantity,
                actual_entry = excluded.actual_entry,
                setup_type = excluded.setup_type,
                initial_stop = excluded.initial_stop,
                current_stop = excluded.current_stop,
                recommended_stop =
                    excluded.recommended_stop,
                highest_price =
                    excluded.highest_price,
                entry_date =
                    excluded.entry_date,
                last_sync_time =
                    excluded.last_sync_time
            """,
            self._position_values(
                position
            ),
        )

    def save_position(
        self,
        position: Position,
    ) -> None:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            self._upsert_position(
                connection,
                position,
            )

    def load_position(
        self,
        ticker: str,
    ) -> Position | None:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.row_factory = (
                sqlite3.Row
            )

            row = connection.execute(
                """
                SELECT *
                FROM positions
                WHERE ticker = ?
                """,
                (
                    ticker.upper(),
                ),
            ).fetchone()

        if row is None:
            return None

        return Position(
            ticker=row["ticker"],

            state=PositionState(
                row["state"]
            ),

            quantity=row["quantity"],

            actual_entry=row[
                "actual_entry"
            ],

            setup_type=(
                SetupType(
                    row["setup_type"]
                )
                if row["setup_type"]
                else None
            ),

            initial_stop=row[
                "initial_stop"
            ],

            current_stop=row[
                "current_stop"
            ],

            recommended_stop=row[
                "recommended_stop"
            ],

            highest_price=row[
                "highest_price"
            ],

            entry_date=(
                datetime.fromisoformat(
                    row["entry_date"]
                )
                if row["entry_date"]
                else None
            ),

            last_sync_time=(
                datetime.fromisoformat(
                    row["last_sync_time"]
                )
                if row["last_sync_time"]
                else None
            ),
        )

    def get_open_positions(
        self,
    ) -> list[Position]:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.row_factory = (
                sqlite3.Row
            )

            rows = connection.execute(
                """
                SELECT ticker
                FROM positions
                WHERE quantity > 0
                  AND state != ?
                ORDER BY ticker
                """,
                (
                    PositionState.CLOSED.value,
                ),
            ).fetchall()

        return [
            self.load_position(
                row["ticker"]
            )
            for row in rows
            if self.load_position(
                row["ticker"]
            ) is not None
        ]

    def get_rollover_holdings(
        self,
    ) -> list[Position]:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.row_factory = (
                sqlite3.Row
            )

            rows = connection.execute(
                """
                SELECT ticker
                FROM positions
                WHERE state = ?
                  AND quantity > 0
                ORDER BY ticker
                """,
                (
                    PositionState
                    .ROLLOVER_HOLDING
                    .value,
                ),
            ).fetchall()

        positions = []

        for row in rows:

            position = (
                self.load_position(
                    row["ticker"]
                )
            )

            if position is not None:
                positions.append(
                    position
                )

        return positions

    def get_sync_error_positions(
        self,
    ) -> list[Position]:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.row_factory = (
                sqlite3.Row
            )

            rows = connection.execute(
                """
                SELECT ticker
                FROM positions
                WHERE state = ?
                """,
                (
                    PositionState
                    .SYNC_ERROR
                    .value,
                ),
            ).fetchall()

        positions = []

        for row in rows:

            position = (
                self.load_position(
                    row["ticker"]
                )
            )

            if position is not None:
                positions.append(
                    position
                )

        return positions

    def update_state(
        self,
        ticker: str,
        state: PositionState,
    ) -> None:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.execute(
                """
                UPDATE positions
                SET state = ?
                WHERE ticker = ?
                """,
                (
                    state.value,
                    ticker.upper(),
                ),
            )

    def update_quantity(
        self,
        ticker: str,
        quantity: float,
    ) -> None:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.execute(
                """
                UPDATE positions
                SET quantity = ?
                WHERE ticker = ?
                """,
                (
                    quantity,
                    ticker.upper(),
                ),
            )

    def update_actual_entry(
        self,
        ticker: str,
        actual_entry: float | None,
    ) -> None:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.execute(
                """
                UPDATE positions
                SET actual_entry = ?
                WHERE ticker = ?
                """,
                (
                    actual_entry,
                    ticker.upper(),
                ),
            )

    def update_current_stop(
        self,
        ticker: str,
        current_stop: float | None,
    ) -> None:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.execute(
                """
                UPDATE positions
                SET current_stop = ?
                WHERE ticker = ?
                """,
                (
                    current_stop,
                    ticker.upper(),
                ),
            )

    def save_recommended_stop(
        self,
        ticker: str,
        recommended_stop: float | None,
    ) -> None:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.execute(
                """
                UPDATE positions
                SET recommended_stop = ?
                WHERE ticker = ?
                """,
                (
                    recommended_stop,
                    ticker.upper(),
                ),
            )

    def save_setup_state(
        self,
        setup: SetupState,
    ) -> None:

        sql = """
            INSERT INTO setup_states (
                ticker,
                setup_type,
                state,
                support_level,
                resistance_level,
                breakout_level,
                breakout_date,
                retest_low,
                last_evaluation_date,
                expiry_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(ticker)
            DO UPDATE SET
                setup_type =
                    excluded.setup_type,
                state =
                    excluded.state,
                support_level =
                    excluded.support_level,
                resistance_level =
                    excluded.resistance_level,
                breakout_level =
                    excluded.breakout_level,
                breakout_date =
                    excluded.breakout_date,
                retest_low =
                    excluded.retest_low,
                last_evaluation_date =
                    excluded.last_evaluation_date,
                expiry_date =
                    excluded.expiry_date
        """

        values = (
            setup.ticker,
            setup.setup_type.value,
            setup.state.value,
            setup.support_level,
            setup.resistance_level,
            setup.breakout_level,

            (
                setup.breakout_date
                .isoformat()
                if setup.breakout_date
                else None
            ),

            setup.retest_low,

            (
                setup.last_evaluation_date
                .isoformat()
                if setup.last_evaluation_date
                else None
            ),

            (
                setup.expiry_date
                .isoformat()
                if setup.expiry_date
                else None
            ),
        )

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.execute(
                sql,
                values,
            )

    def load_setup_state(
        self,
        ticker: str,
    ) -> SetupState | None:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.row_factory = (
                sqlite3.Row
            )

            row = connection.execute(
                """
                SELECT *
                FROM setup_states
                WHERE ticker = ?
                """,
                (
                    ticker.upper(),
                ),
            ).fetchone()

        if row is None:
            return None

        return SetupState(
            ticker=row["ticker"],

            setup_type=SetupType(
                row["setup_type"]
            ),

            state=PositionState(
                row["state"]
            ),

            support_level=row[
                "support_level"
            ],

            resistance_level=row[
                "resistance_level"
            ],

            breakout_level=row[
                "breakout_level"
            ],

            breakout_date=(
                datetime.fromisoformat(
                    row["breakout_date"]
                )
                if row["breakout_date"]
                else None
            ),

            retest_low=row[
                "retest_low"
            ],

            last_evaluation_date=(
                datetime.fromisoformat(
                    row[
                        "last_evaluation_date"
                    ]
                )
                if row[
                    "last_evaluation_date"
                ]
                else None
            ),

            expiry_date=(
                datetime.fromisoformat(
                    row["expiry_date"]
                )
                if row["expiry_date"]
                else None
            ),
        )

    def _insert_event(
        self,
        connection,
        event: TradeEvent,
    ) -> None:

        connection.execute(
            """
            INSERT INTO trade_events (
                ticker,
                event_type,
                timestamp,
                details_json
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                event.ticker,
                event.event_type,
                event.timestamp.isoformat(),

                json.dumps(
                    event.details
                ),
            ),
        )

    def save_event(
        self,
        event: TradeEvent,
    ) -> None:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            self._insert_event(
                connection,
                event,
            )

    def save_position_and_event(
        self,
        position: Position,
        event: TradeEvent,
    ) -> None:
        """
        Atomic reconciliation operation.

        Position update and audit event
        succeed or fail together.
        """

        with sqlite3.connect(
            self.database_path
        ) as connection:

            self._upsert_position(
                connection,
                position,
            )

            self._insert_event(
                connection,
                event,
            )

    def save_watchlist_snapshot(
        self,
        tickers: list[str],
    ) -> None:

        normalized = sorted(
            {
                ticker.strip().upper()
                for ticker in tickers
            }
        )

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.execute(
                """
                INSERT INTO
                    watchlist_snapshots (
                        created_at,
                        tickers_json
                    )
                VALUES (?, ?)
                """,
                (
                    datetime.now()
                    .isoformat(),

                    json.dumps(
                        normalized
                    ),
                ),
            )

    def load_last_watchlist_snapshot(
        self,
    ) -> list[str] | None:

        with sqlite3.connect(
            self.database_path
        ) as connection:

            connection.row_factory = (
                sqlite3.Row
            )

            row = connection.execute(
                """
                SELECT tickers_json
                FROM watchlist_snapshots
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()

        if row is None:
            return None

        tickers = json.loads(
            row["tickers_json"]
        )

        return [
            str(ticker).upper()
            for ticker in tickers
        ]