# Chat 2 Trading Bot V1

Python swing/position trading decision-support bot.

V1 is read-only with respect to IBKR order execution.

The bot may:

- read IBKR positions
- read open orders
- read market data
- reconcile broker positions with SQLite
- generate trading decision-support state

The bot must not:

- place broker orders
- modify broker orders
- cancel broker orders

Manual execution remains with the user.

---

## Python Environment

Create the virtual environment:

```powershell
python -m venv .venv

## Project Status

**Version: V0.1 — Engineering Foundation**

This project is currently frozen after completion of the core
engineering and market-analysis foundation.

The objective of V0.1 was not automated trading. It was to build a
safe, testable, read-only trading decision-support architecture.

### Key Engineering Features

- Native IBKR API integration using asynchronous callbacks
- Read-only broker architecture
- SQLite-based persistent state
- Broker/database reconciliation
- Recovery after broker connectivity failures
- Dynamic watchlist and rollover-position handling
- Completed-candle and stale-market-data validation
- Pure deterministic indicator modules
- Daily and weekly market-structure analysis
- Look-ahead-safe confirmed pivot detection
- Relative-strength comparison
- Higher-timeframe eligibility filtering
- Automated unit and recovery testing

### Safety Principles

- IBKR remains the source of truth for actual ownership
- Broker failure is treated as UNKNOWN, never as zero position
- Existing state is preserved during connectivity failures
- No automated order placement in V0.1
- Historical calculations avoid future-bar leakage

### Current Status

V0.1 is intentionally frozen.

Future strategy and deployment features are tracked in `V2_BACKLOG.md`.