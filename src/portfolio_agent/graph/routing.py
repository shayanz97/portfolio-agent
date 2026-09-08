from __future__ import annotations

from portfolio_agent.graph.state import PortfolioGraphState


def after_reconciliation(state: PortfolioGraphState) -> str:
    return "market_context" if state.get("reconciliation_ok") else "circuit_breaker"


def after_market_context(state: PortfolioGraphState) -> str:
    return "circuit_breaker" if state.get("status") == "DATA_ERROR" else "regime"


def after_risk(state: PortfolioGraphState) -> str:
    return "circuit_breaker"


def after_circuit_breaker(state: PortfolioGraphState) -> str:
    if not state.get("circuit_breaker_ok"):
        return "no_action"
    if not state.get("trade_proposals"):
        return "no_action"
    return "approval"


def after_approval(state: PortfolioGraphState) -> str:
    return "execute" if state.get("approval_status") == "APPROVED" else "rejected"
