from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from portfolio_agent.backtest.engine import BacktestEngine
from portfolio_agent.backtest.feed import HistoricalFeed
from portfolio_agent.backtest.models import HistoricalPoint
from portfolio_agent.config.loader import load_config


def make_data():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = []
    for i in range(120):
        price = Decimal(str(100 + i * 0.3))
        result.append(
            HistoricalPoint(
                instrument="SPY",
                timestamp=start + timedelta(minutes=i),
                open=price,
                high=price + Decimal("0.2"),
                low=price - Decimal("0.2"),
                close=price,
            )
        )
    return result


def strategy(instrument, history, portfolio):
    if len(history) == 10 and portfolio.positions[instrument] == 0:
        return "BUY"
    if len(history) == 100 and portfolio.positions[instrument] > 0:
        return "SELL"
    return "HOLD"


config = load_config(Path(__file__).resolve().parents[1] / "config")
data = make_data()
feed = HistoricalFeed(data)
engine = BacktestEngine(config, feed)

portfolio, metrics = engine.run_single_instrument(
    instrument="SPY",
    timeline=data,
    strategy=strategy,
    order_quantity=Decimal("10"),
)

print(metrics.model_dump())
