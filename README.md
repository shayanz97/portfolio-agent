# Portfolio Agent

A LangGraph-based portfolio management, position monitoring and **paper-trading**
system for a multi-asset universe (equities, crypto, precious metals, energy,
volatility, macro/rates).

It combines a deterministic quantitative core with an orchestrated,
human-in-the-loop workflow: market data is validated, quantitative features and
market-regime signals are computed, positions are assessed over their lifecycle,
portfolio targets and risk-checked trade proposals are produced, and every trade
requires **explicit human approval** before a paper execution is simulated.

> **Safety first.** This project does **not** send real broker orders. The
> official Interactive Brokers TWS API boundary is intentionally left unwired,
> and all execution in this repository is paper/mock only.

---

## Architecture principle

**LangGraph only orchestrates.** All quantitative logic, risk rules, portfolio
rules, market-data validation, news analysis and broker logic live outside graph
nodes as ordinary, independently testable Python modules. The same deterministic
core is reused across live monitoring, paper trading, unit tests and
backtesting — only execution, time and data delivery are swapped.

---

## What it can do

**Configuration & domain**
- Layered YAML configuration merged into a single immutable, validated runtime
  config (Pydantic), with config hashing/versioning for reproducibility.
- Structured domain models and enums (regimes, position states, signals, order
  status).

**Market data**
- Provider abstraction with priority and fallback, normalized quotes, and a
  deterministic mock provider.
- Data-quality gate: staleness (per asset class), future-timestamp, wide-spread
  and non-positive-price rejection, plus a market/session clock.
- Only quotes with acceptable quality reach downstream strategy code.

**Quant & feature engine**
- Windowed returns (1m–24h), ATR, realized volatility, return z-score, momentum,
  rolling correlation and relative strength.
- An initial WTI/Brent oil-shock detector with directional confirmation and
  volatility/z-score-aware scoring.

**Strategy core (deterministic)**
- Market-regime engine (`RISK_ON` / `NEUTRAL` / `RISK_OFF` / `INFLATION_SHOCK` /
  `CRISIS`).
- Asset signal engine (`STRONG_BUY` … `EXIT`).
- Position lifecycle: profit protection, peak-giveback, thesis
  weakening/invalidation, recovery-watch and controlled add candidates.
- Portfolio regime target allocations and capped rebalance instructions.
- Long-side risk engine (ATR/max-loss stop, sizing from a risk budget, TP1/TP2,
  minimum risk/reward) and a trade-proposal builder.

**News & evidence intelligence**
- News ingestion, deduplication, source weighting, relevance and
  independent-domain requirements.
- Evidence status (`SUFFICIENT` / `INSUFFICIENT_EVIDENCE` /
  `CONFLICTING_EVIDENCE`) and a deterministic causal classifier with an
  allowed-cause whitelist. The classifier never fetches its own evidence and
  never invents a cause when evidence is insufficient or conflicting.

**Orchestration (LangGraph)**
- Typed graph state and dependency-injected gateways.
- Flow: reconciliation → market context → news intelligence → regime → signals →
  lifecycle → runtime monitoring → portfolio → risk/trade → circuit breaker.
- Native `interrupt()` for trade approval, resumable with the same `thread_id`.

**Paper trading & monitoring runtime**
- Position high/low-water marks, max unrealized profit and drawdown tracking.
- Alert engine with severity mapping and cooldown/deduplication.
- Performance snapshots and a scheduler-ready `run_once()` wrapper.

**Backtesting & event study**
- Historical simulation outside LangGraph with **look-ahead protection by
  construction** (the strategy only sees `history_until(t)`).
- Execution simulator (latency in bars, spread, slippage, commissions),
  simulated portfolio with a mark-to-market equity curve, and backtest metrics
  (return, max drawdown, win rate, profit factor, costs).
- Event-study engine for T+15m … T+72h horizons.

**Production hardening**
- SQLAlchemy repositories for run and runtime position state, a fail-closed
  startup recovery service, production circuit-breaker counters, structured JSON
  audit logging and a database healthcheck.
- Durable LangGraph checkpointer factory (memory / SQLite / PostgreSQL) kept
  separate from domain persistence.
- Alembic migration environment (SQLite batch mode) and a deployable CLI
  entrypoint.

---

## Requirements

- Python **3.11+**
- Core dependencies (installed automatically): `pydantic`, `pydantic-settings`,
  `PyYAML`, `SQLAlchemy`, `langgraph`, `alembic`,
  `langgraph-checkpoint-sqlite`, `langgraph-checkpoint-postgres`.

> Interactive Brokers' official Python TWS API is distributed by IB separately
> and is intentionally **not** declared as a dependency here.

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Copy the environment template and adjust values:

```bash
cp .env.example .env
```

`.env` holds runtime settings such as `DATABASE_URL` and IBKR connection
parameters (host/port/client id). Application configuration lives in `config/`.

---

## Configuration

`config/config.yaml` is the master file. It sets the version and environment and
merges the following includes into one validated runtime config:

| File | Purpose |
|------|---------|
| `assets.yaml` | Tradable universe, asset classes, markets/sessions |
| `market_data.yaml` | Provider priority, staleness, quality rules, sessions |
| `features.yaml` | Quant feature parameters |
| `events.yaml` / `regime.yaml` | Oil-shock and market-regime parameters |
| `strategy.yaml` | Signal thresholds/weights, position management |
| `portfolio.yaml` | Regime target allocations, rebalance rules |
| `risk.yaml` | Portfolio limits, trade risk, stops, take-profit, circuit breakers |
| `execution.yaml` / `broker.yaml` | Execution policy and IBKR settings |
| `workflow.yaml` | Graph workflow behavior (approval, limits) |
| `news.yaml` | News ingestion, evidence and classification |
| `runtime.yaml` | Scheduling, position tracking, alerts, performance |
| `backtest.yaml` | Historical simulation and event-study settings |
| `production.yaml` | Recovery, checkpoints, observability, circuit breakers |

Every value is validated on load; invalid or inconsistent configuration fails
fast.

---

## Running

**Foundation summary** — prints environment, config version/hash and broker info:

```bash
python -m portfolio_agent.app
```

**Service CLI** (installed as the `portfolio-agent` console script):

```bash
portfolio-agent show-config     # print version, environment, checkpoint backend
portfolio-agent init-db         # create the database schema
portfolio-agent healthcheck     # verify database connectivity (exit 0 = ok)
```

**End-to-end paper workflow demo** — runs the full LangGraph pipeline, pauses at
the human-approval interrupt, then resumes and simulates a paper execution:

```bash
python examples/milestone6_demo.py
```

**Backtest / event-study demo**:

```bash
python examples/milestone9_backtest_demo.py
```

---

## Testing

Run the full test suite (pytest is configured with `pythonpath=src` and
`testpaths=tests`):

```bash
pytest
```

Run a single module or with verbose output:

```bash
pytest tests/test_strategy_m5.py
pytest -q
```

Lint with Ruff (line length 100, target py311):

```bash
ruff check .
```

---

## Database migrations

Alembic is configured against `Base.metadata`, with SQLite batch mode enabled
(SQLite has limited `ALTER TABLE` support):

```bash
alembic revision --autogenerate -m "schema update"
alembic upgrade head
```

For development you can also create the schema directly with
`portfolio-agent init-db`.

---

## Project structure

```
config/                     layered YAML configuration
migrations/                 Alembic environment
examples/                   runnable demos
tests/                      pytest suite
src/portfolio_agent/
├── app.py                  foundation summary entrypoint
├── service.py              deployable CLI (healthcheck / init-db / show-config)
├── observability.py        JSON audit logging + in-memory metrics
├── config/                 loader, models, immutable settings
├── domain/                 core enums and models
├── market_data/            providers, quality, normalization, session clock
├── features/               quant calculations and feature engine
├── events/                 oil-shock detector
├── strategy/               regime, signals, lifecycle, portfolio, risk, trades
├── news/                   ingestion, dedup, evidence, causal classifier
├── graph/                  LangGraph state, nodes, routing, checkpoints, runner
├── runtime/                position tracking, alerts, performance, recovery, CBs
├── backtest/               historical feed, execution sim, portfolio, metrics, event study
└── persistence/            SQLAlchemy models and repositories
```

---

## Status & remaining work

The architecture is feature-complete for paper validation. Before any real
deployment the following still needs to be done:

- Wire the real IBKR TWS facade callbacks and real market/news providers.
- Persist the full fill/execution lifecycle end-to-end and back the alert
  registry with the database.
- Configure PostgreSQL and run real Alembic revisions instead of `create_all`.
- Add an external metrics backend, a secrets manager and deployment files.
- Enforce historical bar continuity/gap handling and add futures-contract
  rollover.
- Perform paper-account soak testing and restart/recovery chaos tests.
