# Portfolio Agent

## Milestone 9 — Backtesting & Event Study Engine

Implemented:
- separate historical backtest path outside LangGraph
- historical feed
- history slicing up to simulated timestamp
- explicit look-ahead protection by construction
- execution simulator
- latency in bars
- spread model
- slippage model
- fixed and percentage commissions
- simulated portfolio
- cash and position accounting
- mark-to-market equity curve
- trade P&L tracking
- backtest metrics:
  - total return
  - max drawdown
  - trade count
  - win rate
  - gross profit/loss
  - profit factor
  - commissions
  - slippage
- event-study engine
- T+15m / T+1h / T+4h / T+12h / T+24h / T+72h support through config
- per-event return outcomes
- event-study summaries with minimum event count
- runnable demo

### Architecture rule

Backtesting does not execute LangGraph.

The historical simulator and the live/paper runtime share the deterministic
Strategy Core, but execution, time and data delivery are replaced by historical
implementations.

### Look-ahead protection

The strategy callback receives only:

`history_until(current_simulated_time)`

Future bars are never passed to the strategy callback.

Execution happens on a later bar according to configured latency, rather than at
the signal bar itself.

### Event studies

This milestone can answer questions such as:

- After confirmed Oil Shock events, what happens to BTC after 15m / 1h / 4h?
- Does Gold react differently from Nasdaq?
- Is the average response statistically useful across enough events?
- Does the sign of the reaction remain consistent over different horizons?

### Current limitations

- single-instrument runner is implemented first
- no futures-roll cost model yet
- no FX conversion model yet
- no borrow/short model yet
- no partial-fill model yet
- event studies currently summarize descriptive outcomes, not statistical significance
- commissions/slippage are simplified configurable assumptions

## Next milestone

Milestone 10: Production Hardening & Persistent Runtime — real repositories,
startup recovery, durable LangGraph checkpoints, database migrations,
observability, circuit-breaker hardening and deployable service entrypoint.
