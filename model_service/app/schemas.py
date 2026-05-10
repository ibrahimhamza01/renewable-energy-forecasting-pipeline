from __future__ import annotations

from pydantic import BaseModel, Field


class LiveAnalyzeRequest(BaseModel):
    station_id: str = Field(..., examples=["KMSP"])


class HealthResponse(BaseModel):
    status: str
    service: str
