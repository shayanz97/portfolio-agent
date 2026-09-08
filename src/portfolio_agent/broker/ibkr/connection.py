from __future__ import annotations
import time
from portfolio_agent.broker.ibkr.facade import IbkrFacade
from portfolio_agent.broker.models import BrokerConnectionState
from portfolio_agent.config.models import RuntimeConfig

class IbkrConnectionManager:
    def __init__(self, config: RuntimeConfig, facade: IbkrFacade, use_gateway: bool = True):
        self.config, self.facade, self.use_gateway = config, facade, use_gateway
        self.state = BrokerConnectionState.DISCONNECTED

    def _port(self):
        c = self.config.broker.ibkr.connection
        paper = self.config.environment in {"development", "paper", "shadow"}
        return (
            c.paper_gateway_port if paper and self.use_gateway else
            c.paper_tws_port if paper else
            c.live_gateway_port if self.use_gateway else
            c.live_tws_port
        )

    def connect(self):
        c = self.config.broker.ibkr.connection
        self.state = BrokerConnectionState.CONNECTING
        last_error = None
        for attempt in range(c.reconnect_attempts + 1):
            try:
                self.facade.connect(c.host, self._port(), c.client_id, c.connect_timeout_seconds)
                if not self.facade.is_connected():
                    raise RuntimeError("facade reported disconnected")
                self.state = BrokerConnectionState.CONNECTED
                return
            except Exception as exc:
                last_error = exc
                self.state = BrokerConnectionState.DEGRADED
                if attempt < c.reconnect_attempts:
                    time.sleep(c.reconnect_backoff_seconds)
        self.state = BrokerConnectionState.DISCONNECTED
        raise RuntimeError(f"IBKR connection failed: {last_error}")

    def disconnect(self):
        self.facade.disconnect()
        self.state = BrokerConnectionState.DISCONNECTED

    def healthcheck(self):
        ok = self.facade.is_connected()
        self.state = BrokerConnectionState.CONNECTED if ok else BrokerConnectionState.DEGRADED
        return ok
