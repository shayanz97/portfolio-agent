from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from portfolio_agent.backtest.execution import ExecutionSimulator
from portfolio_agent.backtest.feed import HistoricalFeed
from portfolio_agent.backtest.metrics import BacktestMetricsEngine
from portfolio_agent.backtest.models import HistoricalPoint, SimOrder, SimSide
from portfolio_agent.backtest.portfolio import BacktestPortfolio
from portfolio_agent.config.models import RuntimeConfig


StrategyFn = Callable[[str, list[HistoricalPoint], BacktestPortfolio], str]


class BacktestEngine:
    """
    Minimal event-driven historical runner.

    The strategy callback sees history only up to the current timestamp.
    It returns one of: BUY / SELL / HOLD.
    """

    def __init__(self, config: RuntimeConfig, feed: HistoricalFeed):
        self.config = config
        self.feed = feed
        self.execution = ExecutionSimulator(config, feed)
        self.metrics_engine = BacktestMetricsEngine()

    def run_single_instrument(
        self,
        *,
        instrument: str,
        timeline: list[HistoricalPoint],
        strategy: StrategyFn,
        order_quantity: Decimal,
    ):
        portfolio = BacktestPortfolio(
            Decimal(str(self.config.backtest.capital.initial_cash))
        )

        for point in sorted(timeline, key=lambda x: x.timestamp):
            history = self.feed.history_until(instrument, point.timestamp)
            action = strategy(instrument, history, portfolio)

            if action in {"BUY", "SELL"}:
                order = SimOrder(
                    order_id=f"bt-{uuid4().hex[:10]}",
                    instrument=instrument,
                    side=SimSide(action),
                    quantity=order_quantity,
                    signal_time=point.timestamp,
                )
                fill = self.execution.execute(order)
                if fill is not None:
                    portfolio.apply_fill(fill)

            portfolio.mark_to_market(
                point.timestamp,
                {instrument: point.close},
            )

        metrics = self.metrics_engine.calculate(portfolio)
        return portfolio, metrics
