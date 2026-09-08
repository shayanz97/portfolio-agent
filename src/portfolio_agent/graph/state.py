from __future__ import annotations

from typing import Any, TypedDict


class PortfolioGraphState(TypedDict, total=False):
    run_id: str
    thread_id: str
    config_version: str
    config_hash: str

    market_context: dict[str, Any]
    regime: dict[str, Any]
    signals: list[dict[str, Any]]
    lifecycle_decisions: list[dict[str, Any]]

    current_weights: dict[str, float]
    portfolio_target: dict[str, Any]
    rebalance_instructions: list[dict[str, Any]]

    trade_candidates: list[dict[str, Any]]
    trade_proposals: list[dict[str, Any]]

    reconciliation_ok: bool
    circuit_breaker_ok: bool

    approval_required: bool
    approval_status: str
    approval_payload: dict[str, Any]

    execution_results: list[dict[str, Any]]

    status: str
    errors: list[str]
