from __future__ import annotations

from decimal import Decimal
from typing import Any

from portfolio_agent.config.loader import config_hash
from portfolio_agent.domain.enums import AssetSignal, MarketRegime
from portfolio_agent.events.models import OilShockEvent
from portfolio_agent.features.models import FeatureSet
from portfolio_agent.graph.dependencies import WorkflowDependencies
from portfolio_agent.graph.state import PortfolioGraphState
from portfolio_agent.strategy.models import (
    PositionLifecycleInput,
    RegimeAssessment,
    SignalAssessment,
)


def initialize_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        return {
            "config_version": deps.config.version,
            "config_hash": config_hash(deps.config),
            "status": "RUNNING",
            "errors": state.get("errors", []),
            "approval_status": "NOT_REQUESTED",
            "execution_results": [],
        }
    return node


def reconciliation_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        ok = bool(deps.reconciliation_gateway.reconcile())
        errors = list(state.get("errors", []))
        if not ok:
            errors.append("portfolio reconciliation failed")
        return {
            "reconciliation_ok": ok,
            "errors": errors,
        }
    return node


def market_context_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        try:
            context = deps.market_context_provider.get_context()
            required = {"features", "current_weights", "positions"}
            missing = sorted(required - set(context))
            if missing:
                raise ValueError(f"market context missing keys: {missing}")
            return {
                "market_context": context,
                "current_weights": context["current_weights"],
            }
        except Exception as exc:
            errors = list(state.get("errors", []))
            errors.append(f"market context error: {exc}")
            return {"errors": errors, "status": "DATA_ERROR"}
    return node


def regime_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        context = state["market_context"]
        raw_features = context["features"]

        def fs(name: str):
            value = raw_features.get(name)
            return FeatureSet.model_validate(value) if value else None

        oil_event = context.get("oil_event")
        event = OilShockEvent.model_validate(oil_event) if oil_event else None

        assessment = deps.regime_engine.assess(
            equities=fs("equities"),
            crypto=fs("crypto"),
            vix=fs("vix"),
            dxy=fs("dxy"),
            yields=fs("yields"),
            oil_event=event,
        )
        return {"regime": assessment.model_dump(mode="json")}
    return node


def signal_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        context = state["market_context"]
        regime = RegimeAssessment.model_validate(state["regime"])
        oil_event = context.get("oil_event")
        event = OilShockEvent.model_validate(oil_event) if oil_event else None

        results = []
        for item in context.get("signal_assets", []):
            features = FeatureSet.model_validate(item["features"])
            result = deps.signal_engine.assess(
                item["instrument"],
                features,
                regime,
                oil_event=event,
                news_score=float(item.get("news_score", 0.0)),
                technical_score=item.get("technical_score"),
            )
            results.append(result.model_dump(mode="json"))
        return {"signals": results}
    return node


def lifecycle_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        decisions = []
        for raw in state["market_context"].get("positions", []):
            item = PositionLifecycleInput.model_validate(raw)
            decision = deps.lifecycle_engine.assess(item)
            decisions.append(decision.model_dump(mode="json"))
        return {"lifecycle_decisions": decisions}
    return node


def portfolio_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        regime = RegimeAssessment.model_validate(state["regime"])
        signals = [SignalAssessment.model_validate(x) for x in state.get("signals", [])]

        target = deps.portfolio_engine.target_for_regime(regime.regime, signals)
        instructions = deps.portfolio_engine.rebalance(
            state.get("current_weights", {}),
            target,
        )
        return {
            "portfolio_target": target.model_dump(mode="json"),
            "rebalance_instructions": [x.model_dump(mode="json") for x in instructions],
        }
    return node


def risk_and_trade_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        context = state["market_context"]
        candidates = context.get("trade_candidates", [])
        proposals = []
        rejected = []

        for candidate in candidates[: deps.config.workflow.max_trade_proposals_per_run]:
            if candidate.get("side", "BUY") != "BUY":
                rejected.append({
                    "instrument": candidate.get("instrument"),
                    "reason": "MVP risk engine currently supports long-entry proposals only",
                })
                continue

            risk = deps.risk_engine.evaluate_long(
                portfolio_value=Decimal(str(candidate["portfolio_value"])),
                entry_price=Decimal(str(candidate["entry_price"])),
                atr=float(candidate["atr"]),
                current_open_risk=float(candidate.get("current_open_risk", 0.0)),
                current_position_weight=float(candidate.get("current_position_weight", 0.0)),
            )

            if not risk.approved:
                rejected.append({
                    "instrument": candidate["instrument"],
                    "reason": "; ".join(risk.reasons),
                })
                continue

            proposal = deps.trade_builder.build_long(
                run_id=state["run_id"],
                instrument=candidate["instrument"],
                entry_price=Decimal(str(candidate["entry_price"])),
                risk=risk,
            )
            proposals.append(proposal.model_dump(mode="json"))

        return {
            "trade_candidates": candidates,
            "trade_proposals": proposals,
            "approval_required": bool(proposals) and deps.config.workflow.require_approval_for_any_trade,
            "market_context": {
                **context,
                "rejected_trade_candidates": rejected,
            },
        }
    return node


def circuit_breaker_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        # Current milestone checks orchestration-level hard failures.
        # Detailed daily-loss/drawdown checks stay in the dedicated risk layer.
        ok = True
        errors = list(state.get("errors", []))

        if deps.config.workflow.stop_on_reconciliation_failure and not state.get("reconciliation_ok", False):
            ok = False
        if deps.config.workflow.stop_on_market_data_failure and state.get("status") == "DATA_ERROR":
            ok = False

        if not ok:
            errors.append("workflow circuit breaker blocked execution")

        return {
            "circuit_breaker_ok": ok,
            "errors": errors,
        }
    return node


def rejected_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        return {
            "approval_status": "REJECTED",
            "status": "REJECTED",
        }
    return node


def execute_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        proposals = state.get("trade_proposals", [])
        results = deps.execution_gateway.execute(proposals)
        return {
            "execution_results": results,
            "status": "EXECUTED",
        }
    return node


def no_action_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        return {
            "status": "NO_ACTION" if not state.get("trade_proposals") else "BLOCKED",
        }
    return node


def persist_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        deps.persistence_gateway.persist(dict(state))
        return {"status": state.get("status", "COMPLETED")}
    return node


def news_intelligence_node(deps: WorkflowDependencies):
    def node(state: PortfolioGraphState):
        gateway = deps.news_intelligence_gateway
        context = state["market_context"]
        oil_event = context.get("oil_event")

        if gateway is None or not oil_event:
            return {
                "news_items": [],
                "evidence_bundle": {},
                "causal_classification": {},
            }

        query = context.get("news_query", "oil")
        items, bundle, classification = gateway.analyse(query=query)

        return {
            "news_items": [x.model_dump(mode="json") for x in items],
            "evidence_bundle": bundle.model_dump(mode="json"),
            "causal_classification": classification.model_dump(mode="json"),
        }
    return node
