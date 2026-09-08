from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from portfolio_agent.domain.enums import DataQuality, MarketStatus


class MarketDataModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RawQuote(MarketDataModel):
    instrument: str
    provider: str
    timestamp: datetime | None
    last: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    volume: Decimal | None = None
    currency: str = "USD"
    metadata: dict[str, str] = Field(default_factory=dict)


class MarketQuote(MarketDataModel):
    instrument: str
    provider: str
    timestamp: datetime
    received_at: datetime
    last: Decimal
    bid: Decimal | None = None
    ask: Decimal | None = None
    mid: Decimal | None = None
    spread_pct: float | None = None
    volume: Decimal | None = None
    currency: str
    delay_seconds: float
    quality: DataQuality
    market_status: MarketStatus
    metadata: dict[str, str] = Field(default_factory=dict)


class MarketSnapshot(MarketDataModel):
    snapshot_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    quotes: dict[str, MarketQuote]
    missing_instruments: list[str] = Field(default_factory=list)
    rejected_instruments: dict[str, str] = Field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return not self.missing_instruments and not self.rejected_instruments
