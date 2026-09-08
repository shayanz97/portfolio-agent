from __future__ import annotations

from decimal import Decimal, ROUND_DOWN

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.strategy.models import RiskCheckResult


class DeterministicRiskEngine:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def evaluate_long(
        self,
        *,
        portfolio_value: Decimal,
        entry_price: Decimal,
        atr: float,
        current_open_risk: float = 0.0,
        current_position_weight: float = 0.0,
    ) -> RiskCheckResult:
        reasons = []

        if portfolio_value <= 0 or entry_price <= 0 or atr <= 0:
            return RiskCheckResult(approved=False, reasons=["invalid inputs"])

        risk_cfg = self.config.trade_risk
        stop_cfg = self.config.stop_loss

        if current_open_risk >= risk_cfg.max_total_open_risk:
            reasons.append("max total open risk reached")

        if current_position_weight >= self.config.portfolio.max_single_asset_weight:
            reasons.append("max single-asset weight reached")

        atr_stop_distance = Decimal(str(atr * stop_cfg.atr_multiplier))
        max_loss_distance = entry_price * Decimal(str(stop_cfg.maximum_loss_pct))
        stop_distance = min(atr_stop_distance, max_loss_distance)

        if stop_distance <= 0:
            reasons.append("non-positive stop distance")
            return RiskCheckResult(approved=False, reasons=reasons)

        risk_amount = portfolio_value * Decimal(str(risk_cfg.max_risk_per_trade))
        size = (risk_amount / stop_distance).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)

        stop_loss = entry_price - stop_distance
        tp1 = entry_price + stop_distance * Decimal(str(self.config.take_profit.tp1.r_multiple))
        tp2 = entry_price + stop_distance * Decimal(str(self.config.take_profit.tp2.r_multiple))

        rr = float((tp2 - entry_price) / stop_distance)
        if rr < risk_cfg.minimum_risk_reward:
            reasons.append("minimum risk/reward not satisfied")

        max_notional = portfolio_value * Decimal(str(self.config.portfolio.max_single_asset_weight))
        if size * entry_price > max_notional:
            size = (max_notional / entry_price).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)

        approved = not reasons and size > 0

        return RiskCheckResult(
            approved=approved,
            reasons=reasons,
            risk_amount=risk_amount,
            position_size=size,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            risk_reward=rr,
        )
