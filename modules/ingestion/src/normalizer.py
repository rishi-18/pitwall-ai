"""
Normalizer — converts raw API responses into shared schemas.
"""

import pandas as pd
import structlog

from shared.schemas.telemetry import (
    TelemetryPoint
)

log = structlog.get_logger()

NULL_RATE_THRESHOLD = 0.2


def normalize_fastf1_telemetry(
    df: pd.DataFrame,
    session_key: int
):
    records = []

    for _, row in df.iterrows():
        try:
            records.append(
                TelemetryPoint(
                    session_key=session_key,
                    driver_number=int(
                        row.get(
                            "driver_number",
                            0
                        )
                    ),
                    timestamp=row["Date"],
                    speed=row.get("Speed"),
                    throttle=row.get("Throttle"),
                    brake=bool(
                        row.get(
                            "Brake",
                            False
                        )
                    ),
                    gear=row.get("nGear"),
                    rpm=row.get("RPM"),
                    drs=row.get("DRS"),
                    x=row.get("X"),
                    y=row.get("Y"),
                    z=row.get("Z"),
                )
            )

        except Exception as e:
            log.debug(
                "row_skip",
                error=str(e)
            )

    return records
