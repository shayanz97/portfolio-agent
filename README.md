# Portfolio Agent

## Milestone 7 — News & Evidence Intelligence

Implemented:
- news provider interface
- deterministic mock provider
- age/language filtering
- title/content deduplication
- content hashing
- source weighting
- relevance scoring
- independent-domain requirement
- evidence-status model
- conflict detection
- causal hints and structured classification
- explicit:
  - `SUFFICIENT`
  - `INSUFFICIENT_EVIDENCE`
  - `CONFLICTING_EVIDENCE`
- allowed-cause whitelist
- safe deterministic classifier fallback
- isolated structured-LLM classifier boundary
- `NewsIntelligenceService`
- LangGraph integration between market context and regime analysis

### Supported initial oil causes
- geopolitical_supply_shock
- opec_supply_change
- inventory_surprise
- demand_growth
- demand_destruction
- currency_move
- refinery_outage
- shipping_disruption
- technical_move
- unknown

### Safety / anti-hallucination rule
The classifier never fetches its own evidence. It receives an already-built
EvidenceBundle. If the evidence is insufficient or materially conflicting, that
state is preserved and the classifier must not invent a causal explanation.

### Graph update

market_context
-> news_intelligence
-> regime
-> signals
-> lifecycle
-> portfolio
-> risk_and_trade
-> approval
-> paper execution

### Next milestone
Milestone 8: Paper Trading & Position Monitoring Runtime — scheduled runs,
persistent run/order history, position high-water marks, lifecycle alerts,
performance tracking and end-to-end paper operation.
