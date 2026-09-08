from decimal import Decimal
from portfolio_agent.broker.ibkr.facade import IbkrFacade
from portfolio_agent.broker.models import AccountSummary, BrokerPosition, OrderExecutionState

class MockIbkrFacade(IbkrFacade):
    def __init__(self):
        self.connected = False
        self.accounts = ["DU123456"]
        self.positions_data = []
        self.orders = {}
        self._next = 1000

    def connect(self, host, port, client_id, timeout_seconds): self.connected = True
    def disconnect(self): self.connected = False
    def is_connected(self): return self.connected
    def get_accounts(self): return list(self.accounts)

    def get_account_summary(self, account_id):
        return AccountSummary(
            account_id=account_id, base_currency="EUR",
            net_liquidation=Decimal("100000"),
            total_cash=Decimal("25000"),
            available_funds=Decimal("60000"),
            buying_power=Decimal("120000"),
            excess_liquidity=Decimal("55000"),
        )

    def get_positions(self, account_id): return list(self.positions_data)
    def get_open_orders(self, account_id): return [x for x in self.orders.values() if x.status not in {"Filled","Cancelled","Rejected"}]

    def next_order_id(self):
        value = self._next
        self._next += 1
        return value

    def place_order(self, broker_order_id, intent):
        state = OrderExecutionState(
            client_order_id=intent.client_order_id,
            broker_order_id=broker_order_id,
            status="Submitted",
            filled=Decimal("0"),
            remaining=intent.quantity,
        )
        self.orders[broker_order_id] = state
        return state

    def cancel_order(self, broker_order_id):
        self.orders[broker_order_id] = self.orders[broker_order_id].model_copy(update={"status":"Cancelled"})

    def get_order_state(self, broker_order_id): return self.orders.get(broker_order_id)
