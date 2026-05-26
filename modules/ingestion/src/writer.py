"""
Bulk telemetry writer.
"""

import structlog

from sqlalchemy.dialects.postgresql import insert

from shared.utils.db import sync_engine

from shared.models.telemetry import (
    TelemetryPoint as TelemetryModel
)

log = structlog.get_logger()

BATCH_SIZE = 5000


def bulk_insert_telemetry(records):
    if not records:
        return 0

    rows = [
        r.model_dump()
        for r in records
    ]

    inserted = 0

    with sync_engine.begin() as conn:
        for i in range(
            0,
            len(rows),
            BATCH_SIZE
        ):
            batch = rows[i:i + BATCH_SIZE]

            conn.execute(
                insert(TelemetryModel)
                .on_conflict_do_nothing(),
                batch
            )

            inserted += len(batch)

    log.info(
        "bulk_insert_complete",
        rows=inserted
    )

    return inserted
