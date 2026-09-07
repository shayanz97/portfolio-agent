from __future__ import annotations

from portfolio_agent.broker.base import BrokerAdapter
from portfolio_agent.config.settings import AppSettings


class IbkrBrokerAdapter(BrokerAdapter):
    """
    Milestone-1 placeholder.

    The production implementation should use Interactive Brokers' official
    TWS API package and connect to Trader Workstation or IB Gateway.

    No order execution is implemented in this milestone.
    """

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self._connected = False

    def connect(self) -> None:
        raise NotImplementedError("IBKR connection is implemented in Milestone 4")

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_positions(self):
        raise NotImplementedError

    def get_cash_balance(self, currency: str = "EUR"):
        raise NotImplementedError

    def get_open_orders(self):
        raise NotImplementedError

    def submit_order(self, proposal):
        raise NotImplementedError

    def cancel_order(self, client_order_id: str):
        raise NotImplementedError

    def get_order_status(self, client_order_id: str):
        raise NotImplementedError
