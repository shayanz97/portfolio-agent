from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from portfolio_agent.domain.enums import AssetSignal, MarketRegime, PositionState


class StrategyModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PositionType(StrEnum):
    LONG_TERM = "LONG_TERM"
    SWING = "SWING"
    MOMENTUM = "MOMENTUM"
    EVENT = "EVENT"
    RECOVERY = "RECOVERY"


class RegimeAssessment(StrategyModel):
    regime: MarketRegime
    score: float = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=1)
    components: dict[str, float]
    explanation: str


class SignalAssessment(StrategyModel):
    instrument: str
    score: float = Field(ge=-1, le=1)
    signal: AssetSignal
    confidence: float = Field(ge=0, le=1)
    components: dict[str, float]
    explanation: str


class ThesisSnapshot(StrategyModel):
    score: float = Field(ge=0, le=100)
    factors: dict[str, float] = Field(default_factory=dict)
    invalidated: bool = False


class PositionLifecycleInput(StrategyModel):
    instrument: str
    position_type: PositionType
    entry_price: Decimal
    current_price: Decimal
    high_water_mark_intraday: Decimal
    high_water_mark_close: Decimal
    atr: float | None = None
    momentum_score: float | None = None
    thesis: ThesisSnapshot | None = None
    recovery_score: float | None = Field(default=None, ge=0, le=100)
    current_weight: float = Field(ge=0, le=1)
    add_events: int = Field(ge=0)
    days_since_last_reversal: int | None = None


class PositionLifecycleDecision(StrategyModel):
    instrument: str
    state: PositionState
    action: AssetSignal
    profit_pct: float
    peak_profit_pct: float
    giveback_pct: float
    profit_risk_score: float = Field(ge=0, le=100)
    recovery_score: float | None = Field(default=None, ge=0, le=100)
    explanation: str


class PortfolioTarget(StrategyModel):
    regime: MarketRegime
    target_weights: dict[str, float]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RebalanceInstruction(StrategyModel):
    bucket: str
    current_weight: float
    target_weight: float
    delta_weight: float
    action: str


class RiskCheckResult(StrategyModel):
    approved: bool
    reasons: list[str] = Field(default_factory=list)
    risk_amount: Decimal | None = None
    position_size: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit_1: Decimal | None = None
    take_profit_2: Decimal | None = None
    risk_reward: float | None = None
