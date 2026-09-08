from __future__ import annotations

from datetime import datetime, timedelta, timezone

from portfolio_agent.runtime.models import AlertEvent


class InMemoryAlertRegistry:
    def __init__(self):
        self._last_sent: dict[str, datetime] = {}
        self.sent: list[AlertEvent] = []

    def should_send(self, alert: AlertEvent, cooldown_minutes: int) -> bool:
        now = alert.created_at
        last = self._last_sent.get(alert.dedup_key)
        if last is None:
            return True
        return now - last >= timedelta(minutes=cooldown_minutes)

    def record(self, alert: AlertEvent) -> None:
        self._last_sent[alert.dedup_key] = alert.created_at
        self.sent.append(alert)
