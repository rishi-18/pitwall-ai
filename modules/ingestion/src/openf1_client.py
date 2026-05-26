"""
OpenF1 API client — polls live session data during race weekends.
"""

import httpx
import structlog

from shared.constants.f1 import (
    OPENF1_POLL_INTERVAL_SECONDS
)

log = structlog.get_logger()

BASE_URL = "https://api.openf1.org/v1"


async def get_latest_session():
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{BASE_URL}/sessions",
            params={"limit": 1}
        )

        resp.raise_for_status()

        data = resp.json()

        return data[0] if data else None


async def get_live_laps(
    session_key: int,
    driver_number: int | None = None
):
    params = {
        "session_key": session_key
    }

    if driver_number:
        params["driver_number"] = driver_number

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            f"{BASE_URL}/laps",
            params=params
        )

        resp.raise_for_status()

        return resp.json()
