"""Pydantic v2 schemas for telemetry data â€” shared across ingestion, API, and ML modules."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TelemetryPoint(BaseModel):
    session_key: int
    driver_number: int
    timestamp: datetime

    speed: Optional[float] = Field(None, ge=0, le=400)
    throttle: Optional[float] = Field(None, ge=0, le=110)
    brake: Optional[bool] = None
    gear: Optional[int] = Field(None, ge=0, le=255)
    rpm: Optional[float] = Field(None, ge=0)
    drs: Optional[int] = None

    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


class LapData(BaseModel):
    session_key: int
    driver_number: int
    lap_number: int

    lap_duration: Optional[float] = None
    sector1_duration: Optional[float] = None
    sector2_duration: Optional[float] = None
    sector3_duration: Optional[float] = None

    compound: Optional[str] = None
    tyre_age_laps: Optional[int] = None

    pit_in_time: Optional[datetime] = None
    pit_out_time: Optional[datetime] = None

    is_pit_out_lap: bool = False


class SessionInfo(BaseModel):
    session_key: int
    session_name: str
    session_type: str

    year: int
    circuit_key: int
    circuit_short_name: str

    date_start: datetime
    date_end: Optional[datetime] = None

    gmt_offset: str