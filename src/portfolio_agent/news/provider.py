from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from portfolio_agent.news.models import NewsItem


class NewsProvider(ABC):
    name: str

    @abstractmethod
    def fetch(
        self,
        *,
        query: str,
        since: datetime,
        limit: int,
    ) -> list[NewsItem]:
        ...
