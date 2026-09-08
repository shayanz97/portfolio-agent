from __future__ import annotations

from datetime import datetime

from portfolio_agent.news.models import NewsItem
from portfolio_agent.news.provider import NewsProvider


class MockNewsProvider(NewsProvider):
    name = "mock"

    def __init__(self, items: list[NewsItem]):
        self.items = list(items)

    def fetch(self, *, query: str, since: datetime, limit: int) -> list[NewsItem]:
        q = query.lower()
        result = []
        for item in self.items:
            haystack = f"{item.title} {item.body} {' '.join(item.entities)}".lower()
            if item.published_at >= since and (not q or q in haystack):
                result.append(item)
        return result[:limit]
