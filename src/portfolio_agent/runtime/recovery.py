from __future__ import annotations


class StartupRecoveryError(RuntimeError):
    pass


class StartupRecoveryService:
    def __init__(
        self,
        config,
        *,
        position_repository,
        runtime_service,
        reconciliation_gateway,
    ):
        self.config = config
        self.position_repository = position_repository
        self.runtime_service = runtime_service
        self.reconciliation_gateway = reconciliation_gateway

    def recover(self) -> dict:
        restored = 0

        try:
            if self.config.production.recovery.restore_position_runtime_state:
                states = self.position_repository.load_all()
                self.runtime_service.positions = {x.instrument: x for x in states}
                restored = len(states)

            reconciled = True
            if self.config.production.recovery.reconcile_before_graph_start:
                reconciled = bool(self.reconciliation_gateway.reconcile())
                if not reconciled:
                    raise StartupRecoveryError("startup reconciliation failed")

            return {
                "restored_positions": restored,
                "reconciled": reconciled,
                "ok": True,
            }
        except Exception:
            if self.config.production.recovery.fail_closed_on_recovery_error:
                raise
            return {
                "restored_positions": restored,
                "reconciled": False,
                "ok": False,
            }
