from __future__ import annotations

import json
import logging
from datetime import datetime, timezone


class JsonEventLogger:
    def __init__(self, name: str = "portfolio_agent.audit"):
        self.logger = logging.getLogger(name)

    def emit(self, event_type: str, **fields) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            **fields,
        }
        self.logger.info(json.dumps(payload, default=str, sort_keys=True))


class InMemoryMetrics:
    def __init__(self):
        self.counters: dict[str, int] = {}
        self.gauges: dict[str, float] = {}

    def inc(self, name: str, amount: int = 1):
        self.counters[name] = self.counters.get(name, 0) + amount

    def set_gauge(self, name: str, value: float):
        self.gauges[name] = value
