from datetime import datetime, timezone
from pathlib import Path

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


def feature(name, r4, momentum=0.1):
    return {
        "instrument": name,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "returns": {"4h": r4},
        "atr": 2.0,
        "realized_volatility": 0.20,
        "return_zscore": 1.5,
        "momentum_score": momentum,
        "sample_size": 100,
    }


config = load_config(Path(__file__).resolve().parents[1] / "config")

context = {
    "features": {
        "equities": feature("QQQ", -0.03),
        "crypto": feature("BTC", -0.04),
        "vix": feature("VIX", 0.04),
        "dxy": feature("DXY", 0.01),
        "yields": feature("US10Y", 0.01),
    },
    "oil_event": {
        "detected_at": datetime.now(timezone.utc).isoformat(),
        "severity": "HIGH",
        "score": 78,
        "direction": "UP",
        "confirmation_score": 0.90,
        "explanation": "Demo oil shock",
    },
    "signal_assets": [
        {"instrument": "SPY", "features": feature("SPY", -0.02), "news_score": -0.2},
    ],
    "positions": [],
    "current_weights": {
        "equity": 0.45,
        "crypto": 0.20,
        "precious_metal": 0.10,
        "energy": 0.05,
        "cash": 0.20,
    },
    "trade_candidates": [
        {
            "instrument": "GLD",
            "side": "BUY",
            "portfolio_value": 100000,
            "entry_price": 220,
            "atr": 4.0,
            "current_open_risk": 0.01,
            "current_position_weight": 0.05,
        }
    ],
}

execution = MockPaperExecutionGateway()
persistence = InMemoryRunPersistenceGateway()

deps = WorkflowDependencies(
    config=config,
    market_context_provider=StaticMarketContextProvider(context),
    reconciliation_gateway=StaticReconciliationGateway(True),
    execution_gateway=execution,
    persistence_gateway=persistence,
)

graph = build_portfolio_graph(deps)
runner = PortfolioGraphRunner(graph, config)

result, lg_config = runner.start()
print(result)

if "__interrupt__" in result:
    result = runner.resume(lg_config, approved=True)
    print(result)
