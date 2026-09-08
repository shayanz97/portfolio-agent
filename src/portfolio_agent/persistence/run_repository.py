from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from portfolio_agent.persistence.db import Base


class StrategyRunRecord(Base):
    __tablename__ = "strategy_run_records"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    config_version: Mapped[str] = mapped_column(String(32), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    state_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SqlAlchemyRunRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def persist(self, state: dict) -> None:
        run_id = state["run_id"]
        with self.session_factory() as session:
            row = session.get(StrategyRunRecord, run_id)
            payload = {
                "status": state.get("status", "UNKNOWN"),
                "config_version": state.get("config_version", "unknown"),
                "config_hash": state.get("config_hash", "unknown"),
                "state_json": json.dumps(state, default=str, sort_keys=True),
                "updated_at": datetime.now(timezone.utc),
            }
            if row is None:
                row = StrategyRunRecord(run_id=run_id, **payload)
                session.add(row)
            else:
                for k, v in payload.items():
                    setattr(row, k, v)
            session.commit()
