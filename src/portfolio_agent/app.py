from portfolio_agent.config.loader import config_hash, load_config
from portfolio_agent.config.settings import AppSettings
from portfolio_agent.logging_setup import configure_logging


def main() -> None:
    configure_logging()

    config = load_config()
    settings = AppSettings()

    print("Portfolio Agent Foundation")
    print(f"Environment: {config.environment}")
    print(f"Config version: {config.version}")
    print(f"Config hash: {config_hash(config)[:12]}")
    print(f"Broker: {config.execution.broker}")
    print(f"IBKR host: {settings.ibkr_host}:{settings.ibkr_port}")


if __name__ == "__main__":
    main()
