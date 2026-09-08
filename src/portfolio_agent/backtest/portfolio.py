from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from portfolio_agent.backtest.models import (
    BacktestTrade,
    EquityPoint,
    SimFill,
    SimSide,
)


class BacktestPortfolio:
    def __init__(self, initial_cash: Decimal):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        self.avg_cost: dict[str, Decimal] = {}
        self.open_trades: dict[str, BacktestTrade] = {}
        self.closed_trades: list[BacktestTrade] = []
        self.total_commission = Decimal("0")
        self.total_slippage = Decimal("0")
        self.equity_curve: list[EquityPoint] = []

    def apply_fill(self, fill: SimFill) -> None:
        self.total_commission += fill.commission
        self.total_slippage += fill.slippage_cost

        signed_qty = fill.quantity if fill.side == SimSide.BUY else -fill.quantity
        notional = fill.fill_price * fill.quantity

        if fill.side == SimSide.BUY:
            self.cash -= notional + fill.commission
            current_qty = self.positions[fill.instrument]
            new_qty = current_qty + fill.quantity

            if current_qty <= 0:
                new_avg = fill.fill_price
            else:
                old_cost = self.avg_cost[fill.instrument] * current_qty
                new_avg = (old_cost + notional) / new_qty

            self.positions[fill.instrument] = new_qty
            self.avg_cost[fill.instrument] = new_avg

            if fill.instrument not in self.open_trades:
                self.open_trades[fill.instrument] = BacktestTrade(
                    instrument=fill.instrument,
                    entry_time=fill.fill_time,
                    quantity=fill.quantity,
                    entry_price=fill.fill_price,
                )
        else:
            current_qty = self.positions[fill.instrument]
            sell_qty = min(fill.quantity, current_qty)
            self.cash += fill.fill_price * sell_qty - fill.commission
            self.positions[fill.instrument] = current_qty - sell_qty

            trade = self.open_trades.get(fill.instrument)
            if trade and self.positions[fill.instrument] == 0:
                gross = (fill.fill_price - trade.entry_price) * trade.quantity
                net = gross - fill.commission
                closed = trade.model_copy(update={
                    "exit_time": fill.fill_time,
                    "exit_price": fill.fill_price,
                    "gross_pnl": gross,
                    "net_pnl": net,
                })
                self.closed_trades.append(closed)
                del self.open_trades[fill.instrument]

    def mark_to_market(
        self,
        timestamp: datetime,
        prices: dict[str, Decimal],
    ) -> Decimal:
        value = self.cash
        for instrument, qty in self.positions.items():
            if qty == 0:
                continue
            price = prices.get(instrument)
            if price is not None:
                value += qty * price

        self.equity_curve.append(
            EquityPoint(timestamp=timestamp, equity=value, cash=self.cash)
        )
        return value
