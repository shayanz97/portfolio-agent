from decimal import Decimal

from portfolio_agent.domain.enums import OrderStatus
from portfolio_agent.domain.models import TradeProposal


def test_trade_proposal_defaults_to_proposed():
    proposal = TradeProposal(
        proposal_id="p-1",
        client_order_id="client-1",
        instrument="SPY",
        side="BUY",
        quantity=Decimal("1"),
        limit_price=Decimal("500"),
    )
    assert proposal.status == OrderStatus.PROPOSED
