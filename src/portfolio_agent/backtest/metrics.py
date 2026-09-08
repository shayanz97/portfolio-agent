from __future__ import annotations

from decimal import Decimal

from portfolio_agent.backtest.models import BacktestMetrics
from portfolio_agent.backtest.portfolio import BacktestPortfolio


class BacktestMetricsEngine:
    def calculate(self, portfolio: BacktestPortfolio) -> BacktestMetrics:
        if not portfolio.equity_curve:
            final_equity = portfolio.cash
        else:
            final_equity = portfolio.equity_curve[-1].equity

        total_return_pct = float(final_equity / portfolio.initial_cash - 1)

        peak = portfolio.initial_cash
        max_drawdown = 0.0
        for point in portfolio.equity_curve:
            if point.equity > peak:
                peak = point.equity
            if peak > 0:
                dd = float(point.equity / peak - 1)
                max_drawdown = min(max_drawdown, dd)

        trades = portfolio.closed_trades
        wins = [t for t in trades if (t.net_pnl or Decimal("0")) > 0]
        losses = [t for t in trades if (t.net_pnl or Decimal("0")) < 0]

        gross_profit = sum((t.net_pnl or Decimal("0")) for t in wins)
        gross_loss_abs = abs(sum((t.net_pnl or Decimal("0")) for t in losses))

        profit_factor = (
            float(gross_profit / gross_loss_abs)
            if gross_loss_abs > 0 else None
        )

        return BacktestMetrics(
            initial_equity=portfolio.initial_cash,
            final_equity=final_equity,
            total_return_pct=total_return_pct,
            max_drawdown_pct=max_drawdown,
            trade_count=len(trades),
            win_rate=(len(wins) / len(trades)) if trades else 0.0,
            gross_profit=gross_profit,
            gross_loss=gross_loss_abs,
            profit_factor=profit_factor,
            total_commission=portfolio.total_commission,
            total_slippage=portfolio.total_slippage,
        )
