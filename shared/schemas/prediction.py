"""Pydantic v2 schemas for ML model inputs/outputs."""

from typing import List
from pydantic import BaseModel, Field


class PitStrategyInput(BaseModel):
    session_key: int
    driver_number: int
    current_lap: int

    tyre_compound: str
    tyre_age: int

    gap_ahead: float = Field(
        description="Gap to car ahead in seconds"
    )

    gap_behind: float = Field(
        description="Gap to car behind in seconds"
    )

    total_laps: int
    track_temp: float
    air_temp: float


class PitStrategyOutput(BaseModel):
    driver_number: int
    current_lap: int

    recommended_pit_lap: int

    confidence: float = Field(
        ge=0,
        le=1
    )

    pit_window: List[int] = Field(
        description="[earliest_lap, latest_lap]"
    )

    predicted_position_delta: float
    model_version: str


class AnomalyResult(BaseModel):
    session_key: int
    driver_number: int
    lap_number: int

    anomaly_score: float
    is_anomaly: bool

    anomalous_channels: List[str]