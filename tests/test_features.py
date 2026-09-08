from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from portfolio_agent.config.loader import load_config
from portfolio_agent.features.calculations import atr, rolling_correlation, return_over_window
from portfolio_agent.features.engine import QuantFeatureEngine
from portfolio_agent.features.models import MarketBar


def config():
    return load_config(Path(__file__).resolve().parents[1] / "config")


def bars(name="X", count=300, start=100.0, step=0.1):
    t0 = datetime(2026, 9, 8, tzinfo=timezone.utc)
    out = []
    for i in range(count):
        p = start + step * i
        out.append(MarketBar(
            instrument=name,
            timestamp=t0 + timedelta(minutes=i),
            open=Decimal(str(p - 0.02)),
            high=Decimal(str(p + 0.10)),
            low=Decimal(str(p - 0.10)),
            close=Decimal(str(p)),
            volume=Decimal("1000"),
            source="test",
        ))
    return out


def test_returns_and_atr():
    series = bars(count=61, start=100, step=1)
    assert round(return_over_window(series, "1h"), 6) == 0.6
    assert atr(series, 14) > 0


def test_feature_engine():
    result = QuantFeatureEngine(config()).calculate("BTC", bars("BTC"))
    assert "1h" in result.returns
    assert result.atr is not None
    assert result.realized_volatility is not None
    assert result.momentum_score > 0


def test_correlation():
    a = bars("A", count=100, start=100, step=1)
    b = bars("B", count=100, start=200, step=2)
    corr = rolling_correlation(a, b, 30, 20)
    assert corr is not None
    assert corr > 0.99
