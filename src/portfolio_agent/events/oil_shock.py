from __future__ import annotations

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.events.models import OilShockEvent
from portfolio_agent.features.models import FeatureSet


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class OilShockDetector:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def detect(self, wti: FeatureSet, brent: FeatureSet) -> OilShockEvent | None:
        if not self.config.oil_shock.enabled:
            return None

        w1, b1 = wti.returns.get("1h"), brent.returns.get("1h")
        w4, b4 = wti.returns.get("4h"), brent.returns.get("4h")

        pairs = [(w1, b1), (w4, b4)]
        confirmations = []
        for left, right in pairs:
            if left is None or right is None:
                continue
            if left * right <= 0:
                confirmations.append(0.0)
            else:
                largest = max(abs(left), abs(right))
                confirmations.append(
                    1.0 if largest == 0 else min(abs(left), abs(right)) / largest
                )

        confirmation = sum(confirmations) / len(confirmations) if confirmations else 0.0

        if (
            self.config.oil_shock.confirmation.require_wti_brent
            and confirmation < self.config.oil_shock.confirmation.minimum_confirmation_score
        ):
            return None

        one_high = self.config.oil_shock.windows["1h"].high_pct / 100
        four_high = self.config.oil_shock.windows["4h"].high_pct / 100

        normalized_moves = [
            _clamp(abs(value) / threshold)
            for value, threshold in ((w1, one_high), (b1, one_high), (w4, four_high), (b4, four_high))
            if value is not None
        ]
        return_component = sum(normalized_moves) / len(normalized_moves) if normalized_moves else 0

        zvals = [abs(x) for x in (wti.return_zscore, brent.return_zscore) if x is not None]
        high_z = self.config.oil_shock.volatility_adjusted.high_zscore
        z_component = _clamp((sum(zvals) / len(zvals)) / high_z) if zvals else 0

        vols = [x for x in (wti.realized_volatility, brent.realized_volatility) if x is not None]
        volatility_component = _clamp(sum(vols) / len(vols)) if vols else 0

        weights = self.config.features.oil_shock_scoring
        score = 100 * (
            return_component * weights.return_weight
            + z_component * weights.zscore_weight
            + confirmation * weights.confirmation_weight
            + volatility_component * weights.volatility_weight
        )
        score = round(score, 2)

        severity = (
            "EXTREME" if score >= 85 else
            "HIGH" if score >= 70 else
            "SIGNIFICANT" if score >= 50 else
            "WATCH" if score >= 30 else
            "NORMAL"
        )
        if severity == "NORMAL":
            return None

        avg_move = sum(x for x in (w4, b4) if x is not None) / len([x for x in (w4, b4) if x is not None])
        direction = "UP" if avg_move > 0 else "DOWN" if avg_move < 0 else "FLAT"

        return OilShockEvent(
            detected_at=max(wti.as_of, brent.as_of),
            severity=severity,
            score=score,
            direction=direction,
            confirmation_score=confirmation,
            wti_return_1h=w1,
            brent_return_1h=b1,
            wti_return_4h=w4,
            brent_return_4h=b4,
            wti_zscore=wti.return_zscore,
            brent_zscore=brent.return_zscore,
            explanation=f"{severity} oil shock, {direction}, score={score:.2f}",
        )
