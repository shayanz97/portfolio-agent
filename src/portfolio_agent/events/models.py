from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OilShockEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detected_at: datetime
    severity: str
    score: float = Field(ge=0, le=100)
    direction: str
    confirmation_score: float = Field(ge=0, le=1)
    wti_return_1h: float | None = None
    brent_return_1h: float | None = None
    wti_return_4h: float | None = None
    brent_return_4h: float | None = None
    wti_zscore: float | None = None
    brent_zscore: float | None = None
    explanation: str
