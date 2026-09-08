from decimal import Decimal
from pathlib import Path

from portfolio_agent.config.loader import load_config
from portfolio_agent.market_data.providers.mock import MockMarketDataProvider
from portfolio_agent.market_data.service import MarketDataService


def _config():
    root = Path(__file__).resolve().parents[1]
    return load_config(root / "config")


def test_market_snapshot_from_mock_provider():
    config = _config()
    provider = MockMarketDataProvider(
        {
            "BTC": Decimal("60000"),
            "WTI": Decimal("95"),
            "SPY": Decimal("500"),
        }
    )
    service = MarketDataService(config, [provider])

    snapshot = service.fetch_snapshot(["BTC", "WTI", "SPY"])

    assert snapshot.is_complete
    assert set(snapshot.quotes) == {"BTC", "WTI", "SPY"}
    assert snapshot.quotes["BTC"].provider == "mock"


def test_missing_instrument_is_reported():
    config = _config()
    provider = MockMarketDataProvider({"BTC": Decimal("60000")})
    service = MarketDataService(config, [provider])

    snapshot = service.fetch_snapshot(["BTC", "WTI"])

    assert "WTI" in snapshot.missing_instruments
