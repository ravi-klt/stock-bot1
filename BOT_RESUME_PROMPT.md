# Trading Bot V1 — Resume & Learning Guide

## 1. Purpose of This File

This file exists so the Trading Bot project can be resumed correctly in a future ChatGPT conversation even if the original conversation is unavailable.

The project is currently intentionally paused.

It was NOT abandoned.

The engineering foundation through Day 10 was completed, committed, and frozen so that career-switch preparation could become the primary priority.

When this project is resumed, continue from **Day 11**.

Do not restart from Day 1.

---

# 2. Current Status

Project:

**Python Swing / Position Trading Decision-Support Bot**

Current completed point:

**Day 10 completed**

Next curriculum day:

**Day 11**

Current project status:

**PAUSED / FROZEN**

Reason:

Career-switch preparation currently has higher priority.

Do not automatically resume this project just because this file is opened.

Resume only when I explicitly say:

- `resume bot`
- `give Day 11 learn`
- `continue trading bot learning`

---

# 3. Core V1 Objective

The bot is a swing/position trading **decision-support system**.

It is NOT an automated trading system.

The bot should:

- read actual IBKR positions
- read open/protective orders when available
- read daily and weekly OHLCV
- analyze technical structure
- identify potential Setup A / Setup B opportunities
- recommend BUY_READY
- recommend structural stop levels
- monitor existing positions
- recommend SL upgrades
- flag EXIT_REVIEW / emergency conditions
- send important Telegram alerts
- persist state across restart

The user manually executes all broker actions.

---

# 4. Non-Negotiable V1 Scope

IBKR integration is **READ-ONLY**.

V1 must NOT automatically:

- place orders
- modify orders
- cancel orders
- buy
- sell
- pyramid
- take automatic partial profits

Do NOT add these unless the user explicitly redesigns V1.

V1 also excludes:

- intraday trading strategies
- options
- crypto trading strategies
- ML price prediction
- AI price forecasting
- Kubernetes
- microservices
- complex AI news-cause classification

Keep the system explainable and deterministic.

---

# 5. Core Architecture

Expected project structure:

```text
chat2_bot/
├── main.py
├── scheduler.py
├── config.py
├── logging_config.py
│
├── broker/
│   ├── __init__.py
│   ├── ibkr_client.py
│   └── reconciliation.py
│
├── data/
│   ├── __init__.py
│   ├── market_data.py
│   ├── indicators.py
│   ├── structure.py
│   ├── relative_strength.py
│   └── corporate_actions.py
│
├── strategy/
│   ├── __init__.py
│   ├── weekly_filter.py
│   ├── setup_a.py
│   ├── setup_b.py
│   ├── entry_engine.py
│   ├── stop_loss.py
│   ├── holding_manager.py
│   ├── trend_winner.py
│   ├── emergency.py
│   └── earnings.py
│
├── state/
│   ├── __init__.py
│   ├── models.py
│   ├── repository.py
│   └── state_machine.py
│
├── notifications/
│   ├── __init__.py
│   └── telegram_notifier.py
│
├── tests/
│   └── __init__.py
│
├── config/
│   └── watchlist.json
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

Some future files may not exist yet.

Do not create future modules before their curriculum day unless required by that day's implementation.

---

# 6. Important System Invariants

These rules must remain true throughout V1.

## Broker truth

IBKR is the source of truth for actual ownership.

If IBKR successfully reports:

```text
quantity = 0
```

an open position may be marked CLOSED.

If IBKR cannot answer:

```text
UNKNOWN / SYNC_ERROR
```

Do NOT assume quantity is zero.

Preserve trusted SQLite state.

---

## Watchlist rule

Deleting a ticker from `watchlist.json` may stop new-entry monitoring.

It must NEVER stop management of an actual IBKR holding.

Removed-but-owned ticker:

```text
ROLLOVER_HOLDING
```

Continue managing it until IBKR confirms quantity = 0.

---

## Stop-loss rule

Existing stop can only move:

```text
UP
```

for a long position.

Never move it lower.

Never widen risk.

---

## Execution rule

`BUY_READY` means:

```text
recommendation / alert
```

It does NOT mean the user owns the stock.

Ownership exists only after IBKR confirms an actual position.

---

## Historical-testing rule

No future-bar / look-ahead leakage.

A pivot becomes known only after the required confirmation bars exist.

Historical replay should proceed one bar at a time.

---

# 7. Completed Days

## Day 1 — Project Foundation

Completed:

- Git repository
- Python virtual environment
- project structure
- `.gitignore`
- `.env`
- `.env.example`
- `requirements.txt`
- `config/watchlist.json`

---

## Day 2 — Domain Models

Completed:

- `PositionState`
- `SetupType`
- `Position`
- `SetupState`
- `TradeEvent`
- state-machine foundation

Key position states include concepts such as:

```text
WATCHING
SETUP_A_ACTIVE
SETUP_B_ACTIVE
WAIT_RETEST
BUY_READY
HOLDING
TREND_WINNER
ROLLOVER_HOLDING
PENDING_REMOVAL
EXIT_REVIEW
CLOSED
SYNC_ERROR
```

---

## Day 3 — SQLite Persistence

Completed:

- SQLite schema
- `positions`
- `setup_states`
- `trade_events`
- `watchlist_snapshots`
- repository persistence layer
- position save/load/update
- setup-state save/load
- event persistence

---

## Day 4 — Configuration + Logging

Completed:

- `AppConfig`
- `.env` loading
- dynamic watchlist loading
- structured JSON logging
- rotating log files
- startup logging
- SQLite initialization

---

## Day 5 — IBKR Integration

Completed:

- native IBKR Python API
- `EClient`
- `EWrapper`
- asynchronous callback handling
- background API thread
- synchronization using `threading.Event`
- read-only connection
- contract resolution
- position-reading foundation
- historical-data foundation

V1 intentionally exposes no broker order execution.

---

## Day 6 — Reconciliation + Market Data Safety

Completed:

- actual broker position reconciliation
- manual buy detection
- manual position increase
- manual partial sell detection
- full close detection
- rollover holdings
- read open orders
- daily OHLCV
- weekly OHLCV
- completed-candle validation
- stale-data detection
- impossible OHLC validation
- broker-failure preservation
- `SYNC_ERROR`

Critical invariant:

```text
IBKR says zero successfully
→ CLOSED

IBKR cannot answer
→ SYNC_ERROR
→ preserve existing state
```

---

## Day 7 — Startup Recovery

Completed:

Startup flow:

```text
Config
  ↓
SQLite
  ↓
IBKR
  ↓
Watchlist
  ↓
Reconciliation
  ↓
System Health
```

Implemented:

- `SystemHealth`
- `READY`
- `DEGRADED`
- restart recovery tests
- broker-unavailable tests
- reconnect/reconciliation tests
- clean shutdown

Real TWS connection was successfully verified.

---

## Day 8 — Indicator Toolkit

Completed:

- ATR14
- VolMA20
- volume ratio
- candle range
- range in ATR
- close location
- EMA20
- MA50

Important principle:

Indicators are measurements.

They do NOT independently generate BUY signals.

---

## Day 9 — Market Structure

Completed:

- confirmed swing highs
- confirmed swing lows
- HH
- HL
- LH
- LL
- support/resistance zones
- daily structure
- weekly structure
- `confirmed_at_index`
- anti-look-ahead pivot handling
- structural price clustering

Daily and weekly structure remain separate.

---

## Day 10 — Weekly Eligibility + Relative Strength + Overhead Room

Completed:

Weekly classification:

```text
UPTREND
→ PASS

DOWNTREND
→ FAIL

MIXED
→ WAIT

UNKNOWN
→ WAIT
```

Relative strength compares:

```text
stock
vs
broad-market benchmark
vs
sector benchmark
```

Output:

```text
STRONG
NEUTRAL
WEAK
```

Relative strength is context/quality.

It is NOT the primary entry trigger.

Also completed:

- next major weekly resistance
- overhead-room assessment
- room in dollars
- room in ATR
- room vs initial risk
- no rigid `2R` rule

Current completed point:

```text
DAY 10
```

Next:

```text
DAY 11
```

---

# 8. Entry Strategy Philosophy

There are exactly two entry families in V1.

```text
Setup A
Pullback / base near support

Setup B
Breakout + retest
```

Do not invent additional entry systems during V1.

---

# 9. Setup A — Core Rules

Setup A sequence:

```text
Prior advance
    ↓
Controlled pullback/base
    ↓
Selling pressure fades
    ↓
Meaningful support holds/reclaims
    ↓
Buyers return
    ↓
No-chase check
    ↓
Weekly overhead room
    ↓
BUY_READY candidate
```

Setup A is NOT:

```text
one hammer candle
one green candle
RSI oversold
price touches EMA20
```

It is a multi-candle structural sequence.

Support should be treated as a zone.

Small undercuts/reclaims may be acceptable using ATR/noise tolerance.

---

# 10. Setup A Reference Progress

Conceptually:

```text
A1_SUPPORT_SETUP_IDENTIFIED
A2_PULLBACK_IN_PROGRESS
A3_SELLING_PRESSURE_FADING
A4_SUPPORT_CONFIRMED
A5_BUYERS_RETURNED
```

Example interpretation:

```text
A1:
support badly fails
+ expanding volume
→ FAIL

A2:
support area tested
but sellers still active
→ WAIT

A3:
selling volume/range contracts
→ improving

A4:
support holds/reclaims
→ healthy

A5:
buyers return
→ BUY_READY candidate
```

---

# 11. Setup B — Core Rules

Setup B:

```text
Meaningful resistance
        ↓
Breakout
        ↓
Classify breakout quality
        ↓
WAIT_RETEST
        ↓
Healthy retest
        ↓
Buyers return
        ↓
BUY_READY candidate
```

Never chase the breakout directly in V1.

Even strong breakouts must wait for retest.

---

# 12. Setup B B1–B5 Reference

Reference scenario:

```text
Resistance = 100
ATR = 4
VolMA20 = 10M
```

## B1

```text
High > 100
Close = 99
Volume = 15M
```

Interpretation:

```text
Rejected breakout
```

---

## B2

```text
Close = 100.20
Volume = 7M
Penetration = +0.05 ATR
```

Interpretation:

```text
Provisional / weak
```

---

## B3

```text
Close = 101
Volume = 10M
Penetration = +0.25 ATR
```

Interpretation:

```text
Acceptable
→ WAIT_RETEST
```

---

## B4

```text
Close = 102
Volume = 13M
Penetration = +0.50 ATR
```

Interpretation:

```text
Strong
→ WAIT_RETEST
```

---

## B5

```text
Close = 103
Volume = 18M
Penetration = +0.75 ATR
```

Interpretation:

```text
Very strong
→ extension check
→ WAIT_RETEST
```

Do not create brittle thresholds such as:

```text
1.29 volume ratio = FAIL
1.30 = PASS
```

Use price + volume + ATR + close quality together.

---

# 13. Healthy Setup B Retest

Healthy retest broadly means:

- old resistance becomes support
- exact touch is not required
- small ATR-tolerant undercut/reclaim may be acceptable
- pullback volume contracts
- candle ranges contract
- selling momentum slows
- relative strength remains acceptable
- buyers eventually resume

Failed retest should reset/fail cleanly.

---

# 14. Initial Stop Philosophy

Initial stop belongs below:

```text
real structural invalidation
+
volatility / noise allowance
```

Do NOT use:

```text
support - $0.01
```

Do NOT use a fixed percentage as the primary stop logic.

Stop should reflect:

```text
"If price trades here, the setup thesis is no longer valid."
```

---

# 15. Stop Upgrade Philosophy

Normal stop management is NOT:

```text
+1R → move stop
+2R → move stop
+10% → move stop
+20% → move stop
```

SL upgrade requires a new meaningful structural floor:

```text
Advance
    ↓
Controlled pullback/base
    ↓
New support forms
    ↓
Support holds
    ↓
Buyers resume
    ↓
Confirmed higher low
    ↓
Potential SL_UPGRADE
```

Hard invariant:

```text
new_stop > current_stop
```

Otherwise reject it.

---

# 16. Holding Management

Once IBKR detects:

```text
quantity > 0
```

entry logic should switch off.

State becomes:

```text
HOLDING
```

Most days should result in:

```text
HOLD_NO_CHANGE
```

Breakout while already holding:

```text
TREND_PROGRESS
```

It does NOT automatically:

- move stop
- take profit
- sell

Meaningful structural deterioration may produce:

```text
EXIT_REVIEW
```

---

# 17. Trend Winner Philosophy

Trend Winner is not defined by:

```text
+2R
```

alone.

Qualification should consider:

- mature weekly structure
- repeated meaningful weekly HH/HL
- strong/resilient relative strength
- healthy bases/pullbacks
- absence of major distribution
- meaningful profit cushion

Weekly structure dominates ordinary management.

Protective stop and emergency checks remain active.

---

# 18. Emergency Philosophy

Emergency/safety logic runs before ordinary HOLDING or TREND_WINNER logic.

Examples:

- gap through stop
- real abnormal daily decline
- extreme ATR move
- high-volume collapse
- major structural support failure
- major unexpected event

A decline around:

```text
15–20%
```

is a REVIEW trigger.

It is NOT automatically:

```text
SELL because percentage threshold hit
```

Use:

- percentage
- ATR
- volume
- support context
- price recovery/failure

Unknown cause is allowed.

Do not fabricate reasons.

---

# 19. Corporate Actions

Before interpreting a huge apparent price decline:

check whether it was caused by:

- stock split
- reverse split
- other mechanical corporate action

Normalize where applicable:

- quantity
- entry
- stop
- structural levels

If validation is uncertain:

```text
DATA / CORPORATE_ACTION_REVIEW
```

rather than generating a confident false exit.

---

# 20. Earnings

For NEW entries:

earnings too close may:

```text
block
or
flag
```

the entry.

For existing holdings:

earnings may generate a warning.

Do NOT automatically sell an existing position because earnings are approaching.

---

# 21. Alert Philosophy

User-facing alerts should be minimal and actionable.

Primary alerts:

```text
BUY_READY
SL_UPGRADE
EXIT_REVIEW
GAP_THROUGH_STOP
ABNORMAL_EVENT / REVIEW
EARNINGS_RISK
STOP_MISMATCH
IBKR_FAILURE
DATA_FAILURE
BOT_FAILURE
```

Internal Setup A / Setup B progress should mainly remain in logs.

Avoid alert spam.

---

# 22. Remaining Curriculum

Continue from here when the project is resumed.

---

## Day 11 — Setup A Building Blocks + Sequence State

Planned time:

**1.5 hours**

Files:

```text
strategy/setup_a.py
state/models.py
tests/test_setup_a.py
```

Learn:

- Setup A is a multi-candle sequence
- prior advance matters
- support must be meaningful
- ATR-tolerant undercut/reclaim
- single candle is insufficient

Build:

- prior-advance qualification
- meaningful-support qualification
- pullback depth
- volume trend
- candle-range trend
- downside deceleration
- persisted Setup A progress

Tests:

- A1
- A2
- A3
- A4
- decisive support failure with expanding volume

Milestone:

```text
Setup A can distinguish a healthy developing pullback
from unresolved or failed support.
```

---

## Day 12 — Complete Setup A + BUY_READY Candidate

Planned time:

**4 hours**

Files:

```text
strategy/setup_a.py
strategy/weekly_filter.py
data/structure.py
tests/test_setup_a.py
```

Build full sequence:

```text
A1_SUPPORT_SETUP_IDENTIFIED
        ↓
A2_PULLBACK_IN_PROGRESS
        ↓
A3_SELLING_PRESSURE_FADING
        ↓
A4_SUPPORT_CONFIRMED
        ↓
A5_BUYERS_RETURNED
```

Buyer-return evidence may include:

- reclaim of pullback pivot
- prior-day-high reclaim
- strong bullish continuation close
- strong reversal close

Also implement:

- proposed entry zone
- max acceptable entry
- no-chase check
- next major weekly resistance
- overhead-room assessment
- structured decision with reasons

Possible results:

```text
NO_SETUP
WAIT
FAIL
BUY_READY candidate
```

Tests:

- all A1–A5 scenarios
- support holds but no buyers return → WAIT
- good setup but price too extended → no chase
- good setup but resistance too close → reject/wait

---

## Day 13 — Setup A Historical Replay

Planned time:

**1.5 hours**

Files:

```text
tests/replay_setup_a.py
or reusable replay utility

tests/test_setup_a.py
```

Build:

- one-bar-at-a-time replay
- several historical pullback/base examples
- state progression inspection
- reason/log inspection

Rules:

Fix:

```text
bugs
calculation errors
state errors
```

Do NOT redesign strategy because one example is imperfect.

Tests:

- no future candle influences earlier output
- restart during Setup A preserves progress

Milestone:

```text
Setup A works end-to-end in deterministic replay.
```

---

## Day 14 — Setup B Breakout Quality B1–B5

Planned time:

**1 hour**

Files:

```text
strategy/setup_b.py
tests/test_setup_b.py
```

Build:

- B1 rejected
- B2 provisional
- B3 acceptable
- B4 strong
- B5 very strong
- breakout level
- breakout date
- breakout quality
- extension warning/check

Use exact reference:

```text
Resistance = 100
ATR = 4
VolMA20 = 10M
```

Do not create brittle volume cliffs.

Milestone:

```text
Bot can classify breakout quality.
```

---

## Day 15 — Setup B Retest + WAIT_RETEST Persistence

Planned time:

**1 hour**

Files:

```text
strategy/setup_b.py
state/repository.py
tests/test_setup_b_retest.py
```

Build:

- retest zone
- support-hold test
- ATR-tolerant undercut/reclaim
- volume contraction
- range contraction
- seller deceleration
- buyer resumption
- failed-retest reset
- persistent WAIT_RETEST

Tests:

- normal retest
- shallow retest
- undercut/reclaim
- failed retest
- restart during WAIT_RETEST

Milestone:

```text
Breakout can progress safely into persistent retest state.
```

---

## Day 16 — Unified Entry Engine + BUY_READY Contract

Planned time:

**1 hour**

Files:

```text
strategy/entry_engine.py
state/state_machine.py
tests/test_entry_engine.py
```

Build:

Route:

```text
support/base context
→ Setup A

breakout/retest context
→ Setup B
```

Apply:

- weekly eligibility
- earnings gate placeholder
- overhead-room check
- no-chase
- ownership check

BUY_READY payload:

- setup family
- preferred entry zone
- maximum acceptable entry
- reasons

Rules:

If IBKR already shows ownership:

```text
no fresh BUY_READY
```

BUY_READY remains recommendation state until:

- actual IBKR ownership appears
- setup expires
- setup resets/fails

Milestone:

```text
Both entry families feed one controlled entry pipeline.
```

---

## Day 17 — Structural Initial Stop + Stop Upgrade

Planned time:

**1.5 hours**

Files:

```text
strategy/stop_loss.py
tests/test_stop_loss.py
```

Build:

- Setup A initial stop
- Setup B initial stop
- volatility/noise buffer
- `calculate_upgraded_stop()`

Hard invariant:

```text
proposed_stop <= current_stop
→ reject
```

Tests:

- wide but structurally valid stop
- attempted widening rejected
- no meaningful support → no upgrade

Milestone:

```text
BUY_READY includes structural SL
and existing SL can never move lower.
```

---

## Day 18 — Complete Setup B + Holding Manager

Planned time:

**4 hours**

Files:

```text
strategy/setup_b.py
strategy/holding_manager.py
strategy/stop_loss.py
broker/reconciliation.py
tests/test_holding_manager.py
```

Build:

```text
Setup B
→ BUY_READY
→ user manually buys
→ IBKR detects position
→ HOLDING
```

Use actual:

- quantity
- average cost

Holding decisions:

```text
HOLD_NO_CHANGE
TREND_PROGRESS
SL_UPGRADE
EXIT_REVIEW
```

Also:

- stop breach safety
- gap-through-stop path
- STOP_MISMATCH

Tests:

- B3/B4/B5 → retest → BUY_READY
- simulated manual fill
- HOLDING
- breakout while holding does not auto-move SL
- meaningful new support → SL_UPGRADE
- structural deterioration → EXIT_REVIEW

---

## Day 19 — Week 3 End-to-End Replay

Planned time:

**1.5 hours**

Files:

```text
tests/replay_end_to_end.py
tests/test_entry_engine.py
tests/test_holding_manager.py
```

Replay:

```text
Setup A
Setup B
manual fill
partial sell
stop recommendation
final close
```

Verify:

- persistence
- legal state transitions
- logging
- no look-ahead
- no automatic order calls

Milestone:

```text
Bot can find entries and manage a normal holding coherently in replay.
```

---

## Day 20 — Trend Winner

Planned time:

**1 hour**

Files:

```text
strategy/trend_winner.py
tests/test_trend_winner.py
```

Build:

- `qualifies(position)`
- weekly higher-support stop management
- weekly structural failure
- `EXIT_REVIEW_TREND_WINNER`

Tests:

- +2R alone does not qualify
- healthy weekly correction → HOLD
- new confirmed weekly support → upward-only SL recommendation

Milestone:

```text
Exceptional winners receive slower weekly-dominant management.
```

---

## Day 21 — Emergency Layer

Planned time:

**1 hour**

Files:

```text
strategy/emergency.py
tests/test_emergency.py
```

Build:

- gap-through-stop
- stop breach
- abnormal move evaluation
- percentage context
- ATR context
- volume context
- support context

Possible outcomes:

```text
ABNORMAL_VOLATILITY_REVIEW
IMMEDIATE_EXIT_REVIEW
```

Tests:

- open below stop → GAP_THROUGH_STOP
- -17% high-volume structural breakdown → immediate review
- large intraday decline that recovers support → review, not automatic sell

---

## Day 22 — Corporate Actions + Earnings

Planned time:

**1 hour**

Files:

```text
data/corporate_actions.py
strategy/earnings.py
tests/test_corporate_actions.py
tests/test_earnings.py
```

Build:

- corporate-action interface
- split normalization
- reverse-split handling
- quantity normalization
- entry normalization
- stop normalization
- structure normalization
- EARNINGS_RISK
- new-entry earnings gate
- DATA/CORPORATE_ACTION_REVIEW

Tests:

- 2-for-1 split does not look like crash
- unknown huge move produces review
- near earnings affects new entry
- near earnings does not automatically sell existing holding

---

## Day 23 — Telegram + Scheduler + Health + Deployment Prep

Planned time:

**1.5 hours**

Files:

```text
notifications/telegram_notifier.py
scheduler.py
health.py
Dockerfile
.env.example
tests/test_notifications.py
```

Build:

Telegram alerts:

- BUY_READY
- SL_UPGRADE
- EXIT_REVIEW
- GAP_THROUGH_STOP
- abnormal review
- earnings warning
- STOP_MISMATCH
- IBKR failure
- DATA failure
- BOT failure

Scheduler jobs:

- periodic IBKR reconciliation
- post-open safety
- post-close daily analysis
- Friday weekly analysis
- periodic earnings checks
- health checks

Recovery:

```text
reconnect
→ reload persistent state
→ re-read broker reality
→ reconcile
```

Deployment preparation:

- Docker/process config
- persistent DB
- persistent logs

Tests:

- real Telegram message
- Telegram failure
- accelerated scheduler
- Docker build if applicable

---

## Day 24 — Hetzner Deployment

Planned time:

**4 hours**

Build:

- Ubuntu VPS
- security hardening
- runtime / Docker
- IB Gateway/TWS connection
- local/private IBKR API exposure
- persistent SQLite
- rotating logs
- Telegram secrets
- systemd/restart policy
- DB backup
- disk/log monitoring
- real read-only reconciliation

Tests:

- restart bot
- reboot server if practical
- break IBKR connection
- verify safe recovery
- verify no public IBKR API port
- verify SQLite persists

Milestone:

```text
V1 runs unattended on Hetzner.
```

---

## Day 25 — Final Acceptance + Shadow Mode

Planned time:

**1.5 hours**

Files:

```text
tests/acceptance/
README.md
release notes
V1 checklist
```

Run full acceptance.

Verify:

- watchlist add/remove
- rollover holding
- manual buy
- partial sell
- full close
- Setup A replay
- Setup B replay
- BUY_READY alert
- SL_UPGRADE alert
- Trend Winner quiet normal correction
- GAP_THROUGH_STOP
- corporate-action normalization
- restart recovery
- IBKR outage
- stale data
- Telegram failure

Then:

- tag deployed V1
- freeze strategy parameters
- fix genuine bugs only
- begin 2–4 week shadow mode
- do not overfit after individual trades

Milestone:

```text
V1 deployed, recoverable, testable and ready for controlled shadow validation.
```

---

# 23. Final V1 Acceptance Checklist

Before declaring V1 complete:

## Architecture

```text
broker/
data/
strategy/
state/
notifications/
```

remain separated.

`main.py` remains orchestration-only.

---

## IBKR

- read-only
- actual positions reconcile
- quantity reconciles
- average cost reconciles
- no automatic broker execution

---

## Watchlist

- reload dynamically
- removed but owned ticker remains managed

---

## Persistence

These must survive restart:

- WAIT_RETEST
- BUY_READY
- HOLDING
- TREND_WINNER
- important events

---

## Market Data

- completed candles only
- invalid/stale data prevents confident decisions

---

## Setup A

Must be:

- multi-candle
- structural
- explainable
- replay-tested

---

## Setup B

Must include:

- B1–B5
- WAIT_RETEST
- successful retest
- failed retest

---

## Entry

Must include:

- weekly eligibility
- no chase
- weekly overhead resistance
- structural initial stop

---

## Holding

Most days:

```text
HOLD_NO_CHANGE
```

SL upgrade only after meaningful new structural support.

---

## Stop Safety

Existing stop:

```text
never moves lower
```

STOP_MISMATCH detectable when broker order visibility permits.

---

## Trend Winner

Weekly-dominant management without disabling:

- protective stop
- emergency layer

---

## Emergency

Gap-through-stop and serious abnormal events bypass ordinary weekly patience.

---

## Corporate Actions

Split/reverse-split handling prevents obvious false crash interpretation.

---

## Earnings

- new-entry risk gate
- limited warning for holdings
- no automatic earnings exit

---

## Telegram

Only actionable messages should reach user.

Internal strategy progression mainly remains in logs.

---

## Deployment

- persistent DB
- persistent logs
- restart policy
- backup
- private IBKR API
- unattended operation

---

## Testing

Must include:

- unit tests
- integration tests
- restart tests
- broker-failure tests
- bar-by-bar replay
- acceptance tests

---

# 24. Learning / Teaching Instructions for Future ChatGPT

The user is an experienced Java/backend engineer learning Python.

Do not merely provide code.

For every curriculum day:

1. explain today's objective
2. explain concepts
3. explain why they matter in this bot
4. identify every file being created/changed
5. explain architecture/data flow
6. implement step-by-step
7. explain every new/materially changed class, function and method
8. use Java comparisons where useful
9. show COMPLETE FINAL CONTENT of every file changed that day
10. give commands to run
11. give tests
12. show expected result/logs
13. explain common mistakes
14. provide completion checklist
15. mention what the next day will build

The user wants to understand everything.

Do not assume code should simply be copied.

---

# 25. Useful Java Comparisons

Use comparisons such as:

```text
Python dataclass
≈ Java DTO / record

Protocol
≈ structural interface

Callable
≈ Supplier / Function / functional interface

dependency injection
≈ Spring service injection

threading.Event
≈ synchronization/event primitive

Enum
≈ Java enum

repository.py
≈ DAO/repository layer

main.py
≈ application orchestration/bootstrap
```

---

# 26. Testing Rule

Every day:

```text
today's tests
+
full pytest suite
```

must pass before declaring the day complete.

Do not say:

```text
Day N completed
```

simply because code was written.

The user explicitly confirms completion.

---

# 27. Strategy Development Rule

During replay and shadow mode:

Fix:

```text
bugs
incorrect calculations
incorrect persistence
incorrect state transitions
look-ahead bugs
failure-handling bugs
```

Do NOT continually modify strategy because:

- one trade lost
- one trade was missed
- one historical example looks imperfect
- another threshold appears slightly better

Avoid strategy overfitting.

---

# 28. Resume Protocol

If this file is pasted into a future ChatGPT conversation:

First understand:

```text
Days completed: 1–10
Next day: 11
Project state: intentionally paused
```

If user says:

```text
resume bot
```

respond with confirmation that the next curriculum day is Day 11.

Do NOT automatically start teaching Day 11.

Wait until user explicitly says:

```text
give Day 11 learn
```

Then continue exactly from Day 11.

Do not:

- restart from Day 1
- create a new curriculum
- expand beyond Day 25
- redesign V1
- add automatic trading
- add ML
- add new strategies

unless the user explicitly asks to change the frozen scope.

---

# 29. Career Priority

The bot was intentionally paused because career-switch preparation became the higher-value objective.

The bot should not become productive procrastination.

Career work has priority unless the user explicitly decides otherwise.

The bot repository is preserved and can be resumed later from Day 11.

---

# 30. Final Project Status

```text
Trading Bot V0.1 Engineering Foundation

Days 1–10: COMPLETE

Days 11–25: PRESERVED FOR FUTURE

Current status: FROZEN / PAUSED

Next day when resumed: DAY 11
```

This is a deliberate project checkpoint, not an abandoned project.