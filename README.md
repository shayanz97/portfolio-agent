# Portfolio Agent

## Milestone 8 — Paper Trading & Position Monitoring Runtime

Implemented:
- runtime configuration
- scheduler-ready `run_once()` wrapper
- position runtime state
- persistent-style high-water / low-water mark model
- max unrealized profit tracking
- max drawdown tracking
- lifecycle-state tracking
- position alert engine
- alert severity mapping
- alert cooldown / deduplication
- paper runtime service
- performance snapshot model
- basic runtime performance metrics
- SQLAlchemy persistence schemas for:
  - position runtime states
  - alerts
  - performance snapshots
- LangGraph runtime-monitoring node after position lifecycle analysis

### Position monitoring flow

Broker / Portfolio
-> Position Lifecycle
-> Runtime Monitoring
   -> High-water mark tracking
   -> Profit-at-risk alerts
   -> Thesis alerts
   -> Recovery alerts
-> Portfolio / Risk / Trade Proposal

### ELF-type behavior

If a position previously reached a strong unrealized gain and later transitions
to `PROFIT_AT_RISK`, the runtime can create an IMPORTANT alert while retaining
its historical high-water mark. Duplicate alerts are suppressed during the
configured cooldown window.

### LULU-type behavior

If the lifecycle engine transitions a losing position to
`RECOVERY_CONFIRMED`, the runtime emits an IMPORTANT alert. The actual add order
still goes through portfolio limits, risk checks, human approval and paper
execution.

### Scheduling

This milestone is scheduler-ready but deliberately does not embed a permanent
background scheduler. `ScheduledRuntimeRunner.run_once()` can be invoked by
cron, systemd timers, a container scheduler, CI jobs or a future service daemon.

### Current limitation

Runtime state is modeled and persistence schemas exist, but the default service
still uses in-memory state for tests. The next persistence hardening step should
wire repositories to PostgreSQL/SQLite and reload position runtime state on
startup.

## Next milestone

Milestone 9: Backtesting & Event Study Engine — historical feed, execution
simulation, look-ahead protection, slippage/commission modeling, strategy
metrics and oil-event lead/lag studies.
