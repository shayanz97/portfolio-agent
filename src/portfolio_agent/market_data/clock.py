from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from portfolio_agent.config.models import AssetConfig, MarketSessionConfig, RuntimeConfig
from portfolio_agent.domain.enums import MarketStatus


def _parse_time(value: str) -> time:
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


class MarketClock:
    def __init__(self, config: RuntimeConfig):
        self.config = config

    def status_for(self, asset: AssetConfig, at: datetime) -> MarketStatus:
        session = self.config.market_data.sessions[asset.session]
        return self._status_for_session(session, at)

    def _status_for_session(
        self,
        session: MarketSessionConfig,
        at: datetime,
    ) -> MarketStatus:
        local = at.astimezone(ZoneInfo(session.timezone))

        if session.kind == "always_open":
            return MarketStatus.OPEN

        if session.kind == "always_available":
            return MarketStatus.AVAILABLE

        if local.weekday() >= 5:
            return MarketStatus.CLOSED

        current = local.time().replace(tzinfo=None)

        if session.kind == "weekday_session":
            pre = _parse_time(session.premarket_open)
            regular_open = _parse_time(session.regular_open)
            regular_close = _parse_time(session.regular_close)
            after = _parse_time(session.afterhours_close)

            if pre <= current < regular_open:
                return MarketStatus.PRE_MARKET
            if regular_open <= current < regular_close:
                return MarketStatus.OPEN
            if regular_close <= current < after:
                return MarketStatus.AFTER_HOURS
            return MarketStatus.CLOSED

        if session.kind == "nearly_24h_weekday":
            break_start = _parse_time(session.daily_break_start)
            break_end = _parse_time(session.daily_break_end)

            if break_start <= current < break_end:
                return MarketStatus.BREAK
            return MarketStatus.OPEN

        return MarketStatus.UNKNOWN
