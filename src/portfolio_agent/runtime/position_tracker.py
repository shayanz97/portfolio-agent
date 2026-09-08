from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from portfolio_agent.domain.enums import PositionState
from portfolio_agent.runtime.models import PositionRuntimeState


class PositionTracker:
    def initialize(
        self,
        *,
        instrument: str,
        entry_price: Decimal,
        quantity: Decimal,
        current_price: Decimal,
        lifecycle_state: PositionState = PositionState.NEW,
    ) -> PositionRuntimeState:
        profit_pct = float(current_price / entry_price - 1) if entry_price > 0 else 0.0

        return PositionRuntimeState(
            instrument=instrument,
            entry_price=entry_price,
            quantity=quantity,
            current_price=current_price,
            high_water_mark_intraday=current_price,
            high_water_mark_close=current_price,
            low_water_mark_intraday=current_price,
            low_water_mark_close=current_price,
            max_unrealized_profit_pct=max(0.0, profit_pct),
            max_drawdown_pct=min(0.0, profit_pct),
            lifecycle_state=lifecycle_state,
        )

    def update(
        self,
        state: PositionRuntimeState,
        *,
        current_price: Decimal,
        intraday_high: Decimal | None = None,
        intraday_low: Decimal | None = None,
        close_price: Decimal | None = None,
        lifecycle_state: PositionState | None = None,
    ) -> PositionRuntimeState:
        high_intraday = max(
            state.high_water_mark_intraday,
            intraday_high or current_price,
        )
        low_intraday = min(
            state.low_water_mark_intraday,
            intraday_low or current_price,
        )

        high_close = state.high_water_mark_close
        low_close = state.low_water_mark_close
        if close_price is not None:
            high_close = max(high_close, close_price)
            low_close = min(low_close, close_price)

        current_profit = (
            float(current_price / state.entry_price - 1)
            if state.entry_price > 0 else 0.0
        )

        max_profit = max(state.max_unrealized_profit_pct, current_profit)
        max_drawdown = min(state.max_drawdown_pct, current_profit)

        return state.model_copy(update={
            "current_price": current_price,
            "high_water_mark_intraday": high_intraday,
            "high_water_mark_close": high_close,
            "low_water_mark_intraday": low_intraday,
            "low_water_mark_close": low_close,
            "max_unrealized_profit_pct": max_profit,
            "max_drawdown_pct": max_drawdown,
            "lifecycle_state": lifecycle_state or state.lifecycle_state,
            "updated_at": datetime.now(timezone.utc),
        })
