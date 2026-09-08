# Portfolio Agent

## Milestone 5 — Strategy Core

Implemented:
- market regime engine
- deterministic regime scoring from equities, crypto, VIX, DXY, yields and Oil-Shock events
- asset signal engine (`STRONG_BUY`, `BUY`, `HOLD`, `REDUCE`, `EXIT`)
- position lifecycle engine
- profit-protection / peak-giveback logic
- thesis weakening / thesis invalidation handling
- recovery-watch and controlled add-candidate logic
- portfolio regime target allocations
- rebalance instructions with per-run cap
- deterministic long-side risk engine
- ATR/max-loss stop selection
- position sizing from portfolio risk budget
- TP1 / TP2 generation
- minimum risk/reward check
- trade proposal builder
- centralized `regime.yaml` and `portfolio.yaml`

### Position lifecycle examples

**ELF-type case**
- strong unrealized profit
- meaningful drawdown from high-water mark
- drawdown also exceeds ATR threshold
- result: `PROFIT_AT_RISK -> REDUCE`

**LULU-type case**
- position below entry
- thesis remains healthy
- recovery score above configured threshold
- add-event and max-position limits still available
- result: `RECOVERY_CONFIRMED -> BUY` candidate

### Safety rule
The Strategy Core still does not send orders. It only produces deterministic assessments and trade proposals. Actual execution remains downstream of risk checks, human approval and the IBKR order layer.

## Next milestone
Milestone 6: LangGraph orchestration — state, routing, persistence/checkpoints, approval interrupts and end-to-end paper workflow.
