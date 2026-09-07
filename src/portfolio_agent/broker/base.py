from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from portfolio_agent.domain.models import PositionSnapshot, TradeProposal


class BrokerAdapter(ABC):
    @abstractmethod
    def connect(self) -> None:
        ...

    @abstractmethod
    def disconnect(self) -> None:
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        ...

    @abstractmethod
    def get_positions(self) -> Sequence[PositionSnapshot]:
        ...

    @abstractmethod
    def get_cash_balance(self, currency: str = "EUR"):
        ...

    @abstractmethod
    def get_open_orders(self):
        ...

    @abstractmethod
    def submit_order(self, proposal: TradeProposal):
        ...

    @abstractmethod
    def cancel_order(self, client_order_id: str):
        ...

    @abstractmethod
    def get_order_status(self, client_order_id: str):
        ...
