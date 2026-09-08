from __future__ import annotations

import math
from statistics import mean, pstdev

from portfolio_agent.features.models import MarketBar


WINDOW_MINUTES = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "24h": 1440,
}


def _bars(bars: list[MarketBar]) -> list[MarketBar]:
    return sorted((b for b in bars if b.is_valid), key=lambda x: x.timestamp)


def pct_change(old: float, new: float) -> float | None:
    return None if old <= 0 else new / old - 1.0


def close_returns(bars: list[MarketBar]) -> list[float]:
    ordered = _bars(bars)
    out = []
    for a, b in zip(ordered, ordered[1:]):
        value = pct_change(float(a.close), float(b.close))
        if value is not None:
            out.append(value)
    return out


def return_over_window(
    bars: list[MarketBar],
    window: str,
    bar_interval_minutes: int = 1,
) -> float | None:
    ordered = _bars(bars)
    steps = math.ceil(WINDOW_MINUTES[window] / bar_interval_minutes)
    if len(ordered) <= steps:
        return None
    return pct_change(float(ordered[-steps - 1].close), float(ordered[-1].close))


def atr(bars: list[MarketBar], period: int) -> float | None:
    ordered = _bars(bars)
    if len(ordered) < period + 1:
        return None
    trs = []
    for prev, cur in zip(ordered, ordered[1:]):
        high, low, prev_close = float(cur.high), float(cur.low), float(prev.close)
        trs.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    recent = trs[-period:]
    return sum(recent) / len(recent)


def realized_volatility(
    bars: list[MarketBar],
    period: int,
    annualization_factor: float,
) -> float | None:
    returns = close_returns(bars)
    if len(returns) < period:
        return None
    return pstdev(returns[-period:]) * math.sqrt(annualization_factor)


def return_zscore(
    bars: list[MarketBar],
    period: int,
    minimum_samples: int,
) -> float | None:
    returns = close_returns(bars)[-period:]
    if len(returns) < minimum_samples:
        return None
    sigma = pstdev(returns)
    if sigma == 0:
        return 0.0
    return (returns[-1] - mean(returns)) / sigma


def momentum_score(bars: list[MarketBar], short_window: int, long_window: int) -> float | None:
    ordered = _bars(bars)
    if len(ordered) < long_window:
        return None
    short_ma = mean(float(x.close) for x in ordered[-short_window:])
    long_ma = mean(float(x.close) for x in ordered[-long_window:])
    raw = short_ma / long_ma - 1.0
    return max(-1.0, min(1.0, raw * 10.0))


def rolling_correlation(
    bars_a: list[MarketBar],
    bars_b: list[MarketBar],
    period: int,
    minimum_samples: int,
) -> float | None:
    a = close_returns(bars_a)[-period:]
    b = close_returns(bars_b)[-period:]
    n = min(len(a), len(b))
    if n < minimum_samples:
        return None
    a, b = a[-n:], b[-n:]
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den_a = sum((x - ma) ** 2 for x in a)
    den_b = sum((y - mb) ** 2 for y in b)
    den = math.sqrt(den_a * den_b)
    if den == 0:
        return None
    return max(-1.0, min(1.0, num / den))


def relative_strength(
    bars: list[MarketBar],
    benchmark: list[MarketBar],
    window: int,
) -> float | None:
    left, right = _bars(bars), _bars(benchmark)
    if len(left) <= window or len(right) <= window:
        return None
    a = pct_change(float(left[-window - 1].close), float(left[-1].close))
    b = pct_change(float(right[-window - 1].close), float(right[-1].close))
    if a is None or b is None:
        return None
    return a - b
