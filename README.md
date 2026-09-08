# Portfolio Agent

## Milestone 4 — Interactive Brokers Foundation

Implemented:
- IBKR paper/live connection config
- TWS vs IB Gateway port selection
- reconnecting connection manager
- account summary and position models
- typed order intents
- broker order state
- business-level `client_order_id`
- idempotency guard against duplicate submissions
- broker numeric order-ID boundary
- cancel and refresh flow
- position and cash reconciliation
- persistence schema for broker orders
- Mock IBKR facade and tests

### Safety
No real IBKR order is sent by this artifact. The official TWS callback adapter remains isolated in `broker/ibkr/tws_facade.py`.

### IBKR callback wiring planned
- `nextValidId` -> order ID allocation
- `managedAccounts` -> account discovery
- `accountSummary` -> balances
- `position` -> positions
- `openOrder` -> acknowledgement
- `orderStatus` -> fill/status tracking
- `error` -> broker error channel

## Next milestone
Milestone 5: Strategy Core — regime detection, asset signals, portfolio targets, position lifecycle, TP/SL and deterministic risk checks.
