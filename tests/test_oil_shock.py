from datetime import datetime, timezone
from pathlib import Path

from portfolio_agent.config.loader import load_config
from portfolio_agent.events.oil_shock import OilShockDetector
from portfolio_agent.features.models import FeatureSet


def config():
    return load_config(Path(__file__).resolve().parents[1] / "config")


def feature(name, r1, r4, z):
    return FeatureSet(
        instrument=name,
        as_of=datetime(2026, 9, 8, 12, tzinfo=timezone.utc),
        returns={"1h": r1, "4h": r4},
        atr=2.0,
        realized_volatility=0.4,
        return_zscore=z,
        momentum_score=0.5,
        sample_size=100,
    )


def test_confirmed_oil_shock():
    event = OilShockDetector(config()).detect(
        feature("WTI", 0.04, 0.07, 3.4),
        feature("BRENT", 0.038, 0.065, 3.2),
    )
    assert event is not None
    assert event.direction == "UP"
    assert event.score >= 50
    assert event.confirmation_score >= 0.6


def test_conflicting_oil_move_is_rejected():
    event = OilShockDetector(config()).detect(
        feature("WTI", 0.04, 0.07, 3.4),
        feature("BRENT", -0.04, -0.06, -3.2),
    )
    assert event is None
