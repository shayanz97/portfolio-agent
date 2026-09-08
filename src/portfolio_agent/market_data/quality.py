from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from portfolio_agent.config.models import AssetConfig, RuntimeConfig
from portfolio_agent.domain.enums import DataQuality
from portfolio_agent.market_data.models import RawQuote


class MarketDataValidationError(ValueError):
    pass


def quote_spread_pct(bid: Decimal | None, ask: Decimal | None) -> float | None:
    if bid is None or ask is None:
        return None
    if bid <= 0 or ask <= 0 or ask < bid:
        return None

    mid = (bid + ask) / Decimal("2")
    if mid == 0:
        return None

    return float((ask - bid) / mid)


class MarketDataQualityChecker:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def evaluate(
        self,
        raw: RawQuote,
        asset: AssetConfig,
        received_at: datetime,
    ) -> tuple[DataQuality, float, float | None]:
        rules = self.config.market_data.quality

        if raw.timestamp is None:
            if rules.reject_missing_timestamp:
                raise MarketDataValidationError("missing timestamp")
            timestamp = received_at
        else:
            timestamp = raw.timestamp

        if timestamp.tzinfo is None:
            raise MarketDataValidationError("timestamp must be timezone-aware")

        delay = (received_at - timestamp).total_seconds()

        if delay < -self.config.market_data.reject_future_timestamps_seconds:
            return DataQuality.FUTURE_TIMESTAMP, delay, None

        price = raw.last
        if price is None and raw.bid is not None and raw.ask is not None:
            price = (raw.bid + raw.ask) / Decimal("2")

        if price is None:
            raise MarketDataValidationError("quote has no usable price")

        if rules.reject_non_positive_prices and price <= 0:
            return DataQuality.INVALID, delay, None

        spread = quote_spread_pct(raw.bid, raw.ask)
        if spread is not None and spread > rules.max_spread_pct:
            return DataQuality.WIDE_SPREAD, delay, spread

        stale_after = self.config.market_data.staleness_seconds[asset.asset_class]
        if delay > stale_after:
            return DataQuality.STALE, delay, spread

        return DataQuality.OK, max(delay, 0.0), spread
