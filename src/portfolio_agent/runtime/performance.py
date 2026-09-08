from __future__ import annotations

from decimal import Decimal

from portfolio_agent.runtime.models import PerformanceSnapshot


class PerformanceEngine:
    def calculate(
        self,
        *,
        run_id: str,
        starting_portfolio_value: Decimal,
        current_portfolio_value: Decimal,
        realized_pnl: Decimal,
        unrealized_pnl: Decimal,
        trade_pnls: list[Decimal],
    ) -> PerformanceSnapshot:
        total_pnl = realized_pnl + unrealized_pnl
        return_pct = (
            float(current_portfolio_value / starting_portfolio_value - 1)
            if starting_portfolio_value > 0
            else 0.0
        )

        wins = sum(1 for x in trade_pnls if x > 0)
        losses = sum(1 for x in trade_pnls if x < 0)
        trade_count = len(trade_pnls)
        win_rate = wins / trade_count if trade_count else 0.0

        # Runtime MVP: drawdown derived from current portfolio vs start.
        # Historical peak-based drawdown comes in backtest/performance history.
        max_drawdown_pct = min(0.0, return_pct)

        return PerformanceSnapshot(
            run_id=run_id,
            portfolio_value=current_portfolio_value,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_pnl=total_pnl,
            return_pct=return_pct,
            max_drawdown_pct=max_drawdown_pct,
            trade_count=trade_count,
            win_count=wins,
            loss_count=losses,
            win_rate=win_rate,
        )
