from __future__ import annotations

import json

from sqlalchemy.orm import Session, sessionmaker

from portfolio_agent.market_data.models import MarketSnapshot
from portfolio_agent.persistence.market_models import MarketQuoteRecord, MarketSnapshotRecord


class SqlAlchemyMarketSnapshotRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self.session_factory = session_factory

    def save(self, snapshot: MarketSnapshot) -> None:
        with self.session_factory() as session:
            record = MarketSnapshotRecord(
                snapshot_id=snapshot.snapshot_id,
                created_at=snapshot.created_at,
            )

            for quote in snapshot.quotes.values():
                record.points.append(
                    MarketQuoteRecord(
                        instrument=quote.instrument,
                        provider=quote.provider,
                        timestamp=quote.timestamp,
                        received_at=quote.received_at,
                        last=float(quote.last),
                        bid=float(quote.bid) if quote.bid is not None else None,
                        ask=float(quote.ask) if quote.ask is not None else None,
                        spread_pct=quote.spread_pct,
                        delay_seconds=quote.delay_seconds,
                        quality=quote.quality.value,
                        market_status=quote.market_status.value,
                        currency=quote.currency,
                        metadata_json=json.dumps(quote.metadata, sort_keys=True),
                    )
                )

            session.add(record)
            session.commit()
