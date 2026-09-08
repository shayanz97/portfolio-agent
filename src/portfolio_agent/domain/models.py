from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from portfolio_agent.domain.enums import AssetSignal, MarketRegime, OrderStatus, PositionState


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MarketPoint(DomainModel):
    instrument: str
    value: Decimal
    timestamp: datetime
    source: str
    quality: str = "OK"
    delay_seconds: int = 0
    market_status: str = "UNKNOWN"


class PositionSnapshot(DomainModel):
    instrument: str
    quantity: Decimal
    average_cost: Decimal
    market_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    currency: str
    timestamp: datetime


class PositionLifecycleSnapshot(DomainModel):
    instrument: str
    state: PositionState
    entry_price: Decimal
    high_water_mark_intraday: Decimal
    high_water_mark_close: Decimal
    current_price: Decimal
    max_unrealized_profit_pct: float
    current_unrealized_profit_pct: float
    drawdown_from_peak_pct: float
    drawdown_from_peak_atr: float | None = None
    position_health_score: float | None = Field(default=None, ge=0, le=100)
    profit_risk_score: float | None = Field(default=None, ge=0, le=100)
    recovery_score: float | None = Field(default=None, ge=0, le=100)


class AssetSignalResult(DomainModel):
    instrument: str
    score: float = Field(ge=-1, le=1)
    signal: AssetSignal
    confidence: float = Field(ge=0, le=1)
    components: dict[str, float]
    explanation: str | None = None


class TradeProposal(DomainModel):
    proposal_id: str
    client_order_id: str
    instrument: str
    side: str
    quantity: Decimal | None = None
    notional: Decimal | None = None
    limit_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit_1: Decimal | None = None
    take_profit_2: Decimal | None = None
    risk_amount: Decimal | None = None
    status: OrderStatus = OrderStatus.PROPOSED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StrategyRun(DomainModel):
    run_id: str
    config_version: str
    config_hash: str
    regime: MarketRegime | None = None
    regime_score: float | None = None
    market_snapshot_id: str | None = None
    portfolio_snapshot_id: str | None = None
    event_ids: list[str] = []
    signal_ids: list[str] = []
    trade_proposal_ids: list[str] = []
    errors: list[str] = []
