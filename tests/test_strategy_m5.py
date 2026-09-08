from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from portfolio_agent.config.loader import load_config
from portfolio_agent.domain.enums import AssetSignal, MarketRegime, PositionState
from portfolio_agent.events.models import OilShockEvent
from portfolio_agent.features.models import FeatureSet
from portfolio_agent.strategy.models import PositionLifecycleInput, PositionType, ThesisSnapshot
from portfolio_agent.strategy.portfolio import PortfolioTargetEngine
from portfolio_agent.strategy.position_lifecycle import PositionLifecycleEngine
from portfolio_agent.strategy.regime import MarketRegimeEngine
from portfolio_agent.strategy.risk import DeterministicRiskEngine
from portfolio_agent.strategy.trade_builder import TradeProposalBuilder


def config():
    return load_config(Path(__file__).resolve().parents[1] / "config")


def feature(name, r4):
    return FeatureSet(
        instrument=name,
        as_of=datetime(2026, 9, 8, 12, tzinfo=timezone.utc),
        returns={"4h": r4},
        atr=2.0,
        realized_volatility=0.2,
        return_zscore=1.0,
        momentum_score=0.1,
        sample_size=100,
    )


def test_regime_detects_risk_off_or_inflation_shock():
    event = OilShockEvent(
        detected_at=datetime(2026, 9, 8, 12, tzinfo=timezone.utc),
        severity="HIGH",
        score=80,
        direction="UP",
        confirmation_score=0.9,
        explanation="test",
    )
    assessment = MarketRegimeEngine(config()).assess(
        equities=feature("QQQ", -0.04),
        crypto=feature("BTC", -0.05),
        vix=feature("VIX", 0.05),
        dxy=feature("DXY", 0.02),
        yields=feature("US10Y", 0.02),
        oil_event=event,
    )
    assert assessment.regime in {MarketRegime.RISK_OFF, MarketRegime.INFLATION_SHOCK, MarketRegime.CRISIS}


def test_profit_at_risk_reduces_position():
    engine = PositionLifecycleEngine(config())
    item = PositionLifecycleInput(
        instrument="ELF",
        position_type=PositionType.MOMENTUM,
        entry_price=Decimal("100"),
        current_price=Decimal("112"),
        high_water_mark_intraday=Decimal("125"),
        high_water_mark_close=Decimal("124"),
        atr=4.0,
        momentum_score=-0.2,
        thesis=ThesisSnapshot(score=80, invalidated=False),
        recovery_score=None,
        current_weight=0.08,
        add_events=0,
    )
    result = engine.assess(item)
    assert result.state == PositionState.PROFIT_AT_RISK
    assert result.action == AssetSignal.REDUCE


def test_recovery_candidate_can_buy():
    engine = PositionLifecycleEngine(config())
    item = PositionLifecycleInput(
        instrument="LULU",
        position_type=PositionType.RECOVERY,
        entry_price=Decimal("300"),
        current_price=Decimal("220"),
        high_water_mark_intraday=Decimal("305"),
        high_water_mark_close=Decimal("300"),
        atr=8.0,
        momentum_score=0.2,
        thesis=ThesisSnapshot(score=82, invalidated=False),
        recovery_score=82,
        current_weight=0.05,
        add_events=0,
    )
    result = engine.assess(item)
    assert result.state == PositionState.RECOVERY_CONFIRMED
    assert result.action == AssetSignal.BUY


def test_portfolio_rebalance_respects_per_run_limit():
    engine = PortfolioTargetEngine(config())
    target = engine.target_for_regime(MarketRegime.CRISIS)
    instructions = engine.rebalance(
        {"equity": 0.60, "crypto": 0.20, "precious_metal": 0.05, "energy": 0.05, "cash": 0.10},
        target,
    )
    assert instructions
    assert all(abs(x.delta_weight) <= config().portfolio.max_rebalance_per_run + 1e-9 for x in instructions)


def test_risk_engine_and_trade_builder():
    risk = DeterministicRiskEngine(config()).evaluate_long(
        portfolio_value=Decimal("100000"),
        entry_price=Decimal("500"),
        atr=10.0,
        current_open_risk=0.01,
        current_position_weight=0.05,
    )
    assert risk.approved
    assert risk.stop_loss < Decimal("500")
    assert risk.take_profit_2 > Decimal("500")

    proposal = TradeProposalBuilder().build_long(
        run_id="run123",
        instrument="SPY",
        entry_price=Decimal("500"),
        risk=risk,
    )
    assert proposal.side == "BUY"
    assert proposal.quantity > 0
