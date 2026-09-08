from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.news.models import (
    CausalClassification,
    CausalStatus,
    EvidenceBundle,
    EvidenceStatus,
)


class CausalClassifier(ABC):
    @abstractmethod
    def classify(self, bundle: EvidenceBundle) -> CausalClassification:
        ...


class DeterministicCausalClassifier(CausalClassifier):
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def classify(self, bundle: EvidenceBundle) -> CausalClassification:
        if bundle.status == EvidenceStatus.INSUFFICIENT_EVIDENCE:
            return CausalClassification(
                status=CausalStatus.INSUFFICIENT_EVIDENCE,
                cause="unknown",
                confidence=0.0,
                evidence_item_ids=[x.item_id for x in bundle.items],
                explanation=bundle.explanation,
            )

        if bundle.status == EvidenceStatus.CONFLICTING_EVIDENCE:
            return CausalClassification(
                status=CausalStatus.CONFLICTING_EVIDENCE,
                cause="unknown",
                confidence=max(0.0, 1.0 - bundle.conflicting_score),
                evidence_item_ids=[x.item_id for x in bundle.items],
                explanation=bundle.explanation,
            )

        weighted_causes = Counter()
        total = 0.0

        for item in bundle.items:
            if not item.cause_hint:
                continue
            score = item.weight * item.relevance
            weighted_causes[item.cause_hint] += score
            total += score

        if not weighted_causes or total == 0:
            return CausalClassification(
                status=CausalStatus.UNKNOWN,
                cause="unknown",
                confidence=0.0,
                evidence_item_ids=[x.item_id for x in bundle.items],
                explanation="No supported cause hint found in sufficient evidence.",
            )

        cause, score = weighted_causes.most_common(1)[0]
        confidence = min(1.0, score / total)

        if cause not in self.config.news.classification.allowed_causes:
            cause = "unknown"

        status = (
            CausalStatus.CLASSIFIED
            if confidence >= self.config.news.classification.minimum_confidence
            else CausalStatus.UNKNOWN
        )

        inflationary = None
        growth_negative = None
        duration = None

        if cause in {
            "geopolitical_supply_shock",
            "opec_supply_change",
            "refinery_outage",
            "shipping_disruption",
        }:
            inflationary = True
            growth_negative = True
            duration = "short_to_medium"
        elif cause == "demand_destruction":
            inflationary = False
            growth_negative = True
            duration = "short_to_medium"
        elif cause == "demand_growth":
            inflationary = True
            growth_negative = False
            duration = "medium"

        return CausalClassification(
            status=status,
            cause=cause,
            confidence=confidence,
            inflationary=inflationary,
            growth_negative=growth_negative,
            expected_duration=duration,
            evidence_item_ids=[x.item_id for x in bundle.items],
            explanation=f"Cause={cause}, confidence={confidence:.2f}",
        )
