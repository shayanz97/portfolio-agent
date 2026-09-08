# Portfolio Agent

## Milestone 6 — LangGraph Orchestration

Implemented:
- small typed `PortfolioGraphState`
- dependency-injected workflow services
- thin LangGraph nodes
- explicit routing
- market-context validation
- portfolio reconciliation gate
- regime -> signals -> lifecycle -> portfolio -> risk/proposal chain
- orchestration-level circuit breaker
- native LangGraph `interrupt()` for trade approval
- resume with the same `thread_id`
- paper execution gateway interface
- persistence gateway interface
- in-memory checkpointer by default
- mock end-to-end gateways
- runnable demo
- node-level tests and optional LangGraph integration test

### Graph

START
-> initialize
-> reconciliation
-> market_context
-> regime
-> signals
-> lifecycle
-> portfolio
-> risk_and_trade
-> circuit_breaker

If no safe trade:
-> no_action
-> persist
-> END

If trade exists:
-> approval interrupt
   -> rejected -> persist -> END
   -> approved -> execute -> persist -> END

### Key architecture rule

LangGraph only orchestrates. Quant, strategy, portfolio, position lifecycle,
risk and broker logic remain ordinary independently testable Python modules.

### Human approval

The approval node uses LangGraph `interrupt()`. A checkpointer and stable
`thread_id` are therefore mandatory. The runner resumes with
`Command(resume=True/False)` using the same thread.

### Production note

`InMemorySaver` is appropriate for development only. Before persistent paper/live
deployment, replace it with a durable LangGraph checkpointer backed by a database.

## Next milestone

Milestone 7: News & Evidence Intelligence — source ingestion, deduplication,
evidence ranking, structured causal classification and safe LLM output.
