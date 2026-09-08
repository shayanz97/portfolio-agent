from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from portfolio_agent.persistence.db import Base

class BrokerOrderRecord(Base):
    __tablename__ = "broker_orders"
    client_order_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    broker_order_id: Mapped[int | None] = mapped_column(Integer, index=True)
    perm_id: Mapped[int | None] = mapped_column(Integer, index=True)
    account_id: Mapped[str] = mapped_column(String(64), index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32))
    intent_json: Mapped[str] = mapped_column(Text)
    state_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
