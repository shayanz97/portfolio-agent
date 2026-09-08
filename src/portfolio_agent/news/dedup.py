from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher

from portfolio_agent.config.models import RuntimeConfig
from portfolio_agent.news.models import NewsItem


def normalize_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value.strip().lower())
    value = re.sub(r"[^a-z0-9äöüß\s-]", "", value)
    return value


def content_hash(item: NewsItem) -> str:
    canonical = f"{normalize_text(item.title)}\n{normalize_text(item.body)}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class NewsDeduplicator:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def deduplicate(self, items: list[NewsItem]) -> list[NewsItem]:
        threshold = self.config.news.deduplication.title_similarity_threshold
        seen_hashes: set[str] = set()
        kept: list[NewsItem] = []

        for item in sorted(items, key=lambda x: x.published_at):
            item_hash = item.content_hash or content_hash(item)

            if (
                self.config.news.deduplication.content_hash_enabled
                and item_hash in seen_hashes
            ):
                continue

            title = normalize_text(item.title)
            duplicate = False
            for existing in kept:
                similarity = SequenceMatcher(
                    None,
                    title,
                    normalize_text(existing.title),
                ).ratio()
                if similarity >= threshold:
                    duplicate = True
                    break

            if duplicate:
                continue

            seen_hashes.add(item_hash)
            kept.append(item.model_copy(update={"content_hash": item_hash}))

        return kept
