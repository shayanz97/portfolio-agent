import logging
from pathlib import Path


def configure_logging(level: int = logging.INFO) -> None:
    Path("logs").mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/portfolio_agent.log", encoding="utf-8"),
        ],
        force=True,
    )
