from decimal import Decimal
from pathlib import Path
from portfolio_agent.config.loader import load_config
from portfolio_agent.broker.ibkr.connection import IbkrConnectionManager
from portfolio_agent.broker.ibkr.mock_facade import MockIbkrFacade
from portfolio_agent.broker.ibkr.service import IbkrBrokerService
from portfolio_agent.broker.ibkr.reconciliation import PortfolioReconciler
from portfolio_agent.broker.models import BrokerOrderType, BrokerSide, BrokerPosition, OrderIntent

def config():
    return load_config(Path(__file__).resolve().parents[1] / "config")

def position(symbol, qty):
    return BrokerPosition(account_id="DU123456", symbol=symbol, quantity=Decimal(str(qty)), average_cost=Decimal("100"))

def test_connection_manager():
    facade = MockIbkrFacade()
    manager = IbkrConnectionManager(config(), facade, use_gateway=True)
    manager.connect()
    assert manager.healthcheck()

def test_order_idempotency_and_cancel():
    facade = MockIbkrFacade()
    facade.connect("127.0.0.1", 4002, 10, 10)
    service = IbkrBrokerService(config(), facade)
    intent = OrderIntent(
        client_order_id="run-1-SPY-buy-001",
        account_id="DU123456",
        symbol="SPY",
        side=BrokerSide.BUY,
        quantity=Decimal("2"),
        order_type=BrokerOrderType.LIMIT,
        limit_price=Decimal("500"),
    )
    first = service.submit(intent)
    second = service.submit(intent)
    assert first.broker_order_id == second.broker_order_id
    assert len(facade.orders) == 1
    service.cancel(intent.client_order_id)
    assert service.refresh_order(intent.client_order_id).status == "Cancelled"

def test_reconciliation():
    r = PortfolioReconciler(config())
    assert r.reconcile_positions([position("SPY",5)], [position("SPY",5)]).ok
    assert not r.reconcile_positions([position("SPY",5)], [position("SPY",4)]).ok
    assert r.reconcile_cash(Decimal("1000"), Decimal("1000.50")).ok
    assert not r.reconcile_cash(Decimal("1000"), Decimal("1005")).ok
