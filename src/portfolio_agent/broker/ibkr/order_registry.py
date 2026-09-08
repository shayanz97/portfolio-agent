from threading import Lock
from portfolio_agent.broker.models import OrderExecutionState

class InMemoryOrderRegistry:
    def __init__(self):
        self._lock = Lock()
        self._states = {}

    def get(self, client_order_id):
        with self._lock:
            return self._states.get(client_order_id)

    def reserve(self, client_order_id):
        with self._lock:
            if client_order_id in self._states:
                return False
            self._states[client_order_id] = OrderExecutionState(client_order_id=client_order_id, status="RESERVED")
            return True

    def update(self, state):
        with self._lock:
            self._states[state.client_order_id] = state
