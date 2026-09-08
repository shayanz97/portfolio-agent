from __future__ import annotations

from uuid import uuid4

from langgraph.types import Command

from portfolio_agent.config.loader import config_hash
from portfolio_agent.graph.state import PortfolioGraphState


class PortfolioGraphRunner:
    def __init__(self, graph, config):
        self.graph = graph
        self.config = config

    def start(self, *, run_id: str | None = None, thread_id: str | None = None):
        run_id = run_id or f"run-{uuid4().hex[:12]}"
        thread_id = thread_id or f"{self.config.workflow.default_thread_prefix}-{run_id}"

        initial: PortfolioGraphState = {
            "run_id": run_id,
            "thread_id": thread_id,
            "config_version": self.config.version,
            "config_hash": config_hash(self.config),
            "errors": [],
            "status": "CREATED",
        }

        lg_config = {"configurable": {"thread_id": thread_id}}
        return self.graph.invoke(initial, config=lg_config), lg_config

    def resume(self, lg_config: dict, approved: bool):
        return self.graph.invoke(Command(resume=approved), config=lg_config)
