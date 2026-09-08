from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class QuantModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MarketBar(QuantModel):
    instrument: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None = None
    source: str = "unknown"

    @property
    def is_valid(self) -> bool:
        return (
            self.open > 0
            and self.high >= max(self.open, self.close, self.low)
            and self.low <= min(self.open, self.close, self.high)
            and self.close > 0
        )


class FeatureSet(QuantModel):
    instrument: str
    as_of: datetime
    returns: dict[str, float] = Field(default_factory=dict)
    atr: float | None = None
    realized_volatility: float | None = None
    return_zscore: float | None = None
    momentum_score: float | None = None
    relative_strength: float | None = None
    correlations: dict[str, float] = Field(default_factory=dict)
    sample_size: int
