from __future__ import annotations

import logging
from collections.abc import Iterable
from datetime import datetime, timezone
from uuid import uuid4

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.domain.enums import DataQuality
from portfolio_agent.market_data.base import MarketDataProvider
from portfolio_agent.market_data.models import MarketQuote, MarketSnapshot
from portfolio_agent.market_data.normalizer import MarketDataNormalizer
from portfolio_agent.market_data.quality import MarketDataValidationError

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Fetches normalized quotes with provider priority and optional fallback.

    Invalid, stale, wide-spread and future-dated quotes are rejected from the
    final snapshot. This keeps downstream strategy code from silently consuming
    low-quality data.
    """

    ACCEPTABLE_QUALITY = {DataQuality.OK}

    def __init__(
        self,
        config: RuntimeConfig,
        providers: Iterable[MarketDataProvider],
    ):
        self.config = config
        self.normalizer = MarketDataNormalizer(config)
        self.providers = {provider.name: provider for provider in providers}

    def _ordered_providers(self) -> list[MarketDataProvider]:
        result = []
        for name in self.config.market_data.provider_priority:
            provider = self.providers.get(name)
            if provider is not None:
                result.append(provider)
        return result

    def fetch_snapshot(
        self,
        instruments: list[str] | None = None,
        received_at: datetime | None = None,
    ) -> MarketSnapshot:
        received_at = received_at or datetime.now(timezone.utc)

        if instruments is None:
            instruments = [
                name for name, asset in self.config.assets.items() if asset.enabled
            ]

        quotes: dict[str, MarketQuote] = {}
        missing: list[str] = []
        rejected: dict[str, str] = {}

        providers = self._ordered_providers()

        for instrument in instruments:
            asset = self.config.assets.get(instrument)
            if asset is None:
                rejected[instrument] = "instrument not configured"
                continue

            attempts: list[str] = []
            accepted = False

            for provider in providers:
                if not provider.supports(instrument):
                    continue

                try:
                    raw = provider.get_quote(instrument)
                    quote = self.normalizer.normalize(raw, asset, received_at)

                    if quote.quality in self.ACCEPTABLE_QUALITY:
                        quotes[instrument] = quote
                        accepted = True
                        break

                    attempts.append(
                        f"{provider.name}: rejected quality={quote.quality.value}"
                    )
                except (KeyError, ValueError, MarketDataValidationError) as exc:
                    attempts.append(f"{provider.name}: {exc}")

                if not self.config.market_data.allow_fallback:
                    break

            if not accepted:
                if attempts:
                    rejected[instrument] = "; ".join(attempts)
                else:
                    missing.append(instrument)

        return MarketSnapshot(
            snapshot_id=f"md-{uuid4().hex}",
            created_at=received_at,
            quotes=quotes,
            missing_instruments=missing,
            rejected_instruments=rejected,
        )
