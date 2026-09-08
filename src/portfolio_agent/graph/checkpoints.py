from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path


class CheckpointerConfigurationError(RuntimeError):
    pass


@contextmanager
def build_checkpointer(config, database_url: str):
    backend = config.production.checkpoints.backend

    if backend == "memory":
        from langgraph.checkpoint.memory import InMemorySaver
        yield InMemorySaver()
        return

    if backend == "sqlite":
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
        except ImportError as exc:
            raise CheckpointerConfigurationError(
                "Install langgraph-checkpoint-sqlite for sqlite checkpointing"
            ) from exc

        path = Path(config.production.checkpoints.sqlite_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with SqliteSaver.from_conn_string(str(path)) as saver:
            yield saver
        return

    if backend == "postgres":
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
        except ImportError as exc:
            raise CheckpointerConfigurationError(
                "Install langgraph-checkpoint-postgres for postgres checkpointing"
            ) from exc

        if not database_url.startswith("postgres"):
            raise CheckpointerConfigurationError(
                "production checkpoint backend=postgres requires PostgreSQL DATABASE_URL"
            )

        with PostgresSaver.from_conn_string(database_url) as saver:
            saver.setup()
            yield saver
        return

    raise CheckpointerConfigurationError(f"unsupported checkpoint backend: {backend}")
