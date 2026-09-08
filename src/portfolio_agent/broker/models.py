from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, model_validator

class BrokerModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class BrokerSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"

class BrokerOrderType(StrEnum):
    LIMIT = "LMT"
    MARKET = "MKT"

class BrokerConnectionState(StrEnum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"

class AccountSummary(BrokerModel):
    account_id: str
    base_currency: str
    net_liquidation: Decimal
    total_cash: Decimal
    available_funds: Decimal
    buying_power: Decimal | None = None
    excess_liquidity: Decimal | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BrokerPosition(BrokerModel):
    account_id: str
    symbol: str
    quantity: Decimal
    average_cost: Decimal
    market_price: Decimal | None = None
    market_value: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    realized_pnl: Decimal | None = None
    currency: str = "USD"
    con_id: int | None = None

class OrderIntent(BrokerModel):
    client_order_id: str
    account_id: str
    symbol: str
    side: BrokerSide
    quantity: Decimal
    order_type: BrokerOrderType = BrokerOrderType.LIMIT
    limit_price: Decimal | None = None
    tif: str = "DAY"
    transmit: bool = True
    con_id: int | None = None
    currency: str = "USD"
    exchange: str = "SMART"

    @model_validator(mode="after")
    def validate_order(self):
        if self.quantity <= 0:
            raise ValueError("quantity must be > 0")
        if self.order_type == BrokerOrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price required for limit order")
        return self

class OrderExecutionState(BrokerModel):
    client_order_id: str
    broker_order_id: int | None = None
    perm_id: int | None = None
    status: str
    filled: Decimal = Decimal("0")
    remaining: Decimal | None = None
    avg_fill_price: Decimal | None = None
    last_fill_price: Decimal | None = None
    error: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReconciliationIssue(BrokerModel):
    kind: str
    symbol: str | None = None
    expected: Decimal | None = None
    actual: Decimal | None = None
    difference: Decimal | None = None
    detail: str

class ReconciliationResult(BrokerModel):
    ok: bool
    issues: list[ReconciliationIssue] = Field(default_factory=list)
