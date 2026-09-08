from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from portfolio_agent.persistence.db import Base


class FeatureSetRecord(Base):
    __tablename__ = "feature_sets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    instrument: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    atr: Mapped[float | None] = mapped_column(Float)
    realized_volatility: Mapped[float | None] = mapped_column(Float)
    return_zscore: Mapped[float | None] = mapped_column(Float)
    momentum_score: Mapped[float | None] = mapped_column(Float)
    relative_strength: Mapped[float | None] = mapped_column(Float)
    returns_json: Mapped[str] = mapped_column(Text, default="{}")
    correlations_json: Mapped[str] = mapped_column(Text, default="{}")
