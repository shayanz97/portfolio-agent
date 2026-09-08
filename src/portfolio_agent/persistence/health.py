from __future__ import annotations

from sqlalchemy import text


class DatabaseHealthcheck:
    def __init__(self, engine):
        self.engine = engine

    def check(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
