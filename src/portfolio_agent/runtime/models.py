from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from portfolio_agent.domain.enums import PositionState


class RuntimeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AlertSeverity(StrEnum):
    INFO = "INFO"
    WATCH = "WATCH"
    IMPORTANT = "IMPORTANT"
    CRITICAL = "CRITICAL"


class PositionRuntimeState(RuntimeModel):
    instrument: str
    entry_price: Decimal
    quantity: Decimal
    current_price: Decimal
    high_water_mark_intraday: Decimal
    high_water_mark_close: Decimal
    low_water_mark_intraday: Decimal
    low_water_mark_close: Decimal
    max_unrealized_profit_pct: float
    max_drawdown_pct: float
    lifecycle_state: PositionState
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AlertEvent(RuntimeModel):
    alert_id: str
    instrument: str
    severity: AlertSeverity
    state: PositionState
    title: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dedup_key: str
    acknowledged: bool = False


class PerformanceSnapshot(RuntimeModel):
    run_id: str
    portfolio_value: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    return_pct: float
    max_drawdown_pct: float
    trade_count: int
    win_count: int
    loss_count: int
    win_rate: float
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
