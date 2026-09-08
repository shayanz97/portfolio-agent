from __future__ import annotations

from datetime import timedelta
from statistics import mean, median

from portfolio_agent.backtest.feed import HistoricalFeed
from portfolio_agent.backtest.models import (
    EventOutcome,
    EventStudySummary,
)


class EventStudyEngine:
    def __init__(self, feed: HistoricalFeed):
        self.feed = feed

    def evaluate_event(
        self,
        *,
        event_id: str,
        event_time,
        instrument: str,
        horizons_minutes: list[int],
    ) -> list[EventOutcome]:
        base = self.feed.exact_or_previous(instrument, event_time)
        if base is None or base.close <= 0:
            return [
                EventOutcome(
                    event_id=event_id,
                    event_time=event_time,
                    instrument=instrument,
                    horizon_minutes=h,
                    return_pct=None,
                )
                for h in horizons_minutes
            ]

        outcomes = []
        for horizon in horizons_minutes:
            future = self.feed.exact_or_previous(
                instrument,
                event_time + timedelta(minutes=horizon),
            )
            if future is None or future.timestamp <= event_time:
                ret = None
            else:
                ret = float(future.close / base.close - 1)

            outcomes.append(
                EventOutcome(
                    event_id=event_id,
                    event_time=event_time,
                    instrument=instrument,
                    horizon_minutes=horizon,
                    return_pct=ret,
                )
            )
        return outcomes

    def summarize(
        self,
        outcomes: list[EventOutcome],
        *,
        minimum_events: int,
    ) -> list[EventStudySummary]:
        grouped = {}
        for item in outcomes:
            key = (item.instrument, item.horizon_minutes)
            grouped.setdefault(key, []).append(item.return_pct)

        summaries = []
        for (instrument, horizon), values in grouped.items():
            valid = [x for x in values if x is not None]

            if len(valid) < minimum_events:
                summaries.append(
                    EventStudySummary(
                        instrument=instrument,
                        horizon_minutes=horizon,
                        event_count=len(valid),
                        average_return_pct=None,
                        median_return_pct=None,
                        positive_rate=None,
                    )
                )
                continue

            summaries.append(
                EventStudySummary(
                    instrument=instrument,
                    horizon_minutes=horizon,
                    event_count=len(valid),
                    average_return_pct=mean(valid),
                    median_return_pct=median(valid),
                    positive_rate=sum(1 for x in valid if x > 0) / len(valid),
                )
            )

        return summaries
