from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class AssetConfig(FrozenModel):
    symbol: str
    asset_class: str
    enabled: bool = True
    trade_enabled: bool = False
    provider: str
    currency: str = "USD"
    market: str
    session: str


class DataQualityRules(FrozenModel):
    max_spread_pct: float = Field(gt=0, le=1)
    reject_non_positive_prices: bool = True
    reject_missing_timestamp: bool = True


class MarketSessionConfig(FrozenModel):
    timezone: str
    kind: Literal[
        "always_open",
        "always_available",
        "weekday_session",
        "nearly_24h_weekday",
    ]
    regular_open: str | None = None
    regular_close: str | None = None
    premarket_open: str | None = None
    afterhours_close: str | None = None
    daily_break_start: str | None = None
    daily_break_end: str | None = None

    @model_validator(mode="after")
    def validate_required_fields(self):
        if self.kind == "weekday_session":
            required = [
                self.regular_open,
                self.regular_close,
                self.premarket_open,
                self.afterhours_close,
            ]
            if any(v is None for v in required):
                raise ValueError("weekday_session requires all equity session times")

        if self.kind == "nearly_24h_weekday":
            if self.daily_break_start is None or self.daily_break_end is None:
                raise ValueError("nearly_24h_weekday requires daily break times")
        return self


class MarketDataConfig(FrozenModel):
    provider_priority: list[str]
    allow_fallback: bool = True
    reject_future_timestamps_seconds: int = Field(ge=0, le=300)
    staleness_seconds: dict[str, int]
    quality: DataQualityRules
    sessions: dict[str, MarketSessionConfig]

    @model_validator(mode="after")
    def validate_staleness(self):
        if not self.provider_priority:
            raise ValueError("provider_priority must not be empty")
        if any(v <= 0 for v in self.staleness_seconds.values()):
            raise ValueError("all staleness thresholds must be > 0")
        return self


class OilWindowConfig(FrozenModel):
    watch_pct: float = Field(gt=0)
    high_pct: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_threshold_order(self):
        if self.high_pct <= self.watch_pct:
            raise ValueError("high_pct must be greater than watch_pct")
        return self


class VolatilityAdjustedConfig(FrozenModel):
    enabled: bool = True
    watch_zscore: float = Field(gt=0)
    high_zscore: float = Field(gt=0)
    extreme_zscore: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_order(self):
        if not self.watch_zscore < self.high_zscore < self.extreme_zscore:
            raise ValueError("z-score thresholds must satisfy watch < high < extreme")
        return self


class OilConfirmationConfig(FrozenModel):
    require_wti_brent: bool = True
    minimum_confirmation_score: float = Field(ge=0, le=1)


class OilShockConfig(FrozenModel):
    enabled: bool = True
    windows: dict[str, OilWindowConfig]
    volatility_adjusted: VolatilityAdjustedConfig
    confirmation: OilConfirmationConfig


class ShockConfig(FrozenModel):
    enabled: bool = True
    watch_zscore: float = Field(gt=0)
    high_zscore: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_order(self):
        if self.high_zscore <= self.watch_zscore:
            raise ValueError("high_zscore must be greater than watch_zscore")
        return self


class SignalThresholds(FrozenModel):
    strong_buy: float = Field(gt=0, le=1)
    buy: float = Field(gt=0, le=1)
    reduce: float = Field(ge=-1, lt=0)
    exit: float = Field(ge=-1, lt=0)

    @model_validator(mode="after")
    def validate_order(self):
        if self.strong_buy <= self.buy:
            raise ValueError("strong_buy must be greater than buy")
        if self.exit >= self.reduce:
            raise ValueError("exit must be less than reduce")
        return self


class SignalWeights(FrozenModel):
    macro: float = Field(ge=0, le=1)
    momentum: float = Field(ge=0, le=1)
    technical: float = Field(ge=0, le=1)
    volatility: float = Field(ge=0, le=1)
    event: float = Field(ge=0, le=1)
    news: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def weights_sum_to_one(self):
        total = (
            self.macro + self.momentum + self.technical
            + self.volatility + self.event + self.news
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"signal weights must sum to 1.0, got {total}")
        return self


class ProfitProtectionConfig(FrozenModel):
    enabled: bool
    activate_after_profit_pct: float = Field(ge=0, le=1)
    max_profit_giveback_pct: float = Field(ge=0, le=1)
    atr_warning_multiple: float = Field(gt=0)


class PartialProfitConfig(FrozenModel):
    enabled: bool
    first_trigger_profit_pct: float = Field(ge=0, le=5)
    first_sell_pct: float = Field(gt=0, le=1)


class TrailingStopConfig(FrozenModel):
    enabled: bool
    atr_multiplier: float = Field(gt=0)


class AveragingDownConfig(FrozenModel):
    enabled: bool
    require_thesis_intact: bool
    require_stabilization: bool
    max_add_events: int = Field(ge=0, le=10)
    max_total_add_pct: float = Field(ge=0, le=2)
    max_position_weight_after_add: float = Field(gt=0, le=1)


class CooldownConfig(FrozenModel):
    minimum_days_between_reversals: int = Field(ge=0)
    signal_hysteresis: float = Field(ge=0, le=1)


class PositionManagementConfig(FrozenModel):
    enabled: bool
    profit_protection: ProfitProtectionConfig
    partial_profit: PartialProfitConfig
    trailing_stop: TrailingStopConfig
    averaging_down: AveragingDownConfig
    cooldown: CooldownConfig


class PortfolioLimits(FrozenModel):
    max_single_asset_weight: float = Field(gt=0, le=1)
    max_crypto_weight: float = Field(ge=0, le=1)
    max_equity_weight: float = Field(ge=0, le=1)
    max_precious_metals_weight: float = Field(ge=0, le=1)
    max_energy_weight: float = Field(ge=0, le=1)
    min_cash_weight: float = Field(ge=0, le=1)
    max_rebalance_per_run: float = Field(gt=0, le=1)


class TradeRiskConfig(FrozenModel):
    max_risk_per_trade: float = Field(gt=0, le=0.10)
    max_total_open_risk: float = Field(gt=0, le=0.50)
    minimum_risk_reward: float = Field(gt=0)
    maximum_open_positions: int = Field(gt=0)


class StopLossConfig(FrozenModel):
    atr_enabled: bool
    atr_multiplier: float = Field(gt=0)
    technical_support_enabled: bool
    maximum_loss_pct: float = Field(gt=0, le=1)


class TpLevel(FrozenModel):
    r_multiple: float = Field(gt=0)
    close_pct: float = Field(gt=0, le=1)


class TrailingTakeProfit(FrozenModel):
    enabled: bool
    remaining_pct: float = Field(ge=0, le=1)


class TakeProfitConfig(FrozenModel):
    tp1: TpLevel
    tp2: TpLevel
    trailing: TrailingTakeProfit

    @model_validator(mode="after")
    def validate_allocations(self):
        total = self.tp1.close_pct + self.tp2.close_pct + self.trailing.remaining_pct
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"take-profit allocations must sum to 1.0, got {total}")
        if self.tp2.r_multiple <= self.tp1.r_multiple:
            raise ValueError("tp2.r_multiple must be greater than tp1.r_multiple")
        return self


class MarginConfig(FrozenModel):
    max_margin_utilization: float = Field(gt=0, le=1)
    minimum_margin_buffer: float = Field(ge=0, le=1)


class CircuitBreakerConfig(FrozenModel):
    daily_loss_pct: float = Field(gt=0, le=1)
    max_drawdown_pct: float = Field(gt=0, le=1)
    stale_market_data_seconds: int = Field(gt=0)
    max_order_rejections: int = Field(gt=0)
    disable_on_broker_disconnect: bool
    disable_on_portfolio_mismatch: bool


class LiveTradingConfig(FrozenModel):
    enabled: bool = False
    require_cli_flag: bool = True
    require_environment_variable: bool = True


class ExecutionConfig(FrozenModel):
    environment: Literal["development", "paper", "shadow", "live"]
    broker: Literal["mock", "ibkr"]
    automatic_execution: bool
    human_approval_required: bool
    market_orders_allowed: bool
    limit_orders_only: bool
    maximum_order_value_eur: float = Field(gt=0)
    daily_trade_limit: int = Field(gt=0)
    live_trading: LiveTradingConfig

    @model_validator(mode="after")
    def block_unsafe_live_defaults(self):
        if self.environment == "live" and not self.live_trading.enabled:
            raise ValueError("environment=live requires live_trading.enabled=true")
        if self.market_orders_allowed and self.limit_orders_only:
            raise ValueError("market_orders_allowed and limit_orders_only cannot both be true")
        return self



class AtrFeatureConfig(FrozenModel):
    enabled: bool = True
    period: int = Field(gt=1, le=500)


class RealizedVolatilityConfig(FrozenModel):
    enabled: bool = True
    period: int = Field(gt=1, le=500)
    annualization_factor: float = Field(gt=0)


class ZScoreFeatureConfig(FrozenModel):
    enabled: bool = True
    period: int = Field(gt=2, le=1000)
    minimum_samples: int = Field(gt=2, le=1000)

    @model_validator(mode="after")
    def validate_samples(self):
        if self.minimum_samples > self.period:
            raise ValueError("zscore.minimum_samples cannot exceed period")
        return self


class MomentumFeatureConfig(FrozenModel):
    enabled: bool = True
    short_window: int = Field(gt=0)
    long_window: int = Field(gt=1)

    @model_validator(mode="after")
    def validate_windows(self):
        if self.short_window >= self.long_window:
            raise ValueError("momentum.short_window must be < long_window")
        return self


class CorrelationFeatureConfig(FrozenModel):
    enabled: bool = True
    period: int = Field(gt=2, le=1000)
    minimum_samples: int = Field(gt=2, le=1000)


class RelativeStrengthFeatureConfig(FrozenModel):
    enabled: bool = True
    window: int = Field(gt=1, le=1000)


class OilShockScoringConfig(FrozenModel):
    return_weight: float = Field(ge=0, le=1)
    zscore_weight: float = Field(ge=0, le=1)
    confirmation_weight: float = Field(ge=0, le=1)
    volatility_weight: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_weights(self):
        total = (
            self.return_weight
            + self.zscore_weight
            + self.confirmation_weight
            + self.volatility_weight
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError("oil shock scoring weights must sum to 1.0")
        return self


class FeaturesConfig(FrozenModel):
    return_windows: list[str]
    atr: AtrFeatureConfig
    realized_volatility: RealizedVolatilityConfig
    zscore: ZScoreFeatureConfig
    momentum: MomentumFeatureConfig
    correlation: CorrelationFeatureConfig
    relative_strength: RelativeStrengthFeatureConfig
    oil_shock_scoring: OilShockScoringConfig



class IbkrConnectionConfig(FrozenModel):
    host: str
    paper_tws_port: int = Field(gt=0, lt=65536)
    paper_gateway_port: int = Field(gt=0, lt=65536)
    live_tws_port: int = Field(gt=0, lt=65536)
    live_gateway_port: int = Field(gt=0, lt=65536)
    client_id: int = Field(ge=0)
    connect_timeout_seconds: int = Field(gt=0)
    heartbeat_seconds: int = Field(gt=0)
    reconnect_attempts: int = Field(ge=0)
    reconnect_backoff_seconds: int = Field(ge=0)

class IbkrAccountConfig(FrozenModel):
    base_currency: str = "EUR"
    require_single_account: bool = False

class IbkrReconciliationConfig(FrozenModel):
    enabled: bool = True
    quantity_tolerance: float = Field(ge=0)
    cash_tolerance: float = Field(ge=0)
    fail_closed: bool = True

class IbkrOrdersConfig(FrozenModel):
    default_tif: Literal["DAY", "GTC"] = "DAY"
    acknowledge_timeout_seconds: int = Field(gt=0)
    status_timeout_seconds: int = Field(gt=0)
    allow_fractional: bool = True
    transmit: bool = True

class IbkrConfig(FrozenModel):
    enabled: bool = True
    connection: IbkrConnectionConfig
    account: IbkrAccountConfig
    reconciliation: IbkrReconciliationConfig
    orders: IbkrOrdersConfig

class BrokerConfig(FrozenModel):
    ibkr: IbkrConfig

class RuntimeConfig(FrozenModel):
    version: str
    environment: Literal["development", "paper", "shadow", "live"]

    assets: dict[str, AssetConfig]
    market_data: MarketDataConfig
    features: FeaturesConfig

    oil_shock: OilShockConfig
    volatility_shock: ShockConfig
    crypto_shock: ShockConfig

    signal_thresholds: SignalThresholds
    signal_weights: SignalWeights
    position_management: PositionManagementConfig

    portfolio: PortfolioLimits
    trade_risk: TradeRiskConfig
    stop_loss: StopLossConfig
    take_profit: TakeProfitConfig
    margin: MarginConfig
    circuit_breakers: CircuitBreakerConfig

    execution: ExecutionConfig
    broker: BrokerConfig

    @model_validator(mode="after")
    def cross_validate(self):
        if self.environment != self.execution.environment:
            raise ValueError("top-level environment must match execution.environment")

        if self.position_management.averaging_down.max_position_weight_after_add > (
            self.portfolio.max_single_asset_weight
        ):
            raise ValueError(
                "averaging_down.max_position_weight_after_add "
                "cannot exceed portfolio.max_single_asset_weight"
            )

        unknown_sessions = {
            asset.session for asset in self.assets.values()
            if asset.session not in self.market_data.sessions
        }
        if unknown_sessions:
            raise ValueError(f"assets reference unknown sessions: {sorted(unknown_sessions)}")

        missing_staleness = {
            asset.asset_class for asset in self.assets.values()
            if asset.asset_class not in self.market_data.staleness_seconds
        }
        if missing_staleness:
            raise ValueError(
                f"missing market-data staleness thresholds for: {sorted(missing_staleness)}"
            )

        return self
