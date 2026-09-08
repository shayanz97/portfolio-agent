from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from portfolio_agent.domain.models import TradeProposal
from portfolio_agent.strategy.models import RiskCheckResult


class TradeProposalBuilder:
    def build_long(
        self,
        *,
        run_id: str,
        instrument: str,
        entry_price: Decimal,
        risk: RiskCheckResult,
    ) -> TradeProposal:
        if not risk.approved or risk.position_size is None:
            raise ValueError("risk result must be approved before building trade")

        suffix = uuid4().hex[:8]
        return TradeProposal(
            proposal_id=f"proposal-{suffix}",
            client_order_id=f"{run_id}-{instrument}-BUY-{suffix}",
            instrument=instrument,
            side="BUY",
            quantity=risk.position_size,
            limit_price=entry_price,
            stop_loss=risk.stop_loss,
            take_profit_1=risk.take_profit_1,
            take_profit_2=risk.take_profit_2,
            risk_amount=risk.risk_amount,
        )
