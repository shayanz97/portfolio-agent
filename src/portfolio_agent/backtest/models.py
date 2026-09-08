from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class BacktestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SimSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class HistoricalPoint(BacktestModel):
    instrument: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal | None = None


class SimOrder(BacktestModel):
    order_id: str
    instrument: str
    side: SimSide
    quantity: Decimal
    signal_time: datetime
    requested_price: Decimal | None = None


class SimFill(BacktestModel):
    order_id: str
    instrument: str
    side: SimSide
    quantity: Decimal
    fill_time: datetime
    raw_price: Decimal
    fill_price: Decimal
    commission: Decimal
    slippage_cost: Decimal


class BacktestTrade(BacktestModel):
    instrument: str
    entry_time: datetime
    exit_time: datetime | None = None
    quantity: Decimal
    entry_price: Decimal
    exit_price: Decimal | None = None
    gross_pnl: Decimal | None = None
    net_pnl: Decimal | None = None


class EquityPoint(BacktestModel):
    timestamp: datetime
    equity: Decimal
    cash: Decimal


class BacktestMetrics(BacktestModel):
    initial_equity: Decimal
    final_equity: Decimal
    total_return_pct: float
    max_drawdown_pct: float
    trade_count: int
    win_rate: float
    gross_profit: Decimal
    gross_loss: Decimal
    profit_factor: float | None
    total_commission: Decimal
    total_slippage: Decimal


class EventOutcome(BacktestModel):
    event_id: str
    event_time: datetime
    instrument: str
    horizon_minutes: int
    return_pct: float | None


class EventStudySummary(BacktestModel):
    instrument: str
    horizon_minutes: int
    event_count: int
    average_return_pct: float | None
    median_return_pct: float | None
    positive_rate: float | None
