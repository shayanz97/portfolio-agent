from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CircuitBreakerCounters:
    consecutive_runtime_errors: int = 0
    stale_runs: int = 0
    reconciliation_failures: int = 0
    execution_errors: int = 0


class ProductionCircuitBreaker:
    def __init__(self, config):
        self.config = config
        self.counters = CircuitBreakerCounters()

    def record_runtime_error(self):
        self.counters.consecutive_runtime_errors += 1

    def record_successful_run(self):
        self.counters.consecutive_runtime_errors = 0

    def record_stale_run(self):
        self.counters.stale_runs += 1

    def record_reconciliation_failure(self):
        self.counters.reconciliation_failures += 1

    def record_execution_error(self):
        self.counters.execution_errors += 1

    def reset_stale_runs(self):
        self.counters.stale_runs = 0

    def reset_reconciliation_failures(self):
        self.counters.reconciliation_failures = 0

    def reset_execution_errors(self):
        self.counters.execution_errors = 0

    def evaluate(self) -> tuple[bool, list[str]]:
        limits = self.config.production.circuit_breakers
        reasons = []

        if self.counters.consecutive_runtime_errors >= limits.max_consecutive_runtime_errors:
            reasons.append("too many consecutive runtime errors")
        if self.counters.stale_runs >= limits.max_stale_runs:
            reasons.append("too many stale-data runs")
        if self.counters.reconciliation_failures >= limits.max_reconciliation_failures:
            reasons.append("reconciliation failure threshold reached")
        if self.counters.execution_errors >= limits.max_execution_errors:
            reasons.append("execution error threshold reached")

        return (not reasons, reasons)
