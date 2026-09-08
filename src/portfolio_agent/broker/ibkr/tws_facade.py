"""
Production boundary for the official IBKR TWS API.

Map these callbacks here:
- nextValidId
- managedAccounts
- accountSummary / accountSummaryEnd
- position / positionEnd
- openOrder
- orderStatus
- error

The official `ibapi` package is distributed by Interactive Brokers separately,
so it is intentionally not imported by default in this project artifact.
"""

from portfolio_agent.broker.ibkr.facade import IbkrFacade

class TwsIbkrFacade(IbkrFacade):
    def __init__(self):
        raise RuntimeError(
            "Official TWS API wiring is intentionally deferred. "
            "Install the official IBKR TWS API and implement callbacks in this boundary."
        )
