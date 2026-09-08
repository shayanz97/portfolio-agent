from datetime import datetime, timezone
from pathlib import Path

from portfolio_agent.config.loader import load_config
from portfolio_agent.graph.dependencies import WorkflowDependencies
from portfolio_agent.graph.mock_gateways import (
    InMemoryRunPersistenceGateway,
    MockPaperExecutionGateway,
    StaticMarketContextProvider,
    StaticReconciliationGateway,
)
from portfolio_agent.graph.nodes import (
    circuit_breaker_node,
    market_context_node,
    reconciliation_node,
    regime_node,
)


def config():
    return load_config(Path(__file__).resolve().parents[1] / "config")


def feature(name, r4):
    return {
        "instrument": name,
        "as_of": datetime(2026, 9, 8, 12, tzinfo=timezone.utc).isoformat(),
        "returns": {"4h": r4},
        "atr": 2.0,
        "realized_volatility": 0.2,
        "return_zscore": 1.0,
        "momentum_score": 0.1,
        "sample_size": 100,
    }


def deps(reconcile=True):
    context = {
        "features": {
            "equities": feature("QQQ", -0.02),
            "crypto": feature("BTC", -0.03),
            "vix": feature("VIX", 0.03),
            "dxy": feature("DXY", 0.01),
            "yields": feature("US10Y", 0.01),
        },
        "positions": [],
        "current_weights": {"equity": 0.4, "crypto": 0.1, "precious_metal": 0.1, "energy": 0.05, "cash": 0.35},
        "signal_assets": [],
        "trade_candidates": [],
    }
    return WorkflowDependencies(
        config=config(),
        market_context_provider=StaticMarketContextProvider(context),
        reconciliation_gateway=StaticReconciliationGateway(reconcile),
        execution_gateway=MockPaperExecutionGateway(),
        persistence_gateway=InMemoryRunPersistenceGateway(),
    )


def test_reconciliation_node():
    d = deps(True)
    out = reconciliation_node(d)({"errors": []})
    assert out["reconciliation_ok"]


def test_failed_reconciliation_triggers_circuit_breaker():
    d = deps(False)
    state = {"errors": []}
    state.update(reconciliation_node(d)(state))
    state.update(circuit_breaker_node(d)(state))
    assert not state["circuit_breaker_ok"]


def test_market_context_and_regime_nodes():
    d = deps(True)
    state = {"errors": []}
    state.update(market_context_node(d)(state))
    assert "market_context" in state
    state.update(regime_node(d)(state))
    assert "regime" in state
