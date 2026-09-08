from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class NewsModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvidenceStatus(StrEnum):
    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"


class CausalStatus(StrEnum):
    CLASSIFIED = "CLASSIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    UNKNOWN = "UNKNOWN"


class NewsItem(NewsModel):
    item_id: str
    title: str
    body: str
    source_name: str
    source_type: str = "unknown"
    domain: str
    url: str | None = None
    published_at: datetime
    ingested_at: datetime
    language: str = "en"
    entities: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    content_hash: str | None = None


class EvidenceItem(NewsModel):
    item_id: str
    title: str
    domain: str
    source_type: str
    weight: float = Field(ge=0)
    relevance: float = Field(ge=0, le=1)
    stance: str
    published_at: datetime
    cause_hint: str | None = None


class EvidenceBundle(NewsModel):
    status: EvidenceStatus
    query: str
    items: list[EvidenceItem] = Field(default_factory=list)
    weighted_score: float = 0.0
    independent_domains: int = 0
    conflicting_score: float = 0.0
    explanation: str


class CausalClassification(NewsModel):
    status: CausalStatus
    cause: str
    confidence: float = Field(ge=0, le=1)
    inflationary: bool | None = None
    growth_negative: bool | None = None
    expected_duration: str | None = None
    evidence_item_ids: list[str] = Field(default_factory=list)
    explanation: str
