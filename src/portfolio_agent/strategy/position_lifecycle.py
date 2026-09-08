from __future__ import annotations

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.domain.enums import AssetSignal, PositionState
from portfolio_agent.strategy.models import (
    PositionLifecycleDecision,
    PositionLifecycleInput,
)


class PositionLifecycleEngine:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def assess(self, item: PositionLifecycleInput) -> PositionLifecycleDecision:
        entry = float(item.entry_price)
        current = float(item.current_price)
        peak = max(float(item.high_water_mark_close), float(item.high_water_mark_intraday))

        profit_pct = current / entry - 1.0
        peak_profit_pct = peak / entry - 1.0

        giveback_pct = 0.0
        if peak_profit_pct > 0:
            giveback_pct = max(0.0, (peak_profit_pct - profit_pct) / peak_profit_pct)

        pm = self.config.position_management

        # Thesis invalidation takes precedence.
        if item.thesis and item.thesis.invalidated:
            return self._decision(
                item, PositionState.THESIS_BROKEN, AssetSignal.EXIT,
                profit_pct, peak_profit_pct, giveback_pct, 100.0,
                "Investment thesis invalidated."
            )

        thesis_score = item.thesis.score if item.thesis else None
        if thesis_score is not None and thesis_score < pm.thesis.weakening_threshold:
            return self._decision(
                item, PositionState.THESIS_WEAKENING, AssetSignal.REDUCE,
                profit_pct, peak_profit_pct, giveback_pct, 80.0,
                "Thesis score below weakening threshold."
            )

        # Profit protection.
        pp = pm.profit_protection
        if pp.enabled and peak_profit_pct >= pp.activate_after_profit_pct:
            atr_multiple = 0.0
            if item.atr and item.atr > 0:
                atr_multiple = (peak - current) / item.atr

            profit_risk = min(
                100.0,
                50.0 * min(1.0, giveback_pct / max(pp.max_profit_giveback_pct, 1e-9))
                + 50.0 * min(1.0, atr_multiple / pp.atr_warning_multiple),
            )

            if (
                giveback_pct >= pp.max_profit_giveback_pct
                and atr_multiple >= pp.atr_warning_multiple
            ):
                return self._decision(
                    item, PositionState.PROFIT_AT_RISK, AssetSignal.REDUCE,
                    profit_pct, peak_profit_pct, giveback_pct, profit_risk,
                    "Peak-profit giveback and ATR drawdown both breached."
                )

            return self._decision(
                item, PositionState.PROFIT_PROTECTION, AssetSignal.HOLD,
                profit_pct, peak_profit_pct, giveback_pct, profit_risk,
                "Profit protection active; no confirmed exit yet."
            )

        # Drawdown / recovery logic.
        if profit_pct < 0:
            recovery = item.recovery_score
            if (
                recovery is not None
                and recovery >= pm.recovery.minimum_score_to_add
                and (not pm.averaging_down.require_thesis_intact or (thesis_score is None or thesis_score >= pm.thesis.healthy_threshold))
                and item.add_events < pm.averaging_down.max_add_events
                and item.current_weight < pm.averaging_down.max_position_weight_after_add
            ):
                return self._decision(
                    item, PositionState.RECOVERY_CONFIRMED, AssetSignal.BUY,
                    profit_pct, peak_profit_pct, giveback_pct, 25.0,
                    "Recovery score high enough for controlled add candidate."
                )

            if recovery is not None and recovery >= pm.recovery.minimum_score_to_watch:
                return self._decision(
                    item, PositionState.RECOVERY_WATCH, AssetSignal.HOLD,
                    profit_pct, peak_profit_pct, giveback_pct, 40.0,
                    "Recovery conditions improving, but add threshold not met."
                )

            return self._decision(
                item, PositionState.DRAWDOWN_WATCH, AssetSignal.HOLD,
                profit_pct, peak_profit_pct, giveback_pct, 50.0,
                "Position is below entry; no qualified recovery signal."
            )

        return self._decision(
            item, PositionState.HEALTHY, AssetSignal.HOLD,
            profit_pct, peak_profit_pct, giveback_pct, 10.0,
            "Position healthy."
        )

    def _decision(self, item, state, action, profit_pct, peak_profit_pct, giveback_pct, risk, explanation):
        return PositionLifecycleDecision(
            instrument=item.instrument,
            state=state,
            action=action,
            profit_pct=profit_pct,
            peak_profit_pct=peak_profit_pct,
            giveback_pct=giveback_pct,
            profit_risk_score=risk,
            recovery_score=item.recovery_score,
            explanation=explanation,
        )
