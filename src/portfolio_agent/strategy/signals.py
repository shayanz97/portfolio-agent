from __future__ import annotations

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.domain.enums import AssetSignal
from portfolio_agent.events.models import OilShockEvent
from portfolio_agent.features.models import FeatureSet
from portfolio_agent.strategy.models import RegimeAssessment, SignalAssessment


def _clip(value: float) -> float:
    return max(-1.0, min(1.0, value))


class AssetSignalEngine:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def assess(
        self,
        instrument: str,
        features: FeatureSet,
        regime: RegimeAssessment,
        *,
        oil_event: OilShockEvent | None = None,
        news_score: float = 0.0,
        technical_score: float | None = None,
    ) -> SignalAssessment:
        w = self.config.signal_weights

        macro = regime.score
        momentum = features.momentum_score or 0.0

        if technical_score is None:
            technical_score = momentum

        volatility = 0.0
        if features.realized_volatility is not None:
            threshold = self.config.technical_defaults.high_volatility_threshold
            volatility = -_clip(features.realized_volatility / threshold)

        event = 0.0
        if oil_event is not None:
            magnitude = oil_event.score / 100.0
            event = -magnitude if oil_event.direction == "UP" else magnitude

        score = _clip(
            macro * w.macro
            + momentum * w.momentum
            + technical_score * w.technical
            + volatility * w.volatility
            + event * w.event
            + _clip(news_score) * w.news
        )

        signal = self._classify(score)
        confidence = min(1.0, abs(score) + 0.25)

        return SignalAssessment(
            instrument=instrument,
            score=score,
            signal=signal,
            confidence=confidence,
            components={
                "macro": macro,
                "momentum": momentum,
                "technical": technical_score,
                "volatility": volatility,
                "event": event,
                "news": _clip(news_score),
            },
            explanation=f"{instrument}: {signal.value} ({score:.3f})",
        )

    def _classify(self, score):
        t = self.config.signal_thresholds
        if score >= t.strong_buy:
            return AssetSignal.STRONG_BUY
        if score >= t.buy:
            return AssetSignal.BUY
        if score <= t.exit:
            return AssetSignal.EXIT
        if score <= t.reduce:
            return AssetSignal.REDUCE
        return AssetSignal.HOLD
