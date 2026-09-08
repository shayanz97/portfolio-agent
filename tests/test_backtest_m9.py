from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from portfolio_agent.backtest.engine import BacktestEngine
from portfolio_agent.backtest.event_study import EventStudyEngine
from portfolio_agent.backtest.feed import HistoricalFeed
from portfolio_agent.backtest.models import HistoricalPoint, SimOrder, SimSide
from portfolio_agent.backtest.execution import ExecutionSimulator
from portfolio_agent.config.loader import load_config


def config():
    return load_config(Path(__file__).resolve().parents[1] / "config")


def data(instrument="SPY", count=120, step=1.0):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    out = []
    for i in range(count):
        price = Decimal(str(100 + i * step))
        out.append(HistoricalPoint(
            instrument=instrument,
            timestamp=start + timedelta(minutes=i),
            open=price,
            high=price + Decimal("0.5"),
            low=price - Decimal("0.5"),
            close=price,
        ))
    return out


def test_history_until_prevents_future_visibility():
    series = data(count=20)
    feed = HistoricalFeed(series)
    cutoff = series[5].timestamp
    history = feed.history_until("SPY", cutoff)
    assert len(history) == 6
    assert all(x.timestamp <= cutoff for x in history)


def test_execution_applies_latency_and_costs():
    series = data(count=20)
    feed = HistoricalFeed(series)
    sim = ExecutionSimulator(config(), feed)

    order = SimOrder(
        order_id="o1",
        instrument="SPY",
        side=SimSide.BUY,
        quantity=Decimal("10"),
        signal_time=series[5].timestamp,
    )
    fill = sim.execute(order)
    assert fill is not None
    assert fill.fill_time > order.signal_time
    assert fill.fill_price > fill.raw_price
    assert fill.commission > 0
    assert fill.slippage_cost > 0


def test_backtest_engine_generates_metrics():
    cfg = config()
    series = data(count=80, step=0.5)
    feed = HistoricalFeed(series)
    engine = BacktestEngine(cfg, feed)

    def strategy(instrument, history, portfolio):
        if len(history) == 5 and portfolio.positions[instrument] == 0:
            return "BUY"
        if len(history) == 60 and portfolio.positions[instrument] > 0:
            return "SELL"
        return "HOLD"

    portfolio, metrics = engine.run_single_instrument(
        instrument="SPY",
        timeline=series,
        strategy=strategy,
        order_quantity=Decimal("10"),
    )

    assert metrics.trade_count == 1
    assert metrics.final_equity > metrics.initial_equity
    assert metrics.total_commission > 0


def test_event_study_returns_expected_positive_move():
    series = data(instrument="BTC", count=200, step=0.2)
    feed = HistoricalFeed(series)
    study = EventStudyEngine(feed)

    event_time = series[20].timestamp
    outcomes = study.evaluate_event(
        event_id="event-1",
        event_time=event_time,
        instrument="BTC",
        horizons_minutes=[15, 60],
    )

    assert len(outcomes) == 2
    assert all(x.return_pct is not None for x in outcomes)
    assert all(x.return_pct > 0 for x in outcomes)


def test_event_study_summary_requires_minimum_events():
    series = data(instrument="BTC", count=200, step=0.2)
    feed = HistoricalFeed(series)
    study = EventStudyEngine(feed)

    outcomes = []
    for i in [20, 40]:
        outcomes.extend(
            study.evaluate_event(
                event_id=f"e-{i}",
                event_time=series[i].timestamp,
                instrument="BTC",
                horizons_minutes=[15],
            )
        )

    summary = study.summarize(outcomes, minimum_events=3)
    assert summary[0].event_count == 2
    assert summary[0].average_return_pct is None
