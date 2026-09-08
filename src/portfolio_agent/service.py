from __future__ import annotations

import argparse
import sys

from portfolio_agent.config.loader import load_config
from portfolio_agent.config.settings import AppSettings
from portfolio_agent.logging_setup import configure_logging
from portfolio_agent.observability import JsonEventLogger
from portfolio_agent.persistence.db import Base, create_session_factory
from portfolio_agent.persistence.health import DatabaseHealthcheck


def bootstrap_database(settings: AppSettings):
    engine, session_factory = create_session_factory(settings.database_url)
    return engine, session_factory


def healthcheck(config, settings) -> int:
    engine, _ = bootstrap_database(settings)
    ok = DatabaseHealthcheck(engine).check()

    logger = JsonEventLogger()
    logger.emit(
        "service_healthcheck",
        database_ok=ok,
        environment=config.environment,
        config_version=config.version,
    )

    return 0 if ok else 2


def main(argv=None):
    parser = argparse.ArgumentParser(prog="portfolio-agent")
    parser.add_argument(
        "command",
        choices=["healthcheck", "init-db", "show-config"],
    )
    args = parser.parse_args(argv)

    configure_logging()
    config = load_config()
    settings = AppSettings()

    if args.command == "healthcheck":
        return healthcheck(config, settings)

    if args.command == "init-db":
        engine, _ = bootstrap_database(settings)
        Base.metadata.create_all(engine)
        print("Database schema initialized.")
        return 0

    if args.command == "show-config":
        print(f"version={config.version}")
        print(f"environment={config.environment}")
        print(f"checkpoint_backend={config.production.checkpoints.backend}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
