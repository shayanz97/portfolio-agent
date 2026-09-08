from datetime import datetime, timezone
from pathlib import Path

from portfolio_agent.config.loader import load_config
from portfolio_agent.domain.enums import MarketStatus
from portfolio_agent.market_data.clock import MarketClock


def _config():
    root = Path(__file__).resolve().parents[1]
    return load_config(root / "config")


def test_crypto_is_always_open():
    config = _config()
    clock = MarketClock(config)
    at = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)  # Sunday

    assert clock.status_for(config.assets["BTC"], at) == MarketStatus.OPEN


def test_us_equity_closed_on_weekend():
    config = _config()
    clock = MarketClock(config)
    at = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)  # Sunday

    assert clock.status_for(config.assets["SPY"], at) == MarketStatus.CLOSED
