# Portfolio Agent

LangGraph-based portfolio management, position monitoring and paper-trading system.

## Architecture principle

LangGraph orchestrates workflows. Quantitative logic, risk rules, portfolio rules,
market-data validation and broker logic stay outside graph nodes as ordinary Python modules.

## Milestone 1 — Foundation

Implemented:
- central YAML configuration
- Pydantic validation
- immutable runtime settings
- config hashing/versioning
- structured domain models
- database foundation
- logging foundation
- broker abstraction
- IBKR settings placeholder
- initial tests

## Milestone 2 — Market Data Foundation

Implemented:
- market-data provider interface
- provider priority and fallback
- normalized quote model
- source/timestamp/delay metadata
- staleness detection by asset class
- future-timestamp detection
- spread-quality checks
- market/session clock
- snapshot service
- SQLAlchemy market snapshot persistence model
- deterministic mock provider
- tests for market clock, quality and snapshot creation

Important design rule:
**Downstream strategy code only consumes normalized quotes with acceptable quality.**
Stale, future-dated, missing or excessively wide-spread quotes are rejected.

### Session note

`FUTURES_APPROX` is intentionally an approximate MVP clock. It must be replaced or
augmented by exchange/provider trading-session metadata before live futures execution.
This prevents us from pretending a hand-written calendar is authoritative for holidays,
special sessions or contract-specific trading hours.

## Not implemented yet

- real live market-data providers
- IBKR market-data adapter
- futures contract resolver / rollover
- feature calculations
- oil-shock detector
- market-regime engine
- LangGraph workflow
- news analysis
- order execution

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

Copy `.env.example` to `.env` and adjust values.

> IBKR's official Python TWS API is distributed by Interactive Brokers and is
> intentionally not declared as a normal PyPI dependency here.
