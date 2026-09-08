from decimal import Decimal
from pathlib import Path

from portfolio_agent.config.loader import load_config
from portfolio_agent.domain.enums import AssetSignal, PositionState
from portfolio_agent.runtime.alert_registry import InMemoryAlertRegistry
from portfolio_agent.runtime.service import PaperRuntimeService
from portfolio_agent.strategy.models import PositionLifecycleDecision


def config():
    return load_config(Path(__file__).resolve().parents[1] / "config")


def test_position_high_water_marks_are_persisted_in_memory():
    runtime = PaperRuntimeService(config())

    first = runtime.upsert_position(
        instrument="ELF",
        entry_price=Decimal("100"),
        quantity=Decimal("10"),
        current_price=Decimal("110"),
        intraday_high=Decimal("112"),
        intraday_low=Decimal("108"),
        close_price=Decimal("110"),
    )

    second = runtime.upsert_position(
        instrument="ELF",
        entry_price=Decimal("100"),
        quantity=Decimal("10"),
        current_price=Decimal("105"),
        intraday_high=Decimal("109"),
        intraday_low=Decimal("103"),
        close_price=Decimal("105"),
    )

    assert second.high_water_mark_intraday >= Decimal("110")
    assert second.high_water_mark_close == Decimal("110")
    assert second.low_water_mark_intraday <= Decimal("105")
    assert second.max_unrealized_profit_pct >= 0.10


def test_profit_at_risk_generates_alert():
    runtime = PaperRuntimeService(config(), alert_registry=InMemoryAlertRegistry())

    decision = PositionLifecycleDecision(
        instrument="ELF",
        state=PositionState.PROFIT_AT_RISK,
        action=AssetSignal.REDUCE,
        profit_pct=0.12,
        peak_profit_pct=0.25,
        giveback_pct=0.52,
        profit_risk_score=90,
        explanation="Peak profit lost materially.",
    )

    alert = runtime.process_lifecycle_decision(decision)

    assert alert is not None
    assert alert.severity.value == "IMPORTANT"


def test_alert_cooldown_prevents_duplicate():
    registry = InMemoryAlertRegistry()
    runtime = PaperRuntimeService(config(), alert_registry=registry)

    decision = PositionLifecycleDecision(
        instrument="ELF",
        state=PositionState.PROFIT_AT_RISK,
        action=AssetSignal.REDUCE,
        profit_pct=0.12,
        peak_profit_pct=0.25,
        giveback_pct=0.52,
        profit_risk_score=90,
        explanation="Peak profit lost materially.",
    )

    first = runtime.process_lifecycle_decision(decision)
    second = runtime.process_lifecycle_decision(decision)

    assert first is not None
    assert second is None
    assert len(registry.sent) == 1


def test_performance_metrics():
    runtime = PaperRuntimeService(config())

    result = runtime.calculate_performance(
        run_id="run-1",
        starting_portfolio_value=Decimal("100000"),
        current_portfolio_value=Decimal("105000"),
        realized_pnl=Decimal("3000"),
        unrealized_pnl=Decimal("2000"),
        trade_pnls=[Decimal("1000"), Decimal("-500"), Decimal("800")],
    )

    assert result.total_pnl == Decimal("5000")
    assert round(result.return_pct, 4) == 0.05
    assert result.trade_count == 3
    assert result.win_count == 2
    assert round(result.win_rate, 4) == round(2 / 3, 4)
