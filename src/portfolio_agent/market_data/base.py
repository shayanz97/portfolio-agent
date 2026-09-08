from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from portfolio_agent.market_data.models import RawQuote


class MarketDataProvider(ABC):
    name: str

    @abstractmethod
    def supports(self, instrument: str) -> bool:
        ...

    @abstractmethod
    def get_quote(self, instrument: str) -> RawQuote:
        ...

    def get_quotes(self, instruments: Sequence[str]) -> list[RawQuote]:
        return [self.get_quote(instrument) for instrument in instruments]
