import structlog

from datetime import datetime

from shared.constants.f1 import (
    OPENF1_POLL_INTERVAL_SECONDS
)

log = structlog.get_logger()


async def poll_and_publish(
    session_key: int
):

    from modules.ingestion.src.openf1_client import (
        get_live_laps
    )

    from shared.utils.redis import (
        get_redis
    )

    from modules.realtime.src.events import (
        LapEvent
    )

    redis = await get_redis()

    laps = await get_live_laps(
        session_key
    )

    for lap in laps:

        driver = lap.get("driver_number")

        lap_num = lap.get("lap_number")

        dedup_key = (
            f"dedup:lap:"
            f"{session_key}:"
            f"{driver}"
        )

        last_seen = await redis.get(
            dedup_key
        )

        if (
            last_seen
            and int(last_seen) >= lap_num
        ):
            continue

        event = LapEvent(
            session_key=session_key,
            driver_number=driver,
            lap_number=lap_num,
            lap_duration=lap.get(
                "lap_duration"
            ),
            position=lap.get("position"),
            compound=lap.get("compound"),
            tyre_age=lap.get(
                "stint_lap_count"
            ),
            timestamp=datetime.utcnow(),
        )

        await redis.set(
            dedup_key,
            lap_num,
            ex=7200
        )

        await redis.publish(
            f"live:session:{session_key}",
            event.model_dump_json()
        )

        log.debug(
            "event_published",
            driver=driver,
            lap=lap_num
        )
