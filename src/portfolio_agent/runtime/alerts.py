from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.domain.enums import PositionState
from portfolio_agent.runtime.models import AlertEvent, AlertSeverity
from portfolio_agent.strategy.models import PositionLifecycleDecision


SEVERITY_ORDER = {
    AlertSeverity.INFO: 0,
    AlertSeverity.WATCH: 1,
    AlertSeverity.IMPORTANT: 2,
    AlertSeverity.CRITICAL: 3,
}


class PositionAlertEngine:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def from_decision(self, decision: PositionLifecycleDecision) -> AlertEvent | None:
        if not self.config.runtime.alerts.enabled:
            return None

        if decision.state.value not in self.config.runtime.alerts.notify_on_states:
            return None

        severity = self._severity(decision)

        minimum = AlertSeverity(self.config.runtime.alerts.minimum_severity)
        if SEVERITY_ORDER[severity] < SEVERITY_ORDER[minimum]:
            return None

        title = f"{decision.instrument}: {decision.state.value}"
        message = (
            f"Action={decision.action.value}; "
            f"profit={decision.profit_pct:.1%}; "
            f"peak={decision.peak_profit_pct:.1%}; "
            f"giveback={decision.giveback_pct:.1%}. "
            f"{decision.explanation}"
        )

        return AlertEvent(
            alert_id=f"alert-{uuid4().hex[:12]}",
            instrument=decision.instrument,
            severity=severity,
            state=decision.state,
            title=title,
            message=message,
            dedup_key=f"{decision.instrument}:{decision.state.value}",
        )

    def _severity(self, decision: PositionLifecycleDecision) -> AlertSeverity:
        if decision.state in {PositionState.THESIS_BROKEN, PositionState.EXIT_CANDIDATE}:
            return AlertSeverity.CRITICAL
        if decision.state in {
            PositionState.PROFIT_AT_RISK,
            PositionState.THESIS_WEAKENING,
            PositionState.RECOVERY_CONFIRMED,
        }:
            return AlertSeverity.IMPORTANT
        if decision.state in {PositionState.RECOVERY_WATCH, PositionState.DRAWDOWN_WATCH}:
            return AlertSeverity.WATCH
        return AlertSeverity.INFO
