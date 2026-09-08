from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from portfolio_agent.config.loader import load_config
from portfolio_agent.domain.enums import DataQuality
from portfolio_agent.market_data.models import RawQuote
from portfolio_agent.market_data.quality import MarketDataQualityChecker


def _config():
    root = Path(__file__).resolve().parents[1]
    return load_config(root / "config")


def test_stale_quote_is_detected():
    config = _config()
    checker = MarketDataQualityChecker(config)
    now = datetime.now(timezone.utc)

    raw = RawQuote(
        instrument="BTC",
        provider="test",
        timestamp=now - timedelta(seconds=120),
        last=Decimal("50000"),
    )

    quality, delay, _ = checker.evaluate(raw, config.assets["BTC"], now)

    assert quality == DataQuality.STALE
    assert delay >= 120


def test_future_quote_is_detected():
    config = _config()
    checker = MarketDataQualityChecker(config)
    now = datetime.now(timezone.utc)

    raw = RawQuote(
        instrument="BTC",
        provider="test",
        timestamp=now + timedelta(seconds=30),
        last=Decimal("50000"),
    )

    quality, _, _ = checker.evaluate(raw, config.assets["BTC"], now)
    assert quality == DataQuality.FUTURE_TIMESTAMP


def test_wide_spread_is_detected():
    config = _config()
    checker = MarketDataQualityChecker(config)
    now = datetime.now(timezone.utc)

    raw = RawQuote(
        instrument="BTC",
        provider="test",
        timestamp=now,
        last=Decimal("100"),
        bid=Decimal("90"),
        ask=Decimal("110"),
    )

    quality, _, spread = checker.evaluate(raw, config.assets["BTC"], now)

    assert quality == DataQuality.WIDE_SPREAD
    assert spread is not None and spread > 0.05
