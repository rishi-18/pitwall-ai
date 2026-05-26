"""
Celery ingestion tasks.
"""

import os

from celery import Celery

celery_app = Celery(
    "pitwall_ingestion",
    broker=os.getenv(
        "CELERY_BROKER_URL",
        "redis://localhost:6379/1"
    ),
    backend=os.getenv(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/2"
    ),
)


@celery_app.task(
    name="ingestion.check_schema_drift"
)
def check_schema_drift():
    from modules.ingestion.src.quality import (
        run_drift_check
    )

    run_drift_check()
