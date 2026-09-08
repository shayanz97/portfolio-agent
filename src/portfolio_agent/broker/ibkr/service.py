from portfolio_agent.broker.ibkr.order_registry import InMemoryOrderRegistry

class IbkrBrokerService:
    def __init__(self, config, facade, registry=None):
        self.config, self.facade = config, facade
        self.registry = registry or InMemoryOrderRegistry()

    def resolve_account_id(self):
        accounts = self.facade.get_accounts()
        if not accounts:
            raise RuntimeError("IBKR returned no accounts")
        if self.config.broker.ibkr.account.require_single_account and len(accounts) != 1:
            raise RuntimeError("multiple accounts returned")
        return accounts[0]

    def account_summary(self, account_id=None):
        return self.facade.get_account_summary(account_id or self.resolve_account_id())

    def positions(self, account_id=None):
        return self.facade.get_positions(account_id or self.resolve_account_id())

    def open_orders(self, account_id=None):
        return self.facade.get_open_orders(account_id or self.resolve_account_id())

    def submit(self, intent):
        existing = self.registry.get(intent.client_order_id)
        if existing is not None:
            return existing
        self.registry.reserve(intent.client_order_id)
        broker_id = self.facade.next_order_id()
        try:
            state = self.facade.place_order(broker_id, intent)
        except Exception as exc:
            state = __import__("portfolio_agent.broker.models", fromlist=["OrderExecutionState"]).OrderExecutionState(
                client_order_id=intent.client_order_id,
                broker_order_id=broker_id,
                status="ERROR",
                error=str(exc),
            )
            self.registry.update(state)
            raise
        self.registry.update(state)
        return state

    def refresh_order(self, client_order_id):
        known = self.registry.get(client_order_id)
        if known is None or known.broker_order_id is None:
            return known
        state = self.facade.get_order_state(known.broker_order_id)
        if state is not None:
            self.registry.update(state)
        return state or known

    def cancel(self, client_order_id):
        known = self.registry.get(client_order_id)
        if known is None or known.broker_order_id is None:
            raise KeyError(client_order_id)
        self.facade.cancel_order(known.broker_order_id)
