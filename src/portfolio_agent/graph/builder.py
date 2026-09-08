from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from portfolio_agent.graph.dependencies import WorkflowDependencies
from portfolio_agent.graph.nodes import (
    circuit_breaker_node,
    execute_node,
    initialize_node,
    lifecycle_node,
    market_context_node,
    no_action_node,
    news_intelligence_node,
    persist_node,
    portfolio_node,
    reconciliation_node,
    regime_node,
    rejected_node,
    risk_and_trade_node,
    signal_node,
    runtime_monitoring_node,
)
from portfolio_agent.graph.routing import (
    after_circuit_breaker,
    after_market_context,
    after_reconciliation,
)
from portfolio_agent.graph.state import PortfolioGraphState


def approval_node(state: PortfolioGraphState):
    proposals = state.get("trade_proposals", [])

    approved = interrupt({
        "type": "TRADE_APPROVAL",
        "run_id": state.get("run_id"),
        "proposal_count": len(proposals),
        "proposals": proposals,
        "question": "Approve these paper-trade proposals?",
    })

    return {
        "approval_status": "APPROVED" if bool(approved) else "REJECTED",
        "approval_payload": {"approved": bool(approved)},
    }


def approval_router(state: PortfolioGraphState) -> str:
    return "execute" if state.get("approval_status") == "APPROVED" else "rejected"


def build_portfolio_graph(
    deps: WorkflowDependencies,
    *,
    checkpointer=None,
):
    builder = StateGraph(PortfolioGraphState)

    builder.add_node("initialize", initialize_node(deps))
    builder.add_node("reconciliation", reconciliation_node(deps))
    builder.add_node("market_context", market_context_node(deps))
    builder.add_node("news_intelligence", news_intelligence_node(deps))
    builder.add_node("regime", regime_node(deps))
    builder.add_node("signals", signal_node(deps))
    builder.add_node("lifecycle", lifecycle_node(deps))
    builder.add_node("runtime_monitoring", runtime_monitoring_node(deps))
    builder.add_node("portfolio", portfolio_node(deps))
    builder.add_node("risk_and_trade", risk_and_trade_node(deps))
    builder.add_node("circuit_breaker", circuit_breaker_node(deps))
    builder.add_node("approval", approval_node)
    builder.add_node("execute", execute_node(deps))
    builder.add_node("rejected", rejected_node(deps))
    builder.add_node("no_action", no_action_node(deps))
    builder.add_node("persist", persist_node(deps))

    builder.add_edge(START, "initialize")
    builder.add_edge("initialize", "reconciliation")

    builder.add_conditional_edges(
        "reconciliation",
        after_reconciliation,
        {
            "market_context": "market_context",
            "circuit_breaker": "circuit_breaker",
        },
    )

    builder.add_conditional_edges(
        "market_context",
        after_market_context,
        {
            "regime": "news_intelligence",
            "circuit_breaker": "circuit_breaker",
        },
    )

    builder.add_edge("news_intelligence", "regime")
    builder.add_edge("regime", "signals")
    builder.add_edge("signals", "lifecycle")
    builder.add_edge("lifecycle", "runtime_monitoring")
    builder.add_edge("runtime_monitoring", "portfolio")
    builder.add_edge("portfolio", "risk_and_trade")
    builder.add_edge("risk_and_trade", "circuit_breaker")

    builder.add_conditional_edges(
        "circuit_breaker",
        after_circuit_breaker,
        {
            "approval": "approval",
            "no_action": "no_action",
        },
    )

    builder.add_conditional_edges(
        "approval",
        approval_router,
        {
            "execute": "execute",
            "rejected": "rejected",
        },
    )

    builder.add_edge("execute", "persist")
    builder.add_edge("rejected", "persist")
    builder.add_edge("no_action", "persist")
    builder.add_edge("persist", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())
