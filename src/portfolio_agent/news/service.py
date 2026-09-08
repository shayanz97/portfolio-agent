from __future__ import annotations

from datetime import datetime, timedelta, timezone

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.news.classifier import CausalClassifier
from portfolio_agent.news.dedup import NewsDeduplicator
from portfolio_agent.news.evidence import EvidenceBuilder
from portfolio_agent.news.models import CausalClassification, NewsItem
from portfolio_agent.news.provider import NewsProvider


class NewsIntelligenceService:
    def __init__(
        self,
        config: RuntimeConfig,
        providers: list[NewsProvider],
        classifier: CausalClassifier,
    ):
        self.config = config
        self.providers = list(providers)
        self.classifier = classifier
        self.deduplicator = NewsDeduplicator(config)
        self.evidence_builder = EvidenceBuilder(config)

    def analyse(
        self,
        *,
        query: str,
        now: datetime | None = None,
    ) -> tuple[list[NewsItem], object, CausalClassification]:
        now = now or datetime.now(timezone.utc)
        since = now - timedelta(minutes=self.config.news.ingestion.max_age_minutes)
        limit = self.config.news.ingestion.max_items_per_run

        items: list[NewsItem] = []
        for provider in self.providers:
            items.extend(provider.fetch(query=query, since=since, limit=limit))

        items = [
            x for x in items
            if x.language in self.config.news.ingestion.language_allowlist
        ]
        items = self.deduplicator.deduplicate(items)
        items = sorted(items, key=lambda x: x.published_at, reverse=True)[:limit]

        bundle = self.evidence_builder.build(query, items)
        classification = self.classifier.classify(bundle)

        return items, bundle, classification
