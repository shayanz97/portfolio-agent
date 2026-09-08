# Portfolio Agent

LangGraph-based portfolio management, position monitoring and paper-trading system.

## Milestone 1 — Foundation
Central configuration, validation, domain models, persistence foundation and broker abstraction.

## Milestone 2 — Market Data Foundation
Provider abstraction, normalized quotes, data quality/staleness checks, market sessions and snapshot service.

## Milestone 3 — Quant & Feature Engine

Implemented:
- historical `MarketBar` model
- configurable returns: 1m / 5m / 15m / 1h / 4h / 24h
- ATR
- realized volatility
- return z-score
- momentum score
- rolling correlation
- relative strength
- reusable `QuantFeatureEngine`
- initial WTI/Brent Oil-Shock detector
- WTI/Brent directional confirmation
- volatility- and z-score-aware event scoring
- persistence model for feature sets
- tests

### Architecture rule
The quant layer is independent of LangGraph and broker APIs. The same functions can therefore be used in live monitoring, paper trading, unit tests and backtesting.

### Important current limitation
Return windows assume evenly spaced bars with a known interval. Before live use, the historical-data layer must enforce bar continuity and mark gaps. Futures contract rollover is still not implemented.

## Next milestone
Milestone 4: Interactive Brokers integration — connection manager, paper account, positions, cash, orders and reconciliation.
