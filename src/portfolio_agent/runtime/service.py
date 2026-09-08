from __future__ import annotations

from decimal import Decimal

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.domain.enums import PositionState
from portfolio_agent.runtime.alert_registry import InMemoryAlertRegistry
from portfolio_agent.runtime.alerts import PositionAlertEngine
from portfolio_agent.runtime.models import PositionRuntimeState
from portfolio_agent.runtime.performance import PerformanceEngine
from portfolio_agent.runtime.position_tracker import PositionTracker
from portfolio_agent.strategy.models import PositionLifecycleDecision


class PaperRuntimeService:
    def __init__(
        self,
        config: RuntimeConfig,
        *,
        alert_registry: InMemoryAlertRegistry | None = None,
    ):
        self.config = config
        self.position_tracker = PositionTracker()
        self.alert_engine = PositionAlertEngine(config)
        self.alert_registry = alert_registry or InMemoryAlertRegistry()
        self.performance_engine = PerformanceEngine()
        self.positions: dict[str, PositionRuntimeState] = {}

    def upsert_position(
        self,
        *,
        instrument: str,
        entry_price: Decimal,
        quantity: Decimal,
        current_price: Decimal,
        intraday_high: Decimal | None = None,
        intraday_low: Decimal | None = None,
        close_price: Decimal | None = None,
        lifecycle_state: PositionState | None = None,
    ) -> PositionRuntimeState:
        existing = self.positions.get(instrument)

        if existing is None:
            state = self.position_tracker.initialize(
                instrument=instrument,
                entry_price=entry_price,
                quantity=quantity,
                current_price=current_price,
                lifecycle_state=lifecycle_state or PositionState.NEW,
            )
        else:
            state = self.position_tracker.update(
                existing,
                current_price=current_price,
                intraday_high=intraday_high,
                intraday_low=intraday_low,
                close_price=close_price,
                lifecycle_state=lifecycle_state,
            )

        self.positions[instrument] = state
        return state

    def process_lifecycle_decision(
        self,
        decision: PositionLifecycleDecision,
    ):
        alert = self.alert_engine.from_decision(decision)
        if alert is None:
            return None

        if self.alert_registry.should_send(
            alert,
            self.config.runtime.alerts.cooldown_minutes,
        ):
            self.alert_registry.record(alert)
            return alert

        return None

    def calculate_performance(
        self,
        *,
        run_id: str,
        starting_portfolio_value: Decimal,
        current_portfolio_value: Decimal,
        realized_pnl: Decimal,
        unrealized_pnl: Decimal,
        trade_pnls: list[Decimal],
    ):
        return self.performance_engine.calculate(
            run_id=run_id,
            starting_portfolio_value=starting_portfolio_value,
            current_portfolio_value=current_portfolio_value,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            trade_pnls=trade_pnls,
        )
