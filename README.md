# Portfolio Agent

Foundation for a LangGraph-based portfolio management, position monitoring and paper-trading system.

## Architecture principle

LangGraph orchestrates workflows. Quantitative logic, risk rules, portfolio rules and broker logic stay outside graph nodes as ordinary Python modules.

## Milestone 1

Implemented:
- central YAML configuration
- Pydantic validation
- immutable runtime settings
- config hashing/versioning
- structured application models
- database foundation
- logging foundation
- broker abstraction
- IBKR settings placeholder
- initial tests

Not implemented yet:
- live market-data providers
- Interactive Brokers order execution
- LangGraph workflow
- news analysis
- signal engine
- paper execution

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

Copy `.env.example` to `.env` and adjust values.

> IBKR's official Python TWS API is distributed by Interactive Brokers and is intentionally not declared as a PyPI dependency here.
