CREATE TABLE IF NOT EXISTS positions (
    ticker TEXT PRIMARY KEY,
    state TEXT NOT NULL,

    quantity REAL NOT NULL DEFAULT 0,
    actual_entry REAL,

    setup_type TEXT,

    initial_stop REAL,
    current_stop REAL,
    recommended_stop REAL,

    highest_price REAL,

    entry_date TEXT,
    last_sync_time TEXT
);


CREATE TABLE IF NOT EXISTS setup_states (
    ticker TEXT PRIMARY KEY,
    setup_type TEXT NOT NULL,
    state TEXT NOT NULL,

    support_level REAL,
    resistance_level REAL,

    breakout_level REAL,
    breakout_date TEXT,

    retest_low REAL,

    last_evaluation_date TEXT,
    expiry_date TEXT
);


CREATE TABLE IF NOT EXISTS trade_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    ticker TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,

    details_json TEXT NOT NULL
);


CREATE TABLE IF NOT EXISTS watchlist_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    created_at TEXT NOT NULL,
    tickers_json TEXT NOT NULL
);