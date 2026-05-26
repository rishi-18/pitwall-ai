from datetime import datetime

from typing import Literal

from pydantic import BaseModel


class LapEvent(BaseModel):

    event_type: Literal["lap"] = "lap"

    session_key: int

    driver_number: int

    lap_number: int

    lap_duration: float | None

    position: int | None

    compound: str | None

    tyre_age: int | None

    timestamp: datetime


class PitEvent(BaseModel):

    event_type: Literal["pit"] = "pit"

    session_key: int

    driver_number: int

    lap_number: int

    pit_duration: float | None

    timestamp: datetime


class SafetyCarEvent(BaseModel):

    event_type: Literal["safety_car"] = "safety_car"

    session_key: int

    category: str

    message: str

    timestamp: datetime


class SessionStateEvent(BaseModel):

    event_type: Literal["session_state"] = "session_state"

    session_key: int

    status: str

    timestamp: datetime


LiveEvent = (
    LapEvent
    | PitEvent
    | SafetyCarEvent
    | SessionStateEvent
)
