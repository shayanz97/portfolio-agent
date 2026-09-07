from pathlib import Path

from portfolio_agent.config.loader import config_hash, load_config


def test_default_config_loads():
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "config")

    assert config.environment == "paper"
    assert config.execution.broker == "ibkr"
    assert config.signal_weights.macro == 0.25
    assert abs(sum(config.signal_weights.model_dump().values()) - 1.0) < 1e-9


def test_config_hash_is_stable():
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "config")

    assert config_hash(config) == config_hash(config)


def test_take_profit_sums_to_one():
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "config")

    total = (
        config.take_profit.tp1.close_pct
        + config.take_profit.tp2.close_pct
        + config.take_profit.trailing.remaining_pct
    )
    assert total == 1.0
