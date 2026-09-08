from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from datetime import datetime

from portfolio_agent.backtest.models import HistoricalPoint


class LookaheadViolation(RuntimeError):
    pass


class HistoricalFeed:
    def __init__(self, data: list[HistoricalPoint], prohibit_lookahead: bool = True):
        self.prohibit_lookahead = prohibit_lookahead
        self._by_instrument: dict[str, list[HistoricalPoint]] = defaultdict(list)

        for point in data:
            self._by_instrument[point.instrument].append(point)

        for instrument, points in self._by_instrument.items():
            points.sort(key=lambda x: x.timestamp)

    def history_until(
        self,
        instrument: str,
        as_of: datetime,
    ) -> list[HistoricalPoint]:
        points = self._by_instrument.get(instrument, [])
        timestamps = [x.timestamp for x in points]
        idx = bisect_right(timestamps, as_of)
        return points[:idx]

    def next_point_after(
        self,
        instrument: str,
        after: datetime,
        bars_ahead: int = 1,
    ) -> HistoricalPoint | None:
        points = self._by_instrument.get(instrument, [])
        timestamps = [x.timestamp for x in points]
        idx = bisect_right(timestamps, after)
        target = idx + max(0, bars_ahead - 1)
        return points[target] if target < len(points) else None

    def exact_or_previous(
        self,
        instrument: str,
        at: datetime,
    ) -> HistoricalPoint | None:
        points = self._by_instrument.get(instrument, [])
        timestamps = [x.timestamp for x in points]
        idx = bisect_right(timestamps, at) - 1
        return points[idx] if idx >= 0 else None
