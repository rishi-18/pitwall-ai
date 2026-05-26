"""
FastF1 client ï¿½ loads historical F1 sessions and extracts telemetry + lap data.
"""

import os
import fastf1
import pandas as pd
import structlog

from pathlib import Path

log = structlog.get_logger()

CACHE_DIR = Path(
    os.getenv(
        "FASTF1_CACHE_DIR",
        "/tmp/fastf1_cache"
    )
)

CACHE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

fastf1.Cache.enable_cache(str(CACHE_DIR))


def load_session(
    year: int,
    round_number: int,
    session_type: str
):
    log.info(
        "loading_session",
        year=year,
        round=round_number,
        type=session_type
    )

    session = fastf1.get_session(
        year,
        round_number,
        session_type
    )

    session.load(
        telemetry=True,
        weather=True,
        messages=True
    )

    log.info(
        "session_loaded",
        laps=len(session.laps)
    )

    return session


def extract_telemetry(session):
    frames = []

    for driver in session.drivers:
        try:
            tel = session.laps.pick_driver(driver).get_telemetry()

            tel["driver_number"] = int(driver)

            tel["session_key"] = session.session_info.get(
                "Key",
                0
            )

            frames.append(tel)

        except Exception as e:
            log.warning(
                "telemetry_extract_failed",
                driver=driver,
                error=str(e)
            )

    if not frames:
        return pd.DataFrame()

    return pd.concat(
        frames,
        ignore_index=True
    )


def extract_laps(session):
    laps = session.laps.copy()

    laps["session_key"] = session.session_info.get(
        "Key",
        0
    )

    return laps
