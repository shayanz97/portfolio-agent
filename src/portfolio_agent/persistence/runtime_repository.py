from __future__ import annotations

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from portfolio_agent.domain.enums import PositionState
from portfolio_agent.persistence.runtime_models import PositionRuntimeRecord
from portfolio_agent.runtime.models import PositionRuntimeState


class SqlAlchemyPositionRuntimeRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def save(self, state: PositionRuntimeState) -> None:
        with self.session_factory() as session:
            row = session.get(PositionRuntimeRecord, state.instrument)
            payload = dict(
                entry_price=float(state.entry_price),
                quantity=float(state.quantity),
                current_price=float(state.current_price),
                high_water_mark_intraday=float(state.high_water_mark_intraday),
                high_water_mark_close=float(state.high_water_mark_close),
                low_water_mark_intraday=float(state.low_water_mark_intraday),
                low_water_mark_close=float(state.low_water_mark_close),
                max_unrealized_profit_pct=state.max_unrealized_profit_pct,
                max_drawdown_pct=state.max_drawdown_pct,
                lifecycle_state=state.lifecycle_state.value,
                updated_at=state.updated_at,
            )
            if row is None:
                row = PositionRuntimeRecord(instrument=state.instrument, **payload)
                session.add(row)
            else:
                for key, value in payload.items():
                    setattr(row, key, value)
            session.commit()

    def load_all(self) -> list[PositionRuntimeState]:
        with self.session_factory() as session:
            rows = session.execute(select(PositionRuntimeRecord)).scalars().all()
            return [
                PositionRuntimeState(
                    instrument=row.instrument,
                    entry_price=Decimal(str(row.entry_price)),
                    quantity=Decimal(str(row.quantity)),
                    current_price=Decimal(str(row.current_price)),
                    high_water_mark_intraday=Decimal(str(row.high_water_mark_intraday)),
                    high_water_mark_close=Decimal(str(row.high_water_mark_close)),
                    low_water_mark_intraday=Decimal(str(row.low_water_mark_intraday)),
                    low_water_mark_close=Decimal(str(row.low_water_mark_close)),
                    max_unrealized_profit_pct=row.max_unrealized_profit_pct,
                    max_drawdown_pct=row.max_drawdown_pct,
                    lifecycle_state=PositionState(row.lifecycle_state),
                    updated_at=row.updated_at,
                )
                for row in rows
            ]
