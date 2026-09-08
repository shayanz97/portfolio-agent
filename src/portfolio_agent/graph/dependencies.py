from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.strategy.portfolio import PortfolioTargetEngine
from portfolio_agent.strategy.position_lifecycle import PositionLifecycleEngine
from portfolio_agent.strategy.regime import MarketRegimeEngine
from portfolio_agent.strategy.risk import DeterministicRiskEngine
from portfolio_agent.strategy.signals import AssetSignalEngine
from portfolio_agent.strategy.trade_builder import TradeProposalBuilder


class MarketContextProvider(Protocol):
    def get_context(self) -> dict[str, Any]:
        ...


class ReconciliationGateway(Protocol):
    def reconcile(self) -> bool:
        ...


class ExecutionGateway(Protocol):
    def execute(self, proposals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ...


class NewsIntelligenceGateway(Protocol):
    def analyse(self, *, query: str):
        ...


class RunPersistenceGateway(Protocol):
    def persist(self, state: dict[str, Any]) -> None:
        ...


@dataclass
class WorkflowDependencies:
    config: RuntimeConfig
    market_context_provider: MarketContextProvider
    reconciliation_gateway: ReconciliationGateway
    execution_gateway: ExecutionGateway
    persistence_gateway: RunPersistenceGateway
    news_intelligence_gateway: NewsIntelligenceGateway | None = None

    @property
    def regime_engine(self) -> MarketRegimeEngine:
        return MarketRegimeEngine(self.config)

    @property
    def signal_engine(self) -> AssetSignalEngine:
        return AssetSignalEngine(self.config)

    @property
    def lifecycle_engine(self) -> PositionLifecycleEngine:
        return PositionLifecycleEngine(self.config)

    @property
    def portfolio_engine(self) -> PortfolioTargetEngine:
        return PortfolioTargetEngine(self.config)

    @property
    def risk_engine(self) -> DeterministicRiskEngine:
        return DeterministicRiskEngine(self.config)

    @property
    def trade_builder(self) -> TradeProposalBuilder:
        return TradeProposalBuilder()
