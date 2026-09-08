from datetime import datetime, timedelta, timezone
from pathlib import Path

from portfolio_agent.config.loader import load_config
from portfolio_agent.news.classifier import DeterministicCausalClassifier
from portfolio_agent.news.dedup import NewsDeduplicator
from portfolio_agent.news.evidence import EvidenceBuilder
from portfolio_agent.news.models import (
    CausalStatus,
    EvidenceStatus,
    NewsItem,
)
from portfolio_agent.news.mock_provider import MockNewsProvider
from portfolio_agent.news.service import NewsIntelligenceService


def config():
    return load_config(Path(__file__).resolve().parents[1] / "config")


def item(item_id, title, body, domain, source_type="major_wire", minutes_ago=5):
    now = datetime(2026, 9, 8, 12, tzinfo=timezone.utc)
    return NewsItem(
        item_id=item_id,
        title=title,
        body=body,
        source_name=domain,
        source_type=source_type,
        domain=domain,
        url=f"https://{domain}/{item_id}",
        published_at=now - timedelta(minutes=minutes_ago),
        ingested_at=now,
        language="en",
        entities=["oil"],
    )


def test_deduplication_removes_near_duplicate():
    d = NewsDeduplicator(config())
    items = [
        item("1", "Oil jumps after Hormuz tanker attack", "Supply disruption reported.", "a.com"),
        item("2", "Oil jumps after Hormuz tanker attack!", "Supply disruption reported.", "b.com"),
    ]
    result = d.deduplicate(items)
    assert len(result) == 1


def test_evidence_requires_independent_domains():
    builder = EvidenceBuilder(config())
    items = [
        item("1", "Oil tanker attack in Hormuz", "Supply disruption.", "a.com"),
        item("2", "Hormuz tanker attack hits oil", "Shipping disruption.", "a.com"),
    ]
    bundle = builder.build("oil", items)
    assert bundle.status == EvidenceStatus.INSUFFICIENT_EVIDENCE


def test_causal_classification_geopolitical_supply_shock():
    cfg = config()
    now = datetime(2026, 9, 8, 12, tzinfo=timezone.utc)
    items = [
        item("1", "Oil rises after tanker attack in Hormuz", "Shipping and supply disruption.", "reuters.com", "major_wire"),
        item("2", "Hormuz disruption lifts crude prices", "Tanker attack disrupts shipping.", "ft.com", "major_financial_media"),
    ]
    bundle = EvidenceBuilder(cfg).build("oil", items)
    result = DeterministicCausalClassifier(cfg).classify(bundle)
    assert bundle.status == EvidenceStatus.SUFFICIENT
    assert result.status == CausalStatus.CLASSIFIED
    assert result.cause == "geopolitical_supply_shock"


def test_service_returns_insufficient_when_too_little_evidence():
    cfg = config()
    now = datetime(2026, 9, 8, 12, tzinfo=timezone.utc)
    provider = MockNewsProvider([
        item("1", "Oil tanker attack in Hormuz", "Supply disruption.", "reuters.com")
    ])
    service = NewsIntelligenceService(
        cfg,
        [provider],
        DeterministicCausalClassifier(cfg),
    )
    _, bundle, classification = service.analyse(query="oil", now=now)
    assert bundle.status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert classification.status == CausalStatus.INSUFFICIENT_EVIDENCE
