import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest

if importlib.util.find_spec("langgraph") is None:
    pytest.skip("langgraph not installed in test runtime", allow_module_level=True)

from portfolio_agent.config.loader import load_config
from portfolio_agent.graph.builder import build_portfolio_graph
from portfolio_agent.graph.dependencies import WorkflowDependencies
from portfolio_agent.graph.mock_gateways import (
    InMemoryRunPersistenceGateway,
    MockPaperExecutionGateway,
    StaticMarketContextProvider,
    StaticReconciliationGateway,
)
from portfolio_agent.graph.runner import PortfolioGraphRunner


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


def test_graph_no_action_path():
    config = load_config(Path(__file__).resolve().parents[1] / "config")
    context = {
        "features": {},
        "positions": [],
        "current_weights": {"equity": .45, "crypto": .15, "precious_metal": .10, "energy": .05, "cash": .25},
        "signal_assets": [],
        "trade_candidates": [],
    }
    persistence = InMemoryRunPersistenceGateway()
    deps = WorkflowDependencies(
        config=config,
        market_context_provider=StaticMarketContextProvider(context),
        reconciliation_gateway=StaticReconciliationGateway(True),
        execution_gateway=MockPaperExecutionGateway(),
        persistence_gateway=persistence,
    )

    graph = build_portfolio_graph(deps)
    result, _ = PortfolioGraphRunner(graph, config).start(run_id="test-no-action")
    assert result["status"] == "NO_ACTION"
    assert persistence.states
