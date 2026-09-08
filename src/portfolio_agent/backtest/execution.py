from __future__ import annotations

from decimal import Decimal

from portfolio_agent.backtest.feed import HistoricalFeed
from portfolio_agent.backtest.models import SimFill, SimOrder, SimSide
from portfolio_agent.config.models import RuntimeConfig


class ExecutionSimulator:
    def __init__(self, config: RuntimeConfig, feed: HistoricalFeed):
        self.config = config
        self.feed = feed

    def execute(self, order: SimOrder) -> SimFill | None:
        cfg = self.config.backtest.execution
        point = self.feed.next_point_after(
            order.instrument,
            order.signal_time,
            bars_ahead=max(1, cfg.latency_bars),
        )
        if point is None:
            return None

        raw = point.open
        side_sign = Decimal("1") if order.side == SimSide.BUY else Decimal("-1")

        spread = Decimal(str(cfg.spread_bps / 10000.0))
        slippage = Decimal(str(cfg.slippage_bps / 10000.0))

        fill_price = raw * (
            Decimal("1") + side_sign * (spread / Decimal("2") + slippage)
        )

        notional = fill_price * order.quantity
        commission = (
            Decimal(str(cfg.commission_fixed))
            + notional * Decimal(str(cfg.commission_pct))
        )

        slippage_cost = abs(fill_price - raw) * order.quantity

        return SimFill(
            order_id=order.order_id,
            instrument=order.instrument,
            side=order.side,
            quantity=order.quantity,
            fill_time=point.timestamp,
            raw_price=raw,
            fill_price=fill_price,
            commission=commission,
            slippage_cost=slippage_cost,
        )
