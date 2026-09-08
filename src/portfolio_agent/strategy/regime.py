from __future__ import annotations

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.domain.enums import MarketRegime
from portfolio_agent.events.models import OilShockEvent
from portfolio_agent.features.models import FeatureSet
from portfolio_agent.strategy.models import RegimeAssessment


def _clip(value: float) -> float:
    return max(-1.0, min(1.0, value))


class MarketRegimeEngine:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def assess(
        self,
        *,
        equities: FeatureSet | None = None,
        crypto: FeatureSet | None = None,
        vix: FeatureSet | None = None,
        dxy: FeatureSet | None = None,
        yields: FeatureSet | None = None,
        oil_event: OilShockEvent | None = None,
    ) -> RegimeAssessment:
        w = self.config.regime.weights

        eq = self._return_component(equities, invert=False)
        cr = self._return_component(crypto, invert=False)
        vol = self._return_component(vix, invert=True)
        dollar = self._return_component(dxy, invert=True)
        yld = self._return_component(yields, invert=True)

        oil = 0.0
        if oil_event is not None:
            magnitude = oil_event.score / 100.0
            oil = -magnitude if oil_event.direction == "UP" else magnitude

        components = {
            "equities": eq,
            "crypto": cr,
            "volatility": vol,
            "dollar": dollar,
            "yields": yld,
            "oil_event": oil,
        }

        score = _clip(
            eq * w.equities
            + cr * w.crypto
            + vol * w.volatility
            + dollar * w.dollar
            + yld * w.yields
            + oil * w.oil_event
        )

        regime = self._classify(score, oil_event, yields)
        confidence = min(1.0, abs(score) + (0.15 if oil_event else 0.0))

        return RegimeAssessment(
            regime=regime,
            score=score,
            confidence=confidence,
            components=components,
            explanation=f"{regime.value} regime with score {score:.3f}",
        )

    def _return_component(self, features: FeatureSet | None, invert: bool) -> float:
        if features is None:
            return 0.0
        value = features.returns.get("4h")
        if value is None:
            value = features.returns.get("1h", 0.0)
        normalized = _clip(value / 0.05)
        return -normalized if invert else normalized

    def _classify(self, score, oil_event, yields):
        t = self.config.regime.thresholds
        inflation = self.config.regime.inflation_shock

        yields_up = False
        if yields is not None:
            y = yields.returns.get("4h", yields.returns.get("1h", 0.0))
            yields_up = y > 0

        oil_ok = (
            oil_event is not None
            and oil_event.direction == "UP"
            and oil_event.score >= inflation.min_oil_score
        )

        if score <= t.crisis:
            return MarketRegime.CRISIS
        if score <= t.inflation_shock:
            if (not inflation.require_oil_event or oil_ok) and (
                not inflation.require_yields_up or yields_up
            ):
                return MarketRegime.INFLATION_SHOCK
        if score <= t.risk_off:
            return MarketRegime.RISK_OFF
        if score >= t.risk_on:
            return MarketRegime.RISK_ON
        return MarketRegime.NEUTRAL
