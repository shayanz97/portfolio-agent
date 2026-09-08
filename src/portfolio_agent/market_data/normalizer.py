from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from portfolio_agent.config.models import AssetConfig, RuntimeConfig
from portfolio_agent.domain.enums import DataQuality
from portfolio_agent.market_data.clock import MarketClock
from portfolio_agent.market_data.models import MarketQuote, RawQuote
from portfolio_agent.market_data.quality import MarketDataQualityChecker


class MarketDataNormalizer:
    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.quality = MarketDataQualityChecker(config)
        self.clock = MarketClock(config)

    def normalize(
        self,
        raw: RawQuote,
        asset: AssetConfig,
        received_at: datetime | None = None,
    ) -> MarketQuote:
        received_at = received_at or datetime.now(timezone.utc)

        quality, delay, spread = self.quality.evaluate(raw, asset, received_at)

        timestamp = raw.timestamp or received_at
        last = raw.last
        mid = None

        if raw.bid is not None and raw.ask is not None and raw.bid > 0 and raw.ask >= raw.bid:
            mid = (raw.bid + raw.ask) / Decimal("2")
            if last is None:
                last = mid

        if last is None:
            raise ValueError("normalization requires usable last price")

        return MarketQuote(
            instrument=raw.instrument,
            provider=raw.provider,
            timestamp=timestamp,
            received_at=received_at,
            last=last,
            bid=raw.bid,
            ask=raw.ask,
            mid=mid,
            spread_pct=spread,
            volume=raw.volume,
            currency=raw.currency,
            delay_seconds=delay,
            quality=quality,
            market_status=self.clock.status_for(asset, received_at),
            metadata=raw.metadata,
        )
