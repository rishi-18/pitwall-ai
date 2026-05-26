"""SQLAlchemy ORM models for TimescaleDB telemetry tables."""
from datetime import datetime
from sqlalchemy import Integer, Float, Boolean, String, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from shared.models.base import Base


class TelemetryPoint(Base):
    __tablename__ = "telemetry"

    # Composite PK required by TimescaleDB hypertable on timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, primary_key=True)
    session_key: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    driver_number: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)

    speed: Mapped[float | None] = mapped_column(Float)
    throttle: Mapped[float | None] = mapped_column(Float)
    brake: Mapped[bool | None] = mapped_column(Boolean)
    gear: Mapped[int | None] = mapped_column(Integer)
    rpm: Mapped[float | None] = mapped_column(Float)
    drs: Mapped[int | None] = mapped_column(Integer)
    x: Mapped[float | None] = mapped_column(Float)
    y: Mapped[float | None] = mapped_column(Float)
    z: Mapped[float | None] = mapped_column(Float)


class LapData(Base):
    __tablename__ = "laps"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_key: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    driver_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lap_number: Mapped[int] = mapped_column(Integer, nullable=False)
    lap_duration: Mapped[float | None] = mapped_column(Float)
    sector1_duration: Mapped[float | None] = mapped_column(Float)
    sector2_duration: Mapped[float | None] = mapped_column(Float)
    sector3_duration: Mapped[float | None] = mapped_column(Float)
    compound: Mapped[str | None] = mapped_column(String(20))
    tyre_age_laps: Mapped[int | None] = mapped_column(Integer)
    is_pit_out_lap: Mapped[bool] = mapped_column(Boolean, default=False)


class SessionInfo(Base):
    __tablename__ = "sessions"

    session_key: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_name: Mapped[str] = mapped_column(String(100))
    session_type: Mapped[str] = mapped_column(String(10))
    year: Mapped[int] = mapped_column(Integer)
    circuit_key: Mapped[int] = mapped_column(Integer)
    circuit_short_name: Mapped[str] = mapped_column(String(50))
    date_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    gmt_offset: Mapped[str] = mapped_column(String(10))