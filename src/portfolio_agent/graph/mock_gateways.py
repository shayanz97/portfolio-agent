from __future__ import annotations

from copy import deepcopy


class StaticMarketContextProvider:
    def __init__(self, context):
        self.context = deepcopy(context)

    def get_context(self):
        return deepcopy(self.context)


class StaticReconciliationGateway:
    def __init__(self, ok=True):
        self.ok = ok

    def reconcile(self):
        return self.ok


class MockPaperExecutionGateway:
    def __init__(self):
        self.executed = []

    def execute(self, proposals):
        results = []
        for p in proposals:
            result = {
                "client_order_id": p["client_order_id"],
                "instrument": p["instrument"],
                "status": "PAPER_SUBMITTED",
            }
            results.append(result)
            self.executed.append(result)
        return results


class InMemoryRunPersistenceGateway:
    def __init__(self):
        self.states = []

    def persist(self, state):
        self.states.append(deepcopy(state))
