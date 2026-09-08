from __future__ import annotations

from collections import Counter

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.news.models import (
    EvidenceBundle,
    EvidenceItem,
    EvidenceStatus,
    NewsItem,
)


POSITIVE_TERMS = {
    "attack", "disruption", "cut", "shortage", "outage",
    "closure", "sanction", "tanker", "hormuz", "supply shock",
}
NEGATIVE_TERMS = {
    "ceasefire", "reopen", "restart", "increase supply",
    "inventory build", "demand weakness", "surplus",
}


class EvidenceBuilder:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def build(self, query: str, items: list[NewsItem]) -> EvidenceBundle:
        evidence: list[EvidenceItem] = []

        for item in items:
            relevance = self._relevance(query, item)
            if relevance <= 0:
                continue

            source_weight = self.config.news.source_weights.get(
                item.source_type,
                self.config.news.source_weights.get("unknown", 0.4),
            )
            stance = self._stance(item)
            cause_hint = self._cause_hint(item)

            evidence.append(
                EvidenceItem(
                    item_id=item.item_id,
                    title=item.title,
                    domain=item.domain,
                    source_type=item.source_type,
                    weight=source_weight,
                    relevance=relevance,
                    stance=stance,
                    published_at=item.published_at,
                    cause_hint=cause_hint,
                )
            )

        weighted_score = sum(x.weight * x.relevance for x in evidence)
        domains = len({x.domain for x in evidence})

        stance_weights = Counter()
        for item in evidence:
            stance_weights[item.stance] += item.weight * item.relevance

        total_stance = sum(stance_weights.values()) or 1.0
        conflicting_score = 0.0
        if len([v for v in stance_weights.values() if v > 0]) > 1:
            ranked = sorted(stance_weights.values(), reverse=True)
            conflicting_score = ranked[1] / total_stance

        status = EvidenceStatus.SUFFICIENT
        reasons = []

        ecfg = self.config.news.evidence
        if len(evidence) < ecfg.minimum_items:
            status = EvidenceStatus.INSUFFICIENT_EVIDENCE
            reasons.append("not enough evidence items")
        if weighted_score < ecfg.minimum_weighted_score:
            status = EvidenceStatus.INSUFFICIENT_EVIDENCE
            reasons.append("weighted evidence score below threshold")
        if domains < ecfg.require_independent_domains:
            status = EvidenceStatus.INSUFFICIENT_EVIDENCE
            reasons.append("not enough independent domains")

        if conflicting_score >= ecfg.conflicting_score_threshold:
            status = EvidenceStatus.CONFLICTING_EVIDENCE
            reasons.append("evidence stances materially conflict")

        explanation = (
            "; ".join(reasons)
            if reasons
            else f"{len(evidence)} evidence items from {domains} independent domains"
        )

        return EvidenceBundle(
            status=status,
            query=query,
            items=evidence,
            weighted_score=weighted_score,
            independent_domains=domains,
            conflicting_score=conflicting_score,
            explanation=explanation,
        )

    def _relevance(self, query: str, item: NewsItem) -> float:
        q = query.lower().strip()
        if not q:
            return 1.0

        text = f"{item.title} {item.body} {' '.join(item.entities)}".lower()
        tokens = [token for token in q.split() if token]
        if not tokens:
            return 1.0

        matches = sum(1 for token in tokens if token in text)
        return min(1.0, matches / max(1, len(tokens)))

    def _stance(self, item: NewsItem) -> str:
        text = f"{item.title} {item.body}".lower()
        pos = sum(term in text for term in POSITIVE_TERMS)
        neg = sum(term in text for term in NEGATIVE_TERMS)

        if pos > neg:
            return "SUPPLY_TIGHTENING"
        if neg > pos:
            return "SUPPLY_EASING"
        return "NEUTRAL"

    def _cause_hint(self, item: NewsItem) -> str | None:
        text = f"{item.title} {item.body}".lower()

        if "hormuz" in text or "tanker" in text or "attack" in text:
            return "geopolitical_supply_shock"
        if "opec" in text and ("cut" in text or "increase" in text):
            return "opec_supply_change"
        if "inventory" in text or "eia" in text:
            return "inventory_surprise"
        if "refinery" in text and ("outage" in text or "shutdown" in text):
            return "refinery_outage"
        if "demand" in text and ("weak" in text or "fall" in text):
            return "demand_destruction"
        if "demand" in text and ("strong" in text or "rise" in text):
            return "demand_growth"
        if "dollar" in text or "currency" in text:
            return "currency_move"

        return None
