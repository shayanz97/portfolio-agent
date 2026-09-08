from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from portfolio_agent.market_data.base import MarketDataProvider
from portfolio_agent.market_data.models import RawQuote


class MockMarketDataProvider(MarketDataProvider):
    name = "mock"

    def __init__(self, prices: dict[str, Decimal | float | int]):
        self.prices = {k: Decimal(str(v)) for k, v in prices.items()}

    def supports(self, instrument: str) -> bool:
        return instrument in self.prices

    def get_quote(self, instrument: str) -> RawQuote:
        if not self.supports(instrument):
            raise KeyError(instrument)

        price = self.prices[instrument]
        spread = price * Decimal("0.0005")

        return RawQuote(
            instrument=instrument,
            provider=self.name,
            timestamp=datetime.now(timezone.utc),
            last=price,
            bid=price - spread,
            ask=price + spread,
            currency="USD",
        )
