from __future__ import annotations

from datetime import datetime, timezone


class ScheduledRuntimeRunner:
    """
    Scheduler-ready runtime wrapper.

    No background scheduler is embedded here on purpose. External scheduling
    (cron, systemd timer, container scheduler, GitHub Actions, etc.) can invoke
    `run_once()` deterministically.
    """

    def __init__(self, graph_runner, runtime_service):
        self.graph_runner = graph_runner
        self.runtime_service = runtime_service

    def run_once(self, *, run_id: str | None = None, thread_id: str | None = None):
        result, lg_config = self.graph_runner.start(
            run_id=run_id,
            thread_id=thread_id,
        )

        return {
            "graph_result": result,
            "langgraph_config": lg_config,
            "ran_at": datetime.now(timezone.utc),
        }
