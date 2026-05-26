"""Sessions router — session listing and telemetry retrieval."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from shared.utils.db import get_async_db

router = APIRouter()


@router.get("/")
async def list_sessions(
    year: int = Query(2024, ge=2018, le=2026),
    session_type: str = Query("R"),
    db=Depends(get_async_db),
):
    result = await db.execute(
        text("SELECT * FROM sessions WHERE year = :year AND session_type = :type"),
        {"year": year, "type": session_type}
    )
    rows = result.mappings().all()
    return {"year": year, "session_type": session_type, "sessions": [dict(r) for r in rows]}


@router.get("/telemetry/summary")
async def telemetry_summary(
    session_key: int = Query(...),
    db=Depends(get_async_db),
):
    """Per-driver telemetry summary for a session."""
    result = await db.execute(text("""
        SELECT
            driver_number,
            COUNT(*) as data_points,
            ROUND(AVG(speed)::numeric, 1) as avg_speed,
            MAX(speed) as top_speed,
            ROUND(AVG(throttle)::numeric, 1) as avg_throttle,
            MIN(timestamp) as session_start,
            MAX(timestamp) as session_end
        FROM telemetry
        WHERE session_key = :session_key
        GROUP BY driver_number
        ORDER BY driver_number
    """), {"session_key": session_key})
    rows = result.mappings().all()
    return {"session_key": session_key, "drivers": [dict(r) for r in rows]}


@router.get("/{session_key}/laps")
async def get_laps(
    session_key: int,
    driver_number: int | None = None,
    db=Depends(get_async_db),
):
    """Get lap data for a session, optionally filtered by driver."""
    if driver_number:
        result = await db.execute(
            text("SELECT * FROM laps WHERE session_key = :key AND driver_number = :driver ORDER BY lap_number"),
            {"key": session_key, "driver": driver_number}
        )
    else:
        result = await db.execute(
            text("SELECT * FROM laps WHERE session_key = :key ORDER BY driver_number, lap_number"),
            {"key": session_key}
        )
    rows = result.mappings().all()
    return {"session_key": session_key, "laps": [dict(r) for r in rows]}


@router.get("/{session_key}/telemetry/{driver_number}")
async def get_telemetry(
    session_key: int,
    driver_number: int,
    downsample: int = Query(10, description="Take every Nth point"),
    db=Depends(get_async_db),
):
    """
    Get telemetry for a driver in a session.
    Downsampled for API response size — default every 10th point.
    """
    result = await db.execute(text("""
        SELECT
            timestamp, speed, throttle, brake,
            gear, rpm, drs, x, y, z
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (ORDER BY timestamp) as rn
            FROM telemetry
            WHERE session_key = :key
            AND driver_number = :driver
        ) sub
        WHERE rn % :downsample = 0
        ORDER BY timestamp
    """), {"key": session_key, "driver": driver_number, "downsample": downsample})
    rows = result.mappings().all()
    return {
        "session_key": session_key,
        "driver_number": driver_number,
        "downsample_factor": downsample,
        "points": len(rows),
        "telemetry": [dict(r) for r in rows]
    }