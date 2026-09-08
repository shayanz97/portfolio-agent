from __future__ import annotations

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.features.calculations import (
    atr,
    momentum_score,
    realized_volatility,
    relative_strength,
    return_over_window,
    return_zscore,
    rolling_correlation,
)
from portfolio_agent.features.models import FeatureSet, MarketBar


class QuantFeatureEngine:
    def __init__(self, config: RuntimeConfig, bar_interval_minutes: int = 1):
        self.config = config
        self.bar_interval_minutes = bar_interval_minutes

    def calculate(
        self,
        instrument: str,
        bars: list[MarketBar],
        benchmark_bars: list[MarketBar] | None = None,
        correlation_bars: dict[str, list[MarketBar]] | None = None,
    ) -> FeatureSet:
        if not bars:
            raise ValueError(f"no historical bars for {instrument}")

        ordered = sorted(bars, key=lambda b: b.timestamp)
        c = self.config.features

        returns = {}
        for window in c.return_windows:
            value = return_over_window(ordered, window, self.bar_interval_minutes)
            if value is not None:
                returns[window] = value

        correlations = {}
        if c.correlation.enabled and correlation_bars:
            for other, series in correlation_bars.items():
                value = rolling_correlation(
                    ordered, series, c.correlation.period, c.correlation.minimum_samples
                )
                if value is not None:
                    correlations[other] = value

        rs = None
        if c.relative_strength.enabled and benchmark_bars:
            rs = relative_strength(ordered, benchmark_bars, c.relative_strength.window)

        return FeatureSet(
            instrument=instrument,
            as_of=ordered[-1].timestamp,
            returns=returns,
            atr=atr(ordered, c.atr.period) if c.atr.enabled else None,
            realized_volatility=(
                realized_volatility(
                    ordered,
                    c.realized_volatility.period,
                    c.realized_volatility.annualization_factor,
                )
                if c.realized_volatility.enabled else None
            ),
            return_zscore=(
                return_zscore(ordered, c.zscore.period, c.zscore.minimum_samples)
                if c.zscore.enabled else None
            ),
            momentum_score=(
                momentum_score(ordered, c.momentum.short_window, c.momentum.long_window)
                if c.momentum.enabled else None
            ),
            relative_strength=rs,
            correlations=correlations,
            sample_size=len(ordered),
        )
