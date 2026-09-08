from decimal import Decimal
from pathlib import Path

from portfolio_agent.config.loader import load_config
from portfolio_agent.domain.enums import PositionState
from portfolio_agent.persistence.db import Base, create_session_factory
from portfolio_agent.persistence.runtime_repository import SqlAlchemyPositionRuntimeRepository
from portfolio_agent.runtime.circuit_breakers import ProductionCircuitBreaker
from portfolio_agent.runtime.models import PositionRuntimeState
from portfolio_agent.runtime.recovery import StartupRecoveryService
from portfolio_agent.runtime.service import PaperRuntimeService


def config():
    return load_config(Path(__file__).resolve().parents[1] / "config")


class ReconcileOK:
    def reconcile(self):
        return True


def test_runtime_repository_roundtrip(tmp_path):
    db = tmp_path / "test.db"
    engine, session_factory = create_session_factory(f"sqlite:///{db}")
    Base.metadata.create_all(engine)

    repo = SqlAlchemyPositionRuntimeRepository(session_factory)
    state = PositionRuntimeState(
        instrument="ELF",
        entry_price=Decimal("100"),
        quantity=Decimal("10"),
        current_price=Decimal("112"),
        high_water_mark_intraday=Decimal("125"),
        high_water_mark_close=Decimal("124"),
        low_water_mark_intraday=Decimal("95"),
        low_water_mark_close=Decimal("97"),
        max_unrealized_profit_pct=0.25,
        max_drawdown_pct=-0.05,
        lifecycle_state=PositionState.PROFIT_AT_RISK,
    )

    repo.save(state)
    loaded = repo.load_all()

    assert len(loaded) == 1
    assert loaded[0].instrument == "ELF"
    assert loaded[0].high_water_mark_intraday == Decimal("125.0")


def test_startup_recovery_restores_positions(tmp_path):
    db = tmp_path / "test.db"
    engine, session_factory = create_session_factory(f"sqlite:///{db}")
    Base.metadata.create_all(engine)

    repo = SqlAlchemyPositionRuntimeRepository(session_factory)
    state = PositionRuntimeState(
        instrument="LULU",
        entry_price=Decimal("300"),
        quantity=Decimal("4"),
        current_price=Decimal("220"),
        high_water_mark_intraday=Decimal("305"),
        high_water_mark_close=Decimal("300"),
        low_water_mark_intraday=Decimal("210"),
        low_water_mark_close=Decimal("215"),
        max_unrealized_profit_pct=0.016,
        max_drawdown_pct=-0.30,
        lifecycle_state=PositionState.DRAWDOWN_WATCH,
    )
    repo.save(state)

    runtime = PaperRuntimeService(config())
    recovery = StartupRecoveryService(
        config(),
        position_repository=repo,
        runtime_service=runtime,
        reconciliation_gateway=ReconcileOK(),
    )
    result = recovery.recover()

    assert result["ok"]
    assert "LULU" in runtime.positions


def test_production_circuit_breaker_trips():
    breaker = ProductionCircuitBreaker(config())
    for _ in range(config().production.circuit_breakers.max_consecutive_runtime_errors):
        breaker.record_runtime_error()

    ok, reasons = breaker.evaluate()

    assert not ok
    assert reasons
