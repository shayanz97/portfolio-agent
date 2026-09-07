from __future__ import annotations

from abc import ABC, abstractmethod

from portfolio_agent.domain.models import StrategyRun


class StrategyRunRepository(ABC):
    @abstractmethod
    def save(self, run: StrategyRun) -> None:
        ...

    @abstractmethod
    def get(self, run_id: str) -> StrategyRun | None:
        ...
