from __future__ import annotations

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.domain.enums import AssetSignal, MarketRegime
from portfolio_agent.strategy.models import PortfolioTarget, RebalanceInstruction, SignalAssessment


class PortfolioTargetEngine:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def target_for_regime(
        self,
        regime: MarketRegime,
        signals: list[SignalAssessment] | None = None,
    ) -> PortfolioTarget:
        base = dict(self.config.portfolio_targets.regimes[regime.value])

        # Only bucket-level adjustment in MVP. Instrument-to-bucket mapping
        # will become explicit when instrument master is implemented.
        if signals:
            adjustments = self.config.portfolio_targets.signal_adjustment
            for signal in signals:
                if signal.signal == AssetSignal.STRONG_BUY:
                    base["cash"] = max(0.0, base["cash"] - adjustments.strong_buy)
                elif signal.signal == AssetSignal.BUY:
                    base["cash"] = max(0.0, base["cash"] - adjustments.buy)
                elif signal.signal == AssetSignal.REDUCE:
                    base["cash"] = min(1.0, base["cash"] - adjustments.reduce)
                elif signal.signal == AssetSignal.EXIT:
                    base["cash"] = min(1.0, base["cash"] - adjustments.exit)

        # Normalize after signal overlays.
        total = sum(base.values())
        normalized = {k: v / total for k, v in base.items()}
        return PortfolioTarget(regime=regime, target_weights=normalized)

    def rebalance(
        self,
        current_weights: dict[str, float],
        target: PortfolioTarget,
    ) -> list[RebalanceInstruction]:
        minimum = self.config.portfolio_targets.rebalance.minimum_weight_change
        max_change = self.config.portfolio.max_rebalance_per_run

        instructions = []
        for bucket in sorted(set(current_weights) | set(target.target_weights)):
            current = current_weights.get(bucket, 0.0)
            desired = target.target_weights.get(bucket, 0.0)
            delta = desired - current

            if abs(delta) < minimum:
                continue

            if self.config.portfolio_targets.rebalance.respect_max_rebalance_per_run:
                delta = max(-max_change, min(max_change, delta))
                desired = current + delta

            instructions.append(
                RebalanceInstruction(
                    bucket=bucket,
                    current_weight=current,
                    target_weight=desired,
                    delta_weight=delta,
                    action="INCREASE" if delta > 0 else "DECREASE",
                )
            )
        return instructions
