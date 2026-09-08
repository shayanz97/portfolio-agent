from decimal import Decimal
from portfolio_agent.broker.models import ReconciliationIssue, ReconciliationResult

class PortfolioReconciler:
    def __init__(self, config):
        self.config = config

    def reconcile_positions(self, expected, actual):
        tol = Decimal(str(self.config.broker.ibkr.reconciliation.quantity_tolerance))
        e = {p.symbol: p for p in expected}
        a = {p.symbol: p for p in actual}
        issues = []
        for symbol in sorted(set(e) | set(a)):
            ep, ap = e.get(symbol), a.get(symbol)
            if ep is None:
                issues.append(ReconciliationIssue(kind="UNEXPECTED_POSITION", symbol=symbol, actual=ap.quantity, detail="broker-only position"))
            elif ap is None:
                issues.append(ReconciliationIssue(kind="MISSING_POSITION", symbol=symbol, expected=ep.quantity, detail="missing at broker"))
            else:
                diff = ap.quantity - ep.quantity
                if abs(diff) > tol:
                    issues.append(ReconciliationIssue(kind="QUANTITY_MISMATCH", symbol=symbol, expected=ep.quantity, actual=ap.quantity, difference=diff, detail="quantity mismatch"))
        return ReconciliationResult(ok=not issues, issues=issues)

    def reconcile_cash(self, expected, actual):
        tol = Decimal(str(self.config.broker.ibkr.reconciliation.cash_tolerance))
        diff = actual - expected
        if abs(diff) <= tol:
            return ReconciliationResult(ok=True)
        return ReconciliationResult(
            ok=False,
            issues=[ReconciliationIssue(kind="CASH_MISMATCH", expected=expected, actual=actual, difference=diff, detail="cash mismatch")]
        )
